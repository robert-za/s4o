from typing import Any, Dict, List, Type

from faker.providers import address
from fastapi.exceptions import HTTPException
from psycopg2.errors import UniqueViolation  # type: ignore[import-untyped]
from pydantic import IPvAnyAddress, ValidationError
from requests import HTTPError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from app.logger import logger
from app.models.geolocation_db import GeolocationDB
from app.schemas.geolocation import GeolocationValidator, GeolocationValidatorWithAddress
from app.services.ipstack_service import ip_stack_service


class GeolocationService:
    @classmethod
    def _get_by_ip(cls, address: str, db_session: Session) -> List[GeolocationDB]:
        return db_session.query(GeolocationDB).filter_by(ip=address).all()

    @classmethod
    def _get_by_address(cls, address: str, db_session: Session) -> List[GeolocationDB]:
        return db_session.query(GeolocationDB).filter_by(address=address).all()

    @staticmethod
    def _create_entry(data: dict, db_session: Session) -> GeolocationDB | Type[GeolocationDB]:
        existing_entry = db_session.query(GeolocationDB).filter_by(ip=data["ip"], address=data.get("address")).first()

        if not existing_entry:
            entry = GeolocationDB(**data)
            db_session.add(entry)
            db_session.commit()
            db_session.refresh(entry)
            return entry

        return existing_entry

    @classmethod
    def _is_ip(cls, address: str) -> bool:
        try:
            IPvAnyAddress(address)  # type: ignore[operator]
            return True
        except ValueError:
            return False

    @classmethod
    def fetch_from_local_database(cls, address: str, db_session: Session) -> List[Dict[str, Any]]:
        is_ip = cls._is_ip(address)
        try:
            db_entries = cls._get_by_ip(address, db_session) if is_ip else cls._get_by_address(address, db_session)
            if db_entries:
                return [GeolocationValidator.model_validate(entry.as_dict()).model_dump() for entry in db_entries]  # type: ignore[call-arg]

            return []
        except SQLAlchemyError:
            logger.error(f"Local database error: {address}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"message": "Service temporarily unavailable. Please come back later."},
            )

    @staticmethod
    def fetch_from_remote_service(address: str) -> Dict[str, Any]:
        try:
            resp, _ = ip_stack_service.get_geolocation_data(address)
        except HTTPError as e:
            logger.error(f"Error processing geolocation query for {str(address)}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"message": "Service temporarily unavailable. Please come back later."},
            )

        if "error" in resp.keys():
            error_details = resp.get("error")
            logger.error(f"Error processing geolocation query for {str(address)}: {error_details}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": f"Something went wrong. Error details: {error_details.get('info') if error_details else 'Something went wrong.'}. Please come back later."
                },
            )

        return resp

    @classmethod
    def validate_data(
        cls, data: Dict[str, Any], address: str
    ) -> GeolocationValidator | GeolocationValidatorWithAddress:
        try:
            validated_data = (
                GeolocationValidatorWithAddress.model_validate({**data, "address": address})
                if not cls._is_ip(address)
                else GeolocationValidator.model_validate(data)
            )
            return validated_data
        except ValidationError as e:
            # this is an edge case for e.g. 0.0.0.0 where fields are null
            logger.error(f"Error processing geolocation query for {str(address)}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Data cannot be provided for {address}."},
            )

    @classmethod
    def save_remote_data_in_local_database(
        cls, data: GeolocationValidator | GeolocationValidatorWithAddress, db_session: Session
    ) -> GeolocationValidator | GeolocationValidatorWithAddress | None:
        try:
            db_entry = cls._create_entry(data.model_dump(), db_session).as_dict()  # type: ignore[call-arg]
            return cls.validate_data(db_entry, data.ip)
        except IntegrityError as err:
            # it handles a scenario where at first we queried by IP and stored without address
            # and then we query by address and there is IP collision, so I just update the old record with URL
            if isinstance(err.orig, UniqueViolation):
                db_session.rollback()
                db_entry = cls._get_by_ip(data.ip, db_session)[0]
                db_entry.address = data.address  # type: ignore[union-attr,attr-defined]
                db_session.add(db_entry)
                db_session.commit()
                db_session.refresh(db_entry)
                return cls.validate_data(db_entry.as_dict(), data.address)  # type: ignore[union-attr,arg-type, attr-defined]
            else:
                db_session.rollback()
                logger.error(f"Error processing geolocation query for {str(address)}: {str(err)}")
            return None

    @classmethod
    def delete(cls, address: str, db_session: Session) -> int:
        is_ip = cls._is_ip(address)

        try:
            db_entries = cls._get_by_ip(address, db_session) if is_ip else cls._get_by_address(address, db_session)

            if not db_entries:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"message": f"Address {address} does not exist in the database."},
                )

            deleted_count = len(db_entries)
            for db_entry in db_entries:
                db_session.delete(db_entry)
            db_session.commit()
            return deleted_count

        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f"Database error while deleting entry: {str(e)}")
            return 0

    @classmethod
    def save_in_local_database(cls, data: GeolocationValidator, db_session: Session) -> bool | None:
        try:
            _ = cls._create_entry(data.model_dump(), db_session)
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error processing geolocation query for {str(data.ip)}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"message": str(e)})

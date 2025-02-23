import re
from typing import Any, ClassVar, Set

import pycountry
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field, IPvAnyAddress, field_validator
from starlette import status


class IpOrAddressValidator(BaseModel):
    address: str = Field(..., examples=["127.0.0.1", "www.wp.pl"])

    URL_WITH_WWW_REGEX: ClassVar[re.Pattern] = re.compile(r"^(www\.)[\w\-]+(\.[\w\-]+)+[/#?]?.*$", re.IGNORECASE)

    @field_validator("address")
    @classmethod
    def validator(cls, value: Any) -> str:
        try:
            IPvAnyAddress(value)  # type: ignore[operator]
            return value
        except ValueError:
            pass

        if cls.URL_WITH_WWW_REGEX.match(value):
            return value

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="IP must be a valid IPv4/IPv6 address or a valid domain name. Try replacing 'http://, https:// by www.'",
        )


class GeolocationValidator(BaseModel):
    ip: str = Field(..., examples=["127.0.0.1", "www.wp.pl"])
    continent_code: str = Field(..., examples=["EU"])
    continent_name: str = Field(..., examples=["Europe"])
    country_code: str = Field(..., examples=["DE"])
    country_name: str = Field(..., examples=["Germany"])
    region_code: str = Field(..., examples=["BE"], min_length=2, max_length=3)
    region_name: str = Field(..., examples=["Berlin"])
    city: str = Field(..., examples=["Berlin"])
    zip: str = Field(..., examples=["10178"])
    latitude: float = Field(..., examples=[52.51919937133789], ge=(-90), le=90)
    longitude: float = Field(..., examples=[13.406100273132324], ge=(-180), le=180)

    VALID_CONTINENT_CODES: ClassVar[Set[str]] = {
        "AF",
        "AN",
        "AS",
        "EU",
        "NA",
        "OC",
        "SA",
    }

    URL_WITH_WWW_REGEX: ClassVar[re.Pattern] = re.compile(r"^(www\.)[\w\-]+(\.[\w\-]+)+[/#?]?.*$", re.IGNORECASE)

    @field_validator("ip")
    @classmethod
    def validator(cls, value: Any) -> str:
        try:
            IPvAnyAddress(value)  # type: ignore[operator]
            return value
        except ValueError:
            pass

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="IP must be a valid IPv4/IPv6 address.",
        )

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, value: str) -> str:
        if not pycountry.countries.get(alpha_2=value.upper()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid country code: {value}"
            )
        return value.upper()

    @field_validator("continent_code")
    @classmethod
    def validate_continent_code(cls, value: str) -> str:
        if value.upper() not in cls.VALID_CONTINENT_CODES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid continent code: {value}"
            )
        return value.upper()


class GeolocationValidatorWithAddress(GeolocationValidator):
    address: str | None = Field(..., examples=["www.onet.pl"])

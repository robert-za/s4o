from typing import Any, Dict

import pytest
from unittest import mock
from fastapi import HTTPException
from requests import HTTPError
from sqlalchemy.orm import Session
from app.services.geolocation_service import GeolocationService
from app.models.geolocation_db import GeolocationDB
from app.schemas.geolocation import GeolocationValidator
from app.services.ipstack_service import ip_stack_service


class TestGeolocationService:
    @pytest.fixture
    def mock_db_session(self) -> mock.MagicMock:
        return mock.MagicMock(Session)

    @pytest.fixture
    def mock_ipstack_service(self) -> mock.MagicMock:
        return mock.MagicMock(ip_stack_service)

    @pytest.fixture
    def valid_geolocation_data(self) -> Dict[str, Any]:
        return {
            "ip": "127.0.0.1",
            "continent_code": "EU",
            "continent_name": "Europe",
            "country_code": "DE",
            "country_name": "Germany",
            "region_code": "BE",
            "region_name": "Berlin",
            "city": "Berlin",
            "zip": "10178",
            "latitude": 52.51919937133789,
            "longitude": 13.406100273132324,
        }

    @mock.patch("app.services.geolocation_service.logger")
    def test_fetch_from_local_database(self, mock_logger: mock.Mock, mock_db_session: mock.MagicMock, valid_geolocation_data: Dict[str, Any]) -> None:
        # given
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = [GeolocationDB(**valid_geolocation_data)]

        # when
        result = GeolocationService.fetch_from_local_database("127.0.0.1", mock_db_session)

        # then
        assert len(result) == 1
        assert result[0]["ip"] == "127.0.0.1"
        assert result[0]["continent_code"] == "EU"

    @mock.patch("app.services.geolocation_service.logger")
    def test_fetch_from_local_database_no_entry(self, mock_logger: mock.Mock, mock_db_session: mock.MagicMock) -> None:
        # given
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = []

        # when
        result = GeolocationService.fetch_from_local_database("127.0.0.1", mock_db_session)

        # then
        assert result == []

    @mock.patch("app.services.geolocation_service.ip_stack_service.get_geolocation_data")
    def test_fetch_from_remote_service_success(self, mock_get_geolocation_data: mock.Mock, mock_ipstack_service: mock.MagicMock) -> None:
        # given
        mock_get_geolocation_data.return_value = {"ip": "127.0.0.1", "continent_code": "EU", "country_code": "DE"}, 200

        # when
        result = GeolocationService.fetch_from_remote_service("127.0.0.1")

        # then
        assert result["ip"] == "127.0.0.1"
        assert result["continent_code"] == "EU"

    @mock.patch("app.services.geolocation_service.ip_stack_service.get_geolocation_data")
    def test_fetch_from_remote_service_error(self, mock_get_geolocation_data: mock.Mock, mock_ipstack_service: mock.MagicMock) -> None:
        # given
        mock_get_geolocation_data.side_effect = HTTPError("Error with remote service")

        # when/then
        with pytest.raises(HTTPException):
            GeolocationService.fetch_from_remote_service("127.0.0.1")

    @mock.patch("app.services.geolocation_service.logger")
    def test_validate_data(self, mock_logger: mock.Mock, valid_geolocation_data: Dict[str, Any]) -> None:
        # when
        validated_data = GeolocationService.validate_data(valid_geolocation_data, "127.0.0.1")

        # then
        assert isinstance(validated_data, GeolocationValidator)
        assert validated_data.ip == "127.0.0.1"

    @mock.patch("app.services.geolocation_service.logger")
    def test_save_remote_data_in_local_database(self, mock_logger: mock.Mock, mock_db_session: mock.MagicMock, valid_geolocation_data: Dict[str, Any]) -> None:
        #given
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        # when
        result = GeolocationService.save_remote_data_in_local_database(GeolocationValidator(**valid_geolocation_data), mock_db_session)

        # then
        assert isinstance(result, GeolocationValidator)
        assert result.ip == valid_geolocation_data["ip"]

    @mock.patch("app.services.geolocation_service.logger")
    def test_delete(self, mock_logger: mock.Mock, mock_db_session: mock.MagicMock) -> None:
        # given
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = [GeolocationDB(ip="127.0.0.1")]

        # when
        deleted_count = GeolocationService.delete("127.0.0.1", mock_db_session)

        # then
        assert deleted_count == 1
        mock_db_session.delete.assert_called_once()

    @mock.patch("app.services.geolocation_service.logger")
    def test_delete_no_entry(self, mock_logger: mock.Mock, mock_db_session: mock.MagicMock) -> None:
        # given
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = []

        # when/then
        with pytest.raises(HTTPException):
            GeolocationService.delete("127.0.0.1", mock_db_session)

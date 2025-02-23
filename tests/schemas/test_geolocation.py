import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from starlette import status

from app.schemas.geolocation import IpOrAddressValidator, GeolocationValidator


class TestIpOrAddressValidator:
    def test_valid_ip(self) -> None:
        # given
        valid_ip = "172.16.31.10"

        # when/then
        assert IpOrAddressValidator(address=valid_ip)

    def test_valid_url(self) -> None:
        valid_url = "www.google.com"

        # when/then
        assert IpOrAddressValidator(address=valid_url)

    def test_url_with_https(self) -> None:
        almost_valid_url = "https://www.google.com"

        # when/then
        with pytest.raises(HTTPException) as exc:
            assert IpOrAddressValidator(address=almost_valid_url)

        assert exc.value.detail == "IP must be a valid IPv4/IPv6 address or a valid domain name. Try replacing 'http://, https:// by www.'"
        assert exc.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGeolocationValidator:
    def test_valid_geolocation_data(self) -> None:
        # given/when
        geolocation_data = GeolocationValidator(
            ip="127.0.0.1",
            continent_code="EU",
            continent_name="Europe",
            country_code="DE",
            country_name="Germany",
            region_code="BE",
            region_name="Berlin",
            city="Berlin",
            zip="10178",
            latitude=52.51919937133789,
            longitude=13.406100273132324,
        )

        # then
        assert geolocation_data.ip == "127.0.0.1"
        assert geolocation_data.continent_code == "EU"
        assert geolocation_data.country_code == "DE"
        assert geolocation_data.region_code == "BE"
        assert geolocation_data.latitude == 52.51919937133789
        assert geolocation_data.longitude == 13.406100273132324

    def test_invalid_country_code(self) -> None:
        # when/then
        with pytest.raises(HTTPException) as exc:
            GeolocationValidator(
                ip="127.0.0.1",
                continent_code="EU",
                continent_name="Europe",
                country_code="ZZ",
                country_name="Germany",
                region_code="BE",
                region_name="Berlin",
                city="Berlin",
                zip="10178",
                latitude=52.51919937133789,
                longitude=13.406100273132324,
            )

        assert exc.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.value.detail == "Invalid country code: ZZ"

    def test_invalid_continent_code(self) -> None:
        # given/when
        with pytest.raises(HTTPException) as exc:
            GeolocationValidator(
                ip="127.0.0.1",
                continent_code="XX",
                continent_name="Unknown Continent",
                country_code="DE",
                country_name="Germany",
                region_code="BE",
                region_name="Berlin",
                city="Berlin",
                zip="10178",
                latitude=52.51919937133789,
                longitude=13.406100273132324,
            )

        # then
        assert exc.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.value.detail == "Invalid continent code: XX"

    def test_invalid_latitude(self) -> None:
        # given/when/then
        with pytest.raises(ValidationError):
            GeolocationValidator(
                ip="127.0.0.1",
                continent_code="EU",
                continent_name="Europe",
                country_code="DE",
                country_name="Germany",
                region_code="BE",
                region_name="Berlin",
                city="Berlin",
                zip="10178",
                latitude=100.0,
                longitude=13.406100273132324,
            )

    def test_invalid_longitude(self) -> None:
        # given/when/then
        with pytest.raises(ValidationError):
            GeolocationValidator(
                ip="127.0.0.1",
                continent_code="EU",
                continent_name="Europe",
                country_code="DE",
                country_name="Germany",
                region_code="BE",
                region_name="Berlin",
                city="Berlin",
                zip="10178",
                latitude=52.51919937133789,
                longitude=200.0,
            )

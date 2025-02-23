import pytest
import faker

from app.models.geolocation_db import GeolocationDB

fake = faker.Faker()

class TestGeolocationDB:
    @pytest.fixture
    def geolocation_instance(self) -> GeolocationDB:
        return GeolocationDB(
            ip=fake.ipv4(),
            address=fake.domain_name(),
            continent_code=fake.random_element(["AF", "AN", "AS", "EU", "NA", "OC", "SA"]),
            continent_name=fake.word(),
            country_code=fake.country_code(),
            country_name=fake.country(),
            region_code=fake.state_abbr(),
            region_name=fake.state(),
            city=fake.city(),
            zip=fake.zipcode(),
            latitude=fake.latitude(),
            longitude=fake.longitude(),
        )

    def test_as_dict(self, geolocation_instance: GeolocationDB) -> None:
        # when
        result = geolocation_instance.as_dict()

        # then
        assert isinstance(result, dict)
        assert "id" not in result
        assert result["ip"] == geolocation_instance.ip
        assert result["address"] == geolocation_instance.address

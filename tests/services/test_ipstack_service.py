import json
from unittest import mock

import pytest
from requests import Response

from app.services.ipstack_service import IPStackService


class TestIPStackService:
    @pytest.fixture
    def ipstack_service(self) -> IPStackService:
        ipstack_service = IPStackService()
        ipstack_service.endpoint_url = "http://www.test.com"
        ipstack_service._access_key = "key"
        ipstack_service._fields = ["elephant", "somersault"]
        return ipstack_service

    @mock.patch('app.services.ipstack_service.IPStackService._construct_url')
    @mock.patch('app.services.ipstack_service.requests.get')
    def test_get_geolocation_data(
            self,
            mock_requests_get: mock.Mock,
            mock_construct_url: mock.Mock,
            ipstack_service: IPStackService
    ) -> None:
        # given
        address = "www.elephant.pl"
        mock_data = {
            "ip": "127.0.0.1",
            "city": "Localhost",
            "country_name": "Country"
        }
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = bytes(json.dumps(mock_data), "utf-8")
        mock_requests_get.return_value = mock_response

        # when
        data, status = ipstack_service.get_geolocation_data(address)

        # then
        assert data == mock_data
        assert status == 200

    def test_construct_url(self, ipstack_service: IPStackService) -> None:
        # given
        address = "www.elephant.pl"

        # when
        url = ipstack_service._construct_url(address)

        # then
        assert url == 'http://www.test.com/www.elephant.pl?access_key=key&fields=elephant%2Csomersault'
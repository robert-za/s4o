import os
import urllib.parse
from typing import Any, Dict

import requests

from app.schemas.geolocation import GeolocationValidator


class IPStackService:
    def __init__(self) -> None:
        self.endpoint_url = os.environ.get("IPSTACK_ENDPOINT_URL")
        self._fields = list(GeolocationValidator.model_fields.keys())
        self._access_key = os.environ.get("IPSTACK_API_KEY")

        if not self.endpoint_url:
            raise EnvironmentError("IPSTACK_BASE_URL in environment variable is not set")
        if not self._access_key:
            raise EnvironmentError("IPSTACK_API_KEY in environment variable is not set")

    def get_geolocation_data(self, address: str) -> tuple[Dict[str, Any], int]:
        url = self._construct_url(address)
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json(), resp.status_code

    def _construct_url(self, address: str, fields: list[str] | None = None) -> str:
        if fields is None:
            fields = self._fields
        query_params = {
            "access_key": self._access_key,
            "fields": ",".join(fields),
        }
        return f"{self.endpoint_url}/{urllib.parse.quote(address)}?{urllib.parse.urlencode(query_params)}"


ip_stack_service = IPStackService()

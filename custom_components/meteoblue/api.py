"""Meteoblue API client."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import PACKAGE_ENDPOINTS

BASE_URL = "https://my.meteoblue.com/packages"


class MeteoblueApiClient:
    """Simple Meteoblue API client."""

    def __init__(self, hass, api_key: str) -> None:
        self._hass = hass
        self._api_key = api_key
        self._session = async_get_clientsession(hass)

    async def async_fetch_package(
        self,
        package: str,
        latitude: float,
        longitude: float,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        endpoint = PACKAGE_ENDPOINTS[package]
        params: dict[str, Any] = {
            "apikey": self._api_key,
            "lat": latitude,
            "lon": longitude,
            "format": "json",
        }
        if extra_params:
            params.update(extra_params)

        url = f"{BASE_URL}/{endpoint}"
        response = await self._session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return await response.json()

"""Data update coordinator for Meteoblue."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import MeteoblueApiClient
from .const import (
    CONF_DAILY_HOUR,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PACKAGES,
    CONF_PVPRO_PARAMS,
    CONF_UPDATE_INTERVAL_HOURS,
    CONF_UPDATE_MODE,
    UPDATE_MODE_DAILY,
)


class MeteoblueCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry) -> None:
        self._entry = entry
        self._client = MeteoblueApiClient(hass, entry.data["api_key"])
        interval = timedelta(hours=entry.options.get(CONF_UPDATE_INTERVAL_HOURS, 1))
        super().__init__(hass, None, name="meteoblue", update_interval=interval)

    async def _async_update_data(self) -> dict[str, Any]:
        options = self._entry.options
        update_mode = options.get(CONF_UPDATE_MODE)
        if update_mode == UPDATE_MODE_DAILY:
            daily_hour = int(options.get(CONF_DAILY_HOUR, 6))
            now = dt_util.now()
            if now.hour != daily_hour:
                return self.data or {}

        lat = self._entry.data[CONF_LATITUDE]
        lon = self._entry.data[CONF_LONGITUDE]
        packages = self._entry.options.get(CONF_PACKAGES, self._entry.data[CONF_PACKAGES])
        pvpro_params = self._entry.options.get(CONF_PVPRO_PARAMS, {})

        result: dict[str, Any] = {}
        for package in packages:
            extra = pvpro_params if package == "pvpro" else None
            try:
                result[package] = await self._client.async_fetch_package(package, lat, lon, extra)
            except Exception as err:
                raise UpdateFailed(f"Error fetching package {package}: {err}") from err

        result["_meta"] = {"last_update": datetime.utcnow().isoformat()}
        return result

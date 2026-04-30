"""Weather platform for Meteoblue."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.weather import Forecast, WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

CONDITION_MAP = {
    "clear": "sunny",
    "pclear": "partlycloudy",
    "cloudy": "cloudy",
    "overcast": "cloudy",
    "rain": "rainy",
    "lightrain": "rainy",
    "heavyrain": "pouring",
    "snow": "snowy",
    "fog": "fog",
    "thunderstorm": "lightning-rainy",
}


def _first_available(data: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        current: Any = data
        ok = True
        for part in path:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                ok = False
                break
        if ok:
            return current
    return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MeteoblueWeatherEntity(coordinator, entry)], True)


class MeteoblueWeatherEntity(CoordinatorEntity, WeatherEntity):
    _attr_has_entity_name = True
    _attr_name = "Weather"
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_weather"

    @property
    def _basic(self) -> dict[str, Any]:
        return self.coordinator.data.get("basic", {})

    @property
    def condition(self) -> str | None:
        pictocode = _first_available(self._basic, ("current", "pictocode"), ("data_current", "pictocode"))
        if not pictocode:
            return None
        return CONDITION_MAP.get(str(pictocode).lower(), None)

    @property
    def native_temperature(self) -> float | None:
        return _first_available(self._basic, ("current", "temperature",), ("data_current", "temperature",))

    @property
    def native_pressure(self) -> float | None:
        return _first_available(self._basic, ("current", "sealevelpressure",), ("data_current", "sealevelpressure",))

    @property
    def humidity(self) -> int | None:
        value = _first_available(self._basic, ("current", "relativehumidity",), ("data_current", "relativehumidity",))
        return int(value) if value is not None else None

    @property
    def native_wind_speed(self) -> float | None:
        return _first_available(self._basic, ("current", "windspeed",), ("data_current", "windspeed",))

    @property
    def wind_bearing(self) -> float | None:
        return _first_available(self._basic, ("current", "winddirection",), ("data_current", "winddirection",))

    async def async_forecast_daily(self) -> list[Forecast] | None:
        data_day = self._basic.get("data_day", {})
        times = data_day.get("time") or data_day.get("datetime") or []
        tmax = data_day.get("temperature_max") or []
        tmin = data_day.get("temperature_min") or []
        precip = data_day.get("precipitation") or []
        wind = data_day.get("windspeed_mean") or []
        uv = data_day.get("uvindex") or []

        if not times:
            return None

        forecasts: list[Forecast] = []
        for i, dt_value in enumerate(times[:7]):
            forecasts.append(
                Forecast(
                    datetime=str(dt_value),
                    native_temperature=tmax[i] if i < len(tmax) else None,
                    native_templow=tmin[i] if i < len(tmin) else None,
                    precipitation=precip[i] if i < len(precip) else None,
                    native_wind_speed=wind[i] if i < len(wind) else None,
                    uv_index=uv[i] if i < len(uv) else None,
                )
            )
        return forecasts

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        data_1h = self._basic.get("data_1h", {})
        times = data_1h.get("time") or data_1h.get("datetime") or []
        temp = data_1h.get("temperature") or []
        precip = data_1h.get("precipitation") or []
        wind = data_1h.get("windspeed") or []

        if not times:
            return None

        forecasts: list[Forecast] = []
        for i, dt_value in enumerate(times[:48]):
            forecasts.append(
                Forecast(
                    datetime=str(dt_value),
                    native_temperature=temp[i] if i < len(temp) else None,
                    precipitation=precip[i] if i < len(precip) else None,
                    native_wind_speed=wind[i] if i < len(wind) else None,
                )
            )
        return forecasts

    @property
    def extra_state_attributes(self):
        return {"source_package": "basic", "last_update": self.coordinator.data.get("_meta", {}).get("last_update")}

"""Sensor platform for Meteoblue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfIrradiance,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


@dataclass(frozen=True)
class MeteoblueSensorDescription:
    key: str
    name: str
    path: tuple[str, ...]
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT


PACKAGE_SENSORS: dict[str, list[MeteoblueSensorDescription]] = {
    "basic": [
        MeteoblueSensorDescription("temperature", "Temperature", ("current", "temperature"), UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
        MeteoblueSensorDescription("relative_humidity", "Relative Humidity", ("current", "relativehumidity"), PERCENTAGE, SensorDeviceClass.HUMIDITY),
        MeteoblueSensorDescription("precipitation", "Precipitation", ("current", "precipitation"), "mm", SensorDeviceClass.PRECIPITATION),
        MeteoblueSensorDescription("wind_speed", "Wind Speed", ("current", "windspeed"), UnitOfSpeed.KILOMETERS_PER_HOUR, SensorDeviceClass.WIND_SPEED),
        MeteoblueSensorDescription("uv_index", "UV Index", ("current", "uvindex"), None, None),
        MeteoblueSensorDescription("sunshine_minutes", "Sunshine Minutes", ("current", "sunshinetime"), "min", None),
    ],
    "current": [
        MeteoblueSensorDescription("temperature", "Temperature", ("data_current", "temperature"), UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
        MeteoblueSensorDescription("feels_like", "Feels Like", ("data_current", "felttemperature"), UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
        MeteoblueSensorDescription("wind_speed", "Wind Speed", ("data_current", "windspeed"), UnitOfSpeed.KILOMETERS_PER_HOUR, SensorDeviceClass.WIND_SPEED),
        MeteoblueSensorDescription("wind_direction", "Wind Direction", ("data_current", "winddirection"), DEGREE, None),
    ],
    "clouds": [
        MeteoblueSensorDescription("total_cloud_cover", "Cloud Cover", ("data_current", "totalcloudcover"), PERCENTAGE, None),
        MeteoblueSensorDescription("low_cloud_cover", "Low Cloud Cover", ("data_current", "lowcloudcover"), PERCENTAGE, None),
        MeteoblueSensorDescription("mid_cloud_cover", "Mid Cloud Cover", ("data_current", "midcloudcover"), PERCENTAGE, None),
        MeteoblueSensorDescription("high_cloud_cover", "High Cloud Cover", ("data_current", "highcloudcover"), PERCENTAGE, None),
    ],
    "pvpro": [
        MeteoblueSensorDescription("pv_power", "PV Power", ("data_current", "pvpower"), UnitOfPower.WATT, SensorDeviceClass.POWER),
        MeteoblueSensorDescription("global_irradiance", "Global Irradiance", ("data_current", "globalirradiance"), UnitOfIrradiance.WATTS_PER_SQUARE_METER, SensorDeviceClass.IRRADIANCE),
        MeteoblueSensorDescription("yield_today", "Yield Today", ("data_day", "yield"), UnitOfEnergy.WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL),
    ],
}


def _get_path_value(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    packages = entry.options.get("packages", entry.data["packages"])
    entities: list[SensorEntity] = []

    for package in packages:
        for description in PACKAGE_SENSORS.get(package, []):
            entities.append(MeteoblueMetricSensor(coordinator, entry, package, description))

        entities.append(MeteobluePackageRawSensor(coordinator, entry, package))

    async_add_entities(entities)


class MeteoblueMetricSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry, package: str, description: MeteoblueSensorDescription) -> None:
        super().__init__(coordinator)
        self._package = package
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{package}_{description.key}"
        self._attr_name = f"Meteoblue {package.upper()} {description.name}"
        self._attr_native_unit_of_measurement = description.unit
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class

    @property
    def native_value(self):
        package_data = self.coordinator.data.get(self._package, {})
        return _get_path_value(package_data, self.entity_description.path)

    @property
    def available(self) -> bool:
        package_data = self.coordinator.data.get(self._package, {})
        return _get_path_value(package_data, self.entity_description.path) is not None


class MeteobluePackageRawSensor(CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:database"
    _attr_entity_category = None

    def __init__(self, coordinator, entry: ConfigEntry, package: str) -> None:
        super().__init__(coordinator)
        self._package = package
        self._attr_unique_id = f"{entry.entry_id}_{package}_raw"
        self._attr_name = f"Meteoblue {package.upper()} Raw"

    @property
    def native_value(self):
        return "ok" if self.coordinator.data.get(self._package) else None

    @property
    def extra_state_attributes(self):
        return {
            "package": self._package,
            "payload": self.coordinator.data.get(self._package),
            "meta": self.coordinator.data.get("_meta", {}),
        }

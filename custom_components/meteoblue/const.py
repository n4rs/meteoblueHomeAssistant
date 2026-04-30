"""Constants for Meteoblue integration."""

from __future__ import annotations

DOMAIN = "meteoblue"
PLATFORMS = ["sensor", "weather"]

CONF_API_KEY = "api_key"
CONF_USE_HA_LOCATION = "use_ha_location"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_PACKAGES = "packages"
CONF_UPDATE_MODE = "update_mode"
CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"
CONF_DAILY_HOUR = "daily_hour"
CONF_PVPRO_PARAMS = "pvpro_params"

UPDATE_MODE_HOURLY = "hourly"
UPDATE_MODE_DAILY = "daily"

PACKAGE_BASIC = "basic"
PACKAGE_CURRENT = "current"
PACKAGE_CLOUDS = "clouds"
PACKAGE_PVPRO = "pvpro"

PACKAGE_LABELS = {
    PACKAGE_BASIC: "Basic",
    PACKAGE_CURRENT: "Current Conditions",
    PACKAGE_CLOUDS: "Clouds",
    PACKAGE_PVPRO: "PV PRO",
}

PACKAGE_ENDPOINTS = {
    PACKAGE_BASIC: "basic-1h_basic-day",
    PACKAGE_CURRENT: "current",
    PACKAGE_CLOUDS: "clouds-1h",
    PACKAGE_PVPRO: "pvpro-1h",
}

DEFAULT_INTERVAL_HOURS = 1
DEFAULT_DAILY_HOUR = 6

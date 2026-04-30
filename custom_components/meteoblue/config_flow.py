"""Config flow for Meteoblue."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from aiohttp import ClientError

from .const import *
from .api import MeteoblueApiClient


class MeteoblueConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            lat = user_input.get(CONF_LATITUDE)
            lon = user_input.get(CONF_LONGITUDE)
            if user_input[CONF_USE_HA_LOCATION]:
                lat = self.hass.config.latitude
                lon = self.hass.config.longitude

            data = {
                CONF_API_KEY: user_input[CONF_API_KEY],
                CONF_USE_HA_LOCATION: user_input[CONF_USE_HA_LOCATION],
                CONF_LATITUDE: lat,
                CONF_LONGITUDE: lon,
                CONF_PACKAGES: user_input[CONF_PACKAGES],
            }

            pvpro_params = {}
            if PACKAGE_PVPRO in user_input[CONF_PACKAGES]:
                if user_input.get(CONF_PVPRO_KWP) is not None:
                    pvpro_params["kwp"] = user_input[CONF_PVPRO_KWP]
                if user_input.get(CONF_PVPRO_SLOPE) is not None:
                    pvpro_params["slope"] = user_input[CONF_PVPRO_SLOPE]
                if user_input.get(CONF_PVPRO_FACING) is not None:
                    pvpro_params["facing"] = user_input[CONF_PVPRO_FACING]
                if user_input.get(CONF_PVPRO_TRACKER):
                    pvpro_params["tracker"] = user_input[CONF_PVPRO_TRACKER]
                if user_input.get(CONF_PVPRO_POWER_EFFICIENCY) is not None:
                    pvpro_params["power_efficiency"] = user_input[CONF_PVPRO_POWER_EFFICIENCY]

            try:
                client = MeteoblueApiClient(self.hass, user_input[CONF_API_KEY])
                first_package = user_input[CONF_PACKAGES][0]
                await client.async_fetch_package(first_package, lat, lon)
            except ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(title="Meteoblue", data=data, options={
                CONF_PACKAGES: user_input[CONF_PACKAGES],
                CONF_UPDATE_MODE: user_input[CONF_UPDATE_MODE],
                CONF_UPDATE_INTERVAL_HOURS: user_input[CONF_UPDATE_INTERVAL_HOURS],
                CONF_DAILY_HOUR: user_input[CONF_DAILY_HOUR],
                CONF_PVPRO_PARAMS: pvpro_params,
            })

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_USE_HA_LOCATION, default=True): bool,
                vol.Optional(CONF_LATITUDE, default=self.hass.config.latitude): vol.Coerce(float),
                vol.Optional(CONF_LONGITUDE, default=self.hass.config.longitude): vol.Coerce(float),
                vol.Required(CONF_PACKAGES, default=[PACKAGE_BASIC, PACKAGE_CURRENT]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": k, "label": v}
                            for k, v in PACKAGE_LABELS.items()
                        ],
                        multiple=True,
                        mode="dropdown",
                    )
                ),
                vol.Required(CONF_UPDATE_MODE, default=UPDATE_MODE_HOURLY): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[UPDATE_MODE_HOURLY, UPDATE_MODE_DAILY],
                        mode="dropdown",
                    )
                ),
                vol.Required(CONF_UPDATE_INTERVAL_HOURS, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
                vol.Required(CONF_DAILY_HOUR, default=6): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                vol.Optional(CONF_PVPRO_KWP): vol.Coerce(float),
                vol.Optional(CONF_PVPRO_SLOPE): vol.All(vol.Coerce(int), vol.Range(min=0, max=90)),
                vol.Optional(CONF_PVPRO_FACING): vol.All(vol.Coerce(int), vol.Range(min=0, max=360)),
                vol.Optional(CONF_PVPRO_TRACKER): str,
                vol.Optional(CONF_PVPRO_POWER_EFFICIENCY): vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MeteoblueOptionsFlowHandler(config_entry)


class MeteoblueOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            pvpro_params = {}
            if user_input.get(CONF_PVPRO_KWP) is not None:
                pvpro_params["kwp"] = user_input.pop(CONF_PVPRO_KWP)
            if user_input.get(CONF_PVPRO_SLOPE) is not None:
                pvpro_params["slope"] = user_input.pop(CONF_PVPRO_SLOPE)
            if user_input.get(CONF_PVPRO_FACING) is not None:
                pvpro_params["facing"] = user_input.pop(CONF_PVPRO_FACING)
            if user_input.get(CONF_PVPRO_TRACKER):
                pvpro_params["tracker"] = user_input.pop(CONF_PVPRO_TRACKER)
            if user_input.get(CONF_PVPRO_POWER_EFFICIENCY) is not None:
                pvpro_params["power_efficiency"] = user_input.pop(CONF_PVPRO_POWER_EFFICIENCY)
            user_input[CONF_PVPRO_PARAMS] = pvpro_params
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_PACKAGES, default=self.config_entry.options.get(CONF_PACKAGES, self.config_entry.data[CONF_PACKAGES])): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": k, "label": v}
                            for k, v in PACKAGE_LABELS.items()
                        ],
                        multiple=True,
                        mode="dropdown",
                    )
                ),
                vol.Required(CONF_UPDATE_MODE, default=self.config_entry.options.get(CONF_UPDATE_MODE, UPDATE_MODE_HOURLY)): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=[UPDATE_MODE_HOURLY, UPDATE_MODE_DAILY], mode="dropdown")
                ),
                vol.Required(CONF_UPDATE_INTERVAL_HOURS, default=self.config_entry.options.get(CONF_UPDATE_INTERVAL_HOURS, 1)): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
                vol.Required(CONF_DAILY_HOUR, default=self.config_entry.options.get(CONF_DAILY_HOUR, 6)): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                vol.Optional(CONF_PVPRO_KWP, default=self.config_entry.options.get(CONF_PVPRO_PARAMS, {}).get("kwp")): vol.Coerce(float),
                vol.Optional(CONF_PVPRO_SLOPE, default=self.config_entry.options.get(CONF_PVPRO_PARAMS, {}).get("slope")): vol.All(vol.Coerce(int), vol.Range(min=0, max=90)),
                vol.Optional(CONF_PVPRO_FACING, default=self.config_entry.options.get(CONF_PVPRO_PARAMS, {}).get("facing")): vol.All(vol.Coerce(int), vol.Range(min=0, max=360)),
                vol.Optional(CONF_PVPRO_TRACKER, default=self.config_entry.options.get(CONF_PVPRO_PARAMS, {}).get("tracker", "")): str,
                vol.Optional(CONF_PVPRO_POWER_EFFICIENCY, default=self.config_entry.options.get(CONF_PVPRO_PARAMS, {}).get("power_efficiency")): vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

from __future__ import annotations

import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant.helpers import storage

from .api import PIDDeparturesApi
from .const import CONF_API_KEY, CONF_STOP_ID, CONF_PLATFORM, DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = "pid_departures_global"
STORAGE_VERSION = 1


class PIDDeparturesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        store = storage.Store(self.hass, STORAGE_VERSION, STORAGE_KEY)
        stored_data = await store.async_load() or {}

        api_key_exists = CONF_API_KEY in stored_data

        if user_input is not None:
            stop_id = user_input[CONF_STOP_ID]
            platform = user_input.get(CONF_PLATFORM)

            api_key = stored_data.get(CONF_API_KEY)

            if not api_key_exists:
                api_key = user_input[CONF_API_KEY]
                await store.async_save({CONF_API_KEY: api_key})

            api = PIDDeparturesApi(api_key)

            try:
                await api.get_stop_departures(stop_id)
            except Exception as err:
                _LOGGER.error("API error: %s", err)
                return self.async_show_form(
                    step_id="user",
                    errors={"base": "cannot_connect"},
                    data_schema=self._build_schema(api_key_exists),
                )

            await self.async_set_unique_id(f"{stop_id}_{platform or 'all'}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input["name"],
                data={
                    CONF_STOP_ID: stop_id,
                    CONF_PLATFORM: platform,
                    "name": user_input["name"],
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(api_key_exists),
        )

    def _build_schema(self, api_key_exists: bool):
        schema = {
            vol.Required("name", default="PID Departures"): str,
            vol.Required(CONF_STOP_ID): str,
            vol.Optional(CONF_PLATFORM): str,
        }

        if not api_key_exists:
            schema[vol.Required(CONF_API_KEY)] = str

        return vol.Schema(schema)
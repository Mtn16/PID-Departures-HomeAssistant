from __future__ import annotations

import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant.helpers import storage

from .api import PIDDeparturesApi
from .const import CONF_API_KEY, CONF_STOP_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = "pid_departures_global"
STORAGE_VERSION = 1


class PIDDeparturesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        store = storage.Store(
            self.hass,
            STORAGE_VERSION,
            STORAGE_KEY
        )

        stored_data = await store.async_load() or {}
        api_key_exists = CONF_API_KEY in stored_data

        if user_input is not None:
            stop_id = user_input[CONF_STOP_ID]

            api_key = stored_data.get(CONF_API_KEY)

            if not api_key_exists:
                api_key = user_input[CONF_API_KEY]

                await store.async_save({
                    CONF_API_KEY: api_key
                })

            api = PIDDeparturesApi(api_key)

            try:
                data = await api.get_stop_departures(stop_id)
            except Exception as err:
                _LOGGER.error("Cannot connect to Golemio API: %s", err)
                return self.async_show_form(
                    step_id="user",
                    errors={"base": "cannot_connect"},
                    data_schema=self._build_schema(api_key_exists)
                )

            stop_name = "Unknown stop"

            if isinstance(data, dict):
                stop = data.get("stop", {})
                if isinstance(stop, dict):
                    stop_name = stop.get("name", stop_name)

            elif isinstance(data, list) and len(data) > 0:
                stop = data[0].get("stop", {})
                if isinstance(stop, dict):
                    stop_name = stop.get("name", stop_name)

            if not stop_name:
                stop_name = stop_id

            await self.async_set_unique_id(stop_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{stop_name}",
                data={
                    CONF_STOP_ID: stop_id
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(api_key_exists)
        )

    def _build_schema(self, api_key_exists: bool):
        schema = {
            vol.Required(CONF_STOP_ID): str
        }

        if not api_key_exists:
            schema[vol.Required(CONF_API_KEY)] = str

        return vol.Schema(schema)
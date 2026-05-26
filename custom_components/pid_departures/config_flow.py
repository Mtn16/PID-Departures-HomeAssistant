from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import storage

from .api import PIDDeparturesApi
from .const import CONF_API_KEY, CONF_STOP_ID, DOMAIN

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
            except Exception:
                return self.async_show_form(
                    step_id="user",
                    errors={"base": "cannot_connect"},
                    data_schema=self._build_schema(api_key_exists)
                )

            stop_name = "Unknown stop"

            if data:
                stop = data[0].get("stop", {})
                stop_name = stop.get("name", stop_name)

            await self.async_set_unique_id(stop_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=stop_name,
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
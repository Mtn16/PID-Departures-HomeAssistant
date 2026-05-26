from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import storage

from .api import PIDDeparturesApi
from .const import CONF_API_KEY, CONF_STOP_ID, DOMAIN, CONF_PLATFORM
from .coordinator import PIDCoordinator

STORAGE_KEY = "pid_departures_global"
STORAGE_VERSION = 1


async def async_setup_entry(hass, entry, async_add_entities):
    store = storage.Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored_data = await store.async_load() or {}

    api = PIDDeparturesApi(stored_data.get(CONF_API_KEY))

    coordinator = PIDCoordinator(
        hass,
        api,
        entry.data[CONF_STOP_ID],
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            PIDLinesSensor(coordinator, entry),
            PIDDeparturesSensor(coordinator, entry),
        ]
    )


class PIDBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry

    @property
    def data(self):
        return self.coordinator.data or {}

    @property
    def stop(self):
        return self.data.get("stop", {})

    @property
    def departures(self):
        return self.data.get("departures", [])

    @property
    def stop_name(self):
        return self.stop.get("name", "Unknown")

    @property
    def platform_name(self):
        return self.stop.get("platform_code", "?")

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.entry.title,
            manufacturer="PID",
        )


class PIDLinesSensor(PIDBaseSensor):
    _attr_icon = "mdi:bus"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_lines"

    @property
    def name(self):
        return f"{self.stop_name} {self.platform_name} Lines"

    @property
    def native_value(self):
        lines = {
            d.get("route", {}).get("short_name")
            for d in self.departures
            if d.get("route", {}).get("short_name")
        }
        return ", ".join(sorted(lines))

    @property
    def extra_state_attributes(self):
        return {
            "lines": sorted(
                list(
                    {
                        d.get("route", {}).get("short_name")
                        for d in self.departures
                        if d.get("route", {}).get("short_name")
                    }
                )
            )
        }


class PIDDeparturesSensor(PIDBaseSensor):
    _attr_icon = "mdi:clock-outline"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_departures"

    @property
    def name(self):
        return f"{self.stop_name} {self.platform_name} Departures"

    @property
    def native_value(self):
        if not self.departures:
            return "No departures"

        first = self.departures[0]

        route = first.get("route", {}).get("short_name", "?")
        headsign = first.get("trip", {}).get("headsign", "?")

        return f"{route} → {headsign}"

    @property
    def extra_state_attributes(self):
        return {
            "departures": [
                {
                    "line": d.get("route", {}).get("short_name"),
                    "destination": d.get("trip", {}).get("headsign"),
                    "departure_timestamp": d.get("departure_timestamp"),
                    "platform": d.get("stop", {}).get("platform_code"),
                }
                for d in self.departures[:5]
            ]
        }
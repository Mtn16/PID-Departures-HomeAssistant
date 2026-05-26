from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import PIDDeparturesApi
from .const import CONF_API_KEY, CONF_STOP_ID, DOMAIN
from .coordinator import PIDCoordinator
from homeassistant.helpers import storage

STORAGE_KEY = "pid_departures_global"
STORAGE_VERSION = 1


async def async_setup_entry(hass, entry, async_add_entities):
    store = storage.Store(
        hass,
        STORAGE_VERSION,
        STORAGE_KEY
    )

    stored_data = await store.async_load()

    api = PIDDeparturesApi(
        stored_data[CONF_API_KEY]
    )

    coordinator = PIDCoordinator(
        hass,
        api,
        entry.data[CONF_STOP_ID]
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        PIDLinesSensor(coordinator, entry),
        PIDDeparturesSensor(coordinator, entry),
    ])


class PIDBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)

        self.entry = entry

    @property
    def stop_data(self):
        if not self.coordinator.data:
            return {}
    
        if isinstance(self.coordinator.data, dict):
            return self.coordinator.data
    
        if isinstance(self.coordinator.data, list):
            return self.coordinator.data[0] if self.coordinator.data else {}
    
        return {}

    @property
    def stop_name(self):
        return self.stop_data.get("stop", {}).get("name", "Unknown")

    @property
    def platform_name(self):
        return self.stop_data.get("stop", {}).get("platform", "?")

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=f"{self.stop_name} {self.platform_name}",
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
        lines = set()

        for dep in self.coordinator.data:
            route = dep.get("route", {})
            short_name = route.get("short_name")

            if short_name:
                lines.add(short_name)

        return ", ".join(sorted(lines))

    @property
    def extra_state_attributes(self):
        return {
            "lines": sorted(list({
                dep.get("route", {}).get("short_name")
                for dep in self.coordinator.data
                if dep.get("route", {}).get("short_name")
            }))
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
        if not self.coordinator.data:
            return "No departures"

        first = self.coordinator.data[0]

        route = first.get("route", {}).get("short_name", "?")
        headsign = first.get("trip", {}).get("headsign", "?")

        return f"{route} → {headsign}"

    @property
    def extra_state_attributes(self):
        departures = []

        for dep in self.coordinator.data[:5]:
            departures.append({
                "line": dep.get("route", {}).get("short_name"),
                "destination": dep.get("trip", {}).get("headsign"),
                "departure_timestamp": dep.get("departure_timestamp"),
                "platform": dep.get("stop", {}).get("platform"),
            })

        return {
            "departures": departures
        }
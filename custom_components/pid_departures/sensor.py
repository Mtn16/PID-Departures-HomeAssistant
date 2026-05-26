from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import storage
from datetime import datetime, timezone

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

    entities = [
        PIDLinesSensor(coordinator, entry),
    ]

    for i in range(5):
        entities.append(PIDDepartureSensor(coordinator, entry, i))
        entities.append(PIDDepartureTimeSensor(coordinator, entry, i))
        entities.append(PIDDepartureInSensor(coordinator, entry, i))

    async_add_entities(entities)

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
    def custom_name(self):
        return self.entry.data.get("name", self.entry.title)

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.entry.data.get("name", self.entry.title),
            manufacturer="PID",
        )
    
    def _parse_departure_time(self, dep):
        ts = dep.get("departure_timestamp")
        if not ts:
            return None

        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None


class PIDLinesSensor(PIDBaseSensor):
    _attr_icon = "mdi:bus"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_lines"

    @property
    def name(self):
        return f"{self.entry.data.get('name', self.entry.title)} Lines"

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
    
class PIDDepartureTimeSensor(PIDBaseSensor):
    _attr_icon = "mdi:clock"

    def __init__(self, coordinator, entry, index: int):
        super().__init__(coordinator, entry)
        self.index = index

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_departure_{self.index + 1}_time"

    @property
    def name(self):
        return f"{self.custom_name} Departure {self.index + 1} Time"

    @property
    def departure(self):
        departures = self.departures
        return departures[self.index] if len(departures) > self.index else None

    @property
    def native_value(self):
        dep = self.departure
        if not dep:
            return None

        dt = self._parse_departure_time(dep)
        if not dt:
            return None

        return dt.strftime("%H:%M")
    
class PIDDepartureSensor(PIDBaseSensor):
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator, entry, index: int):
        super().__init__(coordinator, entry)
        self.index = index

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_departure_{self.index + 1}"

    @property
    def name(self):
        return f"{self.custom_name} Departure {self.index + 1}"

    @property
    def departure(self):
        departures = self.departures
        if len(departures) > self.index:
            return departures[self.index]
        return None

    @property
    def native_value(self):
        dep = self.departure
        if not dep:
            return "No departure"

        route = dep.get("route", {}).get("short_name", "?")
        headsign = dep.get("trip", {}).get("headsign", "?")

        return f"{route} → {headsign}"

    @property
    def extra_state_attributes(self):
        dep = self.departure
        if not dep:
            return {}

        return {
            "line": dep.get("route", {}).get("short_name"),
            "destination": dep.get("trip", {}).get("headsign"),
            "departure_timestamp": dep.get("departure_timestamp"),
            "platform": dep.get("stop", {}).get("platform_code"),
        }
    


class PIDDepartureInSensor(PIDBaseSensor):
    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator, entry, index: int):
        super().__init__(coordinator, entry)
        self.index = index

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_departure_{self.index + 1}_in"

    @property
    def name(self):
        return f"{self.custom_name} Departure {self.index + 1} In"

    @property
    def departure(self):
        departures = self.departures
        return departures[self.index] if len(departures) > self.index else None

    @property
    def native_value(self):
        dep = self.departure
        if not dep:
            return None

        dt = self._parse_departure_time(dep)
        if not dt:
            return None

        now = datetime.now(timezone.utc)

        diff = dt - now
        minutes = int(diff.total_seconds() / 60)

        if minutes < 0:
            return "now"

        return f"{minutes} min"
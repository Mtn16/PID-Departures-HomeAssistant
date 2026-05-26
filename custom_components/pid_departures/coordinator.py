from datetime import timedelta

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import PIDDeparturesApi
from .const import DOMAIN, SCAN_INTERVAL_SECONDS


class PIDCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: PIDDeparturesApi, stop_id: str):
        super().__init__(
            hass,
            logger=hass.logger,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )

        self.api = api
        self.stop_id = stop_id

    async def _async_update_data(self):
        try:
            return await self.api.get_stop_departures(self.stop_id)
        except Exception as err:
            raise UpdateFailed(f"Failed to fetch departures: {err}") from err
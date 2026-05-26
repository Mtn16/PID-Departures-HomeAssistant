from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import PIDDeparturesApi
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class PIDCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: PIDDeparturesApi, stop_id: str):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )

        self.api = api
        self.stop_id = stop_id

    async def _async_update_data(self):
        try:
            _LOGGER.debug("Fetching departures for %s", self.stop_id)
            return await self.api.get_stop_departures(self.stop_id)
        except Exception as err:
            _LOGGER.exception("Failed to fetch departures")
            raise UpdateFailed(str(err)) from err
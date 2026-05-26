import aiohttp
import logging

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class PIDDeparturesApi:
    def __init__(self, api_key: str):
        self._api_key = api_key

    @property
    def headers(self):
        return {
            "X-Access-Token": self._api_key,
            "Content-Type": "application/json",
        }

    async def get_stop_departures(self, stop_id: str):
        url = (
            f"{API_BASE}/pid/departureboards"
            f"?ids={stop_id}"
            f"&limit=5"
            f"&minutesBefore=0"
            f"&minutesAfter=180"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:

                text = await response.text()

                if response.status != 200:
                    _LOGGER.error(
                        "Golemio API error %s\nURL: %s\nResponse body: %s",
                        response.status,
                        url,
                        text,
                    )
                    return {}

                try:
                    data = await response.json()
                except Exception:
                    _LOGGER.error(
                        "Invalid JSON response\nURL: %s\nBody: %s",
                        url,
                        text,
                    )
                    return {}

                if isinstance(data, list):
                    return data[0] if data else {}

                return data or {}
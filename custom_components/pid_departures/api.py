import aiohttp

from .const import API_BASE


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
                response.raise_for_status()
                data = await response.json()
    
                if isinstance(data, list):
                    return data[0] if data else {}
    
                return data or {}
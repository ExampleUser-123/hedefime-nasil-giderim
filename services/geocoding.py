import requests

from services.cache import cached


@cached(ttl_seconds=24 * 3600)
def search_place(query: str):
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "tr"
    }

    headers = {
        "User-Agent": "HEDEFIME-NASIL-GIDICEM/1.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    result = results[0]

    return {
        "display_name": result["display_name"],
        "lat": float(result["lat"]),
        "lon": float(result["lon"])
    }
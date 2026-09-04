import requests

from services.cache import cached


TURKIYE_API_URL = "https://api.turkiyeapi.dev/v2"


@cached(ttl_seconds=86400)
def get_provinces():
    """Türkiye il listesini getirir. Liste neredeyse hiç değişmediği
    için 24 saat önbelleğe alınır. API erişilemezse None döner."""

    try:
        response = requests.get(
            f"{TURKIYE_API_URL}/provinces",
            timeout=10
        )

        response.raise_for_status()

        return response.json()["data"]
    except (requests.RequestException, ValueError, KeyError):
        return None


def find_province(name: str):
    provinces = get_provinces()

    if not provinces:
        return None

    name = name.strip().lower()

    for province in provinces:
        province_name = province["name"].strip().lower()

        if province_name == name:
            return province

    return None

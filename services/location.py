import requests


TURKIYE_API_URL = "https://api.turkiyeapi.dev/v2"


def get_provinces():
    response = requests.get(
        f"{TURKIYE_API_URL}/provinces",
        timeout=10
    )

    response.raise_for_status()

    return response.json()["data"]


def find_province(name: str):
    provinces = get_provinces()

    name = name.strip().lower()

    for province in provinces:
        province_name = province["name"].strip().lower()

        if province_name == name:
            return province

    return None
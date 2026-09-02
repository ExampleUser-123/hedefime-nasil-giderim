import requests


def calculate_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float
):
    route_url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
    )

    response = requests.get(
        route_url,
        params={"overview": "false"},
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if data["code"] != "Ok":
        return None

    route = data["routes"][0]

    distance_km = route["distance"] / 1000
    duration_minutes = route["duration"] / 60

    return {
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration_minutes, 0)
    }
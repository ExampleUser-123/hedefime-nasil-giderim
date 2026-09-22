import requests

from services.cache import cached


@cached(ttl_seconds=3600)
def calculate_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    profile: str = "driving",
):
    route_url = (
        f"https://router.project-osrm.org/route/v1/{profile}/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
    )

    response = requests.get(
        route_url,
        params={
            "overview": "simplified",
            "geometries": "geojson"
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if data["code"] != "Ok":
        return None

    route = data["routes"][0]

    distance_km = route["distance"] / 1000
    duration_minutes = route["duration"] / 60

    geometry = [
        [coord[1], coord[0]]
        for coord in route["geometry"]["coordinates"]
    ]

    return {
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration_minutes, 0),
        "geometry": geometry
    }


@cached(ttl_seconds=3600)
def snap_to_road(
    points: tuple,
    profile: str = "driving",
):
    """Ara noktalari gercek yollara oturtur (Snap-to-Road).

    points: ([lat, lon], ...) — OSRM'e waypoint olarak verilir,
    donen geometri yol virajlarini takip eder.
    Basarisizlikta None doner; cagiran eski duz-cizgi davranisina duser.
    """
    pts = [(float(p[0]), float(p[1])) for p in points]
    if len(pts) < 2:
        return None

    coords = ";".join(f"{lon},{lat}" for lat, lon in pts)
    route_url = f"https://router.project-osrm.org/route/v1/{profile}/{coords}"

    try:
        response = requests.get(
            route_url,
            params={
                "overview": "full",
                "geometries": "geojson",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    geometry = [
        [coord[1], coord[0]]
        for coord in data["routes"][0]["geometry"]["coordinates"]
    ]

    return geometry if len(geometry) >= 2 else None
import re

import requests

from services.cache import cached


# Ucretli gecis gostergeleri (yalnizca OSRM adim adlarinda gercekten
# geciyorsa isaretlenir; ucret tutari tahmini YOKTUR, isim listelenir).
_TOLL_MOTORWAY_RE = re.compile(r"\bO-?\d{1,2}\b", re.IGNORECASE)
_TOLL_CROSSINGS = (
    "şehitler köprüsü", "boğaziçi", "bosphorus",
    "fatih sultan", "yavuz sultan",
    "osmangazi", "osman gazi",
    "1915", "çanakkale köprüsü",
    "avrasya", "eurasia",
)


def detect_toll_roads(names) -> list:
    """OSRM adim adlarindan ucretli yol/kopru gecislerini cikarir.

    names: adimlardaki yol adlari listesi. Donus: tespit edilen adlar
    (sirali, tekrarsiz). Hicbiri yoksa bos liste.
    """
    found: list = []
    for raw in names or []:
        name = str(raw or "").strip()
        if not name:
            continue
        hit = None
        motorway = _TOLL_MOTORWAY_RE.search(name)
        if motorway:
            hit = motorway.group(0).upper()
        else:
            lowered = name.casefold()
            if any(key in lowered for key in _TOLL_CROSSINGS):
                hit = name
        if hit and hit not in found:
            found.append(hit)
    return found


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

    # Public OSRM zaman zaman 429/500 doner; tek seferlik hata tum /plan
    # istehini dusurmesin diye iki deneme yapilir. Basarisizlikta None doner
    # (cagiran hata karti gosterir; istisna firlatilmaz).
    data = None
    for _ in range(2):
        try:
            response = requests.get(
                route_url,
                params={
                    "overview": "simplified",
                    "geometries": "geojson",
                    "steps": "true",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            break
        except Exception:
            data = None
    if not data:
        return None

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    route = data["routes"][0]

    distance_km = route["distance"] / 1000
    duration_minutes = route["duration"] / 60

    geometry = [
        [coord[1], coord[0]]
        for coord in route["geometry"]["coordinates"]
    ]

    step_names: list = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            for key in ("ref", "name"):
                value = (step.get(key) or "").strip()
                if value and (not step_names or step_names[-1] != value):
                    step_names.append(value)
    toll_roads = detect_toll_roads(step_names)

    return {
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration_minutes, 0),
        "geometry": geometry,
        "has_toll": bool(toll_roads),
        "toll_roads": toll_roads,
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

    # Public OSRM zaman zaman 429/500 doner; bir kez daha dene ki harita
    # duz cizgiye dusmesin.
    data = None
    for _ in range(2):
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
            break
        except Exception:
            data = None
    if not data:
        return None

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    geometry = [
        [coord[1], coord[0]]
        for coord in data["routes"][0]["geometry"]["coordinates"]
    ]

    return geometry if len(geometry) >= 2 else None


@cached(ttl_seconds=3600)
def walking_guidance(
    a_lat: float,
    a_lon: float,
    b_lat: float,
    b_lon: float,
):
    """Yurume geometrisi + cadde/sokak adimlari (OSRM foot steps).

    Donus: {"geometry": [[lat, lon], ...], "streets": [...], "duration_min": x}.
    Basarisizlikta None doner; sokak adi yoksa streets bos liste olur.
    """
    route_url = (
        "https://router.project-osrm.org/route/v1/foot/"
        f"{a_lon},{a_lat};{b_lon},{b_lat}"
    )

    data = None
    for _ in range(2):
        try:
            response = requests.get(
                route_url,
                params={
                    "overview": "full",
                    "geometries": "geojson",
                    "steps": "true",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            break
        except Exception:
            data = None
    if not data:
        return None

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    route = data["routes"][0]
    geometry = [
        [coord[1], coord[0]]
        for coord in route["geometry"]["coordinates"]
    ]
    if len(geometry) < 2:
        return None

    streets: list[str] = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            name = (step.get("name") or "").strip()
            if name and (not streets or streets[-1] != name):
                streets.append(name)

    return {
        "geometry": geometry,
        "streets": streets[:5],
        "duration_min": round(route.get("duration", 0) / 60),
    }


def road_geometry(points, profile="driving"):
    """Noktalari yola oturtur; olmazsa duz cizgi duser (hicbir zaman bos donmez).

    points: [[lat, lon], ...] (en az 2 nokta).
    Vapur gibi OSRM'in cozemedigi legler icin duz cizgi dogru davranistir.
    """
    pts = []
    for p in points or []:
        try:
            pts.append([float(p[0]), float(p[1])])
        except (TypeError, ValueError, IndexError):
            continue
    if len(pts) < 2:
        return pts
    try:
        snapped = snap_to_road(tuple(tuple(p) for p in pts), profile)
    except Exception:
        snapped = None
    return snapped or pts
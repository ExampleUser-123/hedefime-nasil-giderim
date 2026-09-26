"""Turkiye'nin ana havalimanlari — OSM Nominatim'den dogrulanmis gercek
koordinatlar (uydurma yok). SAW koordinati OSM rayli ag verisinden.

Kullanim: ucus tahminine havalimani transfer bacaklari eklenir:
koken -> en yakin havalimani (kara yolu) -> ucus -> hedefe en yakin
havalimani -> hedef (kara yolu).
"""

import math

AIRPORTS: list[dict] = [
    {
        "code": "IST",
        "name": "İstanbul Havalimanı",
        "city": "İstanbul",
        # OSM Nominatim: Istanbul Airport, Arnavutkoy
        "lat": 41.2748684,
        "lon": 28.7322749,
    },
    {
        "code": "SAW",
        "name": "Sabiha Gökçen Havalimanı",
        "city": "İstanbul",
        # OSM rayli ag verisi (M4 duragi)
        "lat": 40.90644,
        "lon": 29.31148,
    },
    {
        "code": "ESB",
        "name": "Esenboğa Havalimanı",
        "city": "Ankara",
        # OSM Nominatim: Esenboga Uluslararasi Havalimani
        "lat": 40.1230634,
        "lon": 32.9987209,
    },
    {
        "code": "ADB",
        "name": "Adnan Menderes Havalimanı",
        "city": "İzmir",
        # OSM Nominatim: Adnan Menderes Havalimani, Gaziemir
        "lat": 38.2895350,
        "lon": 27.1588392,
    },
    {
        "code": "AYT",
        "name": "Antalya Havalimanı",
        "city": "Antalya",
        # OSM Nominatim: Antalya Havalimani (AYT), Kepez
        "lat": 36.8999425,
        "lon": 30.7981914,
    },
]


def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_airport(lat: float, lon: float) -> dict | None:
    """En yakin havalimani + kus ucusu mesafe (m). Liste disi bolgede bile
    en yakin doner (Turkiye icin anlamli); liste bossa None."""
    best = None
    best_m = None
    for airport in AIRPORTS:
        try:
            dist = _haversine_m(float(lat), float(lon), airport["lat"], airport["lon"])
        except (TypeError, ValueError, KeyError):
            continue
        if best_m is None or dist < best_m:
            best_m = dist
            best = airport
    if best is None:
        return None
    return {**best, "distance_m": round(best_m)}


def _shuttle_leg(label, from_name, to_name, from_lat, from_lon, to_lat, to_lon):
    from services.routing import road_geometry
    coords = road_geometry(
        [[from_lat, from_lon], [to_lat, to_lon]], "driving"
    )
    return {
        "type": "shuttle",
        "line": "Havalimanı Yolu",
        "name": label,
        "route_id": "airport-transfer",
        "distance_m": None,
        "duration_min": None,
        "departure_time": None,
        "arrival_time": None,
        "from_stop": from_name,
        "to_stop": to_name,
        "direction": None,
        "platform": None,
        "fare": None,
        "stops": [],
        "alternate_lines": [],
        "coords": coords,
    }


def build_flight_legs(start_lat, start_lon, end_lat, end_lon,
                      start_name=None, end_name=None) -> list[dict] | None:
    """Ucus bacaklari: transfer -> ucus -> transfer.

    Ayni havalimani ciksa (kisa mesafe) veya havalimani yoksa None doner.
    """
    dep = nearest_airport(start_lat, start_lon)
    arr = nearest_airport(end_lat, end_lon)
    if dep is None or arr is None:
        return None
    if dep["code"] == arr["code"]:
        return None

    flight_leg = {
        "type": "flight",
        "line": "Uçak",
        "name": f"{dep['code']} → {arr['code']} Uçuşu",
        "route_id": "flight",
        "distance_m": None,
        "duration_min": None,
        "departure_time": None,
        "arrival_time": None,
        "from_stop": dep["name"],
        "to_stop": arr["name"],
        "direction": None,
        "platform": None,
        "fare": None,
        "stops": [],
        "alternate_lines": [],
        "coords": [
            [dep["lat"], dep["lon"]],
            [arr["lat"], arr["lon"]],
        ],
    }

    return [
        _shuttle_leg(
            f"Havalimanı transferi ({dep['code']})",
            start_name, dep["name"],
            start_lat, start_lon, dep["lat"], dep["lon"],
        ),
        flight_leg,
        _shuttle_leg(
            f"Havalimanı transferi ({arr['code']})",
            arr["name"], end_name,
            arr["lat"], arr["lon"], end_lat, end_lon,
        ),
    ]

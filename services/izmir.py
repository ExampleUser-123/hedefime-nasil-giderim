"""
İzmir toplu taşıma sağlayıcısı.

İzmir Büyükşehir Belediyesi açık veri portalındaki ESHOT durak
veri setini kullanır. İETT gibi hazır bir A→B router'ı olmadığı
için "doğrudan hat önerisi" yöntemiyle çalışır:

1. Başlangıç ve hedef noktasına en yakın duraklar bulunur.
2. Bu duraklardan geçen hatların kesişimi alınır.
3. Ortak hatlarla "yürü → bin → in → yürü" önerileri üretilir.
"""

import math
import requests

from services.cache import cached


CKAN_URL = "https://acikveri.bizizmir.com/api/3/action/datastore_search"
ESHOT_STOP_RESOURCE_ID = "0c791266-a2e4-4f14-82b8-9a9b102fbf94"

PAGE_SIZE = 5000
NEAR_RADIUS_M = 600
MAX_STOPS_PER_SIDE = 3
MAX_SUGGESTIONS = 3

WALK_SPEED_M_PER_MIN = 75
BUS_SPEED_M_PER_MIN = 330


def _haversine_m(lat1, lon1, lat2, lon2):
    """İki koordinat arası kuş uçuşu mesafe (metre)."""

    r = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )

    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@cached(ttl_seconds=86400)
def _fetch_eshot_stops():
    """ESHOT durak veri setini indirir ve normalize eder.
    Başarısızlık durumunda None döner (önbelleğe alınmaz)."""

    stops = []
    offset = 0

    while True:
        try:
            response = requests.get(
                CKAN_URL,
                params={
                    "resource_id": ESHOT_STOP_RESOURCE_ID,
                    "limit": PAGE_SIZE,
                    "offset": offset,
                },
                timeout=30,
            )
            response.raise_for_status()
            records = response.json()["result"]["records"]
        except (requests.RequestException, ValueError, KeyError):
            if offset == 0:
                return None
            break

        if not records:
            break

        for record in records:
            try:
                lat = float(record["ENLEM"])
                lon = float(record["BOYLAM"])
            except (TypeError, ValueError, KeyError):
                continue

            raw_lines = record.get("DURAKTAN_GECEN_HATLAR") or ""
            lines = [
                part.strip()
                for part in str(raw_lines).replace(",", "-").split("-")
                if part.strip()
            ]

            stops.append({
                "id": str(record.get("DURAK_ID", "")),
                "name": str(record.get("DURAK_ADI", "")).strip(),
                "lat": lat,
                "lon": lon,
                "lines": lines,
            })

        offset += PAGE_SIZE

    if not stops:
        return None

    return stops


def _stops_within(stops, lat, lon, radius_m):
    """Verilen noktanın çevresindeki durakları mesafeye göre sıralar."""

    near = []

    for stop in stops:
        distance = _haversine_m(lat, lon, stop["lat"], stop["lon"])

        if distance <= radius_m:
            near.append((distance, stop))

    near.sort(key=lambda item: item[0])

    return near


def _walking_leg(distance_m, from_stop, to_stop):
    return {
        "type": "walking",
        "line": None,
        "name": "Yürüme",
        "route_id": "walking",
        "distance_m": round(distance_m),
        "departure_time": None,
        "arrival_time": None,
        "from_stop": from_stop,
        "to_stop": to_stop,
        "stops": [],
        "alternate_lines": [],
        "coords": [],
    }


def _bus_leg(line, board_stop, alight_stop):
    return {
        "type": "bus",
        "line": line,
        "name": f"ESHOT {line}",
        "route_id": f"eshot:{line}",
        "distance_m": None,
        "departure_time": None,
        "arrival_time": None,
        "from_stop": board_stop["name"],
        "to_stop": alight_stop["name"],
        "stops": [],
        "alternate_lines": [],
        "coords": [
            [board_stop["lat"], board_stop["lon"]],
            [alight_stop["lat"], alight_stop["lon"]],
        ],
    }


def _estimate_duration(route_walk_m, bus_straight_m, exit_walk_m):
    """Kaba süre tahmini (dakika): yürüyüş + bekleme + otobüs."""

    bus_time = bus_straight_m / BUS_SPEED_M_PER_MIN
    walk_time = (route_walk_m + exit_walk_m) / WALK_SPEED_M_PER_MIN

    return round(walk_time + bus_time + 5)


def _no_route(message):
    return {
        "transport_type": "public_transport",
        "status": "no_route",
        "error": message,
        "routes": [],
        "source": "ESHOT",
    }


def find_izmir_route(start_lat, start_lon, end_lat, end_lon):
    """
    İzmir için A→B toplu taşıma önerisi üretir.
    Diğer sağlayıcılarla aynı yanıt şemasını döndürür.
    """

    stops = _fetch_eshot_stops()

    if stops is None:
        return {
            "transport_type": "public_transport",
            "status": "error",
            "error": "İzmir toplu taşıma verisine şu anda ulaşılamadı.",
            "routes": [],
            "source": "ESHOT",
        }

    near_start = _stops_within(stops, start_lat, start_lon, NEAR_RADIUS_M)
    near_end = _stops_within(stops, end_lat, end_lon, NEAR_RADIUS_M)

    if not near_start or not near_end:
        return _no_route(
            "Yakın çevrede ESHOT durağı bulunamadı. "
            "Başlangıç ve hedefin İzmir il sınırları içinde olduğundan emin ol."
        )

    suggestions = []

    for start_distance, board_stop in near_start[:MAX_STOPS_PER_SIDE]:
        for end_distance, alight_stop in near_end[:MAX_STOPS_PER_SIDE]:
            if board_stop["id"] == alight_stop["id"]:
                continue

            common_lines = [
                line
                for line in board_stop["lines"]
                if line in alight_stop["lines"]
            ]

            if not common_lines:
                continue

            bus_straight_m = _haversine_m(
                board_stop["lat"],
                board_stop["lon"],
                alight_stop["lat"],
                alight_stop["lon"],
            )

            if bus_straight_m < 200:
                continue

            total_walk = start_distance + end_distance
            duration = _estimate_duration(
                total_walk, bus_straight_m, 0
            )

            for line in common_lines[:2]:
                suggestions.append({
                    "walk_in_m": start_distance,
                    "walk_out_m": end_distance,
                    "duration": duration,
                    "board": board_stop,
                    "alight": alight_stop,
                    "line": line,
                })

    if not suggestions:
        return _no_route(
            "Bu iki nokta arasında doğrudan bir ESHOT hattı bulunamadı. "
            "Aktarmalı yolculuk gerekebilir."
        )

    # En az yürüyüş gerektiren öneriler öne çıkar
    suggestions.sort(key=lambda s: s["walk_in_m"] + s["walk_out_m"])
    suggestions = suggestions[:MAX_SUGGESTIONS]

    routes = []

    for item in suggestions:
        legs = [
            _walking_leg(
                item["walk_in_m"],
                None,
                item["board"]["name"],
            ),
            _bus_leg(item["line"], item["board"], item["alight"]),
            _walking_leg(
                item["walk_out_m"],
                item["alight"]["name"],
                None,
            ),
        ]

        routes.append({
            "fee": None,
            "walking_distance_m": round(
                item["walk_in_m"] + item["walk_out_m"]
            ),
            "calories_burned": None,
            "co2_emission": None,
            "departure_time": None,
            "arrival_time": None,
            "duration_minutes": item["duration"],
            "legs": legs,
        })

    return {
        "transport_type": "public_transport",
        "status": "success",
        "routes": routes,
        "source": "ESHOT",
        "note": "Süre ve mesafeler tahminidir; ESHOT sefer saatleri için eshot.gov.tr'ye bakabilirsin.",
    }

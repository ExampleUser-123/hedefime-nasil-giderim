"""
İzmir toplu taşıma sağlayıcısı.

İzmir Büyükşehir Belediyesi açık veri portalındaki ESHOT durak
veri setini kullanır. İETT gibi hazır bir A→B router'ı olmadığı
için "doğrudan hat önerisi" yöntemiyle çalışır:

1. Başlangıç ve hedef noktasına en yakın duraklar bulunur.
2. Bu duraklardan geçen hatların kesişimi alınır.
3. Ortak hatlarla "yürü → bin → in → yürü" önerileri üretilir.
"""

import json
import math
import os
import requests

from services.cache import cached


CKAN_URL = "https://acikveri.bizizmir.com/api/3/action/datastore_search"
ESHOT_STOP_RESOURCE_ID = "0c791266-a2e4-4f14-82b8-9a9b102fbf94"

IZDENIZ_PIERS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "izdeniz_piers.json",
)

PAGE_SIZE = 5000
NEAR_RADIUS_M = 600
MAX_STOPS_PER_SIDE = 6
MAX_SUGGESTIONS = 3

WALK_SPEED_M_PER_MIN = 75
BUS_SPEED_M_PER_MIN = 330


def _load_izdeniz_stops():
    """
    İZDENİZ iskelelerini sahte durak olarak döndürür.
    Her iskelenin 'hatları', bağlı olduğu iskelelere giden
    vapur bağlantılarıdır (F<küçük id>-<büyük id> anahtarlı).
    """

    try:
        with open(IZDENIZ_PIERS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []

    pier_names = {p["id"]: p["name"] for p in data.get("piers", [])}

    stops = []

    for pier in data.get("piers", []):
        lines = []

        for key, pair in data.get("connections", {}).items():
            if pier["id"] not in pair:
                continue

            other_id = pair[0] if pair[1] == pier["id"] else pair[1]
            other_name = pier_names.get(other_id, "?")

            lines.append({
                "n": key,
                "t": "ferry",
                "l": f"İZDENİZ ({pier['name']} ↔ {other_name})",
            })

        if not lines:
            continue

        stops.append({
            "id": f"izdeniz:{pier['id']}",
            "name": f"{pier['name']} İskelesi",
            "lat": pier["lat"],
            "lon": pier["lon"],
            "lines": lines,
        })

    return stops


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
                {"n": part.strip(), "t": "bus", "l": ""}
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


# İlçe/kasaba merkezine çözümlenen aramalar için kademeli yarıçap
SEARCH_RADII_M = (NEAR_RADIUS_M, 2000, 6000)

# İskeleye "yakın" sayılacak en uzak mesafe (ilçe merkezli aramalar için)
MAX_PIER_DISTANCE_M = 8000


def _stops_near_adaptive(stops, lat, lon):
    """Önce yürüyüş mesafesinde durak arar, yoksa yarıçapı kademeli büyütür."""

    for radius in SEARCH_RADII_M:
        near = _stops_within(stops, lat, lon, radius)

        if near:
            return near

    return []


def _nearest_pier(piers, lat, lon):
    """Noktaya en yakın iskeleyi (mesafe, iskele) döndürür; yoksa None."""

    if not piers:
        return None

    nearest = min(
        piers,
        key=lambda pier: _haversine_m(lat, lon, pier["lat"], pier["lon"]),
    )

    distance = _haversine_m(lat, lon, nearest["lat"], nearest["lon"])

    if distance > MAX_PIER_DISTANCE_M:
        return None

    return (distance, nearest)


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


def _no_route(message, source="ESHOT"):
    return {
        "transport_type": "public_transport",
        "status": "no_route",
        "error": message,
        "routes": [],
        "source": source,
    }


def find_izmir_route(start_lat, start_lon, end_lat, end_lon):
    """
    İzmir için A→B toplu taşıma önerisi üretir.
    Diğer sağlayıcılarla aynı yanıt şemasını döndürür.

    İki geçit halinde çalışır:
    1. ESHOT otobüs: durak-durak ortak hat önerisi
    2. İZDENİZ vapur: iskele-iskele bağlantı önerisi
    """

    eshot_stops = _fetch_eshot_stops()

    if eshot_stops is None:
        return {
            "transport_type": "public_transport",
            "status": "error",
            "error": "İzmir toplu taşıma verisine şu anda ulaşılamadı.",
            "routes": [],
            "source": "ESHOT",
        }

    piers = _load_izdeniz_stops()
    for pier in piers:
        pier["line_keys"] = {line["n"] for line in pier["lines"]}

    for stop in eshot_stops:
        stop["line_keys"] = {line["n"] for line in stop["lines"]}

    suggestions = []

    # -------------------------------------------------
    # Geçit 1: ESHOT otobüs (durak-durak ortak hat)
    # -------------------------------------------------

    near_start = _stops_near_adaptive(eshot_stops, start_lat, start_lon)
    near_end = _stops_near_adaptive(eshot_stops, end_lat, end_lon)

    for start_distance, board_stop in near_start[:MAX_STOPS_PER_SIDE]:
        for end_distance, alight_stop in near_end[:MAX_STOPS_PER_SIDE]:
            if board_stop["id"] == alight_stop["id"]:
                continue

            common_lines = [
                line
                for line in board_stop["lines"]
                if line["n"] in alight_stop["line_keys"]
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

            duration = _estimate_duration(
                start_distance + end_distance, bus_straight_m, 0
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

    # -------------------------------------------------
    # Geçit 2: İZDENİZ vapur (iskele-iskele bağlantı)
    # -------------------------------------------------

    pier_start = _nearest_pier(piers, start_lat, start_lon)
    pier_end = _nearest_pier(piers, end_lat, end_lon)

    if (
        pier_start is not None
        and pier_end is not None
        and pier_start[1]["id"] != pier_end[1]["id"]
    ):
        start_distance, board_pier = pier_start
        end_distance, alight_pier = pier_end

        common_lines = [
            line
            for line in board_pier["lines"]
            if line["n"] in alight_pier["line_keys"]
        ]

        if common_lines:
            bus_straight_m = _haversine_m(
                board_pier["lat"],
                board_pier["lon"],
                alight_pier["lat"],
                alight_pier["lon"],
            )

            duration = _estimate_duration(
                start_distance + end_distance, bus_straight_m, 0
            )

            for line in common_lines[:2]:
                suggestions.append({
                    "walk_in_m": start_distance,
                    "walk_out_m": end_distance,
                    "duration": duration,
                    "board": board_pier,
                    "alight": alight_pier,
                    "line": line,
                })

    if not suggestions:
        return _no_route(
            "Bu iki nokta arasında doğrudan bir hat bulunamadı "
            "(ESHOT otobüsü veya İZDENİZ vapuru). "
            "Aktarmalı yolculuk gerekebilir."
        )

    # En az yürüyüş gerektiren öneriler öne çıkar
    suggestions.sort(key=lambda s: s["walk_in_m"] + s["walk_out_m"])
    suggestions = suggestions[:MAX_SUGGESTIONS]

    routes = []

    for item in suggestions:
        line = item["line"]
        board = item["board"]
        alight = item["alight"]

        bus_leg = _bus_leg(line["n"], board, alight)
        bus_leg["type"] = line["t"]

        if line["t"] == "ferry":
            bus_leg["name"] = "İZDENİZ Vapur"
        else:
            bus_leg["name"] = f"ESHOT {line['n']}"

        if line.get("l"):
            bus_leg["long_name"] = line["l"]

        legs = [
            _walking_leg(
                item["walk_in_m"],
                None,
                board["name"],
            ),
            bus_leg,
            _walking_leg(
                item["walk_out_m"],
                alight["name"],
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
        "source": "ESHOT + İZDENİZ",
        "note": "Süre ve mesafeler tahminidir; sefer saatleri için eshot.gov.tr ve izdeniz.com'a bakabilirsin.",
    }

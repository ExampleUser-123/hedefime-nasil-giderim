import requests
import json
from datetime import datetime

from services.cache import cached


IETT_ROUTER_URL = "https://nasilgiderim.iett.gov.tr/router"


def _timestamp_to_datetime(timestamp):
    """İETT'nin timestamp değerini datetime'a çevirir."""
    if not timestamp:
        return None

    return datetime.fromtimestamp(timestamp / 1000)


def _format_time(timestamp):
    """Timestamp -> HH:MM."""
    dt = _timestamp_to_datetime(timestamp)

    if not dt:
        return None

    return dt.strftime("%H:%M")


def _get_stop_name(stop):
    if not stop:
        return None

    return (
        stop.get("name")
        or stop.get("stopName")
        or stop.get("stationName")
        or None
    )


def _get_stop_names(stops):
    """Bir leg içindeki durak isimlerini temiz şekilde çıkarır."""
    names = []

    for stop in stops:
        name = _get_stop_name(stop)

        if name and name not in names:
            names.append(name)

    return names


def _get_stop_coords(stops):
    """Durak koordinatlarını [lat, lon] listesi olarak çıkarır.
    İETT cevabında koordinat yoksa boş liste döner."""

    coords = []

    for stop in stops:
        if not stop:
            continue

        point = stop.get("point")

        try:
            if point and len(point) >= 2:
                coords.append([float(point[0]), float(point[1])])
        except (TypeError, ValueError):
            continue

    return coords


def _decode_polyline(encoded):
    """Google encoded polyline çözücü → [[lat, lon], ...]"""

    coords = []
    index = 0
    lat = 0
    lon = 0

    while index < len(encoded):
        for multiplier in (1, 100000):
            result = 0
            shift = 0

            while True:
                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5

                if byte < 0x20:
                    break

            value = (result >> 1) ^ -(result & 1)

            if multiplier == 1:
                lat += value
            else:
                lon += value

        coords.append([lat / 100000, lon / 100000])

    return coords


def _get_leg_coords(leg, stops):
    """Leg geometrisini sections polyline'larından çözer,
    yoksa durak noktalarına düşer."""

    coords = []

    for section in leg.get("sections", []):
        polyline = section.get("polyline") if section else None

        if polyline:
            coords.extend(_decode_polyline(polyline))

    if not coords:
        coords = _get_stop_coords(stops)

    return coords


def _parse_leg(leg):
    """
    İETT router'daki tek bir yolculuk ayağını
    uygulamanın kullanacağı formata çevirir.
    """

    route_id = leg.get("routeId")
    line_id = leg.get("lineId")
    line_name = leg.get("lineName", "")
    transport_type = leg.get("type")

    stops = leg.get("stops", [])
    stop_names = _get_stop_names(stops)
    leg_coords = _get_leg_coords(leg, stops)

    # Yürüme ayağı
    if route_id == "walking":
        return {
            "type": "walking",
            "line": None,
            "name": "Yürüme",
            "route_id": "walking",
            "distance_m": leg.get("walkDistance", 0),
            "departure_time": _format_time(
                leg.get("departureTime")
            ),
            "arrival_time": _format_time(
                leg.get("arrivalTime")
            ),
            "from_stop": None,
            "to_stop": None,
            "alternate_lines": [],
            "coords": leg_coords
        }

    # Toplu taşıma ayağı
    return {
        "type": transport_type or "public_transport",
        "line": line_id,
        "name": line_name,
        "route_id": route_id,
        "departure_time": _format_time(
            leg.get("departureTime")
        ),
        "arrival_time": _format_time(
            leg.get("arrivalTime")
        ),
        "from_stop": stop_names[0] if stop_names else None,
        "to_stop": stop_names[-1] if stop_names else None,
        "stops": stop_names,
        "alternate_lines": leg.get("alternateLineId", []),
        "coords": leg_coords
    }


def _fix_leg_connections(legs, start_name, destination_name):
    """
    Leg'ler arasındaki başlangıç/bitiş noktalarını düzeltir.

    Amaç:
    walking -> toplu taşıma -> walking -> toplu taşıma
    gibi zincirlerde durakların doğru bağlanmasını sağlamak.
    """

    if not legs:
        return legs

    for index, leg in enumerate(legs):

        # İlk ayağın başlangıcı
        if index == 0:
            leg["from_stop"] = start_name

        # Son ayağın bitişi
        if index == len(legs) - 1:
            leg["to_stop"] = destination_name

        # Ortadaki ayaklar
        if index > 0:
            previous_leg = legs[index - 1]

            previous_destination = previous_leg.get("to_stop")

            if previous_destination:
                leg["from_stop"] = previous_destination

        # Walking ayağının bir sonraki toplu taşıma
        # ayağına bağlanması
        if leg["type"] == "walking" and index < len(legs) - 1:

            next_leg = legs[index + 1]

            next_from = next_leg.get("from_stop")

            if next_from:
                leg["to_stop"] = next_from

        # Toplu taşıma ayağının bir sonraki walking
        # ayağına bağlanması
        elif leg["type"] != "walking" and index < len(legs) - 1:

            next_leg = legs[index + 1]

            if next_leg["type"] == "walking":
                if leg.get("to_stop"):
                    next_leg["from_stop"] = leg["to_stop"]

    return legs


@cached(ttl_seconds=600, should_cache=lambda r: r.get("status") == "success")
def find_public_transport_route(
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    time="12:00",
    date=None,
    optimizefor="time"
):
    """
    İETT Nasıl Giderim router'ından toplu taşıma rotalarını getirir.
    """

    if date is None:
        date = datetime.now().strftime("%d-%m-%Y")

    params = {
        "from": f"{start_lat},{start_lon}",
        "to": f"{end_lat},{end_lon}",
        "time": time,
        "date": date,
        "isArrival": "false",
        "optimizefor": optimizefor
    }

    try:
        response = requests.get(
            IETT_ROUTER_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()
    except requests.RequestException:
        return {
            "transport_type": "public_transport",
            "status": "error",
            "error": "Toplu taşıma servisine şu anda ulaşılamadı.",
            "routes": []
        }

    # Türkçe karakterlerin düzgün okunması için
    try:
        data = json.loads(response.content.decode("utf-8-sig"))
    except ValueError:
        return {
            "transport_type": "public_transport",
            "status": "error",
            "error": "Toplu taşıma servisi beklenmeyen bir cevap verdi.",
            "routes": []
        }

    # Router hata döndürdüyse
    if data.get("error"):
        return {
            "transport_type": "public_transport",
            "status": "no_route",
            "error": data["error"],
            "routes": []
        }

    routes = []

    for route in data.get("routes", []):

        legs = []

        path = route.get("path", [])

        # Her leg'i parse et
        for leg in path:
            parsed_leg = _parse_leg(leg)
            legs.append(parsed_leg)

        # Leg bağlantılarını düzelt
        legs = _fix_leg_connections(
            legs,
            start_name="start",
            destination_name="destination"
        )

        departure_time = _format_time(
            route.get("departureTime")
        )

        arrival_time = _format_time(
            route.get("arrivalTime")
        )

        duration_minutes = None

        if (
            route.get("departureTime")
            and route.get("arrivalTime")
        ):
            duration_minutes = round(
                (
                    route["arrivalTime"]
                    - route["departureTime"]
                ) / 60000
            )

        routes.append({
            "fee": route.get("totalFee"),
            "walking_distance_m": route.get(
                "walkDistance",
                0
            ),
            "calories_burned": route.get(
                "caloriesBurned"
            ),
            "co2_emission": route.get(
                "CO2Emission"
            ),
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "duration_minutes": duration_minutes,
            "legs": legs
        })

    return {
        "transport_type": "public_transport",
        "status": "success",
        "routes": routes,
        "source": "İETT",
    }


def find_transit_routes(
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    start_province=None,
    end_province=None
):
    """
    İle göre uygun toplu taşıma sağlayıcısını seçer.

    - İstanbul: İETT router (tam A→B rota planı)
    - İzmir: ESHOT açık veri (doğrudan hat önerisi)
    - Kocaeli, Konya: GTFS'ten derlenen veri
    - Antalya, Adana: KentKart servisinden derlenen veri
    """

    def _province_name(province):
        if isinstance(province, dict):
            return province.get("name")
        return province

    start_city = _province_name(start_province)
    end_city = _province_name(end_province)

    if start_city != end_city or start_city is None:
        return find_public_transport_route(
            start_lat,
            start_lon,
            end_lat,
            end_lon
        )

    if start_city == "İzmir":
        from services.izmir import find_izmir_route

        return find_izmir_route(start_lat, start_lon, end_lat, end_lon)

    if start_city == "İstanbul":
        # İETT (otobüs/vapur/dolmuş) + OSM raylı ağ (metro/Marmaray/tramvay)
        from concurrent.futures import ThreadPoolExecutor
        from services.istanbul_rail import find_rail_route

        with ThreadPoolExecutor(max_workers=2) as pool:
            iett_future = pool.submit(
                find_public_transport_route,
                start_lat, start_lon, end_lat, end_lon,
            )
            rail_future = pool.submit(
                find_rail_route,
                start_lat, start_lon, end_lat, end_lon,
            )
            iett_result = iett_future.result()
            rail_result = rail_future.result()

        iett_ok = iett_result.get("status") == "success"
        rail_ok = rail_result.get("status") == "success"

        if iett_ok and rail_ok:
            merged = iett_result["routes"] + rail_result["routes"]
            merged.sort(key=lambda r: r.get("duration_minutes") or 9999)
            iett_result["routes"] = merged
            iett_result["source"] = "İETT + Metro İstanbul"
            return iett_result

        if rail_ok:
            return rail_result

        if iett_ok:
            return iett_result

        return rail_result if rail_result.get("error") else iett_result

    direct_providers = {
        "Kocaeli": ("services.kocaeli", "find_kocaeli_route"),
        "Konya": ("services.konya", "find_konya_route"),
        "Antalya": ("services.antalya", "find_antalya_route"),
        "Adana": ("services.adana", "find_adana_route"),
        "Gaziantep": ("services.kentkart_cities", "find_gaziantep_route"),
        "Muğla": ("services.kentkart_cities", "find_mugla_route"),
        "Sivas": ("services.kentkart_cities", "find_sivas_route"),
        "Düzce": ("services.kentkart_cities", "find_duzce_route"),
        "Erzurum": ("services.kentkart_cities", "find_erzurum_route"),
        "Ordu": ("services.kentkart_cities", "find_ordu_route"),
        "Zonguldak": ("services.kentkart_cities", "find_zonguldak_route"),
        "Çanakkale": ("services.kentkart_cities", "find_canakkale_route"),
        "Samsun": ("services.kentkart_cities", "find_samsun_route"),
        "Edirne": ("services.kentkart_cities", "find_edirne_route"),
    }

    provider = direct_providers.get(start_city)

    if provider is None:
        return find_public_transport_route(
            start_lat,
            start_lon,
            end_lat,
            end_lon
        )

    import importlib

    module = importlib.import_module(provider[0])

    return getattr(module, provider[1])(
        start_lat,
        start_lon,
        end_lat,
        end_lon
    )
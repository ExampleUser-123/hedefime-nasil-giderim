import requests
import json
from datetime import datetime


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
            "alternate_lines": []
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
        "alternate_lines": leg.get("alternateLineId", [])
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

    response = requests.get(
        IETT_ROUTER_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    # Türkçe karakterlerin düzgün okunması için
    data = response.content.decode("utf-8-sig")
    data = json.loads(data)

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
        "routes": routes
    }
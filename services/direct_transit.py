"""
Ortak "dogrudan hat onerisi" saglayici motoru.

Durak-hat verisi (data/ altinda sikistirilmis JSON) olan
sehirler icin calisir: Kocaeli (GTFS'ten derlendi),
Konya (GTFS), Antalya ve Adana (KentKart servisinden derlendi).

Yontem: baslangica ve hedefe en yakın duraklarin gecen hatlarinin
kesisimiyle "yürü → bin → in → yürü" önerileri üretilir.
"""

import gzip
import json
import os

from services.izmir import (
    _bus_leg,
    _estimate_duration,
    _haversine_m,
    _no_route,
    _stops_near_adaptive,
    _walking_leg,
)


# Merkezlerde durak yogunlugu yuksek oldugu icin eslesme havuzu genis tutulur
MAX_PAIR_STOPS_PER_SIDE = 12
MAX_SUGGESTIONS = 3


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_stop_data(filename):
    """Sikistirilmis durak-hat verisini yükler; basarisizsa None döner."""

    path = os.path.join(DATA_DIR, filename)

    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            stops = json.load(f)
    except (OSError, ValueError):
        return None

    for stop in stops:
        stop["line_keys"] = {line["n"] for line in stop["lines"]}

    return stops


def make_finder(
    data_filename,
    source_label,
    city_label,
    hours_note_url=None,
    no_stop_message=None,
    no_route_message=None,
    ferry_label=None,
):
    """
    Bir sehir icin find_route(lat/lon x2) fonksiyonu üretir.
    Döndürülen fonksiyon diger saglayicilarla ayni yanit semasini verir.
    """

    stops = load_stop_data(data_filename)

    def _no_route_msg():
        return (
            no_route_message
            or "Bu iki nokta arasında doğrudan bir hat bulunamadı. "
            "Aktarmalı yolculuk gerekebilir."
        )

    def find_route(start_lat, start_lon, end_lat, end_lon):
        if not stops:
            return {
                "transport_type": "public_transport",
                "status": "error",
                "error": f"{city_label} toplu taşıma verisi yüklenemedi.",
                "routes": [],
                "source": source_label,
            }

        near_start = _stops_near_adaptive(stops, start_lat, start_lon)
        near_end = _stops_near_adaptive(stops, end_lat, end_lon)

        if not near_start or not near_end:
            return _no_route(
                no_stop_message
                or f"Yakın çevrede {city_label} durağı bulunamadı. "
                "Başlangıç ve hedefin şehir sınırları içinde olduğundan emin ol.",
                source=source_label,
            )

        suggestions = []

        for start_distance, board_stop in near_start[:MAX_PAIR_STOPS_PER_SIDE]:
            for end_distance, alight_stop in near_end[:MAX_PAIR_STOPS_PER_SIDE]:
                if board_stop["id"] == alight_stop["id"]:
                    continue

                common_lines = board_stop["line_keys"] & alight_stop["line_keys"]

                if not common_lines:
                    continue

                straight_m = _haversine_m(
                    board_stop["lat"],
                    board_stop["lon"],
                    alight_stop["lat"],
                    alight_stop["lon"],
                )

                if straight_m < 200:
                    continue

                duration = _estimate_duration(
                    start_distance + end_distance, straight_m, 0
                )

                for line_key in sorted(common_lines)[:2]:
                    suggestions.append({
                        "walk_in_m": start_distance,
                        "walk_out_m": end_distance,
                        "duration": duration,
                        "board": board_stop,
                        "alight": alight_stop,
                        "line_key": line_key,
                        "line_info": _line_info(board_stop, line_key),
                    })

        if not suggestions:
            return _no_route(
                _no_route_msg(),
                source=source_label,
            )

        suggestions.sort(key=lambda s: s["walk_in_m"] + s["walk_out_m"])
        suggestions = suggestions[:MAX_SUGGESTIONS]

        routes = []

        for item in suggestions:
            line_display = item["line_key"]
            info = item["line_info"] or {}
            leg_type = info.get("t", "bus")
            long_name = info.get("l") or ""

            bus_leg = _bus_leg(line_display, item["board"], item["alight"])
            bus_leg["type"] = leg_type

            if leg_type == "ferry" and ferry_label:
                bus_leg["name"] = (
                    f"{ferry_label} ({long_name})"
                    if long_name
                    else ferry_label
                )
            else:
                bus_leg["name"] = f"{line_display}"
                if long_name:
                    bus_leg["long_name"] = long_name

            bus_leg["route_id"] = f"{source_label.lower()}:{line_display}"

            legs = [
                _walking_leg(item["walk_in_m"], None, item["board"]["name"]),
                bus_leg,
                _walking_leg(item["walk_out_m"], item["alight"]["name"], None),
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

        note = "Süre ve mesafeler tahminidir."
        if hours_note_url:
            note += f" Sefer saatleri için {hours_note_url} adresine bakabilirsin."

        return {
            "transport_type": "public_transport",
            "status": "success",
            "routes": routes,
            "source": source_label,
            "note": note,
        }

    return find_route


def _line_info(stop, line_key):
    for line in stop["lines"]:
        if line["n"] == line_key:
            return line
    return None

"""
Kocaeli toplu taşıma sağlayıcısı.

Kocaeli Büyükşehir Belediyesi açık veri portalındaki
Toplu Ulaşım GTFS Verisi'nden önceden derlenmiş
'durak -> hatlar' veri dosyasını kullanır (data/kocaeli_transit.json.gz).

İETT gibi hazır bir A→B router'ı olmadığı için İzmir'deki gibi
"doğrudan hat önerisi" yöntemiyle çalışır:

1. Başlangıç ve hedef noktasına en yakın duraklar bulunur.
2. Bu duraklardan geçen hatların kesişimi alınır.
3. Ortak hatlarla "yürü → bin → in → yürü" önerileri üretilir.
"""

import gzip
import json
import math
import os

from services.izmir import (
    MAX_SUGGESTIONS,
    MAX_STOPS_PER_SIDE,
    _bus_leg,
    _estimate_duration,
    _haversine_m,
    _no_route,
    _stops_near_adaptive,
    _walking_leg,
)


DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "kocaeli_transit.json.gz",
)


def _line_display(line):
    return line["n"]


def _load_stops():
    """GTFS'ten derlenmiş durak verisini yükler (sıkıştırılmış JSON)."""

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
        stops = json.load(f)

    # Hat numaralarına hızlı erişim için kesişim karşılaştırmalarını kolaylaştır
    for stop in stops:
        stop["line_keys"] = {
            line["n"] for line in stop["lines"]
        }

    return stops


try:
    _STOPS_CACHE = _load_stops()
except (OSError, ValueError):
    _STOPS_CACHE = None


def _line_type(board_stop, alight_stop, line_key):
    """Ortak hattın taşıma tipini bulur (bus/tram/...)."""

    for line in board_stop["lines"]:
        if line["n"] == line_key:
            return line["t"]
    return "bus"


def _line_long_name(board_stop, line_key):
    for line in board_stop["lines"]:
        if line["n"] == line_key:
            return line.get("l") or ""
    return ""


def find_kocaeli_route(start_lat, start_lon, end_lat, end_lon):
    """
    Kocaeli için A→B toplu taşıma önerisi üretir.
    Diğer sağlayıcılarla aynı yanıt şemasını döndürür.
    """

    stops = _STOPS_CACHE

    if not stops:
        return {
            "transport_type": "public_transport",
            "status": "error",
            "error": "Kocaeli toplu taşıma verisi yüklenemedi.",
            "routes": [],
            "source": "Kocaeli Ulaşım",
        }

    near_start = _stops_near_adaptive(stops, start_lat, start_lon)
    near_end = _stops_near_adaptive(stops, end_lat, end_lon)

    if not near_start or not near_end:
        return _no_route(
            "Yakın çevrede Kocaeli Ulaşım durağı bulunamadı. "
            "Başlangıç ve hedefin Kocaeli il sınırları içinde olduğundan emin ol.",
            source="Kocaeli Ulaşım",
        )

    suggestions = []

    for start_distance, board_stop in near_start[:MAX_STOPS_PER_SIDE]:
        for end_distance, alight_stop in near_end[:MAX_STOPS_PER_SIDE]:
            if board_stop["id"] == alight_stop["id"]:
                continue

            common_lines = board_stop["line_keys"] & alight_stop["line_keys"]

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

            for line_key in sorted(common_lines)[:2]:
                suggestions.append({
                    "walk_in_m": start_distance,
                    "walk_out_m": end_distance,
                    "duration": duration,
                    "board": board_stop,
                    "alight": alight_stop,
                    "line_key": line_key,
                    "line_type": _line_type(board_stop, alight_stop, line_key),
                    "line_long": _line_long_name(board_stop, line_key),
                })

    if not suggestions:
        return _no_route(
            "Bu iki nokta arasında doğrudan bir hat bulunamadı. "
            "Aktarmalı yolculuk gerekebilir.",
            source="Kocaeli Ulaşım",
        )

    # En az yürüyüş gerektiren öneriler öne çıkar
    suggestions.sort(key=lambda s: s["walk_in_m"] + s["walk_out_m"])
    suggestions = suggestions[:MAX_SUGGESTIONS]

    routes = []

    for item in suggestions:
        line_display = item["line_key"]
        leg_type = item["line_type"]

        bus_leg = _bus_leg(line_display, item["board"], item["alight"])
        bus_leg["type"] = leg_type

        if leg_type == "ferry":
            bus_leg["name"] = (
                f"Vapur ({item['line_long']})"
                if item["line_long"]
                else "Vapur"
            )
        else:
            bus_leg["name"] = f"{line_display}"
            if item["line_long"]:
                bus_leg["long_name"] = item["line_long"]
        bus_leg["route_id"] = f"kocaeli:{line_display}"

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

    return {
        "transport_type": "public_transport",
        "status": "success",
        "routes": routes,
        "source": "Kocaeli Ulaşım",
        "note": "Süre ve mesafeler tahminidir; sefer saatleri için kocaeli.bel.tr/hatlar adresine bakabilirsin.",
    }

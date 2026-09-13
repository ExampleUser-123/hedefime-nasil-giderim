# -*- coding: utf-8 -*-
"""
Hat detay sayfasi servisi.

Sehir durak-hat verisinden (data/{sehir}_transit.json.gz veya
data/kentkart_{sehir}.json.gz) bir hattin gectigi duraklari dondurur.
Kullanicinin konumu verildiyse duraklar mesafeye gore siralanir; en yakin
durak icin GTFS'ten gercek kalkis saatleri (varsa) eklenir.
"""

import gzip
import json
import os
from typing import Optional

from services.gtfs_times import next_departures as gtfs_next_departures
from services.offline_data import DATA_DIR, _normalize

_CACHE: dict[str, Optional[list]] = {}


def _load_city(city: str) -> Optional[list]:
    norm = _normalize(city)
    if norm in _CACHE:
        return _CACHE[norm]

    stops = None
    for fname in (f"{norm}_transit.json.gz", f"kentkart_{norm}.json.gz"):
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            continue
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                stops = json.load(f)
            break
        except (OSError, ValueError):
            continue

    _CACHE[norm] = stops
    return stops


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return int(6371000 * 2 * asin(min(1.0, sqrt(a))))


def line_details(city: str, line_no: str, lat: Optional[float] = None,
                 lon: Optional[float] = None) -> Optional[dict]:
    stops = _load_city(city)
    if not stops or not line_no:
        return None

    target = _normalize(line_no)
    matched: list[dict] = []
    line_type: Optional[str] = None
    line_name: Optional[str] = None

    for stop in stops:
        for line in stop.get("lines", []):
            if _normalize(str(line.get("n", ""))) != target:
                continue
            if line_type is None:
                line_type = line.get("t")
                line_name = line.get("l")
            if lat is not None and lon is not None:
                dist = _haversine_m(lat, lon, stop.get("lat", 0), stop.get("lon", 0))
            else:
                dist = None
            matched.append({
                "name": stop.get("name", ""),
                "lat": stop.get("lat"),
                "lon": stop.get("lon"),
                "distance_m": dist,
            })
            break

    if not matched:
        return None

    if lat is not None and lon is not None:
        matched.sort(key=lambda s: s["distance_m"] or 0)

    matched = matched[:300]

    departures: list[dict] = []
    nearest = matched[0]
    if nearest.get("lat") is not None and nearest.get("lon") is not None:
        try:
            departures = gtfs_next_departures(
                city, line_no, nearest["name"], nearest["lat"], nearest["lon"],
            )[:4]
        except Exception:
            departures = []

    return {
        "city": city,
        "line": line_no,
        "name": line_name,
        "type": line_type,
        "stop_count": len(matched),
        "stops": matched,
        "next_departures": departures,
    }

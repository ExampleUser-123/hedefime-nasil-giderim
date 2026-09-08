"""Yakın duraklar + duraktaki sonraki kalkışlar (tüm şehirler).

data/{sehir}_transit.json.gz dosyalarındaki durakları ilk istekte lazy
yükleyip global cache'te tutar. nearby_stops() tüm şehirlerin duraklarını
Haversine ile tarayıp mesafe artan sırada döner; stop_departures() her hat
için GTFS saatini (yoksa tahmini) alıp birleştirir.
"""

from __future__ import annotations

import gzip
import json
import math
import threading
from datetime import datetime
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_lock = threading.Lock()
_all_stops: list[dict] | None = None  # [{"city","stop_id","name","lat","lon","lines":[hat_no,...]}]


def _city_from_filename(fname: str) -> str:
    # "trabzon_transit.json.gz" -> "Trabzon"
    base = fname
    for suffix in (".json.gz", ".gz", ".json"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    base = base.replace("_transit", "").replace("_transit", "")
    return base.replace("_", " ").strip().capitalize()


def _load_all_stops() -> list[dict]:
    """Tüm şehirlerin duraklarını belleğe yükler (thread-safe, bir kez)."""
    global _all_stops
    if _all_stops is not None:
        return _all_stops
    with _lock:
        if _all_stops is not None:
            return _all_stops
        stops: list[dict] = []
        if _DATA_DIR.is_dir():
            for f in sorted(_DATA_DIR.glob("*_transit.json.gz")):
                city = _city_from_filename(f.name)
                try:
                    with gzip.open(f, "rt", encoding="utf-8") as fh:
                        data = json.load(fh)
                    for s in data if isinstance(data, list) else []:
                        try:
                            lat = float(s.get("lat"))
                            lon = float(s.get("lon"))
                        except (TypeError, ValueError):
                            continue
                        lines = []
                        for ln in s.get("lines") or []:
                            n = (ln or {}).get("n")
                            if n is not None and str(n) not in lines:
                                lines.append(str(n))
                        stops.append({
                            "city": city,
                            "stop_id": str(s.get("id") or ""),
                            "name": str(s.get("name") or ""),
                            "lat": lat,
                            "lon": lon,
                            "lines": lines,
                        })
                except Exception:
                    continue
        _all_stops = stops
        return stops


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearby_stops(lat: float, lon: float, limit: int = 8) -> list[dict]:
    """Konuma en yakın duraklar, mesafe artan sırada."""
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return []
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return []
    limit = max(0, int(limit or 8))

    stops = _load_all_stops()
    scored = []
    for s in stops:
        d = _haversine_m(lat, lon, s["lat"], s["lon"])
        scored.append((d, s))
    scored.sort(key=lambda x: x[0])

    return [
        {
            "city": s["city"],
            "stop_id": s["stop_id"],
            "name": s["name"],
            "lat": s["lat"],
            "lon": s["lon"],
            "distance_m": round(d, 1),
            "lines": list(s["lines"]),
        }
        for d, s in scored[:limit]
    ]


def stop_departures(
    city: str,
    stop_name: str,
    lat: float,
    lon: float,
    lines: list[str],
    max_total: int = 6,
) -> list[dict]:
    """Duraktaki tüm hatların sonraki kalkışları, minutes_ahead'e göre sıralı.

    Önce GTFS (services.gtfs_times.next_departures), boşsa tahmini
    (services.estimate_times.estimate_departures). Hiçbir exception dışarı sızmaz.
    """
    try:
        max_total = max(0, int(max_total or 6))
    except (TypeError, ValueError):
        max_total = 6

    now_dt = datetime.now()
    merged: list[dict] = []

    from services.gtfs_times import next_departures, index_ready
    from services.estimate_times import estimate_departures

    # Indeks cache'te yoksa GTFS'i HIC DENEME: kurulum lock'u dakikalar surebilir
    # (Render 502). Tahmini saatlerle hemen cevap ver; warm_index arka planda
    # kurar, sonraki isteklerde gercek GTFS doner.
    gtfs_usable = index_ready(city)

    for line in lines or []:
        line_no = str(line)
        deps: list[dict] = []
        if gtfs_usable:
            try:
                deps = next_departures(city, line_no, stop_name, lat, lon, now_dt)
            except Exception:
                deps = []
        if not deps:
            try:
                deps = estimate_departures(city, line_no, stop_name, now_dt)
            except Exception:
                deps = []
        if not deps:
            continue
        d0 = deps[0]  # her hat için ilk sonraki kalkış
        try:
            ma = int(d0.get("minutes_ahead"))
        except (TypeError, ValueError):
            continue
        merged.append({
            "line": line_no,
            "time": d0.get("time"),
            "source": d0.get("source", "tahmini"),
            "minutes_ahead": ma,
        })

    merged.sort(key=lambda d: d["minutes_ahead"])
    return merged[:max_total]

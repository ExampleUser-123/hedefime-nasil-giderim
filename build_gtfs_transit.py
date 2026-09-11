# -*- coding: utf-8 -*-
"""GTFS zip -> {city}_transit.json.gz (Duraklar sekmesi için durak+hat üretir).

Kullanım: python build_gtfs_transit.py [sehir1 sehir2 ...]
Argümansız: data/gtfs/*_gtfs.zip taranır, {city}_transit.json.gz olmayanlar üretilir.
"""
import csv
import gzip
import io
import json
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
GTFS_DIR = BASE / "data" / "gtfs"
DATA_DIR = BASE / "data"


def build(city: str) -> bool:
    zip_path = GTFS_DIR / f"{city}_gtfs.zip"
    out_path = DATA_DIR / f"{city}_transit.json.gz"
    if not zip_path.exists():
        print(f"{city}: zip yok, atlandi")
        return False

    routes = {}   # route_id -> gorunen hat adi
    trips = {}    # trip_id -> route_id
    stops = {}    # stop_id -> (name, lat, lon)
    stop_lines = {}  # stop_id -> set(route adlari)

    with zipfile.ZipFile(zip_path) as zf:
        def rows(name):
            info = None
            for cand in (name, name.lower()):
                try:
                    info = zf.getinfo(cand)
                    break
                except KeyError:
                    continue
            if info is None:
                return iter(())
            return csv.DictReader(io.TextIOWrapper(zf.open(info), encoding="utf-8-sig"))

        for r in rows("routes.txt"):
            rid = (r.get("route_id") or "").strip()
            if rid:
                routes[rid] = (r.get("route_short_name") or r.get("route_long_name") or "").strip()

        for t in rows("trips.txt"):
            tid = (t.get("trip_id") or "").strip()
            if tid:
                trips[tid] = (t.get("route_id") or "").strip()

        for s in rows("stops.txt"):
            sid = (s.get("stop_id") or "").strip()
            try:
                lat, lon = float(s.get("stop_lat")), float(s.get("stop_lon"))
            except (TypeError, ValueError):
                continue
            if sid:
                stops[sid] = ((s.get("stop_name") or "").strip(), lat, lon)

        for row in rows("stop_times.txt"):
            tid = (row.get("trip_id") or "").strip()
            rid = trips.get(tid)
            sid = (row.get("stop_id") or "").strip()
            if not rid or not sid:
                continue
            name = routes.get(rid)
            if name:
                stop_lines.setdefault(sid, set()).add(name)

    out = []
    for sid, (name, lat, lon) in stops.items():
        lines = sorted(stop_lines.get(sid) or ())
        out.append({
            "id": sid,
            "name": name,
            "lat": lat,
            "lon": lon,
            "lines": [{"n": n} for n in lines],
        })
    out.sort(key=lambda s: s["name"])

    with gzip.open(out_path, "wt", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{city}: {len(out)} durak -> {out_path.name}")
    return True


def main():
    cities = sys.argv[1:]
    if not cities:
        cities = [p.name[:-10] for p in GTFS_DIR.glob("*_gtfs.zip")
                  if not (DATA_DIR / (p.name[:-10] + "_transit.json.gz")).exists()]
    for c in cities:
        build(c)


if __name__ == "__main__":
    main()

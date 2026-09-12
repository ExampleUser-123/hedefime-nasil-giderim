# Diyarbakir + Van derleme (Alanya zaten hazir formatta)
import gzip
import json

def dump(path, stops):
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(stops, f, ensure_ascii=False, separators=(",", ":"))
    print(path, len(stops), "durak")

# --- Diyarbakir: duraklar + hat yonleri (durakId eslesmesi %100) ---
stops = json.load(gzip.open("data/research_se_diyarbakir/diyarbakir_stops_raw.json.gz", "rt", encoding="utf-8"))
lines = json.load(gzip.open("data/research_fix5_diyarbakir/line_directions_all.json.gz", "rt", encoding="utf-8"))

stop_lines = {}  # durakId -> set(lineCode)
for code, obj in lines.items():
    for row in obj["raw"]["data"]:
        stop_lines.setdefault(row["durakId"], set()).add(code.strip())

out = []
for s in stops:
    sid = int(s["id"])
    lns = stop_lines.get(sid, set())
    if not lns:
        continue
    out.append({
        "id": f"dyr_{sid}",
        "name": (s.get("name") or "").strip(),
        "lat": s["lat"],
        "lon": s["lon"],
        "lines": [{"n": c, "t": "bus", "l": ""} for c in sorted(lns)],
    })
dump("data/diyarbakir_transit.json.gz", out)

# --- Van: BelvanKart temiz veri (kendi durak koordinatlarini icerir) ---
routes = json.load(gzip.open("data/research_fix5_van/van_lines_stops_clean.json.gz", "rt", encoding="utf-8"))

acc = {}  # stopId -> stop dict + line set
for rid, r in routes.items():
    title = (r.get("title") or r.get("routeCode") or "").strip()
    no = str(r.get("routeNo") or "").strip()
    for v in r.get("variants", []):
        for st in v.get("stops", []):
            key = int(st["id"])
            e = acc.get(key)
            if e is None:
                e = acc[key] = {
                    "id": f"van_{key}",
                    "name": (st.get("name") or "").strip(),
                    "lat": st["lat"],
                    "lon": st["lon"],
                    "lines": set(),
                }
            e["lines"].add((no, title))

out = []
for e in acc.values():
    if not e["lines"]:
        continue
    out.append({
        "id": e["id"],
        "name": e["name"],
        "lat": e["lat"],
        "lon": e["lon"],
        "lines": [{"n": n, "t": "bus", "l": t} for n, t in sorted(e["lines"])],
    })
dump("data/van_transit.json.gz", out)

# --- Dogrulama ---
checks = {
    "diyarbakir_transit.json.gz": (37.7, 38.1, 40.0, 40.5),
    "van_transit.json.gz": (38.3, 39.2, 43.0, 44.0),
}
for fname, (lat0, lat1, lon0, lon1) in checks.items():
    d = json.load(gzip.open("data/" + fname, "rt", encoding="utf-8"))
    lats = [s["lat"] for s in d]
    lons = [s["lon"] for s in d]
    ok = min(lats) >= lat0 and max(lats) <= lat1 and min(lons) >= lon0 and max(lons) <= lon1
    with_lines = sum(1 for s in d if s["lines"])
    print(fname, "bbox-ok:", ok, "| hatli durak:", with_lines, "/", len(d))

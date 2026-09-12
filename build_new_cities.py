# Yeni sehir verilerini transit formatina derle:
# Sanliurfa, Kahramanmaras, Kastamonu + Samsun kayit duzeltmesi
import gzip, json

def dump(path, stops):
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(stops, f, ensure_ascii=False, separators=(",", ":"))
    print(path, len(stops), "durak")

# --- Sanliurfa: urfakart {id,name,code,display,lat,lng,lines:[kod]}
stops = json.load(open("data/research_se_sanliurfa/urfakart_stops.json", encoding="utf-8"))
out = []
for s in stops:
    out.append({
        "id": f"urf_{s.get('id')}",
        "name": (s.get("display") or s.get("name") or "").strip(),
        "lat": s["lat"],
        "lon": s["lng"],
        "lines": [{"n": str(ln), "t": "bus", "l": ""} for ln in (s.get("lines") or [])],
    })
dump("data/sanliurfa_transit.json.gz", out)

# --- Kahramanmaras: ayni sema
stops = json.load(open("data/research_se_kmaras/kahramanmaras_stops.json", encoding="utf-8"))
out = []
for s in stops:
    out.append({
        "id": f"kmr_{s.get('id')}",
        "name": (s.get("display") or s.get("name") or "").strip(),
        "lat": s["lat"],
        "lon": s["lng"],
        "lines": [{"n": str(ln), "t": "bus", "l": ""} for ln in (s.get("lines") or [])],
    })
dump("data/kahramanmaras_transit.json.gz", out)

# --- Kastamonu: stops_routes.json.gz zaten hedef formatta
stops = json.load(gzip.open("data/research_ka_kastamonu/stops_routes.json.gz", "rt", encoding="utf-8"))
out = []
for s in stops:
    out.append({
        "id": f"kst_{s.get('id')}",
        "name": (s.get("name") or "").strip(),
        "lat": s["lat"],
        "lon": s["lon"],
        "lines": [
            {"n": str(ln.get("n")), "t": "bus", "l": str(ln.get("l") or "")}
            for ln in (s.get("lines") or [])
        ],
    })
dump("data/kastamonu_transit.json.gz", out)

# Koordinat dogrulamasi
checks = {
    "sanliurfa_transit.json.gz": (37.0, 37.35, 38.6, 39.0),
    "kahramanmaras_transit.json.gz": (37.3, 37.7, 36.7, 37.1),
    "kastamonu_transit.json.gz": (41.2, 41.6, 33.5, 34.0),
}
for fname, (lat0, lat1, lon0, lon1) in checks.items():
    d = json.load(gzip.open("data/" + fname, "rt", encoding="utf-8"))
    lats = [s["lat"] for s in d]
    lons = [s["lon"] for s in d]
    ok = min(lats) >= lat0 and max(lats) <= lat1 and min(lons) >= lon0 and max(lons) <= lon1
    with_lines = sum(1 for s in d if s["lines"])
    print(fname, "bbox-ok:", ok, "| hatli durak:", with_lines, "/", len(d))

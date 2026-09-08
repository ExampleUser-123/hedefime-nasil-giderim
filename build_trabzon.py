"""Trabzon TULAS verisini derler: _trb_hat.geojson x _trb_durak.geojson
Hat geometrisine 75m'den yakin duraklar o hatta baglanir.
Cikti: data/trabzon_transit.json.gz
"""

import gzip
import json
import math
import os

MATCH_M = 75.0

durak = json.load(open('_trb_durak.geojson', encoding='utf-8'))['features']
hat = json.load(open('_trb_hat.geojson', encoding='utf-8'))['features']


def haversine_m(lat1, lon1, lat2, lon2):
    r1, r2 = math.radians(lat1), math.radians(lat2)
    dlat = r2 - r1
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(r1) * math.cos(r2) * math.sin(dlon / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(a))


# Izgara indeksi (hat geometri noktalari)
CELL = 0.005
grid = {}
rel_meta = {}

for hidx, hf in enumerate(hat):
    name = (hf['properties'].get('Name') or '').strip()
    if not name:
        continue
    parts = name.split(None, 1)
    line_n = parts[0] if parts and parts[0][:1].isdigit() else name
    line_l = name
    rel_meta[hidx] = (line_n, line_l)

    geom = hf['geometry']
    polys = geom['coordinates'] if geom['type'] == 'MultiLineString' else [geom['coordinates']]
    for line in polys:
        for lon, lat, *_ in line:
            grid.setdefault((int(lat / CELL), int(lon / CELL)), []).append((hidx, lat, lon))


def nearby(lat, lon):
    cy, cx = int(lat / CELL), int(lon / CELL)
    out = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out.extend(grid.get((cy + dy, cx + dx), ()))
    return out


merged = {}

for f in durak:
    name = (f['properties'].get('Name') or '').strip()
    g = f.get('geometry')
    if not name or not g or g['type'] != 'Point':
        continue
    lon, lat = g['coordinates'][0], g['coordinates'][1]

    hit = set()
    for hidx, rlat, rlon in nearby(lat, lon):
        if haversine_m(lat, lon, rlat, rlon) <= MATCH_M:
            hit.add(rel_meta[hidx])

    if not hit:
        continue

    key = (name, round(lat, 3), round(lon, 3))
    if key in merged:
        merged[key]['lines'] |= hit
    else:
        merged[key] = {
            'id': f'trb_{len(merged)}',
            'name': name,
            'lat': lat,
            'lon': lon,
            'lines': set(hit),
        }

stops = []
for e in merged.values():
    seen_n = set()
    lines = []
    for n, l in sorted(e['lines'], key=lambda x: x[0]):
        if n in seen_n:
            continue
        seen_n.add(n)
        lines.append({'n': n, 't': 'bus', 'l': l})
    stops.append({**e, 'lines': lines})

stops.sort(key=lambda s: (s['name'], s['id']))
hat_n = {l['n'] for st in stops for l in st['lines']}
print('durak:', len(stops), 'hat:', len(hat_n))

os.makedirs('data', exist_ok=True)
with gzip.open('data/trabzon_transit.json.gz', 'wt', encoding='utf-8', compresslevel=9) as f:
    json.dump(stops, f, ensure_ascii=False, separators=(',', ':'))

print('yazildi: data/trabzon_transit.json.gz', os.path.getsize('data/trabzon_transit.json.gz') // 1024, 'KB')

# Ornek: ilk 3 duragi yazdir
for st in stops[:3]:
    print('  ornek:', st['name'], '->', [l['n'] for l in st['lines']][:6])

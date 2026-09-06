"""Iliski uye sirasina gore duraklari + cizgi geometrisini ceker -> data/istanbul_rail.json.gz"""

import gzip
import json
import time
import urllib.parse
import urllib.request

OVERPASS = 'https://overpass-api.de/api/interpreter'

KEEP_REFS = {
    'M1A', 'M1B', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M11',
    'T1', 'T2', 'T3', 'T4', 'T5',
    'F1', 'F2', 'F3', 'F4',
    'B1',
}

SKIP_IDS = {19675921, 19675941, 17001642, 19053681}  # baska il/discontinued


def run_query(query, retries=4):
    data = urllib.parse.urlencode({'data': query}).encode()
    req = urllib.request.Request(
        OVERPASS,
        data=data,
        headers={'User-Agent': 'hedefime-nasil-giderim/1.0'},
    )
    for attempt in range(retries):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=300).read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 504) and attempt < retries - 1:
                wait = 25 * (attempt + 1)
                print(f'  HTTP {exc.code}; {wait} sn bekleniyor...', flush=True)
                time.sleep(wait)
                continue
            raise


rels = json.load(open('data/_rail_rels.json', encoding='utf-8'))

selected = []
for rid, tags in rels.items():
    if int(rid) in SKIP_IDS:
        continue
    if (tags.get('ref') or '').strip().upper() in KEEP_REFS:
        selected.append(int(rid))

print(len(selected), 'iliski secildi; uyeler cekiliyor...', flush=True)

geom_data = run_query(
    f'[out:json][timeout:300];rel(id:{",".join(map(str, selected))});out geom;'
)

# rel_id -> sirali durak dugum id listesi + yol geometrisi
per_rel = {}
for el in geom_data['elements']:
    if el['type'] != 'relation':
        continue

    stops = []          # sirali (node_id, lat, lon)
    path = []           # hat cizgisi [lat, lon]

    for member in el.get('members', []):
        if member['type'] == 'node':
            if member.get('role', '') in ('stop', 'stop_position', 'stop_exit_only'):
                stops.append((member['ref'], member['lat'], member['lon']))
            elif not member.get('role'):
                # stack'lenmis durak olmayan dugumler atlanir
                pass
        elif member['type'] == 'way' and member.get('geometry'):
            for pt in member['geometry']:
                if pt.get('lat') is not None:
                    path.append([round(pt['lat'], 5), round(pt['lon'], 5)])

    per_rel[el['id']] = {'tags': el.get('tags', {}), 'stops': stops, 'path': path}

print('Durak isimleri toplanuyor...', flush=True)
node_ids = sorted({nid for v in per_rel.values() for nid, _, _ in v['stops']})

names = {}
CHUNK = 2000
for i in range(0, len(node_ids), CHUNK):
    chunk = node_ids[i:i + CHUNK]
    nd = run_query(f'[out:json][timeout:180];node(id:{",".join(map(str, chunk))});out body;')
    for n in nd.get('elements', []):
        names[n['id']] = (n.get('tags', {}).get('name') or '').strip()
    time.sleep(10)

lines_out = []
for rid, v in per_rel.items():
    tags = v['tags']
    ref = (tags.get('ref') or '').strip()
    clean_stops = []
    seen_names = []
    for nid, lat, lon in v['stops']:
        nm = names.get(nid, '')
        if not nm:
            continue
        if clean_stops and clean_stops[-1]['name'] == nm:
            continue
        clean_stops.append({'name': nm, 'lat': round(lat, 5), 'lon': round(lon, 5)})
        seen_names.append(nm)

    if len(clean_stops) < 3:
        print(f'  atlandi (az durak): {ref} {tags.get("name")}')
        continue

    lines_out.append({
        'ref': ref,
        'name': tags.get('name') or ref,
        'route': tags.get('route'),
        'stops': clean_stops,
        'path': v['path'],
    })
    print(f"  {ref}: {len(clean_stops)} durak | {clean_stops[0]['name']} -> {clean_stops[-1]['name']}", flush=True)

with gzip.open('data/istanbul_rail.json.gz', 'wt', encoding='utf-8') as f:
    json.dump(lines_out, f, ensure_ascii=False, separators=(',', ':'))

print(len(lines_out), 'hat -> data/istanbul_rail.json.gz yazildi')

"""F hatlari + M2 subesi: 2 durakli hatlari cek, onceki dosyaya ekle."""

import gzip
import json
import time
import urllib.parse
import urllib.request

OVERPASS = 'https://overpass-api.de/api/interpreter'

ADD_IDS = [300961, 13313678, 301616, 13313679, 9476599, 9488735, 14738977, 14738978, 7719795, 7719796]


def run_query(query, retries=5):
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
                wait = 30 * (attempt + 1)
                print(f'  HTTP {exc.code}; {wait} sn...', flush=True)
                time.sleep(wait)
                continue
            raise


geom = run_query(
    f'[out:json][timeout:180];rel(id:{",".join(map(str, ADD_IDS))});out geom;'
)

per_rel = {}
node_ids = set()
for el in geom['elements']:
    if el['type'] != 'relation':
        continue
    stops = []
    path = []
    for m in el.get('members', []):
        if m['type'] == 'node':
            if m.get('role', '') in ('stop', 'stop_position'):
                stops.append((m['ref'], m['lat'], m['lon']))
        elif m['type'] == 'way' and m.get('geometry'):
            for pt in m['geometry']:
                if pt.get('lat') is not None:
                    path.append([round(pt['lat'], 5), round(pt['lon'], 5)])
    per_rel[el['id']] = {'tags': el.get('tags', {}), 'stops': stops, 'path': path}
    for nid, _, _ in stops:
        node_ids.add(nid)

print('isimler...', flush=True)
names = {}
nd = run_query(f'[out:json][timeout:120];node(id:{",".join(map(str, sorted(node_ids)))});out body;')
for n in nd.get('elements', []):
    names[n['id']] = (n.get('tags', {}).get('name') or '').strip()

lines_out = json.loads(gzip.open('data/istanbul_rail.json.gz').read().decode('utf-8'))

for rid, v in per_rel.items():
    tags = v['tags']
    ref = (tags.get('ref') or '').strip()
    clean = []
    for nid, lat, lon in v['stops']:
        nm = names.get(nid, '')
        if not nm or (clean and clean[-1]['name'] == nm):
            continue
        clean.append({'name': nm, 'lat': round(lat, 5), 'lon': round(lon, 5)})

    if len(clean) < 2:
        print(f'atlandi: {ref}')
        continue

    lines_out.append({
        'ref': ref,
        'name': tags.get('name') or ref,
        'route': tags.get('route'),
        'stops': clean,
        'path': v['path'],
    })
    print(f"{ref}: {len(clean)} durak | {clean[0]['name']} -> {clean[-1]['name']}", flush=True)

# Ayni hattin cift yonlerini teke dusur: (ref,endpointler) ayniysa birini birak
seen = {}
unique = []
for line in lines_out:
    key = (line['ref'], tuple(sorted([line['stops'][0]['name'], line['stops'][-1]['name']])))
    if key in seen:
        continue
    seen[key] = True
    unique.append(line)

with gzip.open('data/istanbul_rail.json.gz', 'wt', encoding='utf-8') as f:
    json.dump(unique, f, ensure_ascii=False, separators=(',', ':'))

print(len(unique), 'hat (tekrarsiz) kaydedildi')

"""Denizli hat dosyalarini derler: gecerli hatlar -> duraklar.
data/denizli_transit.json.gz uretir.
"""

import glob
import gzip
import json
import re

STOP_NAME_RE = re.compile(r'^[A-ZÇĞİÖŞÜ0-9].{2,}$')


def walk(node, out):
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for i in node:
            walk(i, out)
    elif isinstance(node, dict):
        for v in node.values():
            walk(v, out)


def parse_hat_file(path):
    """(hat_no, hat_adi, [(durak_adi, lat, lon), ...]) veya None."""
    d = json.load(open(path, encoding='utf-8'))
    strs = []
    walk(d, strs)

    # durak ucensusu: ad, lat, lon uc komsu string
    stops = []
    i = 0
    while i < len(strs) - 2:
        s = strs[i]
        if (len(s) >= 3 and not s.startswith('/') and not s.startswith('http')
                and not s.startswith('[') and STOP_NAME_RE.match(s)):
            try:
                lat = float(strs[i + 1])
                lon = float(strs[i + 2])
                if 37.0 < lat < 38.5 and 28.0 < lon < 30.5:
                    stops.append((s.strip(), lat, lon))
                    i += 3
                    continue
            except ValueError:
                pass
        i += 1

    # hat adi: "500 Adalet Aktarma Merkezi - ..." gibi
    hat_name = None
    for s in strs:
        m = re.match(r'^(\d{1,3})\s+(.{4,})$', s)
        if m and ('–' in s or '-' in s):
            hat_name = s
            break

    return hat_name, stops


results = {}
for path in sorted(glob.glob('_denizli_hat_*.json')):
    n = int(re.search(r'_hat_(\d+)\.json', path).group(1))
    try:
        hat_name, stops = parse_hat_file(path)
    except Exception:
        continue
    if stops:
        results[n] = (hat_name, stops)

print('gecerli hat:', len(results))
for n in sorted(results)[:30]:
    hat_name, stops = results[n]
    print(f'  {n}: {len(stops)} durak | {hat_name}')

# durak -> hatlar map
stop_lines = {}
for n, (hat_name, stops) in results.items():
    for name, lat, lon in stops:
        key = (name, round(lat, 3), round(lon, 3))
        entry = stop_lines.setdefault(key, {'name': name, 'lat': lat, 'lon': lon, 'lines': set()})
        entry['lines'].add(n)

out_stops = []
for e in stop_lines.values():
    out_stops.append({
        'id': f"dnz_{abs(hash((e['name'], round(e['lat'], 3), round(e['lon'], 3)))) % 10_000_000}",
        'name': e['name'],
        'lat': e['lat'],
        'lon': e['lon'],
        'lines': sorted(
            ({'n': str(n), 't': 'bus', 'l': f'{n}'} for n in e['lines']),
            key=lambda x: (len(x['n']), x['n']),
        ),
    })
out_stops.sort(key=lambda s: (s['name'], s['id']))

hat_n = {l['n'] for st in out_stops for l in st['lines']}
print('derlenen durak:', len(out_stops), 'hat:', len(hat_n))

with gzip.open('data/denizli_transit.json.gz', 'wt', encoding='utf-8', compresslevel=9) as f:
    json.dump(out_stops, f, ensure_ascii=False, separators=(',', ':'))

import os
print('yazildi:', os.path.getsize('data/denizli_transit.json.gz') // 1024, 'KB')

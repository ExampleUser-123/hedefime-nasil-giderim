"""
Afyonkarahisar (Filozof Locator) verisini derler.
Kaynak: afyon.bel.tr -> /otobus canli takip API'si (REST).
Cikti: data/afyon_transit.json.gz
Kullanim: python build_afyon.py
"""

import gzip
import json
import time
import urllib.request

BASE = 'http://164.90.176.222:3006'
TENANT = 'afyon'


def get(path, retries=4):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(
                BASE + path, headers={'User-Agent': 'Mozilla/5.0'})
            return json.loads(
                urllib.request.urlopen(req, timeout=60).read()
                .decode('utf-8', errors='ignore'))
        except Exception as exc:
            last = exc
            time.sleep(1.5 * (i + 1))
    raise last


def main():
    routes = get(f'/api/t/{TENANT}/routes')
    print('hat sayisi:', len(routes), flush=True)

    stops_geo = get(f'/api/t/{TENANT}/stops')
    coord = {}
    for f in stops_geo.get('features') or []:
        props = f.get('properties') or {}
        geom = f.get('geometry') or {}
        xy = geom.get('coordinates') or []
        sid = props.get('id')
        if sid is None or len(xy) < 2:
            continue
        coord[int(sid)] = (
            (props.get('name') or '').strip(), float(xy[1]), float(xy[0]))

    print('koordinatli durak:', len(coord), flush=True)

    merged = {}
    for r in routes:
        rid = r.get('id')
        name = (str(r.get('name') or '')).strip()
        desc = (r.get('description') or '').strip()
        if rid is None or not name:
            continue
        try:
            det = get(f'/api/t/{TENANT}/routes/{rid}')
        except Exception as exc:
            print('  SKIP hat', name, exc, flush=True)
            continue
        for s in det.get('stops') or []:
            try:
                sid = int(s.get('stopId'))
            except (TypeError, ValueError):
                continue
            nm, lat, lon = coord.get(sid, ((s.get('stopName') or '').strip(),
                                           None, None))
            if lat is None:
                continue
            if not nm:
                nm = (s.get('stopName') or '').strip()
            e = merged.setdefault(sid, {'id': f'afy_{sid}', 'name': nm,
                                        'lat': lat, 'lon': lon, 'lines': {}})
            e['lines'][name] = desc

    out = []
    for e in merged.values():
        out.append({
            'id': e['id'],
            'name': e['name'],
            'lat': e['lat'],
            'lon': e['lon'],
            'lines': [{'n': n, 't': 'bus', 'l': lbl}
                      for n, lbl in sorted(e['lines'].items())],
        })
    out.sort(key=lambda s: s['name'])

    with gzip.open('data/afyon_transit.json.gz', 'wt',
                   encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
    print(f'afyon: {len(out)} durak -> data/afyon_transit.json.gz')


if __name__ == '__main__':
    main()

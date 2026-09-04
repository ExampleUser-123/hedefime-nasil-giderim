"""
Kocaeli GTFS verisini indirip uygulamanin kullanacagi
sikistirilmis 'durak -> hatlar' verisine donusturur.

Bir kez calistirilir; cikti: data/kocaeli_transit.json.gz
"""

import csv
import gzip
import io
import json
import urllib.request

BASE = 'https://kavisacikveri.kocaeli.bel.tr/api/public/OpenDataPublic/attachments'
ATTACHMENTS = {
    'stops': 'f767ade4-85f7-4398-9268-f08101e0a9a4',
    'routes': '530dbd19-7a00-4551-a445-8fb84694e619',
    'trips': '5bcae1a2-edd3-42d0-a1ce-559d78d2b639',
    'stop_times': '96acd81c-a29d-410f-b43e-fff4a21249b1',
}

GTFS_TYPES = {
    '0': 'tram',
    '1': 'metro',
    '2': 'rail',
    '3': 'bus',
    '4': 'ferry',
    '5': 'tram',
    '6': 'gondola',
    '7': 'funicular',
    '11': 'bus',
    '12': 'rail',
}


def download_csv(key):
    import os
    cache_path = os.path.join(os.environ['TEMP'], f'kc_gtfs_{key}.txt')

    if os.path.exists(cache_path):
        print('using cached', key, flush=True)
        raw = open(cache_path, 'rb').read()
    else:
        url = f"{BASE}/{ATTACHMENTS[key]}/download"
        print('downloading', key, '...', flush=True)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        raw = urllib.request.urlopen(req, timeout=600).read()
        with open(cache_path, 'wb') as f:
            f.write(raw)
        print(' ', len(raw) // 1024, 'KB', flush=True)

    text = raw.decode('utf-8-sig', errors='ignore')
    return csv.DictReader(io.StringIO(text))


def main():
    routes = {}
    for row in download_csv('routes'):
        routes[row['route_id']] = {
            'short': (row.get('route_short_name') or '').strip(),
            'long': (row.get('route_long_name') or '').strip(),
            'type': GTFS_TYPES.get((row.get('route_type') or '').strip(), 'bus'),
        }
    print('routes:', len(routes))

    trip_to_route = {}
    for row in download_csv('trips'):
        trip_to_route[row['trip_id']] = row['route_id']
    print('trips:', len(trip_to_route))

    stop_lines = {}
    for row in download_csv('stop_times'):
        route_id = trip_to_route.get(row['trip_id'])
        if not route_id:
            continue
        stop_lines.setdefault(row['stop_id'], set()).add(route_id)
    print('stops with lines:', len(stop_lines))

    stops = []
    for row in download_csv('stops'):
        stop_id = row['stop_id']
        line_ids = stop_lines.get(stop_id)
        if not line_ids:
            continue

        lines = set()
        for route_id in line_ids:
            route = routes.get(route_id)
            if not route or not route['short']:
                continue
            lines.add((route['short'], route['type'], route['long']))

        if not lines:
            continue

        stops.append({
            'id': stop_id,
            'name': (row.get('stop_name') or '').strip(),
            'lat': float(row['stop_lat']),
            'lon': float(row['stop_lon']),
            'lines': sorted(
                ({
                    'n': short,
                    't': ltype,
                    'l': long_name,
                } for short, ltype, long_name in lines),
                key=lambda x: x['n'],
            ),
        })

    print('usable stops:', len(stops))

    import os
    os.makedirs('data', exist_ok=True)
    out_path = 'data/kocaeli_transit.json.gz'
    with gzip.open(out_path, 'wt', encoding='utf-8', compresslevel=9) as f:
        json.dump(stops, f, ensure_ascii=False, separators=(',', ':'))

    import os
    print('written', out_path, os.path.getsize(out_path) // 1024, 'KB')


if __name__ == '__main__':
    main()

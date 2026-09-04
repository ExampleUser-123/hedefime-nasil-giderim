"""
Konya GTFS zip'ini uygulamanin durak-hat verisine donusturur.
Cikti: data/konya_transit.json.gz
"""

import csv
import gzip
import io
import json
import os
import urllib.request

ZIP_URL = (
    'https://acikveri.konya.bel.tr/dataset/'
    'c2e034e6-e015-49c6-8eec-6e2f7de9c105/resource/'
    'ec944ecd-1c1f-4687-a7f6-fcf2dc5bb5db/download/gtfs_11_2025.zip'
)

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


def main():
    import zipfile

    cache_path = os.path.join(os.environ['TEMP'], 'konya_gtfs.zip')

    if not os.path.exists(cache_path):
        print('indiriliyor...', flush=True)
        req = urllib.request.Request(ZIP_URL, headers={'User-Agent': 'Mozilla/5.0'})
        raw = urllib.request.urlopen(req, timeout=600).read()
        with open(cache_path, 'wb') as f:
            f.write(raw)
    else:
        print('onbellekten', flush=True)

    zf = zipfile.ZipFile(cache_path)
    print('dosyalar:', zf.namelist(), flush=True)

    def read_csv(name):
        return csv.DictReader(io.StringIO(zf.read(name).decode('utf-8-sig', errors='ignore')))

    routes = {}
    for row in read_csv('routes.txt'):
        routes[row['route_id']] = {
            'short': (row.get('route_short_name') or '').strip(),
            'long': (row.get('route_long_name') or '').strip(),
            'type': GTFS_TYPES.get((row.get('route_type') or '').strip(), 'bus'),
        }
    print('routes:', len(routes), flush=True)

    trip_to_route = {}
    for row in read_csv('trips.txt'):
        trip_to_route[row['trip_id']] = row['route_id']
    print('trips:', len(trip_to_route), flush=True)

    stop_lines = {}
    for row in read_csv('stop_times.txt'):
        route_id = trip_to_route.get(row['trip_id'])
        if not route_id:
            continue
        stop_lines.setdefault(row['stop_id'], set()).add(route_id)
    print('hatli durak:', len(stop_lines), flush=True)

    stops = []
    for row in read_csv('stops.txt'):
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
                ({'n': n, 't': t, 'l': l} for n, t, l in lines),
                key=lambda x: x['n'],
            ),
        })

    print('kullanilabilir durak:', len(stops), flush=True)

    os.makedirs('data', exist_ok=True)
    out_path = 'data/konya_transit.json.gz'
    with gzip.open(out_path, 'wt', encoding='utf-8', compresslevel=9) as f:
        json.dump(stops, f, ensure_ascii=False, separators=(',', ':'))

    print('yazildi:', out_path, os.path.getsize(out_path) // 1024, 'KB', flush=True)


if __name__ == '__main__':
    main()

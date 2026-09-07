"""
KentKart servislerini kullanan sehirler icin durak-hat verisi derler.
Cikti: data/kentkart_{sehir}.json.gz
"""

import gzip
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = 'https://service.kentkart.com/rl1'

CITIES = {
    'antalya': '026',
    'adana': '003',
    'gaziantep': '028',
    'mugla': '010',
    'sivas': '005',
    'duzce': '036',
    'erzurum': '038',
    'ordu': '031',
    'zonguldak': '020',
    'canakkale': '007',
    'samsun': '025',
    'edirne': '013',
    'burdur': '017',
    'osmaniye': '033',
    'karabuk': '037',
    'bartin': '040',
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
}


def get_json(url, retries=4):
    last_exc = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'},
            )
            return json.loads(
                urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='ignore')
            )
        except Exception as exc:
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    raise last_exc


def compile_city(city_name, region):
    print(f'=== {city_name} (region {region}) ===', flush=True)

    data = get_json(f'{API}/web/nearest/find?region={region}&lang=tr')
    routes = data.get('routeList') or []
    print('hat sayisi:', len(routes), flush=True)

    route_meta = {
        r['routeCode']: {
            'display': r.get('displayRouteCode') or r['routeCode'],
            'name': (r.get('name') or '').strip(),
            'type': GTFS_TYPES.get(str(r.get('routeType', '3')), 'bus'),
        }
        for r in routes
    }

    stop_lines = {}   # stopId -> set(routeCode)
    stop_meta = {}    # stopId -> {name, lat, lon}

    for i, route in enumerate(routes):
        code = route['routeCode']
        display = route_meta[code]['display']

        for direction in ('0', '1'):
            try:
                path = get_json(
                    f'{API}/web/pathInfo?region={region}&lang=tr'
                    f'&direction={direction}&displayRouteCode={urllib.parse.quote(display)}'
                    f'&resultType=001000'
                )
            except Exception as exc:
                print('  SKIP', display, direction, exc, flush=True)
                continue

            for path_item in path.get('pathList') or []:
                for stop in path_item.get('busStopList') or []:
                    stop_id = str(stop.get('stopId') or '')
                    if not stop_id:
                        continue

                    stop_lines.setdefault(stop_id, set()).add(code)

                    if stop_id not in stop_meta:
                        try:
                            lat = float(stop['lat'])
                            lon = float(stop['lng'])
                        except (TypeError, ValueError):
                            continue
                        stop_meta[stop_id] = {
                            'name': (stop.get('stopName') or '').strip(),
                            'lat': lat,
                            'lon': lon,
                        }

        if (i + 1) % 25 == 0:
            print(f'  {i + 1}/{len(routes)} hat islendi', flush=True)

        time.sleep(0.25)

    stops = []
    for stop_id, line_codes in stop_lines.items():
        meta = stop_meta.get(stop_id)

        if not meta:
            continue

        lines = set()
        for code in line_codes:
            info = route_meta.get(code)
            if not info:
                continue
            lines.add((info['display'], info['type'], info['name']))

        if not lines:
            continue

        stops.append({
            'id': stop_id,
            'name': meta['name'],
            'lat': meta['lat'],
            'lon': meta['lon'],
            'lines': sorted(
                ({'n': n, 't': t, 'l': l} for n, t, l in lines),
                key=lambda x: x['n'],
            ),
        })

    print('kullanilabilir durak:', len(stops), flush=True)

    out_path = f'data/kentkart_{city_name}.json.gz'
    with gzip.open(out_path, 'wt', encoding='utf-8', compresslevel=9) as f:
        json.dump(stops, f, ensure_ascii=False, separators=(',', ':'))

    print('yazildi:', out_path, os.path.getsize(out_path) // 1024, 'KB', flush=True)


def main():
    targets = sys.argv[1:] or list(CITIES.keys())
    os.makedirs('data', exist_ok=True)
    for name in targets:
        compile_city(name, CITIES[name])


if __name__ == '__main__':
    main()

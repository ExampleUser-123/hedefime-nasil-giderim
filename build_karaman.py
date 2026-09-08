"""Karaman otobus verisi derleyici.
Kaynak: karamanotobus.com.tr (gonullu rehber, resmi belediye hatlari)
Durak koordinatlari yok -> Photon/Nominatim ile geocode (Karaman sinirlarina filtreli).
Cikti: data/karaman_transit.json.gz
"""

import gzip
import json
import os
import re
import time
import urllib.parse
import urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
PHOTON_UA = {'User-Agent': 'rota-uygulamasi'}

LINE_IDS = ['1', '1-A', '2', '3', '3-A', '4', '5', '6', '7', '8', '9', '10', '11']

# Karaman ili (merkez) sinirlari
BBOX = (37.02, 33.00, 37.40, 33.45)  # s, w, n, e

SUFFIX_RE = re.compile(r'\s*\d+\.\s*Durak\s*$', re.I)


def fetch(url, retries=3):
    last = None
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=30
            ).read().decode('utf-8', errors='ignore')
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise last


def extract_stops(html):
    names = []
    for m in re.finditer(r'<(?:td|li|div|span|p|h[2345]|b|strong)[^>]*>\s*([A-ZÇĞİÖŞÜ][^<>{}]{4,55})\s*<', html):
        n = m.group(1).strip()
        if n.lower().startswith(('http', 'www', 'an detected')):
            continue
        names.append(n)
    # Durak benzeri satirlari suz: "X 1.Durak" veya bilinen yerler
    stop_names = []
    for n in names:
        clean = SUFFIX_RE.sub('', n).strip()
        if len(clean) < 4 or len(clean) > 45:
            continue
        if re.search(r'\d\.Durak', n) or any(k in clean for k in (
                'Cami', 'Cad', 'Bul', 'Park', 'Mah', 'Lise', 'Okul', 'Üniversite', 'Hastane',
                'Terminal', 'Meydan', 'Sanayi', 'Kampüs', 'Stadyum', 'Kavşak', 'Merkez',
                'Gar', 'Çarşı', 'İş Hanı', 'Köprü', 'Giriş', 'Çıkış', 'Pazar', 'Bahçe',
                'Site', 'Kültür', 'Aile', 'Sağlık', 'Durağı')):
            stop_names.append(clean)
    return list(dict.fromkeys(stop_names))


def photon_geocode(query):
    lat, lon = 37.1816, 33.2153
    url = (
        f'https://photon.komoot.io/api/?q={urllib.parse.quote(query)}'
        f'&lat={lat}&lon={lon}&zoom=13&limit=1&lang=de'
    )
    try:
        req = urllib.request.Request(url, headers=PHOTON_UA)
        data = json.loads(urllib.request.urlopen(req, timeout=20).read().decode('utf-8', errors='ignore'))
        feats = data.get('features') or []
        if feats:
            c = feats[0]['geometry']['coordinates']  # [lon, lat]
            props = feats[0].get('properties', {})
            return c[1], c[0], props.get('city') or props.get('county') or props.get('state') or ''
    except Exception:
        pass
    return None


def nominatim_geocode(query):
    url = (
        f'https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}'
        f'&viewbox=33.00,37.40,33.45,37.02&bounded=1&limit=1&format=json'
    )
    try:
        req = urllib.request.Request(url, headers=PHOTON_UA)
        data = json.loads(urllib.request.urlopen(req, timeout=20).read().decode('utf-8', errors='ignore'))
        if data:
            return float(data[0]['lat']), float(data[0]['lon']), data[0].get('display_name', '')
    except Exception:
        pass
    return None


def main():
    # 1) Hat sayfalarindan durak dizilimlerini topla
    lines = {}   # line_id -> stop_names
    for lid in LINE_IDS:
        html = fetch(f'https://karamanotobus.com.tr/line.php?id={urllib.parse.quote(lid)}')
        stops = extract_stops(html)
        if stops:
            lines[lid] = stops
            print(f'hat {lid}: {len(stops)} durak', flush=True)
        else:
            print(f'hat {lid}: 0 durak (yapisi farkli)', flush=True)
        time.sleep(0.6)

    # 2) Tum durak adlarini geocode et (cache'li)
    all_names = sorted({s for stops in lines.values() for s in stops})
    print('\ntoplam tekrarsiz durak:', len(all_names), flush=True)

    coords = {}
    for i, name in enumerate(all_names):
        res = photon_geocode(f'Karaman {name}')
        if not res:
            res = nominatim_geocode(f'{name}, Karaman, Türkiye')
        if res:
            lat, lon, ctx = res
            if BBOX[0] <= lat <= BBOX[2] and BBOX[1] <= lon <= BBOX[3]:
                coords[name] = (lat, lon)
                ok = 'OK '
            else:
                ok = 'DIS '
        else:
            ok = 'YOK'
        if i % 10 == 0 or ok != 'OK ':
            print(f'  [{i + 1}/{len(all_names)}] {ok} {name[:40]}', flush=True)
        time.sleep(1.05)

    print('\ngeocode edilen:', len(coords), '/', len(all_names), flush=True)

    # 3) durak -> hat map
    stop_lines = {}
    for lid, stops in lines.items():
        for name in stops:
            if name not in coords:
                continue
            entry = stop_lines.setdefault(name, {'lines': set(), 'lat': coords[name][0], 'lon': coords[name][1]})
            entry['lines'].add(lid)

    out_stops = []
    for name, e in stop_lines.items():
        out_stops.append({
            'id': f'kr_{abs(hash(name)) % 10_000_000}',
            'name': name,
            'lat': e['lat'],
            'lon': e['lon'],
            'lines': sorted(
                ({'n': l, 't': 'bus', 'l': f'{l} hattı'} for l in e['lines']),
                key=lambda x: (len(x['n']), x['n']),
            ),
        })
    out_stops.sort(key=lambda s: s['name'])

    hat_n = {l['n'] for st in out_stops for l in st['lines']}
    print('derlenen durak:', len(out_stops), 'hat:', len(hat_n), sorted(hat_n))

    with gzip.open('data/karaman_transit.json.gz', 'wt', encoding='utf-8', compresslevel=9) as f:
        json.dump(out_stops, f, ensure_ascii=False, separators=(',', ':'))
    print('yazildi: data/karaman_transit.json.gz', os.path.getsize('data/karaman_transit.json.gz') // 1024, 'KB')


if __name__ == '__main__':
    main()

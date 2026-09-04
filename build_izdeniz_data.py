"""
İzdeniz iskelelerini (CKAN CSV) ve iskeleler arası vapur
bağlantılarını (openapi.izmir.bel.tr) sorgulayıp
data/izdeniz_piers.json dosyasına yazar.
"""

import json
import os
import time
import urllib.request

CKAN_URL = 'https://acikveri.bizizmir.com/api/3/action/datastore_search'
CKAN_RESOURCE = '9e4097db-40a3-434f-adb3-ddbba72a931c'
API_BASE = 'https://openapi.izmir.bel.tr/api/izdeniz'
OUT = 'data/izdeniz_piers.json'


def get_json(url):
    last_exc = None

    for attempt in range(4):
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'},
            )
            return json.loads(
                urllib.request.urlopen(req, timeout=25).read().decode('utf-8', errors='ignore')
            )
        except Exception as exc:
            last_exc = exc
            time.sleep(2 * (attempt + 1))

    raise last_exc


def main():
    d = get_json(f'{CKAN_URL}?resource_id={CKAN_RESOURCE}&limit=100')
    records = d['result']['records']

    piers = []
    for r in records:
        if str(r.get('ISKELE_AKTIF_MI', '')).lower() != 'true':
            continue
        piers.append({
            'id': int(r['ISKELE_ID']),
            'name': r['ISKELE_ADI'].strip(),
            'lat': float(r['ENLEM']),
            'lon': float(r['BOYLAM']),
        })

    print('aktif iskele:', len(piers))

    connections = {}

    for a in piers:
        for b in piers:
            if a['id'] >= b['id']:
                continue

            try:
                data = get_json(f"{API_BASE}/vapursaatleri/{a['id']}/{b['id']}/1/1")
            except Exception as exc:
                print('SKIP', a['name'], '-', b['name'], exc)
                continue

            has_service = False

            for row in (data or []):
                if not isinstance(row, dict):
                    continue
                for service_row in row.get('seferSatirlari') or []:
                    if (
                        not service_row.get('IptalMi', False)
                        and service_row.get('seferSaatleri')
                    ):
                        has_service = True
                        break
                if has_service:
                    break

            if has_service:
                key = f"F{min(a['id'], b['id'])}-{max(a['id'], b['id'])}"
                connections[key] = [a['id'], b['id']]
                print('baglanti:', a['name'], '<->', b['name'])

            time.sleep(0.5)

    out = {'piers': piers, 'connections': connections}

    os.makedirs('data', exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print('yazildi:', OUT, '| baglanti:', len(connections))


if __name__ == '__main__':
    main()

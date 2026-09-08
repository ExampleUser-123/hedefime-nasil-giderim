"""Denizli ulasim portali hat numaralarini tarar: /hat/{n}/__data.json
Basarili hatlari _denizli_hat_{n}.json olarak kaydeder.
"""

import json
import os
import time
import urllib.request

UA = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
    'Accept': '*/*',
    'Referer': 'https://ulasim.denizli.bel.tr/',
}

BULUNAN = []
DENENEN = 0

for n in range(1, 601):
    url = f'https://ulasim.denizli.bel.tr/hat/{n}/__data.json'
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20)
        body = resp.read().decode('utf-8', errors='ignore')
        data = json.loads(body)
        with open(f'_denizli_hat_{n}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        BULUNAN.append(n)
        DENENEN += 1
        print(f'HAT {n} OK ({len(body)} b)', flush=True)
    except urllib.error.HTTPError as exc:
        DENENEN += 1
        if exc.code not in (404, 400):
            print(f'HAT {n} HTTP {exc.code}', flush=True)
        # 404 sessizce atla
    except Exception as exc:
        print(f'HAT {n} HATA {str(exc)[:60]}', flush=True)
    time.sleep(0.12)

print('BITTI. bulunan hatlar:', BULUNAN, flush=True)
with open('_denizli_hat_listesi.txt', 'w') as f:
    f.write(json.dumps(BULUNAN))

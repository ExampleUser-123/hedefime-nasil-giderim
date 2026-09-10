"""Aday region'larin sehirlerini tespit: coklu hat durak isimleri topla."""
import json
import urllib.parse
import urllib.request

API = 'https://service.kentkart.com/rl1'
CANDIDATES = ['004', '019', '023', '024', '027', '032', '039']


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'},
    )
    return json.loads(
        urllib.request.urlopen(req, timeout=20).read().decode('utf-8', errors='ignore')
    )


for rid in CANDIDATES:
    print(f'=== region {rid} ===', flush=True)
    try:
        data = get_json(f'{API}/web/nearest/find?region={rid}&lang=tr')
        routes = data.get('routeList') or []
        names = set()
        for route in routes[:6]:
            display = route.get('displayRouteCode') or route['routeCode']
            try:
                path = get_json(
                    f'{API}/web/pathInfo?region={rid}&lang=tr'
                    f'&direction=0&displayRouteCode={urllib.parse.quote(display)}'
                    f'&resultType=001000'
                )
                for path_item in path.get('pathList') or []:
                    for stop in path_item.get('busStopList') or []:
                        nm = (stop.get('stopName') or '').strip()
                        if nm:
                            names.add(nm)
            except Exception:
                pass

        print(' | '.join(sorted(names)[:14]), flush=True)
    except Exception as exc:
        print('HATA', exc, flush=True)

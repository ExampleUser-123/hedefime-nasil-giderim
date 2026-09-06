"""Belirsiz bolgeler icin birkac hattan daha durak ornekleri ceker."""

import json
import urllib.parse
import urllib.request

API = 'https://service.kentkart.com/rl1'

TARGETS = ['004', '010', '013', '017', '020', '023', '024', '025', '027', '033', '039', '040']


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'},
    )
    return json.loads(
        urllib.request.urlopen(req, timeout=25).read().decode('utf-8', errors='ignore')
    )


for region in TARGETS:
    try:
        data = get_json(f'{API}/web/nearest/find?region={region}&lang=tr')
        routes = data.get('routeList') or []

        print(f'--- {region} ({len(routes)} hat) ---', flush=True)

        seen = 0
        for route in routes[:: max(1, len(routes) // 3)][:3]:
            display = route.get('displayRouteCode') or route['routeCode']

            try:
                path = get_json(
                    f'{API}/web/pathInfo?region={region}&lang=tr'
                    f'&direction=0&displayRouteCode={urllib.parse.quote(display)}'
                    f'&resultType=001000'
                )
            except Exception:
                continue

            names = []
            for path_item in path.get('pathList') or []:
                for stop in path_item.get('busStopList') or []:
                    nm = (stop.get('stopName') or '').strip()
                    if nm:
                        names.append(nm[:38])
                    if len(names) >= 7:
                        break
                if len(names) >= 7:
                    break

            print(f'  {display}: {names}', flush=True)
            seen += 1

            if seen >= 3:
                break
    except Exception as exc:
        print(f'{region}: HATA {str(exc)[:60]}', flush=True)

"""Kentkart tum region'lari tarar: hangi ID hangi sehir, hat sayisi kadar."""
import json
import urllib.request

API = 'https://service.kentkart.com/rl1'


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'},
    )
    return json.loads(
        urllib.request.urlopen(req, timeout=20).read().decode('utf-8', errors='ignore')
    )


for region in range(1, 71):
    rid = f'{region:03d}'
    try:
        data = get_json(f'{API}/web/nearest/find?region={rid}&lang=tr')
        routes = data.get('routeList') or []
        if not routes:
            print(f'{rid}: bos', flush=True)
            continue

        # ilk hattin duraklarindan sehir ipucu
        clue = ''
        display = routes[0].get('displayRouteCode') or routes[0]['routeCode']
        try:
            import urllib.parse
            path = get_json(
                f'{API}/web/pathInfo?region={rid}&lang=tr'
                f'&direction=0&displayRouteCode={urllib.parse.quote(display)}'
                f'&resultType=001000'
            )
            for path_item in path.get('pathList') or []:
                for stop in path_item.get('busStopList') or []:
                    nm = (stop.get('stopName') or '').strip()
                    if nm:
                        clue = nm[:30]
                        break
                if clue:
                    break
        except Exception:
            pass

        print(f'{rid}: {len(routes)} hat | {clue} | ilk hat: {display}', flush=True)
    except Exception as exc:
        print(f'{rid}: HATA {str(exc)[:40]}', flush=True)

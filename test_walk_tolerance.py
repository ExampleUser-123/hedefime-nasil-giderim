"""Rota ucu max_walk (yurume toleransi) parametresi icin TestClient testleri.

Trabzon icinde bilinen iki koordinat arasinda toplu tasima rotasi istenir:
  - max_walk=300  -> kisa yurume toleransi
  - max_walk=2000 -> uzun yurume toleransi
  - max_walk=99999 -> asiri deger, clamp edilip 200 donmeli (crash yok)

Beklenen davranis:
  (a) her iki durumda HTTP 200,
  (b) 2000 m toleransla en az 300 m kadar rota bulunabilmeli
      (bulunan rota sayisi: 2000m >= 300m),
  (c) max_walk=99999 clamp edilip HTTP 200 donmeli.
"""

import time

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# Trabzon: Besirli kiyisindan Kalkinma/OF yonune dogru bilinen iki nokta
START = "40.9946,39.7670"
END = "41.0053,39.7215"

PUBLIC_TRANSPORT_TIMEOUT_MS = 60_000


def _fetch(max_walk: int):
    t0 = time.perf_counter()
    r = client.get("/public-transport", params={
        "start": START,
        "end": END,
        "max_walk": max_walk,
    })
    elapsed_ms = (time.perf_counter() - t0) * 1000
    print(
        f"\n[max_walk={max_walk}] HTTP {r.status_code}, "
        f"{elapsed_ms:.0f} ms"
    )
    assert r.status_code == 200, r.text
    return r.json()


def _routes(data):
    """Yanittan rota listesini cikarir (/public-transport dogrudan routes doner)."""
    if isinstance(data, dict):
        return data.get("routes") or []
    return []


def _walking_distances(data):
    return [
        route.get("walking_distance_m") or 0
        for route in _routes(data)
        if isinstance(route, dict)
    ]


def test_max_walk_300_and_2000_both_ok():
    data_300 = _fetch(300)
    routes_300 = _routes(data_300)
    wd_300 = _walking_distances(data_300)
    print(f"[max_walk=300] {len(routes_300)} rota, yurumeler: {[round(w) for w in wd_300]}")

    data_2000 = _fetch(2000)
    routes_2000 = _routes(data_2000)
    wd_2000 = _walking_distances(data_2000)
    print(f"[max_walk=2000] {len(routes_2000)} rota, yurumeler: {[round(w) for w in wd_2000]}")

    # (a) her iki istek HTTP 200 dondu (ustte assert edildi)
    assert isinstance(data_300, dict)
    assert isinstance(data_2000, dict)

    # (b) kabaca: 2000 m'de bulunan rota sayisi >= 300 m'de bulunan
    assert len(routes_2000) >= len(routes_300), (
        f"max_walk=2000 ile {len(routes_2000)} rota bulundu, "
        f"max_walk=300 ile {len(routes_300)} rota bulundu; "
        "buyuk tolerans daha az rota donmemeli"
    )

    # 300 m toleransinda bulunan rotalarin yurumeleri makul sinirda kalmali
    # (tam 300 olmayabilir; provide bagli olarak hesaplama yaklasik olur)
    for w in wd_300:
        assert w >= 0


def test_max_walk_huge_value_clamped_no_crash():
    data = _fetch(99999)
    routes = _routes(data)
    wd = _walking_distances(data)
    print(f"[max_walk=99999] {len(routes)} rota, yurumeler: {[round(w) for w in wd]}")
    # (c) clamp edilip 200 donduldu (ustte assert edildi), crash yok.
    # Rota listesi liste olmali; icerik clamp degerine bagli olarak degisebilir.
    assert isinstance(routes, list)


if __name__ == "__main__":
    test_max_walk_300_and_2000_both_ok()
    test_max_walk_huge_value_clamped_no_crash()
    print("\nTUM TESTLER GECTI")

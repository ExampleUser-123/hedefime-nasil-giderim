"""Yakın duraklar uçları için TestClient testleri."""

import time

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

TRABZON_CENTER = (41.0027, 39.7168)  # Trabzon Meydan


def test_nearby_stops_trabzon():
    t0 = time.perf_counter()
    r = client.get("/nearby-stops", params={
        "lat": TRABZON_CENTER[0], "lon": TRABZON_CENTER[1], "limit": 8,
    })
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert r.status_code == 200, r.text
    data = r.json()
    results = data["results"]
    print(f"\n[nearby-stops] ilk istek (lazy yukleme dahil): {elapsed_ms:.0f} ms, {len(results)} durak")
    assert len(results) >= 3
    for s in results:
        assert s["city"] == "Trabzon", f"beklenen Trabzon, gelen {s['city']}"
        assert isinstance(s["distance_m"], (int, float))
        assert isinstance(s["lines"], list)
    dists = [s["distance_m"] for s in results]
    assert dists == sorted(dists), "mesafe sirali degil"
    print("[nearby-stops] ilk 3:", [(s["name"], round(s["distance_m"]), s["lines"][:3]) for s in results[:3]])

    # ikinci istek: cache iskinde olmali
    t0 = time.perf_counter()
    client.get("/nearby-stops", params={"lat": TRABZON_CENTER[0], "lon": TRABZON_CENTER[1]})
    cached_ms = (time.perf_counter() - t0) * 1000
    print(f"[nearby-stops] cache'li istek: {cached_ms:.0f} ms")


def test_stop_departures():
    r = client.get("/nearby-stops", params={
        "lat": TRABZON_CENTER[0], "lon": TRABZON_CENTER[1], "limit": 1,
    })
    stop = r.json()["results"][0]
    r2 = client.post("/stop-departures", json={
        "city": stop["city"],
        "stop": stop["name"],
        "lat": stop["lat"],
        "lon": stop["lon"],
        "lines": stop["lines"],
    })
    assert r2.status_code == 200, r2.text
    deps = r2.json()["departures"]
    print(f"\n[stop-departures] {stop['name']} -> {len(deps)} kalkis")
    print("[stop-departures]", deps)
    assert isinstance(deps, list) and len(deps) > 0
    assert len(deps) <= 6
    for d in deps:
        assert d["source"] in ("gtfs", "tahmini")
        assert isinstance(d["minutes_ahead"], int)
        assert d["time"]
    ma = [d["minutes_ahead"] for d in deps]
    assert ma == sorted(ma), "minutes_ahead sirali degil"


def test_bad_coordinates():
    r = client.get("/nearby-stops", params={"lat": 999.0, "lon": 12345.0})
    assert r.status_code in (200, 422), r.status_code
    if r.status_code == 200:
        assert r.json()["results"] == []
    print(f"\n[bad-coords] lat=999 lon=12345 -> HTTP {r.status_code}, crash yok")

    r2 = client.get("/nearby-stops", params={"lat": "abc", "lon": "xyz"})
    assert r2.status_code == 422, r2.status_code
    print("[bad-coords] lat=abc lon=xyz -> HTTP 422 (validasyon), crash yok")


if __name__ == "__main__":
    test_nearby_stops_trabzon()
    test_stop_departures()
    test_bad_coordinates()
    print("\nTUM TESTLER GECTI")

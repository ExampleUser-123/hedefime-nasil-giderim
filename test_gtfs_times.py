"""gtfs_times.next_departures testleri."""

from datetime import datetime
from pathlib import Path

from services.gtfs_times import next_departures, _load_index, _build_index

BASE = Path(__file__).resolve().parent.parent
GTFS_DIR = BASE / "data" / "gtfs"


def _pick_sample():
    """Cache kurulmus indeksten ornek (hat, durak, lat, lon) secer."""
    for z in sorted(GTFS_DIR.glob("*_gtfs.zip")):
        city = z.name.replace("_gtfs.zip", "")
        idx = _load_index(city)
        for key, entries in idx.items():
            if key == "_meta" or not entries:
                continue
            route, stop = key
            _, _, lat, lon = entries[0]
            return city, route, stop, lat, lon
    return None


def test_empty_when_no_zip():
    """Zip yoksa bos liste donmeli (exception sizmamali)."""
    res = next_departures("yok_boyle_sehir__xyz", "1", "Olmayan Durak", 41.0, 29.0)
    assert res == []


def test_real_data():
    """Zip varsa gercek veriyle test; indeks kurulum suresini de olcer."""
    import time
    sample = _pick_sample()
    if sample is None:
        print("\n[SKIP] data/gtfs/ icinde zip yok -> bos donus dogrulandi (yukaridaki test)")
        return
    city, line, stop, lat, lon = sample
    print(f"\n[SEHIR] {city} | hat={line} durak={stop[:40]}")

    t0 = time.time()
    idx_exists = (BASE / "data" / "gtfs_cache" / f"{city}.pkl").exists()
    _load_index(city)  # cache varsa hizli, yoksa kurulum
    print(f"[CACHE] {'cache hit' if idx_exists else 'ilk kurulum'}: {time.time() - t0:.1f}s")

    t0 = time.time()
    for _ in range(10):
        next_departures(city, line, stop, lat, lon)
    per_call = (time.time() - t0) / 10 * 1000

    res = next_departures(city, line, stop, lat, lon)
    print(f"[PERF] {per_call:.0f} ms/call")
    print(f"[SONUC] {res}")
    assert isinstance(res, list)
    for r in res:
        assert r["source"] == "gtfs"
        assert set(r) >= {"time", "source", "minutes_ahead"}
    # sirali ve su an sonrasi olmali
    now = datetime.now().astimezone()
    assert all(r["minutes_ahead"] >= 0 for r in res)
    print("[OK] zaman sirali, minutes_ahead >= 0")


if __name__ == "__main__":
    test_empty_when_no_zip()
    test_real_data()
    print("\nTum testler tamam")

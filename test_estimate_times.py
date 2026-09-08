"""services/estimate_times.py için testler."""

from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.estimate_times import estimate_departures  # noqa: E402


def test_determinism():
    args = ("Trabzon", "101", "Meydan", datetime(2026, 9, 8, 14, 0))
    a = estimate_departures(*args)
    b = estimate_departures(*args)
    assert a == b, f"Determinizm ihlali: {a} != {b}"
    print("OK  determinizm: ayni parametre -> ayni sonuc")
    return a


def test_night_empty():
    for h in (0, 1, 3, 5):
        r = estimate_departures("Trabzon", "101", "Meydan", datetime(2026, 9, 8, h, 30))
        assert r == [], f"Saat {h}:30 icin bos donmeli, geldi: {r}"
    print("OK  gece saatleri (00:30, 01:30, 03:30, 05:30) -> []")


def test_afternoon_returns_3():
    r = estimate_departures("Denizli", "204", "Kale Ici", datetime(2026, 9, 8, 15, 0))
    assert len(r) == 3, f"3 kayit beklenirdi, geldi: {len(r)}"
    for item in r:
        assert item["source"] == "tahmini", "'source' etiketi 'tahmini' olmali"
        assert isinstance(item["minutes_ahead"], int) and item["minutes_ahead"] > 0
        assert len(item["time"]) == 5 and item["time"][2] == ":"
    # kalkislar artan sirada olmali
    times = [item["minutes_ahead"] for item in r]
    assert times == sorted(times), "Kalkislar artan sirada olmali"
    print("OK  ogleden sonra 3 kayit, source='tahmini', artan sira")


def test_source_tag():
    r = estimate_departures("Karaman", "5", "Gar", datetime(2026, 9, 8, 12, 0))
    assert all(i.get("source") == "tahmini" for i in r)
    print("OK  source etiketi zorunlu 'tahmini'")


if __name__ == "__main__":
    sample = test_determinism()
    test_night_empty()
    test_afternoon_returns_3()
    test_source_tag()
    print("\nOrnek cikti (Trabzon/101/Meydan @ 14:00):")
    for item in sample:
        print(f"  {item}")
    print("\nTum testler gecti.")

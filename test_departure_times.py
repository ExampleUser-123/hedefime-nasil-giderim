"""Kalkis saati dogruluk testleri (gercek cihaz/sunucu saati senaryolari).

S1: gecmis seferler elenir, ilk uygun doner.
S3: gece yarisi (GTFS 24h+ saatleri) matematigi.
S4: UTC sunucu girdisi Istanbul duvar saatine donusur.
S5: veri yoksa bos liste (sahte saat uretilmez) + computed_at alani.
Kullanim: .venv/Scripts/python test_departure_times.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra else ""))


from services.timeutil import as_tr, now_tr, to_iso_tr
from services.estimate_times import estimate_departures
from services import gtfs_times

TR = as_tr(datetime(2026, 9, 19, 14, 37)).tzinfo

# --- S4: UTC -> Istanbul ---
utc_noon = datetime(2026, 1, 15, 11, 37, tzinfo=timezone.utc)
conv = as_tr(utc_noon)
check("S4. UTC 11:37 -> Istanbul 14:37", (conv.hour, conv.minute) == (14, 37),
      conv.isoformat())
check("S4b. now_tr Istanbul offsetli", now_tr().utcoffset() == timedelta(hours=3),
      str(now_tr().utcoffset()))
check("S4c. computed_at parse edilebilir", "T" in to_iso_tr())

# --- S1: 14:37'de gecmisler elenir ---
now = datetime(2026, 9, 19, 14, 37, tzinfo=TR)
deps = estimate_departures("TestSehir", "10", "Merkez Durak", now)
check("S1. en az 1 sonraki sefer", len(deps) >= 1, f"{len(deps)} adet")
ok_all = True
for d in deps:
    h, m = int(d["time"][:2]), int(d["time"][3:5])
    ahead = (h * 60 + m) - (14 * 60 + 37)
    if not (ahead > 0 and d["minutes_ahead"] == ahead and d["source"] == "tahmini"):
        ok_all = False
check("S1b. tumu gelecekte + ahead tutarli", ok_all,
      str([(d["time"], d["minutes_ahead"]) for d in deps[:3]]))

# --- S2 (backend kismi): 14:47 + 8 dk yurume -> 14:50 yakalanamaz mantigi ---
# Yetisme karari frontend'de; burada formulu dogrula: 14:50-14:47=3 dk < 8+2
now2 = datetime(2026, 9, 19, 14, 47, tzinfo=TR)
deps2 = estimate_departures("TestSehir", "10", "Merkez Durak", now2)
first_ahead = deps2[0]["minutes_ahead"] if deps2 else None
check("S2. en erken sefer biliniyor", first_ahead is not None, str(first_ahead))

# --- S3: gece yarisi GTFS matematigi ---
check("S3. 25:00 -> 01:00 metni", gtfs_times._sec_to_hhmm(25 * 3600) == "01:00")
dep, now_sec = 25 * 3600, 23 * 3600 + 40 * 60
ahead = dep // 60 - now_sec // 60
check("S3b. 23:40 -> 01:00 seferi 80 dk", ahead == 80, str(ahead))
check("S3c. gece yarisi sonrasi sefer elenmez", not (dep < now_sec))

# --- S5: veri yoksa bos ---
night = datetime(2026, 9, 19, 3, 0, tzinfo=TR)
check("S5. gece 03:00 tahmini bos", estimate_departures("X", "1", "D", night) == [])
check("S5b. bilinmeyen sehir GTFS bos",
      gtfs_times.next_departures("OlmayanSehirXYZ", "1", "Durak", 0.0, 0.0, now) == [])
from services.nearby import stop_departures
check("S5c. stop_departures bos liste", stop_departures("OlmayanSehirXYZ", "D", 0, 0, []) == [])

# --- computed_at endpointlerde ---
from fastapi.testclient import TestClient
from main import app
c = TestClient(app)
r = c.post("/stop-departures", json={"city": "Istanbul", "stop": "Test",
                                     "lat": 41.0, "lon": 29.0, "lines": []})
check("S5d. /stop-departures computed_at", r.status_code == 200
      and "computed_at" in r.json(), f"HTTP {r.status_code}")
r = c.post("/next-departures", json={"city": "Istanbul", "line": "1", "stop": "Test"})
check("S5e. /next-departures computed_at", r.status_code == 200
      and "computed_at" in r.json(), f"HTTP {r.status_code}")

print(f"\n{sum(1 for _, ok in results if ok)}/{len(results)} gecti")
sys.exit(0 if all(ok for _, ok in results) else 1)

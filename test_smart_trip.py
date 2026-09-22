"""Hibrit arama + canli yolculuk testleri.

Kapsar: sorgu varyantlari, Overpass parse, smart_search akisi,
/suggest-places city parametresi, live trip create/ping/get/expiry/viewer.
data dosyalari yedeklenir ve geri yuklenir.
Kullanim: .venv/Scripts/python test_smart_trip.py
"""
import os
import shutil
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.abspath(__file__))
os.environ["ADMIN_KEY"] = "test-admin-key"
os.environ["USER_STORE_ENCRYPTION_KEY"] = "test-sabit-anahtar-xyz"
os.environ["JWT_SECRET"] = "test-sabit-jwt-xyz"

BACKUPS = {}
for _rel in ("data/users.json", "data/users.enc.db", "data/quotas.json"):
    _p = os.path.join(BASE, _rel)
    if os.path.exists(_p):
        _bak = _p + ".testbak6"
        shutil.copy2(_p, _bak)
        BACKUPS[_p] = _bak


def _restore():
    for _p, _bak in BACKUPS.items():
        if os.path.exists(_bak):
            shutil.move(_bak, _p)
    for _rel in ("data/users.json", "data/users.enc.db", "data/quotas.json"):
        _p = os.path.join(BASE, _rel)
        if _p not in BACKUPS and os.path.exists(_p):
            os.remove(_p)
    _t = os.path.join(BASE, "data", "live_trips.json")
    if os.path.exists(_t):
        os.remove(_t)


results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra else ""))


try:
    from services.geocoding import _core_tokens, _query_variants, overpass_search, smart_search_place

    # --- 1. varyant uretimi ---
    v = _query_variants("Kartepe KOTO AOSB Mesleki ve Teknik Anadolu Lisesi", "Kocaeli")
    check("varyant: ham + sehirli + cekirdek", len(v) >= 3 and v[0].startswith("Kartepe")
          and any("Kocaeli" in x for x in v), str(v[:3]))
    check("cekirdek jenerikleri eler",
          "lisesi" not in _core_tokens("Kartepe KOTO AOSB Mesleki ve Teknik Anadolu Lisesi")
          and "kartepe" in _core_tokens("Kartepe KOTO AOSB Mesleki ve Teknik Anadolu Lisesi"))

    # --- Overpass parse (mock ag) ---
    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"elements": [
                {"type": "node", "lat": 40.7, "lon": 29.9,
                 "tags": {"name": "Kartepe Test Lisesi", "addr:city": "Kocaeli"}},
                {"type": "way", "center": {"lat": 40.71, "lon": 29.91},
                 "tags": {"name": "Isimsiz", "addr:county": "Izmit"}},
                {"type": "node", "lat": 40.7, "lon": 29.9, "tags": {}},
            ]}

    with patch("services.geocoding.requests.post", return_value=_Resp()):
        out = overpass_search("Kartepe Test Lisesi", 40.7, 29.9)
    check("overpass 2 POI + sehir", len(out) == 2 and out[0]["name"] == "Kartepe Test Lisesi"
          and out[0]["detail"] == "Kocaeli", str(len(out)))

    # --- smart_search akisi ---
    with patch("services.geocoding.suggest_places", return_value=[]), \
         patch("services.geocoding.overpass_search",
               return_value=[{"name": "X", "detail": "", "display_name": "X",
                              "lat": 1.0, "lon": 2.0}]):
        r = smart_search_place("bilinmeyen yer", 40.0, 29.0, "Kocaeli")
        check("smart overpass'a duser", r is not None and r["lat"] == 1.0)
    with patch("services.geocoding.suggest_places", return_value=[]), \
         patch("services.geocoding.overpass_search", return_value=[]):
        check("smart bos -> None", smart_search_place("yok", 40.0, 29.0) is None)

    from fastapi.testclient import TestClient
    from main import app

    c = TestClient(app)

    # --- /suggest-places city parametresi ---
    seen = {}

    def _fake_suggest(q, lat=None, lon=None, city=None):
        seen.update(q=q, city=city)
        return []

    with patch("services.geocoding.suggest_places", side_effect=_fake_suggest):
        # main modulune import edilmis isme yama gerekir
        import main as _m
        orig = _m.suggest_places
        _m.suggest_places = _fake_suggest
        try:
            r = c.get("/suggest-places", params={"q": "lise", "city": "Kocaeli"})
            check("suggest city gecer", r.status_code == 200 and seen.get("city") == "Kocaeli",
                  str(seen))
        finally:
            _m.suggest_places = orig

    # --- canli yolculuk ---
    def new_user(email):
        with patch("main.mailer.is_configured", return_value=True), \
             patch("main.mailer.send_verification_email", return_value=(True, "ok")), \
             patch("services.mailer.generate_verification_code", return_value="123456"):
            c.post("/auth/register", json={"email": email, "password": "Sifre12345", "name": "T"})
            c.post("/auth/verify-email", json={"email": email, "code": "123456"})
        tok = c.post("/auth/login", json={"email": email, "password": "Sifre12345"}).json()["token"]
        return {"Authorization": f"Bearer {tok}"}

    h = new_user("canli@example.com")
    r = c.post("/live-trips", json={"from": "A", "destination": "B", "dest_lat": 41.1,
                                    "dest_lon": 29.1}, headers=h).json()
    check("trip olusur (id+key)", bool(r.get("id")) and bool(r.get("update_key")))
    tid, key = r["id"], r["update_key"]
    check("trip authsuz olusmaz", c.post("/live-trips", json={}).status_code == 401)

    r = c.post(f"/live-trips/{tid}/ping",
               json={"update_key": key, "lat": 41.05, "lon": 29.05, "eta_min": 12}).json()
    check("ping ok", r.get("ok") is True)
    r = c.post(f"/live-trips/{tid}/ping",
               json={"update_key": "yanlis", "lat": 41.0, "lon": 29.0}).json()
    check("yanlis anahtar 404", "error" in r)
    r = c.get(f"/live-trips/{tid}").json()
    check("takip herkese acik + ETA",
          r.get("eta_min") == 12 and r.get("lat") == 41.05, str(r.get("eta_min")))
    r = c.get(f"/live-trips/{tid}/view")
    check("viewer HTML", r.status_code == 200 and "Canl" in r.text and tid[:8] in r.text,
          str(r.status_code))
    check("bilinmeyen trip 404",
          c.get("/live-trips/xxxxxxyy").status_code == 404)

    # --- sure asimi budama (birim) ---
    from services import share_store as _ss
    import time as _t
    old = {"o": {"id": "o", "update_key": "k", "updated": _t.time() - 13 * 3600}}
    check("12 saati gecen budanir", _ss._trip_prune(old) == {})
    fresh = {"n": {"id": "n", "update_key": "k", "updated": _t.time()}}
    check("taze durur", _ss._trip_prune(fresh) == fresh)
finally:
    _restore()

print(f"\n{sum(1 for _, ok in results if ok)}/{len(results)} gecti")
sys.exit(0 if all(ok for _, ok in results) else 1)

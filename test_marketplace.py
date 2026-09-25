"""Marketplace + Davet + XP Store testleri.

Kapsar: yayin/liste/sil (sahiplik), +30 XP, davet kodu +50 XP (tek seferlik,
kendine davet yok), magaza katalogu, takaslar (4 urun), yetersiz XP,
bonus kota etkisi, vibe_unlock etkisi, lite deneme katmani.
data dosyalari yedeklenir ve geri yuklenir.
Kullanim: .venv/Scripts/python test_marketplace.py
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
        _bak = _p + ".testbak5"
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
    _c = os.path.join(BASE, "data", "community_routes.json")
    if os.path.exists(_c) and _c not in BACKUPS:
        os.remove(_c)


results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra else ""))


try:
    from fastapi.testclient import TestClient
    from main import app
    from services import user_store

    def new_user(email):
        c = TestClient(app)
        with patch("main.mailer.is_configured", return_value=True), \
             patch("main.mailer.send_verification_email", return_value=(True, "ok")), \
             patch("services.mailer.generate_verification_code", return_value="123456"):
            c.post("/auth/register", json={"email": email, "password": "Sifre12345", "name": "T"})
            c.post("/auth/verify-email", json={"email": email, "code": "123456"})
        tok = c.post("/auth/login", json={"email": email, "password": "Sifre12345"}).json()["token"]
        return c, {"Authorization": f"Bearer {tok}"}

    c, h = new_user("pazaryeri@example.com")

    # --- marketplace yayin/liste/sil ---
    r = c.post("/marketplace", json={"title": "", "description": "x"}, headers=h)
    check("basliksiz yayin 400", r.status_code == 400)
    r = c.post("/marketplace", json={
        "title": "Bogaz turu", "description": "Guzel rota",
        "from": "Kadikoy", "to": "Besiktas", "mode": "deniz",
        "place": {"name": "Kiz Kulesi", "city": "Istanbul", "lat": 41.0, "lon": 29.0},
    }, headers=h).json()
    check("yayin +30 XP", r["route"]["title"] == "Bogaz turu" and r["profile"]["xp"] >= 30,
          str(r["profile"]["xp"]))
    rid = r["route"]["id"]
    r = c.get("/marketplace").json()
    check("liste herkese acik (authsuz)", TestClient(app).get("/marketplace").status_code == 200
          and len(r.get("routes", [])) >= 1)
    c2, h2 = new_user("baskasi@example.com")
    check("baskasi silemez (404)", c2.delete(f"/marketplace/{rid}", headers=h2).status_code == 404)
    check("sahibi siler", c.delete(f"/marketplace/{rid}", headers=h).status_code == 200)

    # --- davet ---
    code = c.get("/invite/code", headers=h).json()["code"]
    check("davet kodu uretildi", bool(code) and len(code) == 8, str(code))
    check("kod sabit kalir", c.get("/invite/code", headers=h).json()["code"] == code)
    with patch("main.mailer.is_configured", return_value=True), \
         patch("main.mailer.send_verification_email", return_value=(True, "ok")), \
         patch("services.mailer.generate_verification_code", return_value="123456"):
        c.post("/auth/register", json={"email": "davetli@example.com", "password": "Sifre12345",
                                       "name": "D", "invite_code": code})
        c.post("/auth/verify-email", json={"email": "davetli@example.com", "code": "123456"})
    xp_after = c.get("/gamification/profile", headers=h).json()["xp"]
    check("davet +50 XP", xp_after >= 80, str(xp_after))
    # ayni davetli ikinci kez odullendirmez (yeni kayit ayni kodla ama farkli kisi)
    with patch("main.mailer.is_configured", return_value=True), \
         patch("main.mailer.send_verification_email", return_value=(True, "ok")), \
         patch("services.mailer.generate_verification_code", return_value="123456"):
        c.post("/auth/register", json={"email": "davetli2@example.com", "password": "Sifre12345",
                                       "name": "D2", "invite_code": code})
        c.post("/auth/verify-email", json={"email": "davetli2@example.com", "code": "123456"})
    xp_after2 = c.get("/gamification/profile", headers=h).json()["xp"]
    check("ikinci davetli +50 daha", xp_after2 == xp_after + 50, f"{xp_after}->{xp_after2}")

    # --- XP store (v1.15 katalogu: 6 dijital urun) ---
    r = c.get("/xp-store/items", headers=h).json()
    check("katalog 6 urun", len(r.get("items", [])) == 6, str(len(r.get("items", []))))
    check("bakiye gorunur", r.get("xp", 0) >= 130, str(r.get("xp")))
    # bakiye biriktir (HTTP rate limitine takilmamak icin dogrudan servis)
    from services import gamification as _g, user_store as _us
    _uid = _us.find_user_by_email("pazaryeri@example.com")["id"]
    for _ in range(30):
        _g.award(_uid, "referral")
    xp_before = c.get("/gamification/profile", headers=h).json()["xp"]
    # rozet paketi
    r = c.post("/xp-store/redeem", json={"item": "badge_pack"}, headers=h)
    check("badge_pack takas", r.status_code == 200, str(r.status_code))
    badges = c.get("/gamification/profile", headers=h).json().get("badge_ids", [])
    check("gezgin + yerel rehber rozeti", "gezgin" in badges and "yerel_rehber" in badges, str(badges))
    xp_spent = c.get("/gamification/profile", headers=h).json()["xp"]
    r = c.post("/xp-store/redeem", json={"item": "badge_pack"}, headers=h)
    check("mukerrer rozet 400", r.status_code == 400, str(r.status_code))
    check("mukerrer alimda XP harcanmaz",
          c.get("/gamification/profile", headers=h).json()["xp"] == xp_spent)
    r = c.post("/xp-store/redeem", json={"item": "yokurun"}, headers=h)
    check("gecersiz urun 400", r.status_code == 400)
    # tuketilebilir paketler
    r = c.post("/xp-store/redeem", json={"item": "ai_plus5"}, headers=h)
    check("ai_plus5 takas", r.status_code == 200, str(r.status_code))
    r = c.post("/xp-store/redeem", json={"item": "magic_plus3"}, headers=h)
    check("magic_plus3 takas", r.status_code == 200, str(r.status_code))
    # kalici kilitler
    r = c.post("/xp-store/redeem", json={"item": "night_alert"}, headers=h)
    check("night_alert takas", r.status_code == 200, str(r.status_code))
    r = c.post("/xp-store/redeem", json={"item": "night_alert"}, headers=h)
    check("mukerrer night_alert 400", r.status_code == 400, str(r.status_code))
    r = c.post("/xp-store/redeem", json={"item": "offline_pack"}, headers=h)
    check("offline_pack takas", r.status_code == 200, str(r.status_code))
    owned = {i["id"]: i["owned"] for i in c.get("/xp-store/items", headers=h).json()["items"]}
    check("sahiplik isaretleri", owned.get("badge_pack") and owned.get("night_alert")
          and owned.get("offline_pack"), str(owned))
    # 1 gunluk sinirsiz rota
    r = c.post("/xp-store/redeem", json={"item": "unlimited_day"}, headers=h)
    check("unlimited_day takas", r.status_code == 200, str(r.status_code))
    owned_now = {i["id"]: i["owned"] for i in c.get("/xp-store/items", headers=h).json()["items"]}
    check("unlimited_day sahiplik", owned_now.get("unlimited_day") is True, str(owned_now))
    from main import _unlimited_routes_active
    check("unlimited rota aktif", _unlimited_routes_active(_uid) is True)
    check("toplam harcama tutarli", xp_before - xp_spent >= 150, f"{xp_before}->{xp_spent}")
    # eski vibe_unlock kaldirildi ama onceki sahiplerin hakki korunur
    _us.grant_perk(_uid, "vibe_unlock", True)
    with patch("services.routing.calculate_route",
               return_value={"duration_minutes": 30, "distance_km": 25}), \
         patch("services.public_transport.find_transit_routes",
               return_value={"status": "ok", "routes": []}), \
         patch("services.vehicles.get_vehicle",
               return_value={"name": "T", "fuel_type": "Benzin", "consumption": 7.0}), \
         patch("services.fuel.calculate_fuel_cost",
               return_value={"total_cost": 200, "cost_per_person": 100}), \
         patch("services.location.find_province", return_value={"name": "Istanbul"}):
        body = {"start_lat": 41, "start_lon": 29, "end_lat": 41.1, "end_lon": 29.1,
                "city": "Istanbul", "mood": "manzarali"}
        check("eski vibe_unlock hakki korunur",
              c.post("/vibe-routes", json=body, headers=h).status_code == 200)
    # magic bonus etkisi
    from services import quota_store
    u = user_store.find_user_by_email("pazaryeri@example.com")
    key = quota_store.identity_key(u, "t")
    before = quota_store.get_usage(key)["magic"]
    quota_store.grant_bonus(key, "magic", 1)
    check("bonus kotayi dusurur", quota_store.get_usage(key)["magic"] == max(0, before - 1))

    # --- odullu reklam kota odulu (gunde 3) ---
    r = c.post("/ads/reward", json={"kind": "hatali"}, headers=h)
    check("gecersiz tur 400", r.status_code == 400, str(r.status_code))
    ok_count = 0
    for _ in range(4):
        r = c.post("/ads/reward", json={"kind": "routes"}, headers=h)
        if r.status_code == 200:
            ok_count += 1
    check("gunde 3 odul", ok_count == 3, str(ok_count))
    r = c.post("/ads/reward", json={"kind": "routes"}, headers=h)
    check("4. odul 400", r.status_code == 400, str(r.status_code))
    check("authsuz odul 401", TestClient(app).post("/ads/reward", json={"kind": "routes"}).status_code == 401)

    # --- AI rota detayi (adimlar gercek leg verisinden) ---
    legs = [
        {"type": "walking", "line": None, "name": "Yürüme", "route_id": "rail-walk-in",
         "distance_m": 500, "duration_min": 7, "walking_distance_m": 500,
         "walking_duration_min": 7, "departure_time": None, "arrival_time": None,
         "from_stop": None, "to_stop": "Gebze", "direction": None, "platform": None,
         "fare": None, "stops": [], "alternate_lines": [],
         "coords": [[40.80, 29.43], [40.796, 29.431]],
         "streets": ["Atatürk Caddesi"]},
        {"type": "marmaray", "line": "B1", "name": "Marmaray", "route_id": "rail-1",
         "distance_m": 33000, "duration_min": None, "departure_time": None,
         "arrival_time": None, "from_stop": "Gebze", "to_stop": "Bostancı",
         "direction": "Bostancı", "platform": None, "fare": None,
         "stops": ["Gebze", "Bostancı"], "alternate_lines": [],
         "coords": [[40.796, 29.431], [40.95, 29.10]]},
    ]
    r = c.post("/route-details", json={
        "from": "Gebze", "to": "SAW", "city": "Istanbul",
        "start_lat": 40.80, "start_lon": 29.43, "people": 2,
        "total_minutes": 131, "fee": None, "legs": legs}, headers=h)
    check("route-details 200", r.status_code == 200, str(r.status_code))
    d = r.json()
    check("2 adim", len(d.get("steps", [])) == 2, str(len(d.get("steps", []))))
    check("adim tipleri", [s["step_type"] for s in d["steps"]] == ["WALK", "TRAIN"], str([s["step_type"] for s in d["steps"]]))
    check("platform uydurma yok", d["steps"][1]["platform"] is None)
    check("binsi/inis gercek", d["steps"][1]["departure_stop"] == "Gebze" and d["steps"][1]["arrival_stop"] == "Bostancı")
    check("ozet var", bool(d.get("summary_text")), f"len={len(d.get('summary_text') or '')}")
    check("aktarma sayisi", d.get("transfer_count") == 0, str(d.get("transfer_count")))
    r = c.post("/route-details", json={"from": "A", "to": "B", "legs": []}, headers=h)
    check("bos leg 400", r.status_code == 400, str(r.status_code))
    check("authsuz detay 401", TestClient(app).post("/route-details", json={"from": "A", "to": "B", "legs": legs}).status_code == 401)

    # --- istasyon rehberi (gercek OSM verisi) ---
    r = c.get("/nearest-stations", params={"lat": 40.765, "lon": 29.945})
    check("nearest 200", r.status_code == 200, str(r.status_code))
    st = r.json().get("stations", [])
    check("izmit'e en yakin Izmit Gari", len(st) > 0 and st[0]["name"] == "İzmit Tren Garı", str([s["name"] for s in st][:3]))
    check("gar hat bilgisi", "Ada Ekspresi" in (st[0].get("lines") or []), str(st[0].get("lines")))
    r = c.get("/nearest-stations", params={"lat": 40.89, "lon": 29.24})
    names = [s["name"] for s in r.json().get("stations", [])]
    check("pendik YHT birlesik", any("Pendik YHT" in n for n in names), str(names))
    r = c.get("/nearest-stations", params={"lat": 39.9, "lon": 32.8})
    check("kapsama disi bos", r.json().get("stations") == [], str(r.json().get("stations")))
    r = c.post("/station-guide", json={
        "from": "Izmit", "to": "SAW", "start_lat": 40.765, "start_lon": 29.945,
        "end_lat": 40.905, "end_lon": 29.31}, headers=h)
    check("guide 200", r.status_code == 200, str(r.status_code))
    g = r.json()
    check("guide listeleri", len(g.get("near_start", [])) > 0 and len(g.get("near_end", [])) > 0)
    check("guide anahtarlari", "guidance" in g and "frequency_note" in g)
    check("authsuz guide 401", TestClient(app).post("/station-guide", json={
        "from": "A", "to": "B", "start_lat": 41.0, "start_lon": 29.0,
        "end_lat": 41.1, "end_lon": 29.1}).status_code == 401)

    # --- oylama & yorum ---
    r = c.post("/marketplace", json={"title": "Oy test rotasi"}, headers=h).json()
    rid2 = r["route"]["id"]
    xp0 = c.get("/gamification/profile", headers=h).json()["xp"]
    r = c.post(f"/marketplace/{rid2}/rate", json={"stars": 5}, headers=h)
    check("5 yildiz", r.status_code == 200 and r.json()["route"]["rating_avg"] == 5.0,
          str(r.status_code))
    xp1 = c.get("/gamification/profile", headers=h).json()["xp"]
    check("ilk oy +10 XP", xp1 == xp0 + 10, f"{xp0}->{xp1}")
    r = c.post(f"/marketplace/{rid2}/rate", json={"stars": 3}, headers=h).json()
    check("oy guncelleme (tekrar odul yok)",
          r["route"]["rating_avg"] == 3.0
          and c.get("/gamification/profile", headers=h).json()["xp"] == xp1)
    r = c.post(f"/marketplace/{rid2}/rate", json={"stars": 9}, headers=h)
    check("gecersiz puan 400", r.status_code == 400, str(r.status_code))
    r = c.post(f"/marketplace/{rid2}/comments", json={"text": "Harika rota!"}, headers=h)
    check("yorum + ilk +10 XP",
          r.status_code == 200 and r.json()["route"]["comment_count"] == 1
          and c.get("/gamification/profile", headers=h).json()["xp"] == xp1 + 10,
          str(r.status_code))
    r = c.post(f"/marketplace/{rid2}/comments", json={"text": "  "}, headers=h)
    check("bos yorum 400", r.status_code == 400, str(r.status_code))
    r = c.get("/marketplace?sort=top", headers=h).json()
    tops = [x["id"] for x in r.get("routes", [])]
    check("top siralama", rid2 in tops, str(tops[:3]))
    check("authsuz oy 401",
          TestClient(app).post(f"/marketplace/{rid2}/rate", json={"stars": 5}).status_code == 401)
finally:
    _restore()

print(f"\n{sum(1 for _, ok in results if ok)}/{len(results)} gecti")
sys.exit(0 if all(ok for _, ok in results) else 1)

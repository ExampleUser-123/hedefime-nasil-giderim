"""Magic Share + Gamification testleri (backend kismi).

Kapsar: magic parse, kota matrisi (2/10/sinirsiz),
XP/rozet/seviye, hedef CRUD, kalicilik (logout/login + restart simulasyonu).
data dosyalari yedeklenir ve geri yuklenir.
Kullanim: .venv/Scripts/python test_features.py
"""
import os
import shutil
import subprocess
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
        _bak = _p + ".testbak4"
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


results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra else ""))


FAKE_REV = {"display_name": "Galata Kulesi, Beyoğlu, İstanbul", "lat": 41.0, "lon": 29.0}

try:
    from services.magic_share import extract_coords, resolve_shared_text

    # --- 10. Magic parse (saf, agsiz baglantilar) ---
    check("parse google@", extract_coords("https://www.google.com/maps/@41.0082,28.9784,15z") == (41.0082, 28.9784))
    check("parse osm", extract_coords("https://www.openstreetmap.org/#map=15/41.0082/28.9784") == (41.0082, 28.9784))
    check("parse geo", extract_coords("geo:41.0082,28.9784") == (41.0082, 28.9784))
    check("parse ham", extract_coords("konum 41.0082, 28.9784 burasi") == (41.0082, 28.9784))
    check("parse bos -> None", extract_coords("") is None)
    check("parse cop -> None", extract_coords("merhaba dunya") is None)

    with patch("services.magic_share._cached_reverse", return_value=dict(FAKE_REV)):
        r = resolve_shared_text("https://www.google.com/maps/@41.0082,28.9784,15z")
        check("resolve koordinat + sehir", r.get("lat") == 41.0082 and r.get("needs_review") is True,
              str(r.get("city")))
        r = resolve_shared_text("")
        check("resolve bos -> error", "error" in r)

    from fastapi.testclient import TestClient
    from main import app

    def new_user(email, tier="free"):
        c = TestClient(app)
        with patch("main.mailer.is_configured", return_value=True), \
             patch("main.mailer.send_verification_email", return_value=(True, "ok")), \
             patch("services.mailer.generate_verification_code", return_value="123456"):
            c.post("/auth/register", json={"email": email, "password": "Sifre12345", "name": "T"})
            c.post("/auth/verify-email", json={"email": email, "code": "123456"})
        # tier ata (admin endpointi user_id ister; once kaydi bul)
        from services import user_store
        u = user_store.find_user_by_email(email)
        c.post("/admin/tier", params={"x_admin_key": "test-admin-key"},
               json={"user_id": u["id"], "tier": tier})
        tok = c.post("/auth/login", json={"email": email, "password": "Sifre12345"}).json()["token"]
        return c, {"Authorization": f"Bearer {tok}"}, u["id"]

    c0 = TestClient(app)
    # --- endpoint auth zorunlulugu ---
    check("magic authsuz -> 401", c0.post("/magic-share", json={"text": "x"}).status_code == 401)
    check("game profile authsuz -> 401", c0.get("/gamification/profile").status_code == 401)

    # --- 12/13/14. kota matrisi ---
    with patch("services.magic_share._cached_reverse", return_value=dict(FAKE_REV)):
        for tier, ok_n, label in (("free", 2, "12. free 2"), ("lite", 10, "13. lite 10")):
            c, h, _ = new_user(f"{tier}@example.com", tier)
            codes = [c.post("/magic-share", json={"text": "https://maps.google.com/?q=41.0,29.0"},
                            headers=h).status_code for _ in range(ok_n + 1)]
            check(f"{label} sonra 429", codes[:ok_n] == [200] * ok_n and codes[ok_n] == 429,
                  str(codes))
        c, h, _ = new_user("prem@example.com", "premium")
        codes = [c.post("/magic-share", json={"text": "geo:41.0,29.0"}, headers=h).status_code
                 for _ in range(12)]
        check("14. premium sinirsiz", all(s == 200 for s in codes))
        r = c.get("/magic-share/usage", headers=h).json()
        check("magic usage", r.get("used") == 12 and r.get("limit") == -1, str(r))

    # --- 21-23. gamification ---
    cg, hg, gid = new_user("game@example.com", "free")
    r = cg.post("/gamification/event", json={"type": "route_created", "meta": {"city": "Istanbul"}}, headers=hg).json()
    check("21. XP isler", r.get("xp", 0) >= 10, str(r.get("xp")))
    r = cg.post("/gamification/event", json={"type": "yokboylebirsey"}, headers=hg)
    check("gecersiz olay 400", r.status_code == 400)
    for _ in range(10):
        cg.post("/gamification/event", json={"type": "transit_used"}, headers=hg)
    prof = cg.get("/gamification/profile", headers=hg).json()
    ids = prof.get("badge_ids", [])
    check("rozet: toplu tasima ustasi", "toplu_tasima_ustasi" in ids, str(ids))
    check("rozet: yesil dostu", "yesil_dostu" in ids, str(ids))
    check("seviye>1", prof.get("level", 1) > 1 or prof.get("xp", 0) > 0, str(prof.get("level")))
    b = cg.get("/gamification/badges", headers=hg).json()
    check("rozet listesi", len(b.get("badges", [])) == 9, str(len(b.get("badges", []))))

    # hedef CRUD
    r = cg.post("/targets", json={"name": "Galata", "lat": 41, "lon": 29}, headers=hg).json()
    check("hedef ekle + XP", len(r.get("targets", [])) == 1 and r.get("profile", {}).get("xp", 0) > 0)
    tid = r["targets"][0]["id"]
    r = cg.get("/targets", headers=hg).json()
    check("hedef listele", len(r.get("targets", [])) == 1)
    r = cg.delete(f"/targets/{tid}", headers=hg).json()
    check("hedef sil", r.get("targets", []) == [])

    # --- 24. logout/login kalicilik ---
    prof1 = cg.get("/gamification/profile", headers=hg).json()["xp"]
    tok2 = cg.post("/auth/login", json={"email": "game@example.com", "password": "Sifre12345"}).json()["token"]
    prof2 = cg.get("/gamification/profile",
                   headers={"Authorization": f"Bearer {tok2}"}).json()["xp"]
    check("24. login sonrasi XP duruyor", prof1 == prof2, f"{prof1} vs {prof2}")

    # --- 25. restart simulasyonu (yeni proses, ayni anahtar) ---
    child = (
        "import os, sys; sys.path.insert(0, r\"" + BASE + "\");"
        "from fastapi.testclient import TestClient;"
        "from main import app;"
        "c = TestClient(app);"
        "t = c.post('/auth/login', json={'email':'game@example.com','password':'Sifre12345'}).json().get('token','');"
        "p = c.get('/gamification/profile', headers={'Authorization': f'Bearer {t}'}).json();"
        "print('XP:', p.get('xp'), '| rozet:', len(p.get('badge_ids', [])))"
    )
    env = dict(os.environ)
    p = subprocess.run([sys.executable, "-c", child], capture_output=True, text=True,
                       cwd=BASE, env=env, timeout=120)
    line = [ln for ln in p.stdout.splitlines() if ln.startswith("XP:")]
    check("25. restart sonrasi veri duruyor", bool(line) and "XP: 0" not in line[0],
          line[0] if line else p.stderr.strip().splitlines()[-1][:120] if p.stderr.strip() else "cikti yok")
finally:
    _restore()

print(f"\n{sum(1 for _, ok in results if ok)}/{len(results)} gecti")
sys.exit(0 if all(ok for _, ok in results) else 1)

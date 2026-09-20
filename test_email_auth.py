"""E-posta kayit/dogrulama/giris akisi testleri (TestClient + mock mailer).

Gercek data/users.json ve data/quotas.json YEDEKLENIR, test sonrasi geri yuklenir.
Kullanim: .venv/Scripts/python test_email_auth.py
"""
import os
import shutil
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.abspath(__file__))
BACKUPS = {}
for _rel in ("data/users.json", "data/users.enc.db", "data/quotas.json"):
    _p = os.path.join(BASE, _rel)
    if os.path.exists(_p):
        _bak = _p + ".testbak"
        shutil.copy2(_p, _bak)
        BACKUPS[_p] = _bak

SENT = []


def _fake_send(to_email, code, name=None):
    SENT.append({"to": to_email, "code": code})


def _restore():
    for _p, _bak in BACKUPS.items():
        shutil.move(_bak, _p)
    # test sirasinda olusan dosyalari temizle
    for _rel in ("data/users.json", "data/users.enc.db", "data/quotas.json"):
        _p = os.path.join(BASE, _rel)
        if _p not in BACKUPS and os.path.exists(_p):
            os.remove(_p)


results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra else ""))


try:
    with patch("main.mailer.is_configured", return_value=True), \
         patch("main.mailer.send_verification_email_async", side_effect=_fake_send):
        from fastapi.testclient import TestClient
        from main import app

        c = TestClient(app)
        email = "testkullanici@example.com"

        # 1. kayit
        r = c.post("/auth/register", json={
            "email": email, "password": "GucluSifre123", "name": "Test"})
        check("register -> needs_verification", r.status_code == 200
              and r.json().get("needs_verification") is True, f"HTTP {r.status_code}")
        check("kayitta kod uretildi", len(SENT) == 1 and len(SENT[0]["code"]) == 6)
        code = SENT[0]["code"]

        # 2. dogrulama oncesi giris -> 403
        r = c.post("/auth/login", json={"email": email, "password": "GucluSifre123"})
        check("dogrulanmamis giris -> 403", r.status_code == 403
              and r.json().get("needs_verification") is True, f"HTTP {r.status_code}")

        # 3. yanlis kod -> 400
        r = c.post("/auth/verify-email", json={"email": email, "code": "000000"})
        check("yanlis kod -> 400", r.status_code == 400, r.text[:80])

        # 4. hemen tekrar kod isteme -> limit (60 sn)
        r = c.post("/auth/resend-code", json={"email": email})
        check("hizli resend -> 400/429", r.status_code in (400, 429), f"HTTP {r.status_code}")

        # 5. dogru kod -> token
        r = c.post("/auth/verify-email", json={"email": email, "code": code})
        ok = r.status_code == 200 and bool(r.json().get("token"))
        check("dogru kod -> token", ok, f"HTTP {r.status_code}")
        token = r.json().get("token") if ok else None

        # 6. dogrulama sonrasi giris -> 200
        r = c.post("/auth/login", json={"email": email, "password": "GucluSifre123"})
        check("dogrulanmis giris -> 200", r.status_code == 200
              and bool(r.json().get("token")), f"HTTP {r.status_code}")

        # 7. yanlis sifre -> 401
        r = c.post("/auth/login", json={"email": email, "password": "YanlisSifre999"})
        check("yanlis sifre -> 401", r.status_code == 401, f"HTTP {r.status_code}")

        # 8. /auth/me token ile
        if token:
            r = c.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
            check("/auth/me -> tier bilgisi", r.status_code == 200
                  and "tier" in r.json().get("usage", {}), f"HTTP {r.status_code}")

        # 9. ayni e-posta tekrar kayit -> 409
        r = c.post("/auth/register", json={
            "email": email, "password": "BaskaSifre123", "name": "X"})
        check("cift kayit -> 409", r.status_code == 409, f"HTTP {r.status_code}")

        # 10. SMTP/Resend kapaliyken kayit -> 503 (zorunlu posta)
    with patch("main.mailer.is_configured", return_value=False):
        from fastapi.testclient import TestClient as TC2
        from main import app as app2
        c2 = TC2(app2)
        r = c2.post("/auth/register", json={
            "email": "baska@example.com", "password": "GucluSifre123", "name": "Y"})
        check("SMTP kapali kayit -> 503", r.status_code == 503, f"HTTP {r.status_code}")
finally:
    _restore()

print(f"\n{sum(1 for _, ok in results if ok)}/{len(results)} gecti")
sys.exit(0 if all(ok for _, ok in results) else 1)

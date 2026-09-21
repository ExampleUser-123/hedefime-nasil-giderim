"""Sifre sifirlama akisi testleri (forgot-password + reset-password).

data dosyalari yedeklenir ve geri yuklenir.
Kullanim: .venv/Scripts/python test_password_reset.py
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
        _bak = _p + ".testbak3"
        shutil.copy2(_p, _bak)
        BACKUPS[_p] = _bak


def _restore():
    for _p, _bak in BACKUPS.items():
        shutil.move(_bak, _p)
    for _rel in ("data/users.json", "data/users.enc.db", "data/quotas.json"):
        _p = os.path.join(BASE, _rel)
        if _p not in BACKUPS and os.path.exists(_p):
            os.remove(_p)


results = []
SENT = []


def _fake_mail(to_email, code, name=None):
    SENT.append({"to": to_email, "code": code})
    return True, "gonderildi (test)"


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra else ""))


try:
    with patch("main.mailer.is_configured", return_value=True), \
         patch("main.mailer.send_verification_email", side_effect=_fake_mail), \
         patch("services.mailer.generate_verification_code", return_value="654321"):
        from fastapi.testclient import TestClient
        from main import app

        c = TestClient(app)
        email = "sifremiunuttum@example.com"

        # on hazirlik: kayit + dogrulama (dogrulanmis hesapla sifirlama denenir)
        r = c.post("/auth/register", json={
            "email": email, "password": "EskiSifre123", "name": "S"})
        check("hazirlik kayit", r.status_code == 200, f"HTTP {r.status_code}")
        r = c.post("/auth/verify-email", json={"email": email, "code": "654321"})
        check("hazirlik dogrulama", r.status_code == 200, f"HTTP {r.status_code}")
        n_sent = len(SENT)

        # 60 sn gonderim limitini geriye sar (gercek hayatta zaman gecer)
        from services import user_store as _us
        _users = _us._load()
        _uid = next(u["id"] for u in _users.values() if u.get("email") == email)
        _users[_uid]["last_code_sent_at"] = "2000-01-01T00:00:00"
        _us._save(_users)

        # 1. forgot: kod gider, genel mesaj
        r = c.post("/auth/forgot-password", json={"email": email})
        check("forgot -> ok", r.status_code == 200 and r.json().get("ok") is True,
              f"HTTP {r.status_code}")
        check("forgot kodu gonderildi", len(SENT) == n_sent + 1)

        # 2. kayitsiz e-posta: ayni genel yanit (hesap sayimi yok), kod gitmez
        r = c.post("/auth/forgot-password", json={"email": "yokboylebiri@example.com"})
        check("kayitsiz forgot -> ayni genel yanit",
              r.status_code == 200 and r.json().get("ok") is True
              and len(SENT) == n_sent + 1, f"HTTP {r.status_code}")

        # 3. yanlis kodla reset -> 400
        r = c.post("/auth/reset-password", json={
            "email": email, "code": "000000", "new_password": "YeniSifre456"})
        check("yanlis kod reset -> 400", r.status_code == 400, f"HTTP {r.status_code}")

        # 4. kisa sifre -> 400
        r = c.post("/auth/reset-password", json={
            "email": email, "code": "654321", "new_password": "kisa"})
        check("kisa sifre -> 400", r.status_code == 400, f"HTTP {r.status_code}")

        # 5. dogru kod + yeni sifre -> token (otomatik giris)
        r = c.post("/auth/reset-password", json={
            "email": email, "code": "654321", "new_password": "YeniSifre456"})
        check("reset -> token", r.status_code == 200 and bool(r.json().get("token")),
              f"HTTP {r.status_code}")

        # 6. ayni kod tekrar kullanilamaz
        r = c.post("/auth/reset-password", json={
            "email": email, "code": "654321", "new_password": "Baska7890"})
        check("kod tek kullanimlik", r.status_code == 400, f"HTTP {r.status_code}")

        # 7. yeni sifreyle giris OK, eski sifre RED
        r_new = c.post("/auth/login", json={"email": email, "password": "YeniSifre456"})
        r_old = c.post("/auth/login", json={"email": email, "password": "EskiSifre123"})
        check("yeni sifre giris", r_new.status_code == 200, f"HTTP {r_new.status_code}")
        check("eski sifre red", r_old.status_code == 401, f"HTTP {r_old.status_code}")
finally:
    _restore()

print(f"\n{sum(1 for _, ok in results if ok)}/{len(results)} gecti")
sys.exit(0 if all(ok for _, ok in results) else 1)

"""Resend tabanli e-posta dogrulama uctan uca testleri.

Kapsar: kayit -> Resend cagrisi (mock) -> basarili yanit -> dogrulama ->
yanlis kod -> suresi gecmis kod -> tek kullanim -> resend akisi ->
eski kod gecersizligi -> anahtar sizintisi kontrolu -> CANLI gonderim.

CANLI test: .env'deki RESEND_API_KEY okunur (ASLA yazdirilmaz) ve
delivered@resend.dev adresine gercek API cagrisi yapilir.
Anahtar yoksa/gecersizse canli test atlanir/basarisiz sayilir.

Gercek data/users.json ve data/quotas.json YEDEKLENIR, sonda geri yuklenir.
Kullanim: .venv/Scripts/python test_resend_auth.py
"""
import logging
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


def _restore():
    for _p, _bak in BACKUPS.items():
        shutil.move(_bak, _p)
    for _rel in ("data/users.json", "data/users.enc.db", "data/quotas.json"):
        _p = os.path.join(BASE, _rel)
        if _p not in BACKUPS and os.path.exists(_p):
            os.remove(_p)
    for _f in os.listdir(os.path.join(BASE, "data")):
        if _f.startswith("users.enc.db.corrupt-"):
            os.remove(os.path.join(BASE, "data", _f))


def _load_dotenv_key(name):
    """Degeri DONDURMEZ; dogrudan ortama yazar, hicbir cikti uretmez."""
    try:
        with open(os.path.join(BASE, ".env"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(name + "="):
                    os.environ[name] = line.split("=", 1)[1].strip().strip("'\"")
                    return True
    except OSError:
        pass
    return False


results = []
BODIES = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra else ""))


try:
    os.environ["RESEND_API_KEY"] = "re_test_dummy_key"
    os.environ.pop("RESEND_FROM", None)

    SENT_PARAMS = []

    def _fake_send(params):
        SENT_PARAMS.append(params)
        return {"id": "test-msg-id-123"}

    log_records = []

    class _CapHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record.getMessage())

    logging.getLogger("mailer").addHandler(_CapHandler())
    logging.getLogger("mailer").setLevel(logging.INFO)

    with patch("resend.Emails.send", side_effect=_fake_send), \
         patch("services.mailer.generate_verification_code", return_value="123456"):
        from fastapi.testclient import TestClient
        from main import app
        from services import user_store

        c = TestClient(app)
        email = "resendtest@example.com"

        # 1+2. kayit -> kod uretildi
        r = c.post("/auth/register", json={
            "email": email, "password": "GucluSifre123", "name": "Resend Test"})
        BODIES.append(r.text)
        check("1. kayit -> needs_verification", r.status_code == 200
              and r.json().get("needs_verification") is True, f"HTTP {r.status_code}")

        # 3. Resend API cagrisi gercekten yapildi mi + parametreler
        check("3. Resend.Emails.send cagrildi", len(SENT_PARAMS) == 1)
        p = SENT_PARAMS[0] if SENT_PARAMS else {}
        check("3b. alici dogru", p.get("to") == [email])
        check("3c. from onboarding (domain yok)", "onboarding@resend.dev" in str(p.get("from")))
        check("3d. konu+icerik kodu tasiyor",
              "123456" in str(p.get("subject")) and "123456" in str(p.get("html")))
        check("3e. parametrede anahtar yok", "re_test_dummy_key" not in str(p))

        # 4. basarili yanit islendi (id loglandi, hata yok)
        check("4. basari logu (id)", any("test-msg-id-123" in m for m in log_records))

        # 7. yanlis kod
        r = c.post("/auth/verify-email", json={"email": email, "code": "000000"})
        BODIES.append(r.text)
        check("7. yanlis kod -> 400", r.status_code == 400, f"HTTP {r.status_code}")

        # 8. suresi gecmis kod
        users = user_store._load()
        uid = next(u["id"] for u in users.values() if u.get("email") == email)
        users[uid]["verification_expires_at"] = "2000-01-01T00:00:00"
        user_store._save(users)
        r = c.post("/auth/verify-email", json={"email": email, "code": "123456"})
        BODIES.append(r.text)
        check("8. suresi gecmis kod -> 400", r.status_code == 400
              and "resi" in r.text.lower(), f"HTTP {r.status_code}")
        user_store.set_verification_code(uid, "123456")

        # 6. dogru kodla dogrulama
        r = c.post("/auth/verify-email", json={"email": email, "code": "123456"})
        BODIES.append(r.text)
        check("6. dogru kod -> token", r.status_code == 200
              and bool(r.json().get("token")), f"HTTP {r.status_code}")

        # 9. ayni kod ikinci kez kullanilamaz
        r = c.post("/auth/verify-email", json={"email": email, "code": "123456"})
        BODIES.append(r.text)
        check("9. kod tekrar kullanimi -> 400", r.status_code == 400, f"HTTP {r.status_code}")

        # 10+11. yeni kod eskisini gecersiz kilar (magaza katmaninda)
        email2 = "resendtest2@example.com"
        r = c.post("/auth/register", json={
            "email": email2, "password": "GucluSifre123", "name": "T2"})
        check("10. ikinci kullaniciya kod gonderimi", r.status_code == 200
              and len(SENT_PARAMS) == 2, f"HTTP {r.status_code}")
        users = user_store._load()
        uid2 = next(u["id"] for u in users.values() if u.get("email") == email2)
        user_store.set_verification_code(uid2, "111111")
        user_store.set_verification_code(uid2, "222222")
        r_old = c.post("/auth/verify-email", json={"email": email2, "code": "111111"})
        r_new = c.post("/auth/verify-email", json={"email": email2, "code": "222222"})
        BODIES.append(r_old.text + r_new.text)
        check("11. eski kod gecersiz, yeni kod gecerli",
              r_old.status_code == 400 and r_new.status_code == 200,
              f"eski={r_old.status_code} yeni={r_new.status_code}")

    # 12. anahtar sizintisi: yanitlar + loglarda tam anahtar gecmemeli
    all_text = "\n".join(BODIES + log_records)
    check("12. yanit/loglarda API anahtari yok", "re_test_dummy_key" not in all_text)

    # 5. CANLI: gercek Resend API cagrisi (delivered@resend.dev)
    del os.environ["RESEND_API_KEY"]
    if _load_dotenv_key("RESEND_API_KEY"):
        from services import mailer
        live_ok = mailer._send_via_resend("delivered@resend.dev", "000000", "Canli Test")
        check("5. CANLI Resend gonderimi (delivered@resend.dev)", live_ok,
              "basarili" if live_ok else "anahtar gecersiz veya ag hatasi")
    else:
        check("5. CANLI test ATLANDI (.env'de RESEND_API_KEY yok)", False)
finally:
    _restore()

print(f"\n{sum(1 for _, ok in results if ok)}/{len(results)} gecti")
sys.exit(0 if all(ok for _, ok in results) else 1)

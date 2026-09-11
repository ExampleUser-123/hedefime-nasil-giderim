# -*- coding: utf-8 -*-
"""Kota sistemi testi: free 7 rota siniri + admin tier yukseltme."""
import time

import jwt
from fastapi.testclient import TestClient

import main
from services import quota_store

SECRET = "test-secret-kota"

# Kotalari sifirla (temiz baslangic)
quota_store.QUOTA_FILE.unlink(missing_ok=True)

main.JWT_TEST_SECRET = SECRET
import os
os.environ["JWT_SECRET"] = SECRET
os.environ["ADMIN_KEY"] = "test-admin-key"

client = TestClient(main.app)

# Once kullaniciyi kaydet (admin tier guncelemesi icin kayit sart)
reg = client.post("/auth/register", json={
    "email": "kota@test.local", "password": "test12345", "name": "Kota Test"})
USER_ID = reg.json()["user"]["id"]

tok = jwt.encode(
    {"sub": USER_ID, "email": "kota@test.local", "name": "Kota Test",
     "iat": int(time.time()), "exp": int(time.time()) + 3600},
    SECRET, algorithm="HS256",
)
H = {"Authorization": "Bearer " + tok}

# 8 rota aramasi: ilk 7 gecmeli, 8. 429 donmeli
sonuclar = []
for i in range(8):
    r = client.get("/plan", params={"start": "Kadikoy", "end": "Taksim"},
                   headers=H)
    sonuclar.append(r.status_code)

print("rota durum kodlari:", sonuclar)
print("7 tane 200 + 1 tane 429 beklenir:", sonuclar[:7] == [200]*7 and sonuclar[7] == 429)

# 429 govdesinde mesaj var mi
r8 = client.get("/plan", params={"start": "Kadikoy", "end": "Taksim"}, headers=H)
print("429 mesaji:", r8.json().get("detail", "")[:80])

# Usage raporu
u = client.get("/usage", headers=H).json()
print("usage:", u)

# Admin ile lite'a yukselt -> limit 20 olur
r = client.post("/admin/tier", params={"x_admin_key": "test-admin-key"},
                json={"user_id": USER_ID, "tier": "lite"})
print("tier guncelle:", r.status_code, r.json().get("user", {}).get("tier"))

# Ayni istek artik gecmeli (kullanilan 7 < 20)
r = client.get("/plan", params={"start": "Kadikoy", "end": "Taksim"}, headers=H)
print("lite sonrasi ayni istek:", r.status_code, "(200 beklenir)")

# Admin key korumasi
r = client.post("/admin/tier", json={"user_id": "kota-test-user", "tier": "premium"})
print("adminsiz istek:", r.status_code, "(403 beklenir)")

# Temizlik
quota_store.QUOTA_FILE.unlink(missing_ok=True)

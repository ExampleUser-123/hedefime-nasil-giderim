"""Gunluk kota takibi: ucretsiz/lite/premium katmanlari.

data/quotas.json formati:
{
  "date": "2026-09-12",
  "usage": {
    "u:abc123": {"routes": 3, "ai": 1},
    "ip:9f8e7d...": {"routes": 7, "ai": 2}
  }
}

Tarih degistiginde sayaclar otomatik sifirlanir (gunluk kota).
"""

import hashlib
import json
import threading
from datetime import date
from pathlib import Path

def _paths():
    """Yazilabilir dizine gore (Vercel'de /tmp) cozulmus dosya yolu."""
    from services.storage_dir import writable_base_dir
    base = writable_base_dir()
    return base, base / "quotas.json"


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUOTA_FILE = DATA_DIR / "quotas.json"

# Katman limitleri (None = sinirsiz)
TIERS: dict[str, dict] = {
    "free": {"routes": 7, "ai": 7, "magic": 2},
    "lite": {"routes": 20, "ai": 30, "magic": 10},
    "premium": {"routes": None, "ai": None, "magic": None},
}

_lock = threading.Lock()


def _load() -> dict:
    _, quota_file = _paths()
    try:
        with open(quota_file, encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("date") != date.today().isoformat():
            return {"date": date.today().isoformat(), "usage": {}}
        return data
    except (OSError, ValueError):
        return {"date": date.today().isoformat(), "usage": {}}


def _save(data: dict) -> None:
    _, quota_file = _paths()
    tmp = quota_file.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    tmp.replace(quota_file)


def identity_key(user: dict | None, client_ip: str) -> str:
    """Girisli kullanici icin sabit anahtar; anonim icin IP hash'i."""
    if user:
        return f"u:{user['id']}"
    return "ip:" + hashlib.sha256(client_ip.encode()).hexdigest()[:24]


def tier_of(user: dict | None) -> str:
    t = (user or {}).get("tier") or "free"
    return t if t in TIERS else "free"


def get_usage(key: str) -> dict:
    with _lock:
        data = _load()
        u = data["usage"].get(key) or {}
        return {
            "routes": int(u.get("routes", 0)),
            "ai": int(u.get("ai", 0)),
            "magic": int(u.get("magic", 0)),
        }


def limits_for(tier: str) -> dict:
    return TIERS.get(tier, TIERS["free"])


def check(key: str, tier: str, kind: str) -> tuple[bool, int, int]:
    """(geçti, kullanılan, limit) döner. limit -1 = sinirsiz."""
    limit = limits_for(tier).get(kind)
    used = get_usage(key)[kind]
    if limit is None:
        return True, used, -1
    return used < limit, used, limit


def count(key: str, kind: str) -> None:
    with _lock:
        data = _load()
        u = data["usage"].setdefault(key, {})
        u[kind] = int(u.get(kind, 0)) + 1
        _save(data)


def delete_user_usage(user_id: str) -> bool:
    """Kullanicinin kota kayitlarini siler. Kayit vardiysa True doner."""

    prefix = f"u:{user_id}"
    with _lock:
        data = _load()
        keys = [k for k in data.get("usage", {}) if k == prefix or k.startswith(prefix + ":")]
        for k in keys:
            del data["usage"][k]
        if keys:
            _save(data)
        return bool(keys)

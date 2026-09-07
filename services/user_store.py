"""Kullanici + favori deposu (JSON dosya, chat_store ile ayni yaklasim).

NOT: Render free tier'da dosya sistemi deploy/restart'larda sifirlanir.
Bu, mevcut chat_sessions davranisiyla aynidir; ileride ucretsiz bir
Postgres'e (orn. Supabase) tasinabilir.
"""

import os
import json
import threading
import uuid
from datetime import datetime


DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)

USERS_FILE = os.path.join(DATA_DIR, "users.json")

MAX_FAVORITES = 50

_lock = threading.Lock()


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except (json.JSONDecodeError, OSError):
        return {}


def _save(users: dict):
    _ensure_dir()

    tmp_path = USERS_FILE + ".tmp"

    with open(tmp_path, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False)

    os.replace(tmp_path, USERS_FILE)


def upsert_google_user(payload: dict) -> dict:
    """Google payload'indaki kullaniciyi kaydeder/gunceller; user dict doner."""

    user_id = payload["sub"]
    now = datetime.now().isoformat(timespec="seconds")

    with _lock:
        users = _load()

        user = users.get(user_id) or {
            "id": user_id,
            "created_at": now,
            "favorites": [],
            "ai_request_count": 0,
        }

        user.update({
            "email": payload.get("email"),
            "name": payload.get("name") or "Kullanici",
            "picture": payload.get("picture"),
            "last_login": now,
        })

        users[user_id] = user
        _save(users)

    return user


def get_user(user_id: str) -> dict | None:
    users = _load()
    return users.get(user_id)


def public_user(user: dict) -> dict:
    """Istemciye gonderilecek guvenli alanlar (ic sayaclar haric)."""

    return {
        "id": user["id"],
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture"),
        "created_at": user.get("created_at"),
    }


def count_ai_request(user_id: str):
    """Kullanicinin AI istek sayacini artirir."""

    with _lock:
        users = _load()

        user = users.get(user_id)

        if user is None:
            return

        user["ai_request_count"] = user.get("ai_request_count", 0) + 1
        user["last_ai_request"] = datetime.now().isoformat(timespec="seconds")

        _save(users)


# --- Favoriler -------------------------------------------------------------


def list_favorites(user_id: str) -> list:
    user = get_user(user_id)

    if user is None:
        return []

    return user.get("favorites", [])


def add_favorite(user_id: str, item: dict) -> list | None:
    """Favori ekler; limit asilarsa None doner."""

    now = datetime.now().isoformat(timespec="seconds")

    with _lock:
        users = _load()

        user = users.get(user_id)

        if user is None:
            return None

        favorites = user.setdefault("favorites", [])

        # Ayni guzergah (yon ayrimi olmadan) zaten varsa tekrar ekleme
        for existing in favorites:
            if (existing.get("from") == item.get("from")
                    and existing.get("to") == item.get("to")
                    and existing.get("mode") == item.get("mode")):
                return favorites

        if len(favorites) >= MAX_FAVORITES:
            return None

        favorites.append({
            "id": uuid.uuid4().hex[:12],
            "from": item.get("from"),
            "to": item.get("to"),
            "people": item.get("people", 1),
            "mode": item.get("mode", "tumu"),
            "created_at": now,
        })

        _save(users)

    return user["favorites"]


def remove_favorite(user_id: str, favorite_id: str) -> list | None:
    with _lock:
        users = _load()

        user = users.get(user_id)

        if user is None:
            return None

        favorites = user.get("favorites", [])
        new_favorites = [f for f in favorites if f.get("id") != favorite_id]

        if len(new_favorites) == len(favorites):
            return favorites  # bulunamadi; mevcut listeyi dondur

        user["favorites"] = new_favorites
        _save(users)

    return new_favorites


def admin_user_overview() -> list:
    """Kotuye kullanim incelemesi icin ozet: kullanicilar + sohbet istatistikleri."""

    users = _load()

    overview = []

    for user in users.values():
        overview.append({
            "id": user["id"],
            "email": user.get("email"),
            "name": user.get("name"),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login"),
            "ai_request_count": user.get("ai_request_count", 0),
            "last_ai_request": user.get("last_ai_request"),
            "favorite_count": len(user.get("favorites", [])),
        })

    overview.sort(
        key=lambda u: u.get("last_ai_request") or "",
        reverse=True,
    )

    return overview

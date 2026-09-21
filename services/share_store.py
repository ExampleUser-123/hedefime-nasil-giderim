# -*- coding: utf-8 -*-
"""Paylasim linkleri ve doluluk bildirimleri icin JSON tabanli depo.

Kullanicinin kalicilik beklentisi dusuk: linkler 30 gun, doluluk verisi
7 gun penceresinde toplanir. Render ephemeral diskte sifirlanabilir.
"""

import json
import os
import secrets
import threading
import time

from typing import Optional

from services.storage_dir import writable_base_dir


def _paths():
    base = str(writable_base_dir())
    return (
        os.path.join(base, "share_routes.json"),
        os.path.join(base, "crowding.json"),
        os.path.join(base, "community_routes.json"),
    )


_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_SHARE_PATH, _CROWD_PATH, _COMMUNITY_PATH = _paths()

_LOCK = threading.Lock()

_SHARE_TTL_DAYS = 30
_CROWD_WINDOW_DAYS = 7

CROWD_LEVELS = ("empty", "normal", "crowded", "packed")
PUNCT_LEVELS = ("on_time", "late")


def _load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


# --- Paylasim linkleri -------------------------------------------------------

def save_share_route(start: str, destination: str, people: int, mode: str) -> str:
    rid = secrets.token_urlsafe(6)
    with _LOCK:
        store = _load(_SHARE_PATH)
        # Eski kayitlari temizle
        cutoff = time.time() - _SHARE_TTL_DAYS * 86400
        store = {k: v for k, v in store.items() if v.get("created", 0) > cutoff}
        store[rid] = {
            "start": start[:200],
            "destination": destination[:200],
            "people": max(1, min(int(people or 1), 50)),
            "mode": mode[:20],
            "created": time.time(),
        }
        _save(_SHARE_PATH, store)
    return rid


def get_share_route(rid: str) -> Optional[dict]:
    with _LOCK:
        store = _load(_SHARE_PATH)
    rec = store.get(rid)
    if not rec:
        return None
    cutoff = time.time() - _SHARE_TTL_DAYS * 86400
    if rec.get("created", 0) < cutoff:
        return None
    return {
        "start": rec["start"],
        "destination": rec["destination"],
        "people": rec["people"],
        "mode": rec["mode"],
    }


# --- Doluluk bildirimleri ----------------------------------------------------

def save_crowding_report(city: str, line: str, level: str = "", punctuality: str = "") -> bool:
    # Ya doluluk ya dakiklik (ya da ikisi) gelmeli
    if level not in CROWD_LEVELS and punctuality not in PUNCT_LEVELS:
        return False
    key = f"{city[:60]}|{line[:60]}"
    with _LOCK:
        store = _load(_CROWD_PATH)
        cutoff = time.time() - _CROWD_WINDOW_DAYS * 86400

        rec = store.get(key)
        if not rec or rec.get("created", 0) < cutoff:
            rec = {"city": city[:60], "line": line[:60], "created": time.time(),
                   "counts": {lvl: 0 for lvl in CROWD_LEVELS},
                   "punct": {lvl: 0 for lvl in PUNCT_LEVELS}}

        if level in CROWD_LEVELS:
            counts = rec["counts"]
            counts[level] = counts.get(level, 0) + 1
        if punctuality in PUNCT_LEVELS:
            rec["punct"][punctuality] = rec["punct"].get(punctuality, 0) + 1
        # Pencere tasmasi: eski kayitlari kaba bir orana gore azalt
        total = sum(rec["counts"].values())
        if total > 500:
            for lvl in CROWD_LEVELS:
                rec["counts"][lvl] = int(rec["counts"].get(lvl, 0) * 0.9)
            for lvl in PUNCT_LEVELS:
                rec["punct"][lvl] = int(rec["punct"].get(lvl, 0) * 0.9)

        store[key] = rec
        # Eski kayitlari temizle
        store = {k: v for k, v in store.items() if v.get("created", 0) >= cutoff}
        _save(_CROWD_PATH, store)
    return True


def get_crowding_summary(city: str, lines: list[str]) -> dict:
    out = {}
    with _LOCK:
        store = _load(_CROWD_PATH)
    for line in lines[:12]:
        key = f"{city[:60]}|{str(line)[:60]}"
        rec = store.get(key)
        if not rec:
            continue
        counts = rec.get("counts", {})
        total = sum(counts.values())
        punct = rec.get("punct", {})
        punct_total = sum(punct.values())
        if max(total, punct_total) < 3:
            # Az veri -> yaniltmasin
            continue
        out[line] = {
            "total": total,
            "counts": counts,
            "crowded_share": round((counts.get("crowded", 0) + counts.get("packed", 0)) / total, 2) if total else 0,
            "punct": punct,
        }
    return out


# --- Topluluk rotalari (Marketplace / Kesfet) ----------------------------------

_MAX_COMMUNITY = 500


def publish_community_route(user_id: str, user_name: str, item: dict) -> dict | None:
    """Topluluga rota/mekan yayinlar; kaydi doner. Baslik + guzergah zorunlu."""

    title = (item.get("title") or "").strip()[:80]
    if not title:
        return None
    images = [str(u)[:300] for u in (item.get("image_urls") or [])[:3]]
    place = item.get("place") or {}
    entry = {
        "id": secrets.token_urlsafe(6),
        "user_id": user_id,
        "user_name": (user_name or "Gezgin")[:40],
        "title": title,
        "description": (item.get("description") or "").strip()[:500],
        "from": (item.get("from") or "").strip()[:160],
        "to": (item.get("to") or "").strip()[:160],
        "mode": (item.get("mode") or "tumu").strip()[:20],
        "people": max(1, min(int(item.get("people") or 1), 50)),
        "place": {
            "name": str(place.get("name") or "")[:80],
            "address": str(place.get("address") or "")[:160],
            "city": str(place.get("city") or "")[:60],
            "lat": place.get("lat"),
            "lon": place.get("lon"),
        },
        "image_urls": images,
        "created": time.time(),
    }
    with _LOCK:
        store = _load(_COMMUNITY_PATH)
        store[entry["id"]] = entry
        if len(store) > _MAX_COMMUNITY:
            oldest = sorted(store, key=lambda k: store[k].get("created", 0))
            for k in oldest[: len(store) - _MAX_COMMUNITY]:
                del store[k]
        _save(_COMMUNITY_PATH, store)
    return entry


def list_community_routes(limit: int = 20, offset: int = 0) -> list[dict]:
    """En yeniden eskiye topluluk rotalari (sayfali)."""

    limit = max(1, min(int(limit or 20), 50))
    offset = max(0, int(offset or 0))
    with _LOCK:
        store = _load(_COMMUNITY_PATH)
    ordered = sorted(store.values(), key=lambda e: e.get("created", 0), reverse=True)
    return ordered[offset: offset + limit]


def delete_community_route(entry_id: str, user_id: str) -> bool:
    """Sadece sahibi silebilir."""

    with _LOCK:
        store = _load(_COMMUNITY_PATH)
        rec = store.get(entry_id)
        if not rec or rec.get("user_id") != user_id:
            return False
        del store[entry_id]
        _save(_COMMUNITY_PATH, store)
    return True

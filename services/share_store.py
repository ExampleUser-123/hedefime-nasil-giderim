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
        os.path.join(base, "live_trips.json"),
    )


_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_SHARE_PATH, _CROWD_PATH, _COMMUNITY_PATH, _TRIP_PATH = _paths()

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


def list_community_routes(limit: int = 20, offset: int = 0, sort: str = "new") -> list[dict]:
    """Topluluk rotalari: new (varsayilan) veya top (ortalama puan)."""

    limit = max(1, min(int(limit or 20), 50))
    offset = max(0, int(offset or 0))
    with _LOCK:
        store = _load(_COMMUNITY_PATH)
    items = [_with_rating(e) for e in store.values()]
    if sort == "top":
        ordered = sorted(items, key=lambda e: (-e["rating_avg"], -e.get("created", 0)))
    else:
        ordered = sorted(items, key=lambda e: e.get("created", 0), reverse=True)
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


def _with_rating(entry: dict) -> dict:
    """Kopyaya ortalama puan + oy sayisi ekler (ham kayit degismez)."""

    ratings = entry.get("ratings") or {}
    vals = [int(v) for v in ratings.values()
            if isinstance(v, int) and 1 <= v <= 5]
    out = dict(entry)
    out["rating_avg"] = round(sum(vals) / len(vals), 1) if vals else 0.0
    out["rating_count"] = len(vals)
    comments = entry.get("comments") or []
    out["comments"] = comments[-10:]
    out["comment_count"] = len(comments)
    return out


def rate_community_route(entry_id: str, user_id: str, stars: int) -> tuple[dict | None, bool]:
    """1-5 puan verir (kisi basi tek oy, guncellenebilir).

    Donus: (guncel kayit, ilk_kez_mi). Ilk oyda +10 XP icin ilk_kez kullanilir.
    """

    if not isinstance(stars, int) or not 1 <= stars <= 5:
        return None, False
    # bool int'in alt sinifi; True/False oy olmasin
    if isinstance(stars, bool):
        return None, False
    with _LOCK:
        store = _load(_COMMUNITY_PATH)
        rec = store.get(entry_id)
        if not rec:
            return None, False
        ratings = rec.setdefault("ratings", {})
        first = user_id not in ratings
        ratings[user_id] = stars
        _save(_COMMUNITY_PATH, store)
        return _with_rating(rec), first


def comment_community_route(entry_id: str, user_id: str, user_name: str,
                            text: str) -> tuple[dict | None, bool]:
    """Kisa yorum ekler. Donus: (guncel kayit, ilk_yorum_mu)."""

    text = (text or "").strip()[:300]
    if not text:
        return None, False
    with _LOCK:
        store = _load(_COMMUNITY_PATH)
        rec = store.get(entry_id)
        if not rec:
            return None, False
        comments = rec.setdefault("comments", [])
        first = not any(c.get("user_id") == user_id for c in comments)
        comments.append({
            "user_id": user_id,
            "user_name": (user_name or "Gezgin")[:40],
            "text": text,
            "created": time.time(),
        })
        _save(_COMMUNITY_PATH, store)
        return _with_rating(rec), first


# --- Canli yolculuk paylasimi ---------------------------------------------------

_TRIP_TTL_SECONDS = 12 * 3600


def _trip_prune(store: dict) -> dict:
    cutoff = time.time() - _TRIP_TTL_SECONDS
    return {k: v for k, v in store.items() if v.get("updated", 0) > cutoff}


def create_live_trip(user_id: str, user_name: str, item: dict) -> dict:
    """Takip oturumu acar. Donus: {id, update_key} (key ping kimligidir)."""

    entry = {
        "id": secrets.token_urlsafe(6),
        "update_key": secrets.token_urlsafe(16),
        "user_id": user_id,
        "user_name": (user_name or "Gezgin")[:40],
        "from": str(item.get("from") or "")[:160],
        "destination": str(item.get("destination") or "")[:160],
        "dest_lat": item.get("dest_lat"),
        "dest_lon": item.get("dest_lon"),
        "lat": item.get("lat"),
        "lon": item.get("lon"),
        "eta_min": item.get("eta_min"),
        "created": time.time(),
        "updated": time.time(),
    }
    with _LOCK:
        store = _trip_prune(_load(_TRIP_PATH))
        store[entry["id"]] = entry
        _save(_TRIP_PATH, store)
    return {"id": entry["id"], "update_key": entry["update_key"]}


def ping_live_trip(trip_id: str, update_key: str, lat, lon, eta_min) -> dict | None:
    """Konum gunceller. Anahtar yanlissa None (yetkisiz)."""

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return None
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None
    try:
        eta = None if eta_min is None else max(0, int(float(eta_min)))
    except (TypeError, ValueError):
        eta = None
    with _LOCK:
        store = _trip_prune(_load(_TRIP_PATH))
        rec = store.get(trip_id)
        if not rec or rec.get("update_key") != update_key:
            _save(_TRIP_PATH, store)
            return None
        rec["lat"] = lat
        rec["lon"] = lon
        rec["eta_min"] = eta
        rec["updated"] = time.time()
        _save(_TRIP_PATH, store)
        return _public_trip(rec)


def get_live_trip(trip_id: str) -> dict | None:
    """Takip gorunumu (herkese acik). Suresi dolmussa None."""

    with _LOCK:
        store = _trip_prune(_load(_TRIP_PATH))
    rec = store.get(trip_id)
    if not rec:
        return None
    return _public_trip(rec)


def _public_trip(rec: dict) -> dict:
    return {
        "from": rec.get("from", ""),
        "destination": rec.get("destination", ""),
        "user_name": rec.get("user_name", ""),
        "lat": rec.get("lat"),
        "lon": rec.get("lon"),
        "eta_min": rec.get("eta_min"),
        "updated": rec.get("updated", 0),
    }

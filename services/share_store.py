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

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_SHARE_PATH = os.path.join(_DATA_DIR, "share_routes.json")
_CROWD_PATH = os.path.join(_DATA_DIR, "crowding.json")

_LOCK = threading.Lock()

_SHARE_TTL_DAYS = 30
_CROWD_WINDOW_DAYS = 7

CROWD_LEVELS = ("empty", "normal", "crowded", "packed")


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

def save_crowding_report(city: str, line: str, level: str) -> bool:
    if level not in CROWD_LEVELS:
        return False
    key = f"{city[:60]}|{line[:60]}"
    with _LOCK:
        store = _load(_CROWD_PATH)
        cutoff = time.time() - _CROWD_WINDOW_DAYS * 86400

        rec = store.get(key)
        if not rec or rec.get("created", 0) < cutoff:
            rec = {"city": city[:60], "line": line[:60], "created": time.time(),
                   "counts": {lvl: 0 for lvl in CROWD_LEVELS}}

        counts = rec["counts"]
        counts[level] = counts.get(level, 0) + 1
        # Pencere tasmasi: eski kayitlari kaba bir orana gore azalt
        total = sum(counts.values())
        if total > 500:
            for lvl in CROWD_LEVELS:
                counts[lvl] = int(counts[lvl] * 0.9)

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
        if total < 3:
            # Az veri -> yaniltmasin
            continue
        out[line] = {
            "total": total,
            "counts": counts,
            "crowded_share": round((counts.get("crowded", 0) + counts.get("packed", 0)) / total, 2),
        }
    return out

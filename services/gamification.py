"""Gamification — Rozetler + XP + Seviye.

Tum durum kullanici kaydinda (`user["game"]`) tutulur; mevcut user_store
uzeninden okunur/yazilir, ayri tablo/DB yok. Rozetler uyelikten bagimsizdir
(free/lite/premium hepsinde acik).

XP tablosu (olay bazinda):
  route_created: 10 | transit_used: 15 | car_used: 10 | walk_used: 15
  target_added: 10 | city_explored: 25 (yeni sehir) | night_route: 15

Seviye: her 200 XP'de +1 (seviye = xp // 200 + 1).
"""

from __future__ import annotations

from datetime import datetime

from services import user_store

XP_TABLE = {
    "route_created": 10,
    "transit_used": 15,
    "car_used": 10,
    "walk_used": 15,
    "target_added": 10,
    "city_explored": 25,
    "night_route": 15,
    "route_published": 30,
    "referral": 50,
    "rated_route": 10,
    "commented_route": 10,
}

LEVEL_STEP = 200

BADGES = {
    "gece_kusu": {
        "name": "Gece Kuşu", "icon": "🌙",
        "desc": "Gece saatlerinde rota kullandı.",
    },
    "sehir_kasifi": {
        "name": "Şehir Kaşifi", "icon": "🗺️",
        "desc": "3 farklı şehirde rota oluşturdu.",
    },
    "yesil_dostu": {
        "name": "Yeşil Dostu", "icon": "🌱",
        "desc": "5 kez yürüyüş veya toplu taşıma tercih etti.",
    },
    "toplu_tasima_ustasi": {
        "name": "Toplu Taşıma Ustası", "icon": "🚍",
        "desc": "10 toplu taşıma rotası kullandı.",
    },
    "yolcu": {
        "name": "Yolcu", "icon": "🚗",
        "desc": "10 araç rotası oluşturdu.",
    },
    "kasif": {
        "name": "Kaşif", "icon": "🧭",
        "desc": "5 farklı hedef ekledi.",
    },
}

# Rozet sarti: (sayac_turu, esik). Sayıclar game["counters"] altinda tutulur.
BADGE_RULES = {
    "gece_kusu": ("night_routes", 1),
    "sehir_kasifi": ("cities_count", 3),
    "yesil_dostu": ("green_trips", 5),
    "toplu_tasima_ustasi": ("transit_trips", 10),
    "yolcu": ("car_trips", 10),
    "kasif": ("targets_count", 5),
}


def level_for_xp(xp: int) -> dict:
    """{level, progress} — progress bir sonraki seviyeye yuzde."""
    level = max(1, int(xp or 0) // LEVEL_STEP + 1)
    base = (level - 1) * LEVEL_STEP
    progress = min(100, int(((int(xp or 0) - base) / LEVEL_STEP) * 100))
    return {"level": level, "progress": progress}


def spend_xp(user_id: str, amount: int) -> tuple[bool, dict]:
    """XP harcar. (basarili_mi, guncel_profil) doner; yetersizse (False, profil)."""

    amount = max(0, int(amount or 0))
    game = user_store.get_game(user_id)
    if game["xp"] < amount:
        return False, profile(user_id)
    game["xp"] = game["xp"] - amount
    user_store.save_game(user_id, game)
    return True, profile(user_id)


def _is_night(now: datetime | None = None) -> bool:
    from services.timeutil import now_tr
    h = (now or now_tr()).hour
    return h >= 22 or h < 6


def profile(user_id: str) -> dict:
    """Kullanici oyun profili: xp, seviye, rozetler, sehirler, hedef sayisi."""
    game = user_store.get_game(user_id)
    xp = game["xp"]
    info = level_for_xp(xp)
    badges = [
        {"id": bid, **BADGES[bid]}
        for bid in game["badges"] if bid in BADGES
    ]
    return {
        "xp": xp,
        "level": info["level"],
        "progress": info["progress"],
        "badges": badges,
        "badge_ids": list(game["badges"]),
        "cities": list(game["cities"]),
        "targets_count": len(game["targets"]),
    }


def award(user_id: str, event: str, meta: dict | None = None) -> dict:
    """Olayi isler: XP + sayac + rozet. Guncel profili doner.

    Bilinmeyen olay reddedilir (value error). Sehir/Gece turetimleri
    meta'dan alinir: {city, hour, mode}.
    """
    meta = meta or {}
    if event not in XP_TABLE:
        raise ValueError(f"Bilinmeyen olay: {event}")

    game = user_store.get_game(user_id)
    counters = game.setdefault("counters", {})
    xp_gain = XP_TABLE[event]
    game["xp"] = game.get("xp", 0) + xp_gain

    if event == "route_created":
        city = (meta.get("city") or "").strip()
        if city and city not in game["cities"]:
            game["cities"].append(city)
            game["xp"] += XP_TABLE["city_explored"]
    if event in ("transit_used", "walk_used"):
        counters["green_trips"] = counters.get("green_trips", 0) + 1
    if event == "transit_used":
        counters["transit_trips"] = counters.get("transit_trips", 0) + 1
    if event == "car_used":
        counters["car_trips"] = counters.get("car_trips", 0) + 1
    if event == "walk_used":
        counters["walk_trips"] = counters.get("walk_trips", 0) + 1
    if event == "target_added":
        counters["targets_count"] = len(game.get("targets", []))
    if event == "night_route" or _is_night() and event in (
            "route_created", "transit_used", "car_used", "walk_used"):
        counters["night_routes"] = counters.get("night_routes", 0) + 1
    counters["cities_count"] = len(game.get("cities", []))

    new_badges: list[str] = []
    owned = set(game.get("badges", []))
    for bid, (counter, threshold) in BADGE_RULES.items():
        if bid not in owned and counters.get(counter, 0) >= threshold:
            owned.add(bid)
            new_badges.append(bid)
    game["badges"] = sorted(owned)

    user_store.save_game(user_id, {**game, "counters": counters})
    result = profile(user_id)
    result["xp_gain"] = xp_gain
    result["new_badges"] = [
        {"id": bid, **BADGES[bid]} for bid in new_badges if bid in BADGES
    ]
    return result

"""Vibe-Based Routing — "Moduma Gore Rota".

Mevcut rota altyapisi (search_place + calculate_route + find_transit_routes)
uzerinden mood'a gore siralama/not/POI onerisi uretir. Yeni rota motoru YOK.

Modlar: sakin, ekonomik, manzarali, kahve.
Ucretsiz planda sakin+ekonomik acik; manzarali/kahve Lite/Premium (backend
zorunlu kontrol — frontend kilidi tek basina yeterli degil).
"""

from __future__ import annotations

MOODS = ("sakin", "ekonomik", "manzarali", "kahve")

FREE_MOODS = ("sakin", "ekonomik")


def mood_allowed(mood: str, tier: str) -> bool:
    """Ucretsizde kilitli modlari reddet."""
    if mood not in MOODS:
        return False
    if tier in ("lite", "premium"):
        return True
    return mood in FREE_MOODS


def _estimate_mood(plan: dict, mood: str) -> dict:
    """Plan sozlugunden mood basiligi cikar (hepsi opsiyonel alan)."""
    car = plan.get("car") or {}
    transit = plan.get("public_transport") or {}
    routes = transit.get("routes") or []
    first = routes[0] if routes else {}
    legs = first.get("legs") or []
    walk_m = sum((leg.get("distance_m") or 0) for leg in legs
                 if str(leg.get("type", "")).upper() == "WALKING")
    return {
        "car_minutes": car.get("duration_minutes"),
        "car_cost": car.get("total_cost"),
        "transit_minutes": first.get("duration_minutes"),
        "transit_fee": first.get("fee"),
        "walk_m": walk_m,
        "transit_count": len(routes),
    }


def rank_for_mood(plan: dict, mood: str) -> dict:
    """Mood'a gore oneri siralamasi + not. Girdi plani degistirmez."""

    est = _estimate_mood(plan, mood)
    notes: list[str] = []
    order: list[str] = []
    highlights: dict = {}

    if mood == "sakin":
        order = ["transit", "walk", "car"]
        if est["walk_m"]:
            notes.append(f"Aktarmasiz/yurumesi az secenekler one cikarildi (yurume ~{int(est['walk_m'])} m).")
        else:
            notes.append("Sakin mod: kalabalik saatlerde rayli + az aktarmali hatlar oncelikli.")
        highlights = {"prefer": "az yurume ve az aktarma"}

    elif mood == "ekonomik":
        order = ["transit", "car", "walk"]
        fees = [r.get("fee") for r in (plan.get("public_transport") or {}).get("routes", [])
                if r.get("fee") is not None]
        if fees:
            notes.append(f"En ucuz toplu tasima ~{min(fees)} TL'den basliyor.")
        if est["car_cost"] is not None:
            notes.append(f"Ozel arac maliyeti ~{est['car_cost']} TL (kisi basi bolusur).")
        if not fees and est["car_cost"] is None:
            notes.append("Ucret bilgisi bulunamadi; sureye gore siralama yapildi.")
        highlights = {"prefer": "dusuk ucret"}

    elif mood == "manzarali":
        order = ["ferry", "transit", "walk", "car"]
        notes.append("Manzarali mod: mumkunse vapur/sahil hatti ve yurume agirlikli secenekler.")
        highlights = {"prefer": "vapur ve sahil"}

    elif mood == "kahve":
        order = ["transit", "walk", "car"]
        notes.append("Kahve molali mod: varis cevresi icin asagidaki mola noktalarina bak.")
        highlights = {"prefer": "mola noktasi yakinligi"}

    else:
        order = ["transit", "car", "walk"]

    return {"mood": mood, "order": order, "notes": notes,
            "highlights": highlights, "estimate": est}


def suggest_pois(lat: float, lon: float, city: str, mood: str,
                 limit: int = 3) -> list[dict]:
    """Manzara/kahve icin ucretsiz POI onerisi (Photon/Nominatim).

    Rota geometrisini degistirmez; yalnizca yakin oneri listesi doner.
    Basarisizsa bos liste (uygulama cokmez, fallback calisir).
    """
    queries = {
        "kahve": [f"kafe {city}", f"kahve {city}"],
        "manzarali": [f"park {city}", f"sahil {city}", f"manzara {city}"],
    }.get(mood, [])
    out: list[dict] = []
    try:
        from services.geocoding import suggest_places
        for q in queries:
            try:
                for s in suggest_places(q, lat, lon) or []:
                    out.append({
                        "name": s.get("name", ""),
                        "detail": s.get("detail", ""),
                        "lat": s.get("lat"),
                        "lon": s.get("lon"),
                    })
                    if len(out) >= limit:
                        return out
            except Exception:
                continue
    except Exception:
        pass
    return out[:limit]

"""Rota detay zinciri: gercek leg verisi -> adim adim RouteStep listesi.

KRITIK KURAL: Bu moduldaki tum adim alanlari backend'in urettigi gercek
verilerden (durak adlari, hat adlari, sureler, koordinatlar, GTFS sefer
saatleri) doldurulur. Veri yoksa alan None birakilir; ASLA uydurulmaz.
Gemini yalnizca ozet metni (summary_text) uretir, adim uretmez.
"""

RAIL_TYPES = ("METRO", "MARMARAY", "TRAM", "FUNIC", "RAIL", "NOSTAL")


def _step_type(leg_type: str) -> str:
    t = (leg_type or "").upper()
    if t == "WALKING":
        return "WALK"
    if "MARMARAY" in t or "TRAIN" in t or "YHT" in t:
        return "TRAIN"
    if any(k in t for k in ("METRO", "TRAM", "FUNIC", "RAIL", "NOSTAL")):
        return "METRO"
    if "FERRY" in t or "VAPUR" in t or "DENIZ" in t:
        return "FERRY"
    return "BUS"


def _fmt_duration(minutes) -> str | None:
    if minutes is None:
        return None
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return None
    if minutes < 60:
        return f"~{minutes} dk"
    return f"~{minutes // 60} sa {minutes % 60:02d} dk"


def _departure_times(city, leg, lat, lon):
    """Gercek sefer saatleri (GTFS). Yoksa/hata varsa None."""
    line = leg.get("line")
    stop = leg.get("from_stop")
    if not line or not stop or lat is None or lon is None:
        return None
    try:
        from services.gtfs_times import next_departures
        found = next_departures(city, line, stop, float(lat), float(lon)) or []
        times = [d.get("time") for d in found if d.get("time")]
        return times[:3] or None
    except Exception:
        return None


def _walking_instruction(leg) -> str:
    dist = leg.get("walking_distance_m") or leg.get("distance_m") or 0
    dur = leg.get("walking_duration_min") or leg.get("duration_min")
    target = leg.get("to_stop") or "hedef"
    text = f"{target} yönüne {round(dist)} m yürü"
    if dur:
        text += f" (~{dur} dk)"
    streets = [s for s in (leg.get("streets") or []) if s]
    if streets:
        text += f": {' → '.join(streets[:3])} üzerinden"
    return text + "."


def _transit_instruction(leg) -> str:
    line = leg.get("line") or ""
    name = leg.get("name") or ""
    title = f"{line} {name}".strip() or "Toplu taşıma"
    frm = leg.get("from_stop") or "biniş durağı"
    to = leg.get("to_stop") or "iniş durağı"
    text = f"{title} ile {frm} durağından bin, {to} durağında in."
    stops = leg.get("stops") or []
    if len(stops) > 1:
        text += f" ({len(stops) - 1} durak)"
    dur = _fmt_duration(leg.get("duration_min"))
    if dur:
        text += f" {dur}."
    return text


def leg_to_step(leg, city=None, lat=None, lon=None) -> dict:
    """Tek leg -> RouteStep dict. Tum alanlar gercek veriden."""
    is_walk = (leg.get("type") or "").upper() == "WALKING"
    duration = None
    if is_walk:
        duration = _fmt_duration(
            leg.get("walking_duration_min") or leg.get("duration_min")
        )
    else:
        duration = _fmt_duration(leg.get("duration_min"))

    return {
        "step_type": _step_type(leg.get("type", "")),
        "instruction": _walking_instruction(leg) if is_walk else _transit_instruction(leg),
        "departure_stop": leg.get("from_stop"),
        "arrival_stop": leg.get("to_stop"),
        "line_name": (leg.get("name") or leg.get("line")),
        "departure_times": None if is_walk else _departure_times(city, leg, lat, lon),
        "duration": duration,
        "walking_distance_m": leg.get("walking_distance_m") or leg.get("distance_m"),
        "walking_duration_min": leg.get("walking_duration_min") or leg.get("duration_min"),
        "direction": leg.get("direction"),
        "platform": None,
        "fare": None,
    }


def route_to_details(route, people=1, city=None, lat=None, lon=None) -> dict:
    """TransitRoute dict -> RouteDetailResponse dict (summary_text haric)."""
    legs = route.get("legs", []) or []
    steps = [leg_to_step(leg, city=city, lat=lat, lon=lon) for leg in legs]

    total_min = route.get("duration_minutes")
    fee = route.get("fee")
    total_walk = route.get("walking_distance_m") or sum(
        (leg.get("walking_distance_m") or leg.get("distance_m") or 0)
        for leg in legs
        if (leg.get("type") or "").upper() == "WALKING"
    )

    return {
        "total_duration": _fmt_duration(total_min) or "Süre verisi yok",
        "total_price": (
            f"~{round(fee * people)} TL ({people} kişi, tahmini)"
            if fee is not None else "Ücret verisi yok"
        ),
        "total_walking_m": round(total_walk),
        "transfer_count": max(0, len([l for l in legs if (l.get("type") or "").upper() != "WALKING"]) - 1),
        "summary_text": "",
        "steps": steps,
    }

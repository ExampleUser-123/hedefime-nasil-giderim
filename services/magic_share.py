"""Magic Share — "Beni Buraya Götür" baglanti cozucu.

Paylasilmis metin icinden konum cikarir (deterministik, AI'siz):
- Google Maps: `@lat,lon`, `?q=`, `?query=`, `place/...`
- Apple Maps: `?ll=lat,lon`, `?q=`
- OpenStreetMap: `#map=z/lat/lon`, `?mlat=&mlon=`
- geo: URI, ham "lat,lon" metni
Koordinat bulunamazsa metindeki sorguyla yer aramasi yapilir; sonuc
reverse-geocode ile sehir/adres acisindan dogrulanir.

AI sonucuna koru korune guvenilmez: cikti her zaman `needs_review`
bayragiyla doner; kullanici onaylamadan hedefe eklenmez.
"""

from __future__ import annotations

import re
from urllib.parse import unquote_plus

from services.cache import cached

_COORD_RE = re.compile(
    r"(?P<lat>-?\d{1,2}(?:\.\d+)?)\s*[,;]\s*(?P<lon>-?\d{1,3}(?:\.\d+)?)"
)
_GOOGLE_AT_RE = re.compile(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")
_OSM_HASH_RE = re.compile(r"#map=\d+/(-?\d+(?:\.\d+)?)/(-?\d+(?:\.\d+)?)")
_GEO_RE = re.compile(r"geo:(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")


def _valid(lat: float, lon: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0 and not (
        lat == 0.0 and lon == 0.0)


def _from_query_params(text: str) -> tuple[float, float] | None:
    for key in ("query=", "q=", "ll="):
        idx = text.find(key)
        if idx < 0:
            continue
        raw = unquote_plus(text[idx + len(key):].split("&")[0].split("#")[0])
        m = _COORD_RE.search(raw)
        if m:
            try:
                lat, lon = float(m.group("lat")), float(m.group("lon"))
            except ValueError:
                continue
            if _valid(lat, lon):
                return lat, lon
    return None


def extract_coords(text: str) -> tuple[float, float] | None:
    """Metinden koordinat cikarir; bulamazsa None."""
    if not text:
        return None
    for pattern in (_GOOGLE_AT_RE, _OSM_HASH_RE, _GEO_RE):
        m = pattern.search(text)
        if m:
            try:
                lat, lon = float(m.group(1)), float(m.group(2))
            except ValueError:
                continue
            if _valid(lat, lon):
                return lat, lon
    found = _from_query_params(text)
    if found:
        return found
    # Ham "lat,lon" (link disi metin); Turkiye civari makul aralik sarti
    m = _COORD_RE.search(text)
    if m:
        try:
            lat, lon = float(m.group("lat")), float(m.group("lon"))
        except ValueError:
            return None
        if _valid(lat, lon) and 35.0 <= lat <= 43.0 and 25.0 <= lon <= 45.0:
            return lat, lon
    return None


def _query_text(text: str) -> str:
    """Koordinatsiz metinden aranabilir sorgu cikarir (URL'ler temizlenir)."""
    cleaned = re.sub(r"https?://\S+", " ", text or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:160]


def _detect_city(lat: float, lon: float) -> str:
    """Cevrimdisi il tespiti (bbox); basarisizsa bos doner."""
    try:
        from services.city_detect import city_for_point
        return city_for_point(lat, lon) or ""
    except Exception:
        return ""


@cached(3600)
def _cached_search(query: str):
    from services.geocoding import smart_search_place
    try:
        return smart_search_place(query)
    except Exception:
        return None


@cached(3600)
def _cached_reverse(lat: float, lon: float):
    from services.geocoding import reverse_geocode
    try:
        return reverse_geocode(lat, lon)
    except Exception:
        return None


def resolve_shared_text(text: str) -> dict:
    """Paylasilmis metni konum adayina cozer.

    Donus: {name, address, city, lat, lon, confidence, needs_review, error?}
    Koordinat/adres dogrulanamazsa error doner (uydurma konum uretilmez).
    """
    text = (text or "").strip()
    if not text:
        return {"error": "Paylaşılan metin boş. Bir link veya adres yapıştırın."}

    coords = extract_coords(text)
    if coords:
        lat, lon = coords
        place = _cached_reverse(lat, lon)
        if not place:
            return {"error": "Bu koordinat için adres bulunamadı."}
        name = place.get("display_name", "").split(",")[0].strip() or "Konum"
        city = _detect_city(lat, lon)
        return {
            "name": name,
            "address": place.get("display_name", ""),
            "city": city,
            "lat": lat,
            "lon": lon,
            "confidence": "high" if city else "medium",
            "needs_review": True,
        }

    query = _query_text(text)
    if not query:
        return {"error": "Metinden konum çıkarılamadı. Link veya açık adres yapıştırın."}
    place = _cached_search(query)
    if not place or place.get("lat") is None:
        return {"error": "Bu adres bulunamadı. Yazımı kontrol edip tekrar deneyin."}
    try:
        lat, lon = float(place["lat"]), float(place["lon"])
    except (TypeError, ValueError):
        return {"error": "Konum doğrulanamadı."}
    if not _valid(lat, lon):
        return {"error": "Konum doğrulanamadı."}
    name = (place.get("display_name", "") or query).split(",")[0].strip()
    return {
        "name": name or query,
        "address": place.get("display_name", ""),
        "city": _detect_city(lat, lon),
        "lat": lat,
        "lon": lon,
        "confidence": "medium",
        "needs_review": True,
    }

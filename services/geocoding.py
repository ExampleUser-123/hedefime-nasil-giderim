import requests

from services.cache import cached


# Turkiye telefon/klavye kisaltmalari + tur adlari: sorgudan dusurulup
# anlamli cekirdek birakilir ("Kartepe KOTO AOSB Mesleki ve Teknik
# Anadolu Lisesi" -> "Kartepe KOTO AOSB").
_GENERIC_TOKENS = frozenset("""
mesleki teknik anadolu lisesi liseler lisesi okulu okul ilkokulu ilkokul
ortaokulu ortaokul hastanesi hastane devlet sehir universitesi universite
fakultesi avm alisveris merkezi belediyesi mudurlugu ve veya bir
""".split())


def _core_tokens(query: str) -> list[str]:
    """Jenerik kelimeleri eleyip anlamli jetonlari dondurur."""
    words = [w for w in query.lower().split() if len(w) >= 3]
    core = [w for w in words if w not in _GENERIC_TOKENS]
    return core or words


def _query_variants(query: str, city: str | None = None) -> list[str]:
    """Denenebilir sorgu varyantlari: ham -> sehir baglamli -> cekirdek."""
    q = (query or "").strip()
    out: list[str] = []
    if q:
        out.append(q)
    if city and city.strip():
        c = city.strip()
        if c.lower() not in q.lower():
            out.append(f"{q} {c}")
    core = _core_tokens(q)
    if len(core) >= 2:
        short = " ".join(core[:4])
        if short.lower() != q.lower():
            out.append(short)
        if city and city.strip():
            combo = f"{short} {city.strip()}"
            if combo not in out:
                out.append(combo)
    return out[:4]


@cached(ttl_seconds=24 * 3600)
def search_place(query: str):
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "tr"
    }

    headers = {
        "User-Agent": "HEDEFIME-NASIL-GIDERIM/1.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    result = results[0]

    return {
        "display_name": result["display_name"],
        "lat": float(result["lat"]),
        "lon": float(result["lon"])
    }


@cached(ttl_seconds=24 * 3600)
def suggest_places(query: str, lat: float | None = None, lon: float | None = None,
                   city: str | None = None):
    """Yazarken öneri: sorguya uyan yer listesi (autocomplete).

    Birincil kaynak Photon (OSM tabanli, yazim hatasina toleransli,
    POI sonuclarini on planda tutar: "adnan men" -> Adnan Menderes
    Havalimani). lat/lon verilirse sonuclar o noktanin cevresine
    onceliklendirilir (mahalle/ilce dogru bolgeden cikar).
    Cevap gelmezse Nominatim'e dener.

    city verilirse sorgu varyantlari (ham -> sehir baglamli -> cekirdek)
    sirasiyla denenir; okul/hastane/AVM gibi uzun kurum adlarinda isabeti
    artirir. Son care Overpass (harf-hatasina toleransli ad aramasi).
    """

    q = query.strip()

    if len(q) < 3:
        return []

    headers = {
        "User-Agent": "hedefime-nasil-giderim/1.0 (rota uygulamasi)"
    }

    for variant in _query_variants(q, city):
        if len(variant) < 3:
            continue
        got = _suggest_single(variant, lat, lon, headers)
        if got:
            return got

    # --- 3) Overpass son care (koordinat varsa cevrede ad aramasi) ---
    if lat is not None and lon is not None:
        try:
            got = overpass_search(q, lat, lon)
            if got:
                return got
        except Exception:
            pass

    return []


def _suggest_single(q: str, lat: float | None, lon: float | None, headers: dict):
    """Tek sorgu varyanti: Photon, olmazsa Nominatim. Bos liste doner."""

    # --- 1) Photon (konum bicimi yapilabilir) ---
    try:
        photon_params = {"q": q, "limit": 6, "lang": "default"}

        if lat is not None and lon is not None:
            photon_params["lat"] = str(lat)
            photon_params["lon"] = str(lon)
            photon_params["zoom"] = "13"

        response = requests.get(
            "https://photon.komoot.io/api/",
            params=photon_params,
            headers=headers,
            timeout=8
        )

        response.raise_for_status()

        suggestions = []

        for feature in response.json().get("features", []):
            props = feature["properties"]
            name = props.get("name")

            if not name:
                continue

            # Detay: ilce/sehir + il (varsa)
            detail_parts = []
            for key in ("city", "county", "state"):
                value = props.get(key)
                if value and value not in detail_parts:
                    detail_parts.append(value)

            coord = feature["geometry"]["coordinates"]

            suggestions.append({
                "name": name,
                "detail": ", ".join(detail_parts[:2]),
                "display_name": ", ".join([name] + detail_parts[:3]),
                "lat": float(coord[1]),
                "lon": float(coord[0])
            })

        if suggestions:
            return suggestions
    except Exception:
        pass

    # --- 2) Nominatim yedegi (konum varsa yakin bolgeye oncelik) ---
    nominatim_params = {
        "q": q,
        "format": "json",
        "limit": 6,
        "countrycodes": "tr",
        "accept-language": "tr"
    }

    if lat is not None and lon is not None:
        # Kullanici etrafinda ~50 km'lik pencere; bounded=0 varsayilani
        # ile disindaki sonuclar da donebilir ama yakinlar one cikar.
        nominatim_params["viewbox"] = f"{lon - 0.5},{lat + 0.5},{lon + 0.5},{lat - 0.5}"

    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params=nominatim_params,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    suggestions = []

    for result in response.json():
        parts = [p.strip() for p in result["display_name"].split(",")]

        suggestions.append({
            "name": parts[0],
            "detail": ", ".join(parts[1:4]),
            "display_name": result["display_name"],
            "lat": float(result["lat"]),
            "lon": float(result["lon"])
        })

    if suggestions:
        return suggestions

    return []


@cached(ttl_seconds=24 * 3600)
def overpass_search(query: str, lat: float, lon: float,
                    radius_m: int = 50000) -> list[dict]:
    """Overpass API ile cevrede ad aramasi (harf-hatasina toleransli).

    Photon/Nominatim bulamazsa son care. Buyuk/kucuk harf duyarsiz alt
    dizgi eslesmesi yapar; okul/hastane gibi POI'leri yakalar.
    Basarisizsa bos liste doner (uygulama cokmez).
    """
    import re as _re

    core = _core_tokens(query)
    if not core:
        return []
    # En ayirt edici ilk 2 jetonla regex (asiri genislemeyi onler)
    pattern = ".*".join(_re.escape(w) for w in core[:2])
    ql = (
        f'[out:json][timeout:15];'
        f'(nwr["name"~"{pattern}",i](around:{int(radius_m)},{lat},{lon}););'
        f'out center 5;'
    )
    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": ql},
            headers={"User-Agent": "hedefime-nasil-giderim/1.0 (rota uygulamasi)"},
            timeout=18,
        )
        response.raise_for_status()
        elements = response.json().get("elements", [])
    except Exception:
        return []

    out = []
    for el in elements:
        tags = el.get("tags") or {}
        name = (tags.get("name") or "").strip()
        if not name:
            continue
        if el.get("type") == "node":
            elat, elon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center") or {}
            elat, elon = center.get("lat"), center.get("lon")
        try:
            elat, elon = float(elat), float(elon)
        except (TypeError, ValueError):
            continue
        city = tags.get("addr:city") or tags.get("addr:county") or ""
        out.append({
            "name": name,
            "detail": city,
            "display_name": ", ".join(p for p in (name, city) if p),
            "lat": elat,
            "lon": elon,
        })
    return out


def smart_search_place(query: str, lat: float | None = None,
                       lon: float | None = None,
                       city: str | None = None) -> dict | None:
    """Tekil yer cozumu: varyantli oneriler, olmazsa Overpass.

    Donus search_place ile ayni semada ({display_name, lat, lon}) veya None.
    Uydurma sonuc uretilmez.
    """
    try:
        suggestions = suggest_places(query, lat, lon, city)
    except Exception:
        suggestions = []
    if suggestions:
        first = suggestions[0]
        return {
            "display_name": first.get("display_name", ""),
            "lat": first.get("lat"),
            "lon": first.get("lon"),
        }
    if lat is not None and lon is not None:
        try:
            pois = overpass_search(query, lat, lon)
        except Exception:
            pois = []
        if pois:
            first = pois[0]
            return {
                "display_name": first.get("display_name", ""),
                "lat": first.get("lat"),
                "lon": first.get("lon"),
            }
    return None


@cached(ttl_seconds=24 * 3600)
def reverse_geocode(lat: float, lon: float):
    """Koordinattan yere ismi bulur (GPS konumu için)."""

    url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 16,
        "accept-language": "tr"
    }

    headers = {
        "User-Agent": "HEDEFIME-NASIL-GIDERIM/1.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    display_name = data.get("display_name")

    if not display_name:
        return None

    return {
        "display_name": display_name,
        "lat": float(lat),
        "lon": float(lon)
    }
import requests

from services.cache import cached


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
def suggest_places(query: str, lat: float | None = None, lon: float | None = None):
    """Yazarken öneri: sorguya uyan yer listesi (autocomplete).

    Birincil kaynak Photon (OSM tabanli, yazim hatasina toleransli,
    POI sonuclarini on planda tutar: "adnan men" -> Adnan Menderes
    Havalimani). lat/lon verilirse sonuclar o noktanin cevresine
    onceliklendirilir (mahalle/ilce dogru bolgeden cikar).
    Cevap gelmezse Nominatim'e dener.
    """

    q = query.strip()

    if len(q) < 3:
        return []

    headers = {
        "User-Agent": "hedefime-nasil-giderim/1.0 (rota uygulamasi)"
    }

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

    return suggestions


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
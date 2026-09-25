"""Istasyon rehberi: OSM rayli ag verisinden gercek en-yakin-istasyonlar.

Tum isim/koordinat/hat bilgileri data/istanbul_rail.json.gz'den hesaplanir;
disaridan isim UYDURULMAZ. Gemini yalnizca bu gercek listeyi yorumlayan
kisa rehber metni uretir (saat uyduramaz).
"""

from services.istanbul_rail import _build_network, _haversine_m


def nearest_stations(lat: float, lon: float, limit: int = 3,
                     max_distance_m: float = 100_000) -> list[dict]:
    """Verilen noktaya en yakin rayli sistem istasyonlari.

    Donus: [{name, lat, lon, distance_m, lines: [hat ref/ad]}].
    Ag kapsama disiysa (100 km'den uzak) bos liste doner.
    """
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        return []

    limit = max(1, min(5, int(limit or 3)))
    net = _build_network()

    scored = []
    for idx, cluster in enumerate(net["clusters"]):
        try:
            dist = _haversine_m(lat_f, lon_f, cluster["lat"], cluster["lon"])
        except (TypeError, ValueError, KeyError):
            continue
        if dist <= max_distance_m:
            scored.append((dist, idx))
    scored.sort(key=lambda item: item[0])

    lines_of = {}
    for idx in [i for _, i in scored[:limit]]:
        refs: list[str] = []
        for _, _, line_idx in net["edges"].get(idx, []):
            try:
                line = net["lines"][line_idx]
            except (IndexError, TypeError):
                continue
            ref = line.get("ref") or line.get("name")
            if ref and ref not in refs:
                refs.append(ref)
        lines_of[idx] = refs

    out = []
    for dist, idx in scored[:limit]:
        cluster = net["clusters"][idx]
        out.append({
            "name": cluster.get("name"),
            "lat": cluster.get("lat"),
            "lon": cluster.get("lon"),
            "distance_m": round(dist),
            "lines": lines_of.get(idx, []),
        })
    return out

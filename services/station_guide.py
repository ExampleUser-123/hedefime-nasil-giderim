"""Istasyon rehberi: rayli ag verisi + dogrulanmis TCDD istasyonlari.

Tum isim/koordinatlar gercektir: ag kumeleri data/istanbul_rail.json.gz'den,
ek TCDD istasyonlari OSM Nominatim'den dogrulanmis koordinatlarla gelir.
Hat etiketleri muhafazakar tutulur; saat bilgisi bu modulde yoktur.
Gemini yalnizca bu gercek listeyi yorumlayan kisa rehber metni uretir.
"""

from services.istanbul_rail import _build_network, _haversine_m


# TCDD/YHT ana istasyonlari — OSM Nominatim'den dogrulanmis gercek
# koordinatlar (uydurma yok). OSM rayli aginda olmayan sehirlerarasi
# istasyonlari kapsar. "lines" etiketleri muhafazakar tutulur: YHT
# durak bilgisi TCDD tarifesine gore degisebildigi icin yalnizca kesin
# olanlar yazilir.
EXTRA_STATIONS: list[dict] = [
    {
        "name": "İzmit Tren Garı",
        "lat": 40.7617997,
        "lon": 29.9176868,
        "lines": ["Ada Ekspresi", "TCDD"],
    },
    {
        "name": "Derince Garı",
        # OSM'deki iki peron noktasinin ortalamasi (40.7544435,29.8345710
        # ve 40.7538853,29.8328070)
        "lat": 40.7541644,
        "lon": 29.833689,
        "lines": ["Ada Ekspresi", "TCDD"],
    },
    {
        "name": "Pendik YHT",
        # OSM Pendik Kavsagi istasyon noktasi; agdaki Pendik kumesine
        # ~1 m oldugu icin gorunumde onunla birlesir (cift satir cikmaz).
        "lat": 40.8886547,
        "lon": 29.2385810,
        "lines": ["YHT"],
    },
]

# Ayni fiziksel istasyon sayilir ve tek satirda birlesir (metre)
MERGE_M = 300


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

    # TCDD ek istasyonlari: tum agda 300 m icinde kume varsa onunla birles
    # (hat etiketleri kumeye eklenir, cift satir cikmaz); yoksa ve kapsama
    # icindeyse ayri satir olarak ekle.
    for extra in EXTRA_STATIONS:
        try:
            dist = _haversine_m(lat_f, lon_f, extra["lat"], extra["lon"])
        except (TypeError, ValueError, KeyError):
            continue
        if dist > max_distance_m:
            continue
        target = None
        for idx, cluster in enumerate(net["clusters"]):
            try:
                gap = _haversine_m(extra["lat"], extra["lon"],
                                   cluster["lat"], cluster["lon"])
            except (TypeError, ValueError, KeyError):
                continue
            if gap <= MERGE_M:
                target = idx
                break
        if target is not None:
            for row_pos, (d, idx) in enumerate(scored[:limit]):
                if idx == target:
                    row = out[row_pos]
                    for ref in extra.get("lines", []):
                        if ref and ref not in row["lines"]:
                            row["lines"].append(ref)
                    if extra["name"] not in (row["name"] or ""):
                        row["name"] = f"{row['name']} / {extra['name']}"
                    break
            # Hedef kume listede degilse bile ag kapsiyor demektir; cift
            # satir cikmamasi icin ek satir ekleme.
            continue
        out.append({
            "name": extra["name"],
            "lat": extra["lat"],
            "lon": extra["lon"],
            "distance_m": round(dist),
            "lines": list(extra.get("lines", [])),
        })

    out.sort(key=lambda row: row["distance_m"])
    return out[:limit]

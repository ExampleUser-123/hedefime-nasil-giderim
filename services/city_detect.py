# -*- coding: utf-8 -*-
"""Sehir tespit servisi: verilen (lat, lon) noktasinin hangi ilde oldugunu
kaba bbox (dortlu sinir) tablosu uzerinden bulur.

Il siniri poligonu kullanilmaz; bbox'lar il merkezi + genis cevreyi kapsar.
Birden fazla ilin bbox'ina dusen nokta, il merkezine en yakin il olarak
degerlendirilir. Hicbir bbox'a dusmeyen noktalar icin None doner.
"""

import math

# (il_adi, south, west, north, east)
PROVINCES = [
    ("Adana",             36.80, 34.80, 38.30, 36.40),
    ("Adıyaman",          37.20, 37.40, 38.30, 39.30),
    ("Afyonkarahisar",    38.00, 29.40, 39.20, 31.60),
    ("Ağrı",              39.00, 42.20, 40.10, 44.80),
    ("Aksaray",           37.80, 33.30, 38.90, 34.80),
    ("Amasya",            40.30, 34.60, 41.20, 36.30),
    ("Ankara",            38.90, 31.00, 40.40, 33.50),
    ("Antalya",           35.90, 29.30, 37.60, 32.40),
    ("Ardahan",           40.60, 42.30, 41.50, 43.60),
    ("Artvin",            40.60, 41.20, 41.50, 42.60),
    ("Aydın",             37.00, 27.00, 38.10, 28.90),
    ("Balıkesir",         39.00, 26.30, 40.40, 28.40),
    ("Bartın",            41.30, 32.30, 42.00, 33.20),
    ("Batman",            37.30, 40.90, 38.20, 41.80),
    ("Bayburt",           39.90, 39.40, 40.60, 40.70),
    ("Bilecik",           39.90, 29.70, 40.50, 31.10),
    ("Bingöl",            38.40, 40.20, 39.30, 41.50),
    ("Bitlis",            38.00, 41.50, 39.10, 42.70),
    ("Bolu",              40.20, 30.50, 41.20, 32.60),
    ("Burdur",            37.00, 29.20, 38.10, 31.10),
    ("Bursa",             39.60, 28.20, 40.60, 29.70),
    ("Çanakkale",         39.40, 26.00, 40.60, 27.70),
    ("Çankırı",           40.20, 32.20, 41.10, 34.20),
    ("Çorum",             40.00, 34.00, 41.20, 35.90),
    ("Denizli",           37.40, 28.10, 38.40, 30.30),
    ("Diyarbakır",        37.40, 39.30, 38.80, 41.30),
    ("Düzce",             40.60, 30.70, 41.20, 31.70),
    ("Edirne",            40.60, 26.30, 41.80, 27.00),
    ("Elazığ",            37.80, 38.20, 39.00, 39.90),
    ("Erzincan",          39.10, 38.20, 40.30, 40.30),
    ("Erzurum",           39.40, 40.20, 40.60, 42.60),
    ("Eskişehir",         38.90, 30.00, 40.20, 32.10),
    ("Gaziantep",         36.60, 37.00, 37.90, 38.80),
    ("Giresun",           40.30, 37.90, 41.10, 39.20),
    ("Gümüşhane",         39.90, 38.70, 40.80, 40.30),
    ("Hakkâri",           37.20, 43.30, 38.00, 44.80),
    ("Hatay",             35.80, 35.90, 37.30, 36.90),
    ("Iğdır",             39.30, 43.40, 40.20, 44.90),
    ("Isparta",           37.30, 30.00, 38.40, 31.60),
    ("İstanbul",          40.50, 27.90, 41.60, 29.90),
    ("İzmir",             37.70, 26.30, 39.40, 28.50),
    ("Kahramanmaraş",     37.00, 36.20, 38.40, 37.80),
    ("Karabük",           40.90, 32.00, 41.50, 33.30),
    ("Karaman",           36.90, 32.40, 38.00, 34.20),
    ("Kars",              40.00, 42.50, 41.00, 44.00),
    ("Kastamonu",         40.80, 32.60, 42.10, 34.60),
    ("Kayseri",           37.80, 34.50, 39.20, 36.60),
    ("Kırıkkale",         39.30, 32.90, 40.10, 34.10),
    ("Kırklareli",        41.00, 26.90, 42.10, 27.70),
    ("Kırşehir",          38.90, 33.70, 39.70, 34.70),
    ("Kilis",             36.50, 36.90, 37.20, 37.60),
    ("Kocaeli",           40.40, 29.30, 41.30, 30.60),
    ("Konya",             36.90, 31.20, 38.90, 33.80),
    ("Kütahya",           38.80, 28.90, 39.70, 30.60),
    ("Malatya",           37.90, 37.00, 39.00, 38.90),
    ("Manisa",            38.20, 27.00, 39.60, 28.70),
    ("Mardin",            36.90, 39.90, 38.10, 41.20),
    ("Mersin",            35.90, 32.20, 37.50, 35.00),
    ("Muğla",             36.40, 27.20, 37.60, 29.20),
    ("Muş",               38.50, 40.90, 39.50, 42.20),
    ("Nevşehir",          38.20, 34.00, 39.10, 35.20),
    ("Niğde",             37.30, 34.00, 38.60, 35.30),
    ("Ordu",              40.40, 37.10, 41.10, 38.40),
    ("Osmaniye",          36.80, 36.00, 37.50, 36.80),
    ("Rize",              40.60, 40.30, 41.20, 41.20),
    ("Sakarya",           40.30, 29.80, 41.00, 31.10),
    ("Samsun",            40.80, 35.50, 41.80, 37.30),
    ("Siirt",             37.30, 41.50, 38.10, 42.40),
    ("Sinop",             41.10, 34.10, 42.30, 35.60),
    ("Sivas",             38.60, 35.80, 40.30, 38.40),
    ("Şanlıurfa",         36.60, 37.70, 38.20, 40.20),
    ("Şırnak",            37.00, 41.50, 37.90, 43.30),
    ("Tekirdağ",          40.50, 26.60, 41.40, 28.10),
    ("Tokat",             39.70, 35.60, 40.70, 37.50),
    ("Trabzon",           40.50, 38.90, 41.20, 40.50),
    ("Tunceli",           38.80, 38.70, 39.60, 40.10),
    ("Uşak",              38.20, 28.90, 39.00, 30.20),
    ("Van",               37.60, 42.30, 39.10, 44.30),
    ("Yalova",            40.40, 28.80, 40.90, 29.40),
    ("Yozgat",            38.80, 34.10, 40.30, 36.30),
    ("Zonguldak",         41.00, 31.30, 41.80, 32.60),
]

_center_cache = {
    name: ((s + n) / 2.0, (w + e) / 2.0) for name, s, w, n, e in PROVINCES
}


def _dist(lat1, lon1, lat2, lon2):
    """Yaklasik mesafe (km) — kucuk acilar icin yeterli."""
    dy = (lat2 - lat1) * 111.0
    dx = (lon2 - lon1) * 111.0 * math.cos(math.radians((lat1 + lat2) / 2.0))
    return math.hypot(dy, dx)


def city_for_point(lat: float, lon: float) -> str | None:
    """Noktanin bulundugu ilin adini dondurur; disarida ise None."""
    matches = [
        name
        for name, s, w, n, e in PROVINCES
        if s <= lat <= n and w <= lon <= e
    ]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    # Cakisma varsa il merkezine en yakin olan kazanir.
    return min(
        matches,
        key=lambda name: _dist(lat, lon, *_center_cache[name]),
    )


if __name__ == "__main__":
    tests = [
        (41.005, 39.721, "Trabzon"),
        (38.42, 27.14, "İzmir"),
        (37.87, 32.49, "Konya"),
        (41.02, 28.97, "İstanbul"),
        (39.75, 30.48, "Eskişehir"),
    ]
    for lat, lon, expected in tests:
        got = city_for_point(lat, lon)
        status = "OK " if got == expected else "FAIL"
        print(f"[{status}] ({lat}, {lon}) -> {got} (beklenen: {expected})")

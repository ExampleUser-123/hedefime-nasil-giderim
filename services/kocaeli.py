"""
Kocaeli toplu taşıma sağlayıcısı (GTFS'ten derlenmiş veri).
"""

from services.direct_transit import make_finder


find_kocaeli_route = make_finder(
    "kocaeli_transit.json.gz",
    source_label="Kocaeli Ulaşım",
    city_label="Kocaeli",
    hours_note_url="kocaeli.bel.tr/hatlar",
    ferry_label="Vapur",
)

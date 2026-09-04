"""
Konya toplu taşıma sağlayıcısı (belediye GTFS'ten derlenmiş veri).
"""

from services.direct_transit import make_finder


find_konya_route = make_finder(
    "konya_transit.json.gz",
    source_label="Konya Ulaşım",
    city_label="Konya",
    hours_note_url="konya.bel.tr",
)

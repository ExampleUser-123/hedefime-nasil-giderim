"""
Adana toplu taşıma sağlayıcısı (KentKart servisinden derlenmiş veri).
"""

from services.direct_transit import make_finder


find_adana_route = make_finder(
    "kentkart_adana.json.gz",
    source_label="Adana Ulaşım",
    city_label="Adana",
    hours_note_url="adana.bel.tr",
)

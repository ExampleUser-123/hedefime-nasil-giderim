"""
Antalya toplu taşıma sağlayıcısı (KentKart servisinden derlenmiş veri).
"""

from services.direct_transit import make_finder


find_antalya_route = make_finder(
    "kentkart_antalya.json.gz",
    source_label="Antalya Ulaşım",
    city_label="Antalya",
    hours_note_url="antalyaulasim.com.tr",
)

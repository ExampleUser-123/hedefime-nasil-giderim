"""
KentKart servisinden derlenen sehirler icin ortak toplu tasima saglayicilari.
Her sehir icin ayri dosya yerine tek modulde toplanir.
"""

from services.direct_transit import make_finder


find_gaziantep_route = make_finder(
    "kentkart_gaziantep.json.gz",
    source_label="Gaziantep Ulaşım",
    city_label="Gaziantep",
    hours_note_url="gaziantep.bel.tr",
)

find_mugla_route = make_finder(
    "kentkart_mugla.json.gz",
    source_label="Muğla Ulaşım",
    city_label="Muğla",
    hours_note_url="mugla.bel.tr",
)

find_sivas_route = make_finder(
    "kentkart_sivas.json.gz",
    source_label="Sivas Ulaşım",
    city_label="Sivas",
    hours_note_url="sivas.bel.tr",
)

find_duzce_route = make_finder(
    "kentkart_duzce.json.gz",
    source_label="Düzce Ulaşım",
    city_label="Düzce",
    hours_note_url="duzce.bel.tr",
)

find_erzurum_route = make_finder(
    "kentkart_erzurum.json.gz",
    source_label="Erzurum Ulaşım",
    city_label="Erzurum",
    hours_note_url="erzurum.bel.tr",
)

find_ordu_route = make_finder(
    "kentkart_ordu.json.gz",
    source_label="Ordu Ulaşım",
    city_label="Ordu",
    hours_note_url="ordu.bel.tr",
)

find_zonguldak_route = make_finder(
    "kentkart_zonguldak.json.gz",
    source_label="Zonguldak Ulaşım",
    city_label="Zonguldak",
    hours_note_url="zonguldak.bel.tr",
)

find_canakkale_route = make_finder(
    "kentkart_canakkale.json.gz",
    source_label="Çanakkale Ulaşım",
    city_label="Çanakkale",
    hours_note_url="canakkale.bel.tr",
)

find_samsun_route = make_finder(
    # kentkart_samsun.json.gz yanlislikla Kastamonu verisiydi; GTFS'ten
    # derlenen gercek Samsun verisi kullanilir (1632 durak).
    "samsun_transit.json.gz",
    source_label="Samsun Ulaşım",
    city_label="Samsun",
    hours_note_url="samsun.bel.tr",
)

find_edirne_route = make_finder(
    "kentkart_edirne.json.gz",
    source_label="Edirne Ulaşım",
    city_label="Edirne",
    hours_note_url="edirne.bel.tr",
)

"""
Genisletilmis sehir durak-hat verileri (data/<sehir>_transit.json.gz).
Bursa, Mersin, Hatay, Kayseri, Ankara, Manisa, Tekirdag, Balikesir.
Kaynaklar: belediye/ullasim API'leri ve OSM (detay: veri toplama notlari).
"""

from services.direct_transit import make_finder

find_ankara_route = make_finder(
    "ankara_transit.json.gz",
    source_label="EGO / Ankara Büyükşehir",
    city_label="Ankara",
    hours_note_url="ego.ankara.bel.tr",
)

find_bursa_route = make_finder(
    "bursa_transit.json.gz",
    source_label="Burulaş",
    city_label="Bursa",
    hours_note_url="burulas.com.tr",
)

find_mersin_route = make_finder(
    "mersin_transit.json.gz",
    source_label="Mersin Büyükşehir",
    city_label="Mersin",
    hours_note_url="ulasim.mersin.bel.tr",
)

find_hatay_route = make_finder(
    "hatay_transit.json.gz",
    source_label="Hatay Metropolitan",
    city_label="Hatay",
    hours_note_url="hatay.bel.tr",
)

find_kayseri_route = make_finder(
    "kayseri_transit.json.gz",
    source_label="Kayseri Ulaşım (Tramvay + Otobüs)",
    city_label="Kayseri",
    hours_note_url="kayseri.bel.tr",
)

find_manisa_route = make_finder(
    "manisa_transit.json.gz",
    source_label="Manisa Büyükşehir",
    city_label="Manisa",
    hours_note_url="manisa.bel.tr",
)

find_tekirdag_route = make_finder(
    "tekirdag_transit.json.gz",
    source_label="Tekirdağ Büyükşehir",
    city_label="Tekirdağ",
    hours_note_url="tekirdag.bel.tr",
)

find_balikesir_route = make_finder(
    "balikesir_transit.json.gz",
    source_label="Balıkesir Büyükşehir",
    city_label="Balıkesir",
    hours_note_url="balikesir.bel.tr",
)

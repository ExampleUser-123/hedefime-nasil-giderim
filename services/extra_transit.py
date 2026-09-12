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

find_kirklareli_route = make_finder(
    "kentkart_kirklareli.json.gz",
    source_label="39 Burda (Kırklareli)",
    city_label="Kırklareli",
    hours_note_url="kirklareli.bel.tr",
)

find_tokat_route = make_finder(
    "kentkart_tokat.json.gz",
    source_label="Tokat Belediye Otobüsleri",
    city_label="Tokat",
    hours_note_url="tokat.bel.tr",
)

find_malatya_route = make_finder(
    "malatya_transit.json.gz",
    source_label="Motaş (Malatya)",
    city_label="Malatya",
    hours_note_url="motas.com.tr",
)

find_isparta_route = make_finder(
    "isparta_transit.json.gz",
    source_label="Isparta Belediye Otobüsleri",
    city_label="Isparta",
    hours_note_url="isparta.bel.tr",
)

find_rize_route = make_finder(
    "rize_transit.json.gz",
    source_label="Rize Belediye Otobüsleri",
    city_label="Rize",
    hours_note_url="rize.bel.tr",
)

find_mardin_route = make_finder(
    "kentkart_mardin.json.gz",
    source_label="Mardin Belediye Otobüsleri",
    city_label="Mardin",
    hours_note_url="mardin.bel.tr",
)

find_nigde_route = make_finder(
    "kentkart_nigde.json.gz",
    source_label="Niğde Belediye Otobüsleri",
    city_label="Niğde",
    hours_note_url="nigde.bel.tr",
)

find_burdur_route = make_finder(
    "kentkart_burdur.json.gz",
    source_label="Burdur Belediye Otobüsleri",
    city_label="Burdur",
    hours_note_url="burdur.bel.tr",
)

find_osmaniye_route = make_finder(
    "kentkart_osmaniye.json.gz",
    source_label="Osmaniye Belediye Otobüsleri",
    city_label="Osmaniye",
    hours_note_url="osmaniye.bel.tr",
)

find_karabuk_route = make_finder(
    "kentkart_karabuk.json.gz",
    source_label="Karabük Belediye Otobüsleri",
    city_label="Karabük",
    hours_note_url="karabuk.bel.tr",
)

find_bartin_route = make_finder(
    "kentkart_bartin.json.gz",
    source_label="Bartın Belediye Otobüsleri",
    city_label="Bartın",
    hours_note_url="bartin.bel.tr",
)

find_trabzon_route = make_finder(
    "trabzon_transit.json.gz",
    source_label="TULAŞ / Trabzon Büyükşehir",
    city_label="Trabzon",
    hours_note_url="trabzon.bel.tr",
)

find_denizli_route = make_finder(
    "denizli_transit.json.gz",
    source_label="Denizli Ulaşım A.Ş. / Denizli Büyükşehir",
    city_label="Denizli",
    hours_note_url="ulasim.denizli.bel.tr",
)

find_karaman_route = make_finder(
    "karaman_transit.json.gz",
    source_label="Karaman Belediye Otobüsleri",
    city_label="Karaman",
    hours_note_url="karaman.bel.tr",
)

find_afyon_route = make_finder(
    "afyon_transit.json.gz",
    source_label="Afyonkarahisar Belediye Otobüsleri",
    city_label="Afyonkarahisar",
    hours_note_url="afyon.bel.tr/otobus",
)

# -*- coding: utf-8 -*-
"""SEO sehir sayfalari uretici: docs/ altina sehir-ulasim.html sayfalari yazar."""
import io, os

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

TPL = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<style>
  :root {{ --bg:#0b1220; --surface:#121a2b; --line:#22304d; --text:#e6edf7; --muted:#93a4c3; --accent:#2dd4bf; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.7; }}
  .wrap {{ max-width:760px; margin:0 auto; padding:28px 20px 60px; }}
  a.back {{ color:var(--accent); text-decoration:none; font-size:.95rem; }}
  h1 {{ font-size:1.7rem; margin:18px 0 12px; line-height:1.35; }}
  h2 {{ font-size:1.2rem; color:var(--accent); margin:28px 0 10px; }}
  p, li {{ color:var(--muted); font-size:1rem; }}
  p {{ margin:10px 0; }}
  ul {{ margin:10px 0 10px 22px; }}
  li {{ margin:6px 0; }}
  strong {{ color:var(--text); }}
  .cta {{ margin:30px 0; text-align:center; background:var(--surface); border:1px solid var(--line); border-radius:18px; padding:26px 18px; }}
  .cta a.btn {{ display:inline-block; background:linear-gradient(135deg,#2dd4bf,#14b8a6); color:#06281f; font-weight:700; padding:14px 34px; border-radius:999px; text-decoration:none; }}
  .cta p {{ font-size:.9rem; margin-top:10px; }}
  .links {{ margin-top:34px; border-top:1px solid var(--line); padding-top:18px; }}
  .links a {{ display:inline-block; color:var(--accent); text-decoration:none; font-size:.92rem; margin:4px 14px 4px 0; }}
  footer {{ margin-top:40px; font-size:.82rem; border-top:1px solid var(--line); padding-top:16px; }}
  footer a {{ color:var(--accent); text-decoration:none; }}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="index.html">&larr; Ana sayfa</a>
  <h1>{h1}</h1>
  {body}
  <div class="cta">
    <a class="btn" href="app/">🚀 {cta_text}</a>
    <p>Ucretsiz, uyeliksiz — tarayicinda hemen dene.</p>
  </div>
  <div class="links">
    <strong style="font-size:.9rem">Diger sehirler:</strong><br>
    {city_links}
  </div>
  <footer>
    <p><a href="index.html">Hedefime Nasil Giderim</a> · <a href="privacy.html">Gizlilik Politikasi</a></p>
  </footer>
</div>
</body>
</html>
"""

CITIES = {
    "istanbul": {
        "slug": "istanbul-otobus-metro-saatleri.html",
        "title": "Istanbul Otobus, Metro ve Vapur Saatleri (2026) — Nasil Gidilir?",
        "desc": "Istanbul'da IETT otobusu, metro, tramvay, Marmaray ve vapur saatleri, hat bilgileri ve rota planlama. Hedefime Nasil Giderim ile Istanbul'da en uygun yolu bulun.",
        "h1": "Istanbul'da Nasil Gidilir? Otobus, Metro, Tramvay, Marmaray ve Vapur Rehberi",
        "cta": "Istanbul rota ara",
        "body": """
<p>Istanbul, Turkiye'nin en buyuk sehir agina sahip ulasim aglarindan birine ev sahipligi yapiyor. Iki kitayi birbirine baglayan sehirde gunluk islerinizi iceride tutmak icin dogru rotayi bulmak cok onemli. Iste bilmeniz gerekenler:</p>
<h2>Istanbul'da ulasim turleri</h2>
<ul>
  <li><strong>IETT otobusleri:</strong> Sehrin her noktasina yayilmis yuzlerce hat. Yogun guzergahlarda <strong>metrobüs</strong> (34, 34A, 34Z...) hicbir sehir ici ulasimin rakipsiz hizini sunar.</li>
  <li><strong>Metro ve tramvay:</strong> M1'den M11'e metro hatlari, T1 Kabatas-Bagcilar tramvayi ve funikulerler ile tiksiz ulasim mumkun.</li>
  <li><strong>Marmaray:</strong> Avrupa ile Anadolu'yu deniz altindan baglayan hat, Bosphorus'u asmanin en hizli yollarindan.</li>
  <li><strong>Vapur ve feribot:</strong> Kadikoy-Karakoy, Besiktas-Uskudar gibi hatlarda trafikten tamamen bagimsiz, manzarali ulasim.</li>
  <li><strong>Minibus ve dolmus:</strong> Metro ve otobusun gitmedigi sokaklara inen tamamlayici ulasim.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Metro hatlari genellikle <strong>06:00-00:00</strong> arasi calisir. IETF otobusleri hat bazli degisir ama cogu hat sabah 06:00 ile gece 23:30 arasinda sefer duzenler. Vapurlarda tarife hattin yogunluguna gore degisir; Kadikoy-Karakoy hatti aksamlara kadar sefer verir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> uygulamasinda nereden ve nereye gideceginizi yazin; uygulama IETT, metro, Marmaray ve vapur verilerini birlestirip <strong>aktarmali rotalar</strong> dahil en mantikli secenegini onerir. Sure, yuruyus mesafesi ve tahmini ucret bilgisiyle karsilastirarak secim yaparsiniz.</p>
""",
    },
    "ankara": {
        "slug": "ankara-otobus-metro-saatleri.html",
        "title": "Ankara Otobus ve Metro Saatleri (2026) — EGO Rehberi",
        "desc": "Ankara'da EGO otobusu, Ankaray ve metro saatleri, hat bilgileri ve rota planlama. Ankara'da en uygun ulasim rotasini bulun.",
        "h1": "Ankara'da Nasil Gidilir? EGO, Ankaray ve Metro Rehberi",
        "cta": "Ankara rota ara",
        "body": """
<p>Baskent Ankara'da ulasimin belkemigi EGO otobusleri, Ankaray hafif rayli sistem ve metro hatlaridir. Sehrin genis cografyasinda en hizli yol genellikle rayli sistemlerdir.</p>
<h2>Ankara'da ulasim turleri</h2>
<ul>
  <li><strong>EGO otobusleri:</strong> Sehrin tamamini kapsayan genis hat agi. Cografya buyuk olmasina ragmen mahalle mahalle hizmet verir.</li>
  <li><strong>Ankaray (A1):</strong> Dikimevi - ASTI hattinda yuksek kapasiteli, hizli ulasim.</li>
  <li><strong>Metro (M1-M4):</strong> Kirazlidere, Koru, Ataturek Kultur Merkezi ve Tophatlar arasindaki hatlar sehrin ana omurgasidir.</li>
  <li><strong>Başkent dolmuslari:</strong> Metro ve EGO'nun gitmedigi baglantilari tamamlar.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Ankaray ve metro hatlari sabah ~06:00 ile gece ~23:30 arasinda calisir. EGO otobuslerinde saatler hattan hatta degisir; ana koridorlarda sefer sikligi yuksektir, mahalle hatlarinda sabah 06:30 ile aksam 23:00 arasindadir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Ankara icinde rota ararken uygulama EGO ve metro verilerini birlestirir, aktarma secenekleri ve yuruyus mesafeleriyle birlikte en dengeli rotayi onerir. Uluslararasi seyahatlerde ASTI otogarina nasil gideceginizi de ayni sekilde planlayabilirsiniz.</p>
""",
    },
    "izmir": {
        "slug": "izmir-otobus-metro-vapur-saatleri.html",
        "title": "Izmir Otobus, Metro ve Vapur Saatleri (2026) — ESHOT Rehberi",
        "desc": "Izmir'de ESHOT otobusu, Izmetro, tramvay ve vapur saatleri. Izmir'de nasil gidilir, en uygun rota nasil bulunur?",
        "h1": "Izmir'de Nasil Gidilir? ESHOT, Metro, Tramvay ve Vapur Rehberi",
        "cta": "Izmir rota ara",
        "body": """
<p>Ege'nin incisi Izmir'de ulasim ESHOT otobusleri, Izmetro, tramvay ve Kordon vapurlariyla dokumustur. Sahil seridinde yasayanlar icin vapur hem hizli hem keyifli bir secenektir.</p>
<h2>Izmir'de ulasim turleri</h2>
<ul>
  <li><strong>ESHOT otobusleri:</strong> Cigli'den Gaziemir'e, Buca'dan Narlidere'ye sehrin her noktasina hizmet.</li>
  <li><strong>Izmetro (M1):</strong> Evka 3 - Fahrettin Altay hatti sehrin ana omurgasidir; Bornova ve Karsiyaka hattinda hizli ulasim sunar.</li>
  <li><strong>Tramvay:</strong> Karsiyaka ve Alsancak hatlari sahil seridinde keyifli ulasim.</li>
  <li><strong>Vapur:</strong> Karsiyaka, Alsancak, Konak ve Bostanli iskeleleri arasinda kisa ve sik seferler.</li>
  <li><strong>Fahrettin Altay transfer:</strong> Metro ve tramvay bulusma noktasi, sehrin guneyine inen hatlarin merkezi.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Izmetro sabah ~06:00 ile gece ~00:00 arasinda calisir. ESHOT hatlarinin buyuk bolumu 06:00-23:30 arasinda sefer duzenler. Vapurlarda siklik hattan hatta degisir ama ana iskeleler arasi seferler yogundur.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> uygulamasi Izmir'de ESHOT, metro, tramvay ve vapur verilerini harmanlar. Ornegin Buca'dan Karsiyaka'ya giderken otobus+metro+vapur kombinasyonunu sure ve maliyeti ile karsilastirarak gorebilirsiniz.</p>
""",
    },
    "bursa": {
        "slug": "bursa-otobus-metro-saatleri.html",
        "title": "Bursa Otobus ve Metro Saatleri (2026) — Bursaray Rehberi",
        "desc": "Bursa'da Bursaray, otobus ve tramvay saatleri, hat bilgileri. Bursa'da nasil gidilir, en uygun rota nasil bulunur?",
        "h1": "Bursa'da Nasil Gidilir? Bursaray, Otobus ve Tramvay Rehberi",
        "cta": "Bursa rota ara",
        "body": """
<p>Bursa'da ulasimin ana omurgasi <strong>Bursaray</strong> hattidir. Sehrin dogusundan batisina uzanan hat, yogun guzergahlarda otobusun cok uzerinde bir hiz sunar.</p>
<h2>Bursa'da ulasim turleri</h2>
<ul>
  <li><strong>Bursaray:</strong> Arabayatagi - Emek / Kestel hattinda nilufer, Osman Gazi ve Uludag universitesi koridorlarini baglar.</li>
  <li><strong>Otobusler:</strong> Bursa Uludag Universitesi, Nilufer ve Yildirim semtlerini birbirine baglayan genis hat agi.</li>
  <li><strong>Tramvay (T1 ve T3):</strong> Kent konseyi, Cumhuriyet Caddesi ve Zafer Plaza hatti ile tarihi merkezde rahat ulasim.</li>
  <li><strong>Teleferik:</strong> Uludag'a cikarken hem ulasim hem keyif.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Bursaray sabah ~06:00 ile gece ~23:30 arasinda calisir. Otobus hatlari 06:00-23:00 arasinda sefer verir. Yogun hatlarda (Arabayatagi, Emek) sefer araliklari kisadir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Bursa icinde rota ararken uygulama Bursaray ve otobus hatlarini birlestirerek en hizli secenegini onerir. Orhangazi, Inegol gibi ilcelere giderken de sure ve tahmini maliyeti gorebilirsiniz.</p>
""",
    },
    "antalya": {
        "slug": "antalya-otobus-tramvay-saatleri.html",
        "title": "Antalya Otobus ve Tramvay Saatleri (2026) — Antalya Ulasim Rehberi",
        "desc": "Antalya'da otobus hatlari, nostalgia tramvayi ve fazilet hatti. Antalya'da nasil gidilir, rota nasil planlanir?",
        "h1": "Antalya'da Nasil Gidilir? Otobus ve Tramvay Rehberi",
        "cta": "Antalya rota ara",
        "body": """
<p>Turizmin baskenti Antalya'da ulasim genis otobus agi ve iki ozel tramvay hattiyla saglanir. Yaz aylarinda turist yogunlugu nedeniyle hatlar normalden daha kalabaliktir.</p>
<h2>Antalya'da ulasim turleri</h2>
<ul>
  <li><strong>Otobus hatlari:</strong> Lara'dan Kemer'e, Kepez'den Aksu'ya uzanan yuzlerce hat. Antalya Kart ile ucretler uyumlu.</li>
  <li><strong>Nostalgia Tramvay (T1):</strong> Ataturk Caddesi - Iskele hattinda tarihi merkez ulasimi.</li>
  <li><strong>Fazilet Hatti (T1A):</strong> Alanya'da Antalya, Meydan ve Guzellik Park iskeleleri arasi.</li>
  <li><strong>Yeni Antalya tramvay hatti:</strong> Sehrin guneyindeki yogun guzergahlarda hizli ulasim.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Antalya'da otobusler genellikle <strong>06:00-00:00</strong> arasinda calisir; yaz aylarinda plaj hatlarinda seferler gecen saatlere kadar uzayabilir. Tramvay 06:30-23:30 arasindadir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Antalya'da havalimanindan merkeze, Kaleici'den Lara'ya nasil gideceginizi tek aramada planlayabilirsiniz. Uygulama sure ve tahmini ucreti gostererek en uygun secenegi onerir.</p>
""",
    },
    "konya": {
        "slug": "konya-otobus-tramvay-saatleri.html",
        "title": "Konya Otobus ve Tramvay Saatleri (2026) — Konya Ulasim Rehberi",
        "desc": "Konya'da otobus hatlari ve tramvay saatleri. Konya'da nasil gidilir, rota nasil planlanir?",
        "h1": "Konya'da Nasil Gidilir? Otobus ve Tramvay Rehberi",
        "cta": "Konya rota ara",
        "body": """
<p>Mevlana'nin sehri Konya'da ulasim genis otobus agi ve merkez tramvay hattiyle saglanir. Sehir flat oldugu icin hem otobus hem bisiklet ulasimi rahattir.</p>
<h2>Konya'da ulasim turleri</h2>
<ul>
  <li><strong>Otobusler:</strong> Merkez ilceleri (Selcuklu, Meram, Karatay) ve beldeleri baglayan genis hat agi.</li>
  <li><strong>Tramvay:</strong> Alatin - Ankara Caddesi hatti Mevlana Muzesi ve Alattin Tepesi gibi merkez noktalari baglar.</li>
  <li><strong>Konya Kart:</strong> Otobus ve tramvayda ortak kullanilan indirim karti.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Konya'da otobusler genellikle <strong>06:00-23:30</strong> arasinda calisir. Tramvay benzer saatlerde sefer duzenler. Yogun hatlarda (Ankara Caddesi hatti) sefer araliklari kisadir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Konya'da otogardan Mevlana Muzesi'ne, Selcuklu'dan Meram'a nasil gideceginizi sure ve tahmini maliyeti gore planlayabilirsiniz.</p>
""",
    },
    "kocaeli": {
        "slug": "izmit-kocaeli-otobus-saatleri.html",
        "title": "Izmit / Kocaeli Otobus Saatleri (2026) — Kocaeli Ulasim Rehberi",
        "desc": "Kocaeli ve Izmit'te otobus hatlari, duraklar ve sefer saatleri. Kocaeli'de nasil gidilir, rota nasil planlanir?",
        "h1": "Izmit / Kocaeli'de Nasil Gidilir? Otobus Rehberi",
        "cta": "Kocaeli rota ara",
        "body": """
<p>Kocaeli, sanayisiyle bilinen hareketli bir sehir. Izmit merkez ve cevre ilcelerde (Gebze, Darica, Golcuk, Kandira) ulasim agirlikli olarak otobus hatlariyla saglanir.</p>
<h2>Kocaeli'de ulasim turleri</h2>
<ul>
  <li><strong>Kent otobusleri:</strong> Izmit merkez ve ilcelerde yuzlerce hat. 600'den fazla durak tespit edilmistir.</li>
  <li><strong>Kocaeli Kart:</strong> Otobuslerde ortak kullanilan indirim karti.</li>
  <li><strong>Ilceler arasi hatlar:</strong> Gebze - Izmit - Golcuk koridorunda sik seferler.</li>
  <li><strong>Istanbul baglantisi:</strong> Gebze'den Istanbul'a Marmaray ve otobus baglantilari mevcut.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Kocaeli'de otobusler genellikle <strong>06:00-23:00</strong> arasinda calisir. Sanayi bolgesi hatlarinda vardiya saatlerine bagli ek seferler duzenlenir. Hafta sonu hat sikligi bazi hatlarda azalir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> Kocaeli'de GTFS verisiyle calisir; Uyacik, Basiskale, Kosekoy gibi mahalle ve ilcelere rota ararken gercek durak bilgisi kullanir. Izmit icinde veya ilceler arasi rota ararken sure ve tahmini maliyeti gosterir.</p>
""",
    },
    "adana": {
        "slug": "adana-otobus-metro-saatleri.html",
        "title": "Adana Otobus ve Metro Saatleri (2026) — Adana Ulasim Rehberi",
        "desc": "Adana'da otobus hatlari ve metro saatleri. Adana'da nasil gidilir, rota nasil planlanir?",
        "h1": "Adana'da Nasil Gidilir? Otobus ve Metro Rehberi",
        "cta": "Adana rota ara",
        "body": """
<p>Cukurova'nin kalbi Adana'da ulasim genis otobus agi ve metro hattiyla saglanir. Seyhan nehri sehrin iki yakasini koparir, kopruler ulasimin merkezidir.</p>
<h2>Adana'da ulasim turleri</h2>
<ul>
  <li><strong>Otobusler:</strong> Seyhan, Ceyhan, Yuregir ve Cukurova ilcelerini baglayan genis hat agi.</li>
  <li><strong>Adana Metro:</strong> Hastane - Turk Kurumu Koridoru hatti sehrin kuzey-guney omurgasidir.</li>
  <li><strong>Adana Kart:</strong> Otobus ve metroya ortak gecis karti.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Adana'da otobusler genellikle <strong>06:00-23:30</strong> arasinda calisir. Metro 06:00-23:00 arasinda sefer duzenler. Yaz aylarinda oglen sikligi biraz azalabilir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Adana'da otogardan merkez pazaryerine, Seyhan'dan Cukurova Universitesi'ne nasil gideceginizi planlayabilir, sure ve tahmini ucreti gorebilirsiniz.</p>
""",
    },
    "eskisehir": {
        "slug": "eskisehir-otobus-tramvay-saatleri.html",
        "title": "Eskisehir Otobus ve Tramvay Saatleri (2026) — Eskisehir Ulasim Rehberi",
        "desc": "Eskisehir'de otobus hatlari ve EsTram saatleri. Eskisehir'de nasil gidilir, rota nasil planlanir?",
        "h1": "Eskisehir'de Nasil Gidilir? Otobus ve EsTram Rehberi",
        "cta": "Eskisehir rota ara",
        "body": """
<p>Ogrenci sehrinin kalbi Eskisehir'de ulasimin yildizi <strong>EsTram</strong> tramvay hattidir. Universite cografyasi oldugu icin hatlar gecen saatlere kadar yogundur.</p>
<h2>Eskisehir'de ulasim turleri</h2>
<ul>
  <li><strong>EsTram:</strong> Ogrenci sitesi - Emekos - OPET hatti, sehrin iki ucunu birlestirir. Anadolu Universitesi ve Osmangazi Universitesi koridorlarinda can kurtaricidir.</li>
  <li><strong>Otobusler:</strong> Tepebasi ve Odunpazari ilcelerini kapsayan genis hat agi.</li>
  <li><strong>EsKart:</strong> Tramvay ve otobuslerde ortak gecis.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>EsTram sabah ~06:00 ile gece ~00:30 arasinda calisir — universite sehrinin gec yasam uyumuna paralel. Otobusler 06:15-23:45 arasinda sefer duzenler.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Eskisehir'de universiteden cikista otogara, Odunpazari'dan Tepebasi'ye nasil gideceginizi sure ve tahmini ucreti ile planlayabilirsiniz.</p>
""",
    },
    "gaziantep": {
        "slug": "gaziantep-otobus-saatleri.html",
        "title": "Gaziantep Otobus Saatleri (2026) — Gaziantep Ulasim Rehberi",
        "desc": "Gaziantep'te otobus hatlari ve sefer saatleri. Gaziantep'te nasil gidilir, rota nasil planlanir?",
        "h1": "Gaziantep'te Nasil Gidilir? Otobus Rehberi",
        "cta": "Gaziantep rota ara",
        "body": """
<p>Gaziantep'te ulasim genis otobus agiyla saglanir. Sehir buyuklugune ragmen hat duzeni mantikli; merkez ilceler (Sahinbey, Sehitkamil) arasi baglanti gucludur.</p>
<h2>Gaziantep'te ulasim turleri</h2>
<ul>
  <li><strong>Otobusler:</strong> Merkez ve ilceleri baglayan yuzlerce hat. Gaziantep Kart ile gecis saglanir.</li>
  <li><strong>Ilceler arasi hatlar:</strong> Nizip, Islahiye, Kilis yonu hatlari merkez otogar uzerinden isler.</li>
  <li><strong>Otogar baglantisi:</strong> Sehirler arasi otogardan merkeze duzenli ulasim.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Gaziantep'te otobusler genellikle <strong>06:00-23:30</strong> arasinda calisir. Yogun koridorlarda (Gar - Sahinbey hatti gibi) sefer araliklari kisadir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Gaziantep'te otogardan bakircilar carsisina, Sahinbey'den Sehitkamil'e nasil gideceginizi planlayabilir, sure ve tahmini ucreti gorebilirsiniz.</p>
""",
    },
    "mersin": {
        "slug": "mersin-otobus-saatleri.html",
        "title": "Mersin Otobus Saatleri (2026) — Mersin Ulasim Rehberi",
        "desc": "Mersin'de otobus hatlari ve sefer saatleri. Mersin'de nasil gidilir, rota nasil planlanir?",
        "h1": "Mersin'de Nasil Gidilir? Otobus Rehberi",
        "cta": "Mersin rota ara",
        "body": """
<p>Mersin'de ulasim EGO'ya benzer duzende toplu otobus hatlariyla saglanir. Sahil seridinde uzanan sehirde hatlar genellikle sahil yolunu ve merkezi baglar.</p>
<h2>Mersin'de ulasim turleri</h2>
<ul>
  <li><strong>Otobusler:</strong> Yenisehir, Akdeniz, Toroslar ve Mezitli ilcelerini baglayan hatlar.</li>
  <li><strong>Mersin Kart:</strong> Otobuslerde kullanilan gecis karti.</li>
  <li><strong>Otogar baglantisi:</strong> Sehirler arasi otogardan merkez ve universiteye ulasim.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Mersin'de otobusler genellikle <strong>06:00-23:00</strong> arasinda calisir. Universite hattinda ogrenci yogunluguna gore ek seferler duzenlenir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Mersin'de otogardan Universite'ye, Mezitli'den merkeze nasil gideceginizi planlayabilirsiniz. Uygulama sure, yuruyus ve tahmini ucreti bir arada gosterir.</p>
""",
    },
    "samsun": {
        "slug": "samsun-otobus-tramvay-saatleri.html",
        "title": "Samsun Otobus ve Tramvay Saatleri (2026) — Samsun Ulasim Rehberi",
        "desc": "Samsun'da otobus hatlari ve tramvay saatleri. Samsun'da nasil gidilir, rota nasil planlanir?",
        "h1": "Samsun'da Nasil Gidilir? Otobus ve Tramvay Rehberi",
        "cta": "Samsun rota ara",
        "body": """
<p>Karadeniz'in en buyuk sehri Samsun'da ulasim otobusler ve sahil tramvay hattiyla saglanir. Atakum - Atakent - Cumhuriyet Meydani hatti sehrin ana omurgasidir.</p>
<h2>Samsun'da ulasim turleri</h2>
<ul>
  <li><strong>Otobusler:</strong> Ilkadim, Atakum, Canik ilcelerini baglayan genis hat agi.</li>
  <li><strong>Tramvay:</strong> Sahil seridinde Atakum'dan merkeze hizli ve rahat ulasim.</li>
  <li><strong>Samsun Kart:</strong> Otobus ve tramvayda ortak gecis.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Samsun'da otobusler genellikle <strong>06:00-23:30</strong> arasinda calisir. Tramvay benzer saatlerde sefer duzenler; universite hattinda ders saatlarine paralel siklasir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Samsun'da Atakum'dan Cumhuriyet Meydani'na, otogardan universiteye nasil gideceginizi planlayabilir, sure ve tahmini ucreti gorebilirsiniz.</p>
""",
    },
    "kayseri": {
        "slug": "kayseri-otobus-tramvay-saatleri.html",
        "title": "Kayseri Otobus ve Tramvay Saatleri (2026) — Kayseray Rehberi",
        "desc": "Kayseri'de otobus hatlari ve Kayseray tramvay saatleri. Kayseri'de nasil gidilir, rota nasil planlanir?",
        "h1": "Kayseri'de Nasil Gidilir? Otobus ve Kayseray Rehberi",
        "cta": "Kayseri rota ara",
        "body": """
<p>Kayseri'de ulasimin simgesi <strong>Kayseray</strong> tramvay hattidir. Sehirde otobus agi ve tramvay birbirini tamamlayan bir duzende calisir.</p>
<h2>Kayseri'de ulasim turleri</h2>
<ul>
  <li><strong>Kayseray:</strong> Cumhuriyet Meydani, Erkilet ve Talas yonu hatlari. Universite hattinda yogunluk yuksektir.</li>
  <li><strong>Otobusler:</strong> Melikgazi, Kocasinan ve Talas ilcelerini baglayan hatlar.</li>
  <li><strong>Kayseri Kart:</strong> Tramvay ve otobuslerde ortak gecis karti.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Kayseri'de tramvay sabah ~06:00 ile gece ~00:00 arasinda calisir. Otobusler 06:00-23:30 arasinda sefer duzenler.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Kayseri'de otogardan Erciyes Universitesi'ne, Talas'tan merkeze nasil gideceginizi planlayabilirsiniz.</p>
""",
    },
    "trabzon": {
        "slug": "trabzon-otobus-saatleri.html",
        "title": "Trabzon Otobus Saatleri (2026) — Trabzon Ulasim Rehberi",
        "desc": "Trabzon'da otobus hatlari ve dolmus guzergahlari. Trabzon'da nasil gidilir, rota nasil planlanir?",
        "h1": "Trabzon'da Nasil Gidilir? Otobus Rehberi",
        "cta": "Trabzon rota ara",
        "body": """
<p>Karadeniz'in incisi Trabzon'da ulasim otobus hatlari ve yogun dolmus agiyla saglanir. Sahil seridinde uzanan sehirde hatlar Ortahisar merkez ile batigazi arasinda isler.</p>
<h2>Trabzon'da ulasim turleri</h2>
<ul>
  <li><strong>Otobusler:</strong> Merkez Ortahisar, Akcaabat ve Arsin yonu hatlar.</li>
  <li><strong>Trabzon Kart:</strong> Otobuslerde kullanilan gecis karti.</li>
  <li><strong>Havalimani baglantisi:</strong> Trabzon Havalimani'ndan merkeze duzenli otobus ve dolmus hatlari.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Trabzon'da otobusler genellikle <strong>06:00-23:00</strong> arasinda calisir. Dolmuslar sabah erken saatlerden gece yarilarina kadar isler.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Trabzon'da havalimanindan Meydan Park'a, Akcaabat'tan merkeze nasil gideceginizi sure ve tahmini ucreti ile planlayabilirsiniz.</p>
""",
    },
    "denizli": {
        "slug": "denizli-otobus-saatleri.html",
        "title": "Denizli Otobus Saatleri (2026) — Denizli Ulasim Rehberi",
        "desc": "Denizli'de otobus hatlari ve sefer saatleri. Denizli'de nasil gidilir, rota nasil planlanir?",
        "h1": "Denizli'de Nasil Gidilir? Otobus Rehberi",
        "cta": "Denizli rota ara",
        "body": """
<p>Denizli'de ulasim genis otobus agiyla saglanir. Merkez ilceler (Pamukkale, Merkezefendi) arasi hatlar sik; horoz tipi sehir yapisinda rota bulmak kolaydir.</p>
<h2>Denizli'de ulasim turleri</h2>
<ul>
  <li><strong>Otobusler:</strong> Merkezefendi ve Pamukkale ilcelerini baglayan hatlar. Denizli Kart ile gecis.</li>
  <li><strong>Pamukkale baglantisi:</strong> Dunya mirasi Pamukkale travertenlerine merkezden duzenli otobus.</li>
  <li><strong>Otogar baglantisi:</strong> Sehirler arasi otogardan merkeze ulasim kolaydir.</li>
</ul>
<h2>Saatler ne zaman?</h2>
<p>Denizli'de otobusler genellikle <strong>06:00-23:30</strong> arasinda calisir. Universite hattinda ogrenci saatlarine paralel siklasir.</p>
<h2>Akilli rota planlama</h2>
<p><strong>Hedefime Nasil Giderim</strong> ile Denizli'de otogardan merkeze, merkezden Pamukkale'ye nasil gideceginizi planlayabilir, sure ve tahmini ucreti gorebilirsiniz.</p>
""",
    },
}

def render_city(slug_key, info, all_keys):
    links = []
    for k in all_keys:
        if k != slug_key:
            links.append('<a href="{0}">{1}</a>'.format(CITIES[k]["slug"], k.capitalize()))
    return TPL.format(
        title=info["title"],
        desc=info["desc"],
        h1=info["h1"],
        body=info["body"],
        cta_text=info["cta"],
        city_links="\n    ".join(links),
    )

def main():
    keys = list(CITIES.keys())
    urls = []
    for key in keys:
        info = CITIES[key]
        path = os.path.join(DOCS, info["slug"])
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(render_city(key, info, keys))
        urls.append("https://exampleuser-123.github.io/hedefime-nasil-giderim/" + info["slug"])
        print("yazildi:", info["slug"])

    # sitemap
    static = ["", "privacy.html", "hakkinda.html", "app/"]
    items = []
    today = "2026-09-11"
    for s in static:
        items.append("https://exampleuser-123.github.io/hedefime-nasil-giderim/" + s)
    items.extend(urls)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in items:
        sm.append("  <url><loc>{0}</loc><lastmod>{1}</lastmod></url>".format(u.rstrip("/") if u.endswith("/") else u, today))
    sm.append("</urlset>")
    with io.open(os.path.join(DOCS, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(sm))
    print("sitemap.xml yazildi,", len(items), "url")

if __name__ == "__main__":
    main()

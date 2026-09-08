# Play Store Hazırlık Dosyası — Hedefime Nasıl Giderim

Bu dosya, Play Console'da doldurulacak HER ŞEYIN hazır cevaplarını içerir.
Kopyala-yapıştır yapabilirsin.

---

## 1. Uygulama bilgileri

| Alan | Değer |
|---|---|
| Uygulama adı (max 30 kr) | Hedefime Nasıl Giderim |
| Kısa açıklama (max 80 kr) | Türkiye'de toplu taşıma, otobüs saati ve yol maliyeti ile rota planlayın. |
| Kategori | Seyahat ve Yerel Rehberler |
| Etiketler | rota planlama, toplu taşıma, yol maliyeti, duraklar |
| E-posta | hedefimenasilgiderim@gmail.com |
| Gizlilik politikası URL | https://hedefime-nasil-giderim-api.onrender.com/privacy |

## 2. Uzun açıklama (max 4000 kr)

Hedefime Nasıl Giderim ile Türkiye'nin her yerinde yolculuğunu planla!

🚌 TOPLU TAŞIMA ROTALARI
38 ilde şehir içi toplu taşıma: İstanbul, Ankara, İzmir, Bursa, Antalya ve daha fazlası. Otobüs, metro, tramvay, vapur ve minübüs hatlarıyla nereden nereye gideceğini dakikalarıyla öğren.

⏱ YAKLAŞAN SEFERLER
"Şimdi mi kalkar?" sorusuna cevap: seçtiğin hattın durağından bir sonraki sefer saatini gör. GTFS verisi olan illerde gerçek sefer saatleri, diğer illerde tahmini sefer aralığı.

🚏 YAKIN DURAKLAR
Konumunu al, en yakın durakları mesafesiyle listele. Durağa dokun, geçen hatları ve bir sonraki seferleri gör.

💰 MALİYET HESABI
Kişi sayısına göre toplam maliyet: biniş ücreti, yakıt, motorin hesabı. Kaç kişi gidiyorsan kişi başı ve toplam masrafı gör.

🚗 ARAÇ SEÇİMİ
538 araç modeli: benzinli, dizel, LPG ve elektrikli otomobiller (Tesla, Togg, BYD dahil) + motosikletler. "Arabamı hatırla" ile bir kez seç, her seferinde aynı gelsin.

✈️ ŞEHİRLER ARASI
Uçak, otobüs, tren ve özel araçla şehirlerarası seyahat maliyetini ve süresini karşılaştır.

🤖 AI ASİSTAN
"Yarın 4 kişi İzmit'ten İzmir'e en ucuz nasıl gideriz?" diye sor, asistan rota seçeneklerini hazırlasın.

📊 EKSTRALAR
• Rota sıralama: en az yürüme, en az aktarma
• Yürüyüş toleransı seçimi (300 m - 2 km)
• Sesli rehberlik
• Yolculuk raporu ve paylaşım
• Ev ve iş konumu kısayolları
• Hava durumu bilgisi

Dönüştürülebilir, ücretsiz. Kayıt olmadan rota arayabilirsin.

---

## 3. Grafik varlıklar (SEN YAPACAKSIN)

**Uygulama simgesi:** 512×512 PNG — zaten var (`frontend/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png`'den ölçeklenebilir; gerekirse söyle büyütürüm).

**Öne çıkan görsel:** 1024×500 PNG/JPG — zorunlu. İstersen bunu tasarlarım (create_image ile) — söylemen yeterli.

**Telefon ekran görüntüleri:** min 2, max 8; min kenar 320 px, max 3840 px; PNG/JPG. Telefondan şunları al:
1. Ana ekran (Nereden/Nereye dolu, rota çipleri görünür)
2. Sonuç ekranı (seçenek kartları, "şimdi kalkar mı" rozeti)
3. Yakın duraklar ekranı (Duraklar sekmesi)
4. Harita görünümü
5. AI asistan sohbeti
6. Detay kartı (sefer saatleri + maliyet)

**Sadece telefon desteği:** Bu sürüm telefon içindir; 7" / 10" tablet görseli istenirse "tablet desteği yok" demek serbest.

## 4. İçerik derecelendirme anketi cevapları (hepsi HAYIR)

- Uygulamanın adı/reklamında yetişkin temalı içerik var mı? → Hayır
- Şiddet, korku, cinsellik, uyuşturucu, dil/küfür, kumar, sözde tıbbi bilgi → hepsi Hayır
- Kullanıcılar birbirine içerik paylaşabiliyor mu? → Hayır (sohbet AI'a karşı, insanlara görünmez)
- Kişisel bilgi topluyor mu (kendi beyanı) → Evet: e-posta + kullanıcı adı (isteğe bağlı hesap) ve konum (işlevsel). Paylaşım yok, silme talebi e-postayla.
- Uygulamada online alışveriş/dijital mal var mı? → Hayır (reklam var, satış yok)
- Uygulama 13 yaş altına hitap ediyor mu? → Hayır

Beklenen sonuç: **Herkes (PEGI 3 / ESRB E)**.

## 5. Veri güvenliği formu cevapları

Veri türü → topluyor musunuz / zorunlu mu / amaç / silme talebi:

| Veri | Toplanıyor mu | Amaç | Silme |
|---|---|---|---|
| E-posta (Google girişi, isteğe bağlı) | Evet | Hesap yönetimi, kötüye kullanım önleme | Evet (e-posta talebi) |
| Kullanıcı adı / profil fotoğrafı (Google) | Evet | Uygulama içi profil gösterimi | Evet |
| Konum (yaklaşık/kesin, işlevsel) | Evet | Yakın durak gösterimi, rota başlangıcı | Saklanmaz, kalıcı kayıt yok |
| Uygulama etkileşimi (arama geçmişi) | Evet (cihazda; hesaplıysa favori+sohbet sunucuda) | Uygulama işlevselliği | Evet |
| Cihaz/kimlikler (AdMob reklam kimliği) | Evet (Google işler) | Reklam | Google'ın reklam ayarları |

Bilgilerin şifreli olarak iletilmesi: Evet (HTTPS)
Veri silme talebi mekanizması: Evet (e-posta + uygulama içi favori/sohbet silme)

## 6. Adım adım Play Console yolu (senin tarafın)

1. https://play.google.com/console → 25 $'lık tek seferlik kayıt ücreti → kimlik doğrulama (18 yaş altıysan aile üyesi hesabıyla — daha önce konuştuğumuz gibi ebeveyn hesabı).
2. "Uygulama oluştur" → adı gir → "Uygulama" seç → ücretsiz.
3. Sol menüden sırayla:
   - **Mağaza varlığı → Ana mağaza kaydı**: 2. bölümdeki metinleri + görselleri yükle
   - **Politika → Uygulama içeriği**: Gizlilik politikası URL'si (yukarıda), reklam var → Evet, içerik derecelendirme anketi (4. bölüm cevapları), hedef kitle: 13+ (çocuklara yönelik DEĞİL işaretle), veri güvenliği (5. bölüm), hükümet uygulaması: Hayır
   - **Sürüm → Üretim**: `HedefimeNasilGiderim-release.aab` yükle (masaüstünde)
   - Sürüm notu (ilk sürüm): "İlk sürüm."
4. **Ülke/bölge**: Türkiye (istersen hepsi).
5. Gönder → inceleme genelde 1-7 gün.

## 7. Yayından ÖNCE unutma (kod tarafında yapacağım/gerektiğinde)

- [ ] Google OAuth consent screen'i "Test"ten "Production"a çek (test kullanıcı sınırı kalkar). Google Cloud Console → OAuth consent screen → Publish.
- [ ] AdMob: uygulama Play'de yayınlandıktan sonra Play Console'daki paket adıyla eşleştiğini kontrol et (com.hedefime.giderim — zaten eşleşiyor).
- [ ] Keystore'un yedeğini al (KEYSTORE-BILGI.txt yanına; kaybedersen güncelleme YAPAMAZSIN).

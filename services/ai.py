import json
import os
import re
import time

from google import genai
from google.genai import types

from services.geocoding import search_place as _search_place
from services.routing import calculate_route
from services.fuel import calculate_fuel_cost
from services.vehicles import get_vehicle
from services.public_transport import find_transit_routes
from services.location import find_province
from services.weather import get_weather


MODEL_NAME = "gemini-3.6-flash"

SYSTEM_INSTRUCTION = """
Sen "Hedefime Nasıl Giderim" uygulamasının AI asistanısın.
Kullanıcılar Türkiye içinde seyahat planlaması konusunda sana soru sorar.

Görevlerin:
- Kullanıcı bir rota/seyahat sorusu sorduğunda elindeki fonksiyonları
  (araçla rota, yakıt maliyeti, toplu taşıma, yer arama) kullanarak
  gerçek veriye dayalı cevap ver.
- Uygulamanın kapsamı dışındaki bilgiler için (örneğin başka şehirlerin
  toplu taşıma hatları, güncel yol durumu, ulaşım fiyatları, ilginç
  yerler) web_ara fonksiyonuyla internette arama yap.
- Asla bilgi uydurma. Emin olmadığın bir şey varsa araştır veya sor.

Kurallar:
- Her zaman Türkçe cevap ver.
- Cevaplarını kısa, net ve düzenli tut. Gerektiğinde madde işaretleri kullan.
- Rota verirken süre, mesafe, maliyet gibi sayıları mutlaka belirt.
- Kullanıcı başlangıç veya hedef noktası belirtmemişse, tahmin yürütmek
  yerine sor.
- Saat formatı HH:MM, tarih formatı DD-MM-YYYY'dir. "yarın", "bugün"
  gibi ifadeler geçerse kesin tarih/saat bilmiyorsan kullanıcıya sor.

Türkiye'ye özgü ulaşım bilinci:
- Dolmuş ve minibüs hatları Türkiye'de çok yaygındır. Kullanıcı bir
  güzergah sorarsa ve uygulama verisinde toplu taşıma rotası yoksa bile
  dolmuş/minibüs alternatifini mutlaka değerlendir: hangi dolmuş hattı
  (ör. İzmit-gebze dolmuş hattı, mahalle dolmuşları), nereden binilir,
  tahmini ücret ne kadardır. Emin değilsen web_ara ile araştır.
- Şehirler arası yolculuklarda otobüs firmalarını (Kamil Koç, Metro,
  Varan, Pamukkale, Nilüfer vb.) ve ücret aralıklarını da araştırarak
  karşılaştır; öğrenci indirimi sorulursa hatırlat.
- Metro/otobüs yoksa "ulaşım yoktur" demeden önce dolmuş, minibüs,
  belediye otobüsü ve bölgesel tren alternatiflerini kontrol et.

Rota detayı verirken (adım adım anlatım):
- Biniş durağı, hat adı, iniş/aktarma durağı ve varsa kalkış saatlerini
  SADECE fonksiyon sonuçlarındaki gerçek veriden al; listede olmayan
  durak/saat/hat adı asla yazma.
- Bir bilgi fonksiyonda yoksa "bu bilgi mevcut ulaşım verisinde
  bulunamadı" de, tahmin yürütme.
"""


def _load_api_key():
    """
    API anahtarını önce ortam değişkeninden,
    sonra .env dosyasından okur.
    """
    key = os.environ.get("GEMINI_API_KEY")

    if key:
        return key

    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".env"
    )

    if not os.path.exists(env_path):
        return None

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            name, value = line.split("=", 1)
            name = name.strip()
            value = value.strip().strip('"').strip("'")

            if name == "GEMINI_API_KEY" and value:
                return value

    return None


client = None


def _get_client():
    global client

    if client is None:
        api_key = _load_api_key()

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY bulunamadı. Lütfen .env dosyasına ekleyin."
            )

        client = genai.Client(api_key=api_key)

    return client


# =========================================================
# AI'NIN KULLANACAĞI FONKSİYONLAR
# =========================================================

def yer_ara(query: str) -> dict:
    """Türkiye içinde bir yer arar ve koordinatlarını döndürür.

    Args:
        query: Aranacak yer adı (örn. "Kadıköy Rıhtım").

    Returns:
        Yer bilgisi (display_name, lat, lon) veya hata.
    """
    place = _search_place(query)

    if place is None:
        return {"error": f"Yer bulunamadı: {query}"}

    return place


def arabayla_rota(
    start: str,
    end: str,
    vehicle_id: str = "toyota_corolla",
    people: int = 1
) -> dict:
    """İki nokta arasındaki araç rotasını ve yakıt maliyetini hesaplar.

    Args:
        start: Başlangıç noktası (örn. "Kadıköy, İstanbul").
        end: Hedef noktası (örn. "Taksim, İstanbul").
        vehicle_id: Araç kimliği. Geçerli değerler:
            toyota_corolla (Benzin, 7.0 L/100km),
            fiat_egea (Motorin, 5.0 L/100km),
            renault_clio (Benzin, 6.0 L/100km).
        people: Araçtaki kişi sayısı (maliyet kişi başına bölünür).

    Returns:
        Mesafe, süre ve yakıt maliyeti bilgileri.
    """
    start_place = _search_place(start)

    if start_place is None:
        return {"error": f"Başlangıç noktası bulunamadı: {start}"}

    end_place = _search_place(end)

    if end_place is None:
        return {"error": f"Hedef noktası bulunamadı: {end}"}

    route_result = calculate_route(
        start_place["lat"],
        start_place["lon"],
        end_place["lat"],
        end_place["lon"]
    )

    if route_result is None:
        return {"error": "Rota bulunamadı."}

    vehicle = get_vehicle(vehicle_id)

    if vehicle is None:
        return {"error": f"Geçersiz araç: {vehicle_id}"}

    fuel_result = calculate_fuel_cost(
        distance_km=route_result["distance_km"],
        fuel_type=vehicle["fuel_type"],
        fuel_consumption=vehicle["consumption"],
        people=people
    )

    if "error" in fuel_result:
        return fuel_result

    return {
        "start": start_place["display_name"],
        "destination": end_place["display_name"],
        "vehicle": vehicle["name"],
        **route_result,
        **fuel_result
    }


def toplu_tasima_rota(
    start: str,
    end: str,
    time: str | None = None,
    date: str | None = None
) -> dict:
    """İki nokta arasındaki toplu taşıma rotalarını bulur.

    Desteklenen illerde ilgili saglayiciyi (IETT, ESHOT, KentKart vb.)
    sehir bazli secen find_transit_routes kullanilir.

    Args:
        start: Başlangıç noktası.
        end: Hedef noktası.

    Returns:
        Toplu taşıma rota listesi (hatlar, duraklar, süre, ücret).
    """
    start_place = _search_place(start)

    if start_place is None:
        return {"error": f"Başlangıç noktası bulunamadı: {start}"}

    end_place = _search_place(end)

    if end_place is None:
        return {"error": f"Hedef noktası bulunamadı: {end}"}

    result = find_transit_routes(
        start_place["lat"],
        start_place["lon"],
        end_place["lat"],
        end_place["lon"],
        start_province=find_province(start_place["lat"], start_place["lon"]),
        end_province=find_province(end_place["lat"], end_place["lon"]),
    )

    if result.get("status") != "success":
        return {
            "status": result.get("status"),
            "message": "Toplu taşıma rotası bulunamadı."
        }

    # AI'ya çok uzun veri göndermemek için özet çıkarıyoruz
    summaries = []

    for route in result["routes"][:3]:
        legs = []

        for leg in route["legs"]:
            legs.append({
                "tip": leg["type"],
                "hat": leg["name"],
                "nereden": leg["from_stop"],
                "nereye": leg["to_stop"],
                "kalkis": leg["departure_time"],
                "varis": leg["arrival_time"],
                "yuruyus_metro_veya_durak_sayisi": len(
                    leg.get("stops", [])
                )
            })

        summaries.append({
            "ucret_tl": route["fee"],
            "toplam_sure_dk": route["duration_minutes"],
            "yuruyus_metro": route["walking_distance_m"],
            "kalkis": route["departure_time"],
            "varis": route["arrival_time"],
            "ayaklar": legs
        })

    return {
        "start": start_place["display_name"],
        "destination": end_place["display_name"],
        "rotalar": summaries
    }


def hava_durumu(place: str, days: int = 3) -> dict:
    """Türkiye'de bir yerin anlık hava durumunu ve günlük tahminini döndürür.

    Args:
        place: Yer adı (örn. "İstanbul", "Bursa, Nilüfer").
        days: Tahmin gün sayısı (1-7).

    Returns:
        Anlık hava durumu ve günlük tahmin listesi.
    """
    place_result = _search_place(place)

    if place_result is None:
        return {"error": f"Yer bulunamadı: {place}"}

    try:
        weather = get_weather(
            place_result["lat"],
            place_result["lon"],
            days
        )
    except Exception:
        return {"error": "Hava durumu bilgisi alınamadı."}

    return {
        "yer": place_result["display_name"],
        **weather
    }


def web_ara(query: str) -> dict:
    """Internette arama yapar. Türkiye ulaşım hatları, güncel fiyatlar,
    yol durumu, hava durumu ve uygulamanın kapsamı dışındaki
    bilgiler için kullanılır.

    Args:
        query: Aranacak konu (örn. "Ankara EGO otobüs hatları").

    Returns:
        Arama sonuçları (baslik, url, ozet listesi).
    """
    from ddgs import DDGS

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query,
                region="tr-tr",
                max_results=5
            ))
    except Exception as e:
        return {"error": f"Arama yapılamadı: {e}"}

    if not results:
        return {"message": "Sonuç bulunamadı."}

    return {
        "sonuclar": [
            {
                "baslik": r.get("title"),
                "url": r.get("href"),
                "ozet": r.get("body")
            }
            for r in results
        ]
    }


# =========================================================
# ANA ASISTAN FONKSİYONU
# =========================================================

def _send_with_retry(chat, message: str, max_retries: int = 2):
    """Gemini mesajını gönderir; geçici hatalarda (503/yoğunluk)
    kısa bekleyip tekrar dener. Kota (429) hatasında özel istisna
    tipiyle döner."""

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return chat.send_message(message)
        except Exception as exc:
            last_error = exc
            text = str(exc)

            if "429" in text or "RESOURCE_EXHAUSTED" in text:
                raise QuotaExceededError() from exc

            retryable = (
                "503" in text
                or "UNAVAILABLE" in text
                or "500" in text
                or "INTERNAL" in text
            )

            if not retryable or attempt == max_retries:
                raise

            time.sleep(2 * (attempt + 1))

    raise last_error


class QuotaExceededError(Exception):
    """Gemini ücretsiz kota limiti aşıldı."""


def parse_route_intent(text: str) -> dict:
    """
    Doğal dili rota form alanlarına çevirir.

    "Yarın 4 kişi İzmit'ten İzmir'e en ucuz nasıl gideriz?" gibi bir
    cümleyden {"start", "end", "people", "mode"} alanlarını çıkarır.
    """

    ai_client = _get_client()

    prompt = f"""Aşağıdaki Türkçe cümleyi rota arama formu alanlarına ayrıştır.

Cümle: "{text}"

SADECE şu JSON formatında cevap ver, başka hiçbir şey yazma:
{{"start": "başlangıç yeri", "end": "hedef yeri", "people": <1-8 arası sayı>, "mode": "<otobus|metro|tramvay|deniz|arac|motosiklet|ucak|tren|yuruyus|null>"}}

Kurallar:
- start veya end cümlede belirtilmemişse null yaz.
- people belirtilmemişse 1 yaz.
- mode belirtilmemişse null yaz. "en ucuz" gibi ifadelerde mode null kalır.
- Şehir isimlerini sadeleştir: "İzmit'ten" → "İzmit".
"""

    try:
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
        )
    except Exception as exc:
        text_repr = str(exc)

        if "429" in text_repr or "RESOURCE_EXHAUSTED" in text_repr:
            raise QuotaExceededError() from exc

        raise

    raw = (response.text or "").strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()

    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)

    if not match:
        return {"error": "İstekünü rota alanlarına ayrıştıramadım."}

    try:
        data = json.loads(match.group(0))
    except ValueError:
        return {"error": "İstekünü rota alanlarına ayrıştıramadım."}

    return {
        "start": data.get("start"),
        "end": data.get("end"),
        "people": max(1, min(8, int(data.get("people") or 1))),
        "mode": data.get("mode") if data.get("mode") in (
            "otobus", "metro", "tramvay", "deniz", "arac", "motosiklet", "ucak", "tren", "yuruyus"
        ) else None,
    }


ROUTE_DETAIL_INSTRUCTION = """
Sen "Hedefime Nasıl Giderim" uygulamasının rota özetleyicisisin.
Sana GERÇEK ulaşım verisinden üretilmiş adım listesi (JSON) verilir.

MUTLAK KURALLAR (ihalali kullanıcıya yalan söylemek olur):
- SADECE verilen adımlardaki durak, hat, saat ve süreleri kullan.
- Yeni durak/istasyon/hat adı UYDURMA. Yeni kalkış saati UYDURMA.
- Bir bilgi adımlarda yoksa (null) onu "bilinmiyor" diye belirt ya da hiç değinme.
- departure_times listesindeki saatler gerçektir; listede olmayan saati yazma.
- Cevabın SADECE şu JSON olsun, başka hiçbir şey yazma:
  {"summary_text": "2-3 cümlelik Türkçe yolculuk özeti"}
- Özet: toplam süre, aktarma sayısı ve kritik biniş noktasını vurgula.
"""


def summarize_route_details(steps: list, from_name: str, to_name: str) -> str:
    """Gercek adimlardan Gemini ile 2-3 cumlelik ozet uretir.

    Gemini'ye adim URETTIRILMEZ; adimlar parametre olarak verilir ve
    prompt halüsinasyonu yasaklar. Basarisizlikta sablon ozet doner.
    """
    fallback = (
        f"{from_name} → {to_name}: {len(steps)} adımlı yolculuk. "
        "Detaylar yukarıdaki adımlarda."
    )

    if not steps:
        return fallback

    try:
        ai_client = _get_client()
    except Exception:
        return fallback

    prompt = (
        "Aşağıdaki GERÇEK rota adımlarını 2-3 cümleyle özetle.\n"
        "Kurallar: adımda yazmayan durak/saat/hat ekleme; "
        "eksik bilgiyi uydurma.\n\n"
        f"Güzergah: {from_name} → {to_name}\n"
        f"Adımlar (JSON): {json.dumps(steps, ensure_ascii=False)[:4000]}"
    )

    try:
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=ROUTE_DETAIL_INSTRUCTION,
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        text_repr = str(exc)
        if "429" in text_repr or "RESOURCE_EXHAUSTED" in text_repr:
            raise QuotaExceededError() from exc
        return fallback

    raw = (response.text or "").strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return fallback
    try:
        data = json.loads(match.group(0))
        summary = str(data.get("summary_text") or "").strip()
        return summary if summary else fallback
    except ValueError:
        return fallback


STATION_GUIDE_INSTRUCTION = """
Sen "Hedefime Nasıl Giderim" uygulamasının istasyon rehberisin.
Sana GERÇEK raylı sistem verisinden hesaplanmış en-yakın-istasyon
listeleri verilir (isim, hat, mesafe).

MUTLAK KURALLAR:
- SADECE verilen listedeki istasyon isimlerini kullan; listede olmayan
  istasyon/durak adı ASLA yazma.
- Kalkış saati ASLA yazma (canlı tarife sende yok).
- Hat sıklığı yazarsan mutlaka "değişebilir, güncel tarifeyi kontrol
  edin" uyarısını ekle; kesin sayı verme.
- Cevabın SADECE şu JSON olsun, başka hiçbir şey yazma:
  {"guidance": "2-3 cümlelik Türkçe yönlendirme",
   "frequency_note": "hat sıklığı notu ya da null"}
"""


def station_guidance(near_start: list, near_end: list,
                     from_name: str, to_name: str) -> dict:
    """Gercek istasyon listelerinden kisa AI rehberi.

    Donus: {"guidance": str|None, "frequency_note": str|None}.
    Basarisizlikta ikisi de None (arayuz genel karta duser).
    """
    empty = {"guidance": None, "frequency_note": None}
    if not near_start and not near_end:
        return empty

    try:
        ai_client = _get_client()
    except Exception:
        return empty

    def _short(stations):
        return [
            {"name": s.get("name"), "lines": s.get("lines", []),
             "distance_m": s.get("distance_m")}
            for s in (stations or [])[:3]
        ]

    prompt = (
        "Aşağıdaki GERÇEK istasyon listelerine göre yolcuya 2-3 cümlelik "
        "yönlendirme yaz. Kurallar: listede olmayan istasyon adı yazma, "
        "saat yazma.\n\n"
        f"Güzergah: {from_name} → {to_name}\n"
        f"Başlangıca yakın istasyonlar (JSON): "
        f"{json.dumps(_short(near_start), ensure_ascii=False)}\n"
        f"Hedefe yakın istasyonlar (JSON): "
        f"{json.dumps(_short(near_end), ensure_ascii=False)}"
    )

    try:
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=STATION_GUIDE_INSTRUCTION,
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        text_repr = str(exc)
        if "429" in text_repr or "RESOURCE_EXHAUSTED" in text_repr:
            raise QuotaExceededError() from exc
        return empty

    raw = (response.text or "").strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return empty
    try:
        data = json.loads(match.group(0))
        return {
            "guidance": str(data.get("guidance") or "").strip() or None,
            "frequency_note": str(data.get("frequency_note") or "").strip() or None,
        }
    except ValueError:
        return empty


def ask_assistant(message: str, history: list | None = None) -> dict:
    """
    AI asistana mesaj gönderir ve cevabı döndürür.

    history: [{"role": "user" | "model", "text": "..."}, ...]
    """

    ai_client = _get_client()

    contents = []

    if history:
        for entry in history:
            role = entry.get("role", "user")

            if role not in ("user", "model"):
                continue

            text = entry.get("text", "")

            if not text:
                continue

            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=text)]
            ))

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[
            yer_ara,
            arabayla_rota,
            toplu_tasima_rota,
            hava_durumu,
            web_ara
        ],
        temperature=0.4,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=False,
            maximum_remote_calls=10
        )
    )

    chat = ai_client.chats.create(
        model=MODEL_NAME,
        config=config,
        history=contents
    )

    try:
        response = _send_with_retry(chat, message)
    except QuotaExceededError:
        return {
            "reply": "Şu anda ücretsiz kota limitine ulaştık. "
                     "Yarım dakika kadar bekleyip tekrar yazarsan devam edebilirim.",
            "search_used": False
        }
    except Exception:
        return {
            "reply": "AI sunucusuna şu anda ulaşamadım. "
                     "Birkaç saniye sonra tekrar dener misin?",
            "search_used": False
        }

    reply = ""

    if response.candidates:
        parts = response.candidates[0].content.parts or []

        reply = "".join(
            part.text
            for part in parts
            if part.text is not None
        )

    search_used = False

    history_items = list(
        chat.get_history() or []
    )

    history_items += list(
        getattr(
            response,
            "automatic_function_calling_history",
            []
        ) or []
    )

    for content in history_items:
        for part in (content.parts or []):
            call = getattr(part, "function_call", None)

            if call and getattr(call, "name", "") == "web_ara":
                search_used = True

    return {
        "reply": reply,
        "search_used": search_used
    }

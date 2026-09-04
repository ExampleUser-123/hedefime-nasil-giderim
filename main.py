import logging

from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime

from services.geocoding import search_place, reverse_geocode
from services.routing import calculate_route
from services.fuel import get_fuel_prices, calculate_fuel_cost
from services.vehicles import get_vehicles, get_vehicle
from services.public_transport import find_transit_routes
from services.location import find_province
from services.weather import get_weather
from services.flight import estimate_flight

from services.gtfs import (
    search_stops,
    find_nearest_stops,
    get_routes_at_stop,
    get_stops_at_route,
    get_trips_at_route,
    get_trip_stop_times,
    is_service_active
)

from services.ai import ask_assistant, parse_route_intent, QuotaExceededError
from services.cache import cache_stats, cache_clear
from services.chat_store import (
    create_session,
    get_session,
    list_sessions,
    append_message,
    update_title_if_needed,
    delete_session,
    get_ai_history
)


app = FastAPI(title="HEDEFİME NASIL GİDERİM")

logger = logging.getLogger("hng")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Beklenmeyen her hatayı JSON hata mesajına çevirir;
    arayüz her zaman anlaşılır bir cevap görür."""

    logger.exception("İşlenmeyen hata: %s %s", request.method, request.url.path)

    return JSONResponse(
        status_code=500,
        content={"error": "Sunucuda beklenmeyen bir hata oluştu. Lütfen tekrar dene."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Android uygulaması (Capacitor WebView)
        "http://localhost",
        "https://localhost",
        # Aynı Wi-Fi'daki telefonlar
        "http://192.168.1.123:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================

def find_province_from_place(place):
    """
    Nominatim tarafından dönen display_name içindeki
    adres parçalarından Türkiye ilini bulur.

    Örnek:
    "Büyük Selimiye Camii, Üsküdar, İstanbul, Türkiye"

    -> İstanbul
    """

    if not place:
        return None

    display_name = place.get("display_name")

    if not display_name:
        return None

    parts = [
        part.strip()
        for part in display_name.split(",")
        if part.strip()
    ]

    # Adresin sonundan başlayarak il arıyoruz.
    # Çünkü Türkiye adreslerinde il genellikle sona yakındır.
    for part in reversed(parts):
        province = find_province(part)

        if province is not None:
            return province

    return None


def clean_public_transport_result(result, start_name, destination_name):
    """
    Toplu taşıma sonucundaki başlangıç ve hedef isimlerini düzeltir.
    """

    if result.get("status") != "success":
        return result

    for route in result.get("routes", []):
        legs = route.get("legs", [])

        if not legs:
            continue

        if legs[0].get("from_stop") == "start":
            legs[0]["from_stop"] = start_name

        if legs[-1].get("to_stop") == "destination":
            legs[-1]["to_stop"] = destination_name

    return result


def add_public_transport_recommendations(result):
    """
    Toplu taşıma rotaları içerisinden:

    - En hızlı
    - En ucuz
    - En az yürüyüşlü

    rotaları belirler.
    """

    if result.get("status") != "success":
        return result

    routes = result.get("routes", [])

    if not routes:
        result["recommendations"] = {
            "fastest": None,
            "cheapest": None,
            "least_walking": None
        }

        return result

    # Aynı rotaların tekrar etmesini engelle
    unique_routes = []
    seen = set()

    for route in routes:

        route_key = (
            route.get("fee"),
            route.get("walking_distance_m"),
            route.get("departure_time"),
            route.get("arrival_time"),
            tuple(
                (
                    leg.get("type"),
                    leg.get("line"),
                    leg.get("route_id")
                )
                for leg in route.get("legs", [])
            )
        )

        if route_key not in seen:
            seen.add(route_key)
            unique_routes.append(route)

    routes = unique_routes

    result["routes"] = routes

    # Ücreti belli olan rotalar
    valid_fee_routes = [
        route
        for route in routes
        if route.get("fee") is not None
    ]

    # En hızlı rota
    fastest = min(
        routes,
        key=lambda route: route.get(
            "duration_minutes",
            float("inf")
        )
    )

    # En az yürüyüşlü rota
    least_walking = min(
        routes,
        key=lambda route: route.get(
            "walking_distance_m",
            float("inf")
        )
    )

    # En ucuz rota
    cheapest = None

    if valid_fee_routes:
        cheapest = min(
            valid_fee_routes,
            key=lambda route: route.get(
                "fee",
                float("inf")
            )
        )

    result["recommendations"] = {
        "fastest": fastest,
        "cheapest": cheapest,
        "least_walking": least_walking
    }

    return result


# =========================================================
# ANA API
# =========================================================

@app.get("/")
def home():
    return {
        "message": "HEDEFİME NASIL GİDERİM API çalışıyor!"
    }


# =========================================================
# ARAÇ LİSTESİ
# =========================================================

@app.get("/vehicles")
def vehicles_endpoint():
    return [
        {"id": vehicle_id, **data}
        for vehicle_id, data in get_vehicles().items()
    ]


# =========================================================
# YER ARAMA
# =========================================================

@app.get("/search-place")
def search_place_endpoint(q: str):
    result = search_place(q)

    if result is None:
        return {
            "error": f"Yer bulunamadı: {q}"
        }

    return {
        "query": q,
        "result": result
    }


@app.get("/reverse-geocode")
def reverse_geocode_endpoint(lat: float, lon: float):

    result = reverse_geocode(lat, lon)

    if result is None:
        return {
            "error": "Bu koordinatta yer bulunamadı."
        }

    return result


# =========================================================
# ÖZEL ARAÇ ROTASI
# =========================================================

@app.get("/route")
def route(
    start: str,
    end: str,
    vehicle_id: str = "toyota_corolla",
    people: int = 1
):

    start_place = search_place(start)

    if start_place is None:
        return {
            "error": f"Başlangıç noktası bulunamadı: {start}"
        }

    end_place = search_place(end)

    if end_place is None:
        return {
            "error": f"Hedef noktası bulunamadı: {end}"
        }

    start_province = find_province_from_place(start_place)
    end_province = find_province_from_place(end_place)

    route_result = calculate_route(
        start_place["lat"],
        start_place["lon"],
        end_place["lat"],
        end_place["lon"]
    )

    if route_result is None:
        return {
            "error": "Rota bulunamadı."
        }

    vehicle = get_vehicle(vehicle_id)

    if vehicle is None:
        return {
            "error": f"Geçersiz araç: {vehicle_id}"
        }

    fuel_result = calculate_fuel_cost(
        distance_km=route_result["distance_km"],
        fuel_type=vehicle["fuel_type"],
        fuel_consumption=vehicle["consumption"],
        people=people
    )

    return {
        "start": start_place["display_name"],
        "destination": end_place["display_name"],
        "vehicle": vehicle["name"],
        "fuel_type": vehicle["fuel_type"],
        "fuel_consumption": vehicle["consumption"],
        **route_result,
        **fuel_result
    }


# =========================================================
# YAKIT FİYATLARI
# =========================================================

@app.get("/fuel-prices")
def fuel_prices():
    return {
        "prices": get_fuel_prices()
    }


# =========================================================
# YAKIT MALİYETİ HESAPLAMA
# =========================================================

@app.get("/calculate-cost")
def calculate_cost(
    distance_km: float,
    fuel_type: str,
    fuel_consumption: float,
    people: int
):

    result = calculate_fuel_cost(
        distance_km=distance_km,
        fuel_type=fuel_type,
        fuel_consumption=fuel_consumption,
        people=people
    )

    return result


# =========================================================
# MANUEL ARAÇ + ROTA
# =========================================================

@app.get("/plan-trip")
def plan_trip(
    start: str,
    end: str,
    fuel_type: str,
    fuel_consumption: float,
    people: int
):

    start_place = search_place(start)

    if start_place is None:
        return {
            "error": f"Başlangıç noktası bulunamadı: {start}"
        }

    end_place = search_place(end)

    if end_place is None:
        return {
            "error": f"Hedef noktası bulunamadı: {end}"
        }

    route_result = calculate_route(
        start_place["lat"],
        start_place["lon"],
        end_place["lat"],
        end_place["lon"]
    )

    if route_result is None:
        return {
            "error": "Rota bulunamadı."
        }

    fuel_result = calculate_fuel_cost(
        distance_km=route_result["distance_km"],
        fuel_type=fuel_type,
        fuel_consumption=fuel_consumption,
        people=people
    )

    if "error" in fuel_result:
        return fuel_result

    return {
        "start": start_place["display_name"],
        "destination": end_place["display_name"],
        **route_result,
        **fuel_result
    }


# =========================================================
# ARAÇLAR
# =========================================================

@app.get("/vehicles")
def vehicles():
    return {
        "vehicles": get_vehicles()
    }


# =========================================================
# BELİRLİ ARAÇLA ROTA
# =========================================================

@app.get("/plan-trip-by-vehicle")
def plan_trip_by_vehicle(
    start: str,
    end: str,
    vehicle_id: str,
    people: int
):

    start_place = search_place(start)

    if start_place is None:
        return {
            "error": f"Başlangıç noktası bulunamadı: {start}"
        }

    end_place = search_place(end)

    if end_place is None:
        return {
            "error": f"Hedef noktası bulunamadı: {end}"
        }

    vehicle = get_vehicle(vehicle_id)

    if vehicle is None:
        return {
            "error": f"Araç bulunamadı: {vehicle_id}"
        }

    route_result = calculate_route(
        start_place["lat"],
        start_place["lon"],
        end_place["lat"],
        end_place["lon"]
    )

    if route_result is None:
        return {
            "error": "Rota bulunamadı."
        }

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


# =========================================================
# TOPLU TAŞIMA
# =========================================================

@app.get("/public-transport")
def public_transport(
    start: str,
    end: str,
    time: str | None = None,
    date: str | None = None,
    optimizefor: str = "time"
):

    start_place = search_place(start)

    if start_place is None:
        return {
            "error": f"Başlangıç noktası bulunamadı: {start}"
        }

    end_place = search_place(end)

    if end_place is None:
        return {
            "error": f"Hedef noktası bulunamadı: {end}"
        }

    # Saat verilmediyse mevcut saati kullan
    if time is None:
        time = datetime.now().strftime("%H:%M")

    result = find_public_transport_route(
        start_place["lat"],
        start_place["lon"],
        end_place["lat"],
        end_place["lon"],
        time=time,
        date=date,
        optimizefor=optimizefor
    )

    result = clean_public_transport_result(
        result,
        start_place["display_name"],
        end_place["display_name"]
    )

    result = add_public_transport_recommendations(result)

    return {
        "start": start_place["display_name"],
        "destination": end_place["display_name"],
        **result
    }


# =========================================================
# DURAK ARAMA
# =========================================================

@app.get("/search-stops")
def search_stops_endpoint(
    query: str,
    limit: int = 10
):

    return {
        "query": query,
        "results": search_stops(query, limit)
    }


# =========================================================
# EN YAKIN DURAKLAR
# =========================================================

@app.get("/nearest-stops")
def nearest_stops(
    lat: float,
    lon: float,
    limit: int = 5
):

    return {
        "latitude": lat,
        "longitude": lon,
        "results": find_nearest_stops(
            lat,
            lon,
            limit
        )
    }


# =========================================================
# DURAĞA GELEN HATLAR
# =========================================================

@app.get("/stop-routes")
def stop_routes(stop_id: str):

    return {
        "stop_id": stop_id,
        "routes": get_routes_at_stop(stop_id)
    }


# =========================================================
# HATTIN DURAKLARI
# =========================================================

@app.get("/route-stops")
def route_stops(
    route_id: str,
    direction_id: str | None = None
):

    return {
        "route_id": route_id,
        "direction_id": direction_id,
        "stops": get_stops_at_route(
            route_id,
            direction_id
        )
    }


# =========================================================
# HATTIN SEFERLERİ
# =========================================================

@app.get("/route-trips")
def route_trips(
    route_id: str,
    direction_id: str | None = None
):

    return {
        "route_id": route_id,
        "direction_id": direction_id,
        "trips": get_trips_at_route(
            route_id,
            direction_id
        )
    }


# =========================================================
# SEFERİN DURAK ZAMANLARI
# =========================================================

@app.get("/trip-stop-times")
def trip_stop_times(trip_id: str):

    return {
        "trip_id": trip_id,
        "stops": get_trip_stop_times(trip_id)
    }


# =========================================================
# SERVİS AKTİF Mİ?
# =========================================================

@app.get("/service-active")
def service_active(service_id: str):

    return {
        "service_id": service_id,
        "active": is_service_active(service_id)
    }


# =========================================================
# ANA SEYAHAT PLANLAMA
# =========================================================

@app.get("/plan")
def plan(
    start: str,
    end: str,
    people: int = 1,
    vehicle: str = "toyota_corolla"
):

    # -----------------------------------------------------
    # BAŞLANGIÇ VE HEDEF YERİ (PARALEL)
    # -----------------------------------------------------

    with ThreadPoolExecutor(max_workers=2) as pool:
        start_future = pool.submit(search_place, start)
        end_future = pool.submit(search_place, end)

        start_place = start_future.result()
        end_place = end_future.result()

    if start_place is None:
        return {
            "error": f"Başlangıç noktası bulunamadı: {start}"
        }

    if end_place is None:
        return {
            "error": f"Hedef noktası bulunamadı: {end}"
        }

    # -----------------------------------------------------
    # İLLERİ BUL
    # -----------------------------------------------------

    start_province = find_province_from_place(start_place)
    end_province = find_province_from_place(end_place)

    # -----------------------------------------------------
    # ARAÇ ROTASI + TOPLU TAŞIMA (PARALEL)
    # -----------------------------------------------------

    with ThreadPoolExecutor(max_workers=2) as pool:
        route_future = pool.submit(
            calculate_route,
            start_place["lat"],
            start_place["lon"],
            end_place["lat"],
            end_place["lon"]
        )

        public_future = pool.submit(
            find_transit_routes,
            start_place["lat"],
            start_place["lon"],
            end_place["lat"],
            end_place["lon"],
            start_province,
            end_province
        )

        route_result = route_future.result()
        public_result = public_future.result()

    # Başlangıç ve hedef isimlerini düzelt
    public_result = clean_public_transport_result(
        public_result,
        start_place["display_name"],
        end_place["display_name"]
    )

    # Toplu taşıma önerilerini hesapla
    public_result = add_public_transport_recommendations(
        public_result
    )

    # -----------------------------------------------------
    # DESTEKLENMEYEN İLLERDE BİLGİLENDİRMESİ
    # (İstanbul: İETT router, İzmir: ESHOT açık veri)
    # -----------------------------------------------------

    SUPPORTED_TRANSIT_CITIES = {
        "İstanbul",
        "İzmir",
        "Kocaeli",
        "Konya",
        "Antalya",
        "Adana",
    }

    start_city = start_province.get("name") if start_province else None
    end_city = end_province.get("name") if end_province else None

    has_provider = (
        start_city in SUPPORTED_TRANSIT_CITIES
        and end_city == start_city
    )

    if (
        public_result.get("status") != "success"
        and not has_provider
    ):
        public_result["error"] = (
            "Toplu taşıma verisi şu an İstanbul, İzmir, Kocaeli, Konya, "
            "Antalya ve Adana için mevcut. Diğer illerde Araç veya Uçak "
            "modunu kullanabilirsin; şehir içi toplu taşıma desteği "
            "il il eklenecek."
        )

    # -----------------------------------------------------
    # VARSAYILAN ARAÇ VE YAKIT MALİYETİ
    # (araç kısmı hata verirse rota bilgisi kaybolmasın)
    # -----------------------------------------------------

    vehicle_data = get_vehicle(vehicle)

    if vehicle_data is None:
        vehicle_data = get_vehicle("toyota_corolla")

    car_result = None
    car_error = None

    if route_result is None:
        car_error = "Araç rotası bulunamadı."
    else:
        fuel_result = calculate_fuel_cost(
            distance_km=route_result["distance_km"],
            fuel_type=vehicle_data["fuel_type"],
            fuel_consumption=vehicle_data["consumption"],
            people=people
        )

        if "error" in fuel_result:
            car_error = fuel_result["error"]
        else:
            car_result = {
                "vehicle": vehicle_data["name"],
                "fuel_type": vehicle_data["fuel_type"],
                "fuel_consumption": vehicle_data["consumption"],
                **route_result,
                **fuel_result
            }

    # -----------------------------------------------------
    # UÇAK TAHMİNİ (kuş uçuşu mesafe üzerinden)
    # -----------------------------------------------------

    flight_result = None

    if route_result is not None:
        # Araç rotası mesafesi karayolu olduğu için kuş uçuşu ~%75 alıyoruz
        straight_km = route_result["distance_km"] * 0.75
        flight_result = estimate_flight(straight_km, people)

    # -----------------------------------------------------
    # SONUÇ
    # -----------------------------------------------------

    return {
        "start": start_place["display_name"],
        "destination": end_place["display_name"],
        "people": people,

        "start_coord": {
            "lat": start_place["lat"],
            "lon": start_place["lon"]
        },

        "end_coord": {
            "lat": end_place["lat"],
            "lon": end_place["lon"]
        },

        "locations": {
            "start_province": start_province,
            "end_province": end_province
        },

        "car": car_result,
        "car_error": car_error,

        "vehicle_selected": vehicle_data["name"],

        "flight": flight_result,

        "public_transport": public_result,

        "recommendations": public_result.get(
            "recommendations",
            {
                "fastest": None,
                "cheapest": None,
                "least_walking": None
            }
        )
    }


# =========================================================
# HAVA DURUMU
# =========================================================

@app.get("/weather")
def weather(
    place: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    days: int = 3
):

    if lat is None or lon is None:
        if not place:
            return {
                "error": "place veya lat/lon parametrelerinden biri gerekli."
            }

        place_result = search_place(place)

        if place_result is None:
            return {
                "error": f"Yer bulunamadı: {place}"
            }

        lat = place_result["lat"]
        lon = place_result["lon"]
        location_name = place_result["display_name"]

    else:
        location_name = f"{lat}, {lon}"

    try:
        weather_result = get_weather(lat, lon, days)

    except Exception:
        return {
            "error": "Hava durumu bilgisi alınamadı."
        }

    return {
        "location": location_name,
        **weather_result
    }


# =========================================================
# AI ASİSTAN
# =========================================================

class AssistantMessage(BaseModel):
    message: str
    session_id: str | None = None
    history: list[dict] = []


class IntentMessage(BaseModel):
    message: str


@app.post("/parse-intent")
def parse_intent(body: IntentMessage):
    """Doğal dili rota formu alanlarına çevirir (AI asistan hızlı girişi)."""

    message = body.message.strip()

    if not message:
        return {"error": "Mesaj boş olamaz."}

    try:
        return parse_route_intent(message)

    except QuotaExceededError:
        return {
            "error": "AI asistanının dakikalık kullanım limiti doldu. "
            "Birkaç saniye sonra tekrar dene."
        }

    except Exception:
        return {
            "error": "AI asistanına şu anda ulaşılamıyor. Formu elle doldurabilirsin."
        }


@app.post("/ai-assistant")
def ai_assistant(body: AssistantMessage):

    message = body.message.strip()

    if not message:
        return {
            "error": "Mesaj boş olamaz."
        }

    # -----------------------------------------------------
    # OTURUM: session_id verildiyse geçmişi oradan al
    # -----------------------------------------------------

    session = None
    history = body.history

    if body.session_id:
        session = get_session(body.session_id)

        if session is None:
            return {
                "error": f"Sohbet oturumu bulunamadı: {body.session_id}"
            }

        history = get_ai_history(session)

    # -----------------------------------------------------
    # AI'YA SOR
    # -----------------------------------------------------

    try:
        result = ask_assistant(
            message=message,
            history=history
        )

    except RuntimeError as e:
        return {
            "error": str(e)
        }

    except Exception:
        return {
            "error": "AI asistanına şu anda ulaşılamıyor. Lütfen tekrar deneyin."
        }

    # -----------------------------------------------------
    # OTURUMA KAYDET
    # -----------------------------------------------------

    if session is not None:
        append_message(body.session_id, "user", message)
        append_message(
            body.session_id,
            "model",
            result.get("reply", "")
        )

        update_title_if_needed(body.session_id, message)

        result["session_id"] = body.session_id

    return result


# =========================================================
# SOHBET OTURUMLARI
# =========================================================

@app.post("/chat/sessions")
def create_chat_session(title: str | None = None):

    session = create_session(
        title or "Yeni sohbet"
    )

    return session


@app.get("/chat/sessions")
def list_chat_sessions():

    return {
        "sessions": list_sessions()
    }


@app.get("/chat/sessions/{session_id}")
def get_chat_session(session_id: str):

    session = get_session(session_id)

    if session is None:
        return {
            "error": f"Sohbet oturumu bulunamadı: {session_id}"
        }

    return session


@app.delete("/chat/sessions/{session_id}")
def delete_chat_session(session_id: str):

    if not delete_session(session_id):
        return {
            "error": f"Sohbet oturumu bulunamadı: {session_id}"
        }

    return {
        "message": "Sohbet oturumu silindi.",
        "session_id": session_id
    }


# =========================================================
# ÖNBELLEK
# =========================================================

@app.get("/cache-stats")
def cache_statistics():
    return cache_stats()


@app.post("/cache-clear")
def clear_cache():
    cache_clear()

    return {
        "message": "Önbellek temizlendi."
    }
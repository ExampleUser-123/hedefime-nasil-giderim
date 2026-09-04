# Uçak yolculuğu tahmini (ücretsiz veri kaynağı yok; mesafe bazlı kestirim)
# Not: Canlı bilet fiyatı API'leri (Amadeus, Skyscanner vb.) ücretlidir.

MIN_FLIGHT_KM = 300
CRUISE_SPEED_KMH = 750
BASE_PRICE_TL = 950
PRICE_PER_KM_TL = 1.0
AIRPORT_OVERHEAD_MINUTES = 100  # taksi, check-in, güvenlik, bekleme


def estimate_flight(distance_km: float, people: int = 1):
    """Mesafeye göre tahmini uçuş maliyeti ve süresi.

    distance_km: karayolu mesafesi değil, iki nokta arası kuş uçuşu mesafeye
    yakın olmalı. Çağıran taraf budaymış gibi gönderir.
    """

    distance_km = round(distance_km)

    if distance_km < MIN_FLIGHT_KM:
        return {
            "available": False,
            "reason": f"{distance_km} km için uçak önerilmez; "
                      f"{MIN_FLIGHT_KM} km üzerinde anlamlı olur.",
        }

    price_per_person = round(BASE_PRICE_TL + PRICE_PER_KM_TL * distance_km)

    flight_minutes = round(distance_km / CRUISE_SPEED_KMH * 60)
    total_minutes = flight_minutes + AIRPORT_OVERHEAD_MINUTES

    return {
        "available": True,
        "distance_km": distance_km,
        "duration_minutes": total_minutes,
        "estimated_price_per_person": price_per_person,
        "total_price": price_per_person * people,
        "people": people,
        "note": "Tahmini fiyat; gerçek bilet fiyatı tarihe, havayoluna ve "
                "yoğunluğa göre değişir.",
    }

# Tren yolculuğu tahmini (TCDD'nin ücretsiz açık fiyat API'si yok; mesafe bazlı kestirim)
# YHT (Yüksek Hızlı Tren) hatları Ankara-İstanbul, Ankara-İzmir, Ankara-Eskişehir,
# İstanbul-Konya vb. diğer hatlarda konvansiyonel tren çalışır. Karışım hız kullanılır.

MIN_TRAIN_KM = 40
AVG_SPEED_KMH = 110          # YHT ~160-250, konvansiyonel ~70-90; harman ortalama
BASE_PRICE_TL = 60
PRICE_PER_KM_TL = 1.1        # YHT ~1.3 TL/km, konvansiyonel ~0.7 TL/km harmanı
STATION_OVERHEAD_MINUTES = 30  # istasyona git, bekleme, iniş kalkış


def estimate_train(distance_km: float, people: int = 1):
    """Mesafeye göre tahmini tren maliyeti ve süresi."""

    distance_km = round(distance_km)

    if distance_km < MIN_TRAIN_KM:
        return {
            "available": False,
            "reason": f"{distance_km} km için tren önerilmez; "
                      f"{MIN_TRAIN_KM} km üzerinde anlamlı olur.",
        }

    price_per_person = round(BASE_PRICE_TL + PRICE_PER_KM_TL * distance_km)

    ride_minutes = round(distance_km / AVG_SPEED_KMH * 60)
    total_minutes = ride_minutes + STATION_OVERHEAD_MINUTES

    return {
        "available": True,
        "distance_km": distance_km,
        "duration_minutes": total_minutes,
        "estimated_price_per_person": price_per_person,
        "total_price": price_per_person * people,
        "people": people,
        "note": "Tahmini fiyat; gerçek bilet fiyatı TCDD seferine ve "
                "vagon tipine göre değişir. YHT hatlarında daha hızlı ve pahalıdır.",
    }

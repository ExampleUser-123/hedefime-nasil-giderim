import requests

from services.cache import cached


WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# WMO hava durumu kodları -> Türkçe açıklama
WEATHER_CODES = {
    0: "Açık ve güneşli",
    1: "Az bulutlu",
    2: "Parçalı bulutlu",
    3: "Kapalı",
    45: "Puslu",
    48: "Kırağılı pus",
    51: "Hafif çiseleme",
    53: "Çiseleme",
    55: "Yoğun çiseleme",
    56: "Hafif dondurucu çiseleme",
    57: "Dondurucu çiseleme",
    61: "Hafif yağmurlu",
    63: "Yağmurlu",
    65: "Şiddetli yağmurlu",
    66: "Hafif dondurucu yağmur",
    67: "Dondurucu yağmur",
    71: "Hafif kar yağışlı",
    73: "Kar yağışlı",
    75: "Yoğun kar yağışlı",
    77: "Kar taneli",
    80: "Hafif sağanak",
    81: "Sağanak yağışlı",
    82: "Şiddetli sağanak",
    85: "Hafif kar sağanağı",
    86: "Yoğun kar sağanağı",
    95: "Gök gürültülü fırtına",
    96: "Dolulu fırtına",
    99: "Şiddetli dolulu fırtına"
}


def _describe_code(code):
    if code is None:
        return None

    return WEATHER_CODES.get(code, f"Bilinmeyen durum ({code})")


@cached(ttl_seconds=600)
def get_weather(
    lat: float,
    lon: float,
    days: int = 3
):
    """
    Open-Meteo'dan anlık hava durumu ve
    günlük tahmini getirir. API anahtarı gerekmez.
    """

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,"
            "weather_code,"
            "wind_speed_10m,"
            "relative_humidity_2m"
        ),
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "weather_code,"
            "precipitation_probability_max"
        ),
        "timezone": "Europe/Istanbul",
        "forecast_days": min(max(days, 1), 7)
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    current = data.get("current", {})
    daily = data.get("daily", {})

    forecast = []

    dates = daily.get("time", [])
    date_count = len(dates)

    for index in range(date_count):
        forecast.append({
            "date": dates[index],
            "temp_max": daily.get("temperature_2m_max", [])[index],
            "temp_min": daily.get("temperature_2m_min", [])[index],
            "condition": _describe_code(
                (daily.get("weather_code") or [])[index]
            ),
            "precipitation_probability": (
                daily.get("precipitation_probability_max") or []
            )[index]
        })

    return {
        "current": {
            "temperature": current.get("temperature_2m"),
            "condition": _describe_code(current.get("weather_code")),
            "wind_speed": current.get("wind_speed_10m"),
            "humidity": current.get("relative_humidity_2m")
        },
        "forecast": forecast
    }

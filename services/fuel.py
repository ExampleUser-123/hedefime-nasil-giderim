import requests

from services.cache import cached


@cached(ttl_seconds=3600)
def get_fuel_prices():
    """Ulusal yakıt fiyatlarını getirir. API erişilemezse None döner
    (önbelleğe alınmaz, sonraki istekte tekrar denenir)."""

    url = "https://ucuzyakitbul.com.tr/api/prices/national"

    try:
        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    prices = {}

    for fuel in data.get("prices", []):
        fuel_type = fuel.get("fuelType")
        price = fuel.get("price")
        date = fuel.get("date")

        if fuel_type and price is not None:
            prices[fuel_type] = {
                "price": price,
                "date": date
            }

    return prices or None


def calculate_fuel_cost(
    distance_km: float,
    fuel_type: str,
    fuel_consumption: float,
    people: int
):
    prices = get_fuel_prices()

    valid_fuels = ["Benzin", "Motorin", "LPG", "Elektrik"]

    if prices is None:
        return {
            "error": "Yakıt fiyatları şu anda alınamıyor. Lütfen tekrar dene."
        }

    if fuel_type not in valid_fuels:
        return {
            "error": "Geçersiz yakıt türü. Benzin, Motorin veya LPG kullanın."
        }

    if people < 1:
        return {
            "error": "Kişi sayısı en az 1 olmalıdır."
        }

    if fuel_consumption <= 0:
        return {
            "error": "Yakıt tüketimi 0'dan büyük olmalıdır."
        }

    if fuel_type not in prices:
        if fuel_type == "Elektrik":
            # Fiyat API'si elektrik yayınlamıyor; ort. halka açık şarj maliyeti (TL/kWh)
            prices[fuel_type] = {
                "price": 6.5,
                "date": "tahmini · şarj yeri ve tarifesine göre değişir",
            }
        else:
            return {
                "error": "Yakıt fiyatı bulunamadı."
            }

    fuel_price = prices[fuel_type]["price"]
    price_date = prices[fuel_type]["date"]

    fuel_liters = distance_km * fuel_consumption / 100

    total_cost = fuel_liters * fuel_price

    cost_per_person = total_cost / people

    return {
        "distance_km": round(distance_km, 2),
        "fuel_type": fuel_type,
        "fuel_price": fuel_price,
        "price_date": price_date,
        "fuel_consumption": fuel_consumption,
        "fuel_liters": round(fuel_liters, 2),
        "people": people,
        "total_cost": round(total_cost, 2),
        "cost_per_person": round(cost_per_person, 2)
    }
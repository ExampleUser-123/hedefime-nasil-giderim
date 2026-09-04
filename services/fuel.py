import requests

from services.cache import cached


@cached(ttl_seconds=3600)
def get_fuel_prices():
    url = "https://ucuzyakitbul.com.tr/api/prices/national"

    response = requests.get(
        url,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    prices = {}

    for fuel in data["prices"]:
        fuel_type = fuel["fuelType"]
        price = fuel["price"]
        date = fuel["date"]

        prices[fuel_type] = {
            "price": price,
            "date": date
        }

    return prices


def calculate_fuel_cost(
    distance_km: float,
    fuel_type: str,
    fuel_consumption: float,
    people: int
):
    prices = get_fuel_prices()

    valid_fuels = ["Benzin", "Motorin", "LPG"]

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
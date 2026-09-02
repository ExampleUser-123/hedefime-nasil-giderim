from fastapi import FastAPI
from datetime import datetime

from services.geocoding import search_place
from services.routing import calculate_route
from services.fuel import get_fuel_prices, calculate_fuel_cost
from services.vehicles import get_vehicles, get_vehicle
from services.public_transport import find_public_transport_route
from services.gtfs import (
    search_stops,
    find_nearest_stops,
    get_routes_at_stop,
    get_stops_at_route,
    get_trips_at_route,
    get_trip_stop_times,
    is_service_active
)

app = FastAPI(title="HEDEFİME NASIL GİDİCEM")


@app.get("/")
def home():
    return {
        "message": "HEDEFİME NASIL GİDİCEM API çalışıyor!"
    }


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


@app.get("/fuel-prices")
def fuel_prices():
    return {
        "prices": get_fuel_prices()
    }


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


@app.get("/vehicles")
def vehicles():
    return {
        "vehicles": get_vehicles()
    }


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

    # Rota başarılıysa başlangıç ve hedef isimlerini yerleştir
    if result.get("status") == "success":
        for route in result.get("routes", []):
            legs = route.get("legs", [])

            if not legs:
                continue

            if legs[0].get("from_stop") == "start":
                legs[0]["from_stop"] = start_place["display_name"]

            if legs[-1].get("to_stop") == "destination":
                legs[-1]["to_stop"] = end_place["display_name"]

    # Rotalar varsa işle
    if result.get("status") == "success" and result.get("routes"):
        routes = result["routes"]

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

        # Ücret bilgisi olan rotaları bul
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

    return {
        "start": start_place["display_name"],
        "destination": end_place["display_name"],
        **result
    }


@app.get("/search-stops")
def search_stops_endpoint(query: str, limit: int = 10):
    return {
        "query": query,
        "results": search_stops(query, limit)
    }


@app.get("/nearest-stops")
def nearest_stops(lat: float, lon: float, limit: int = 5):
    return {
        "latitude": lat,
        "longitude": lon,
        "results": find_nearest_stops(lat, lon, limit)
    }


@app.get("/stop-routes")
def stop_routes(stop_id: str):
    return {
        "stop_id": stop_id,
        "routes": get_routes_at_stop(stop_id)
    }


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


@app.get("/trip-stop-times")
def trip_stop_times(trip_id: str):
    return {
        "trip_id": trip_id,
        "stops": get_trip_stop_times(trip_id)
    }


@app.get("/service-active")
def service_active(service_id: str):
    return {
        "service_id": service_id,
        "active": is_service_active(service_id)
    }

@app.get("/plan")
def plan(
    start: str,
    end: str,
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

    # Özel araç rotası
    route_result = calculate_route(
        start_place["lat"],
        start_place["lon"],
        end_place["lat"],
        end_place["lon"]
    )

    if route_result is None:
        return {
            "error": "Araç rotası bulunamadı."
        }

    # Varsayılan araç
    vehicle = get_vehicle("toyota_corolla")

    fuel_result = calculate_fuel_cost(
        distance_km=route_result["distance_km"],
        fuel_type=vehicle["fuel_type"],
        fuel_consumption=vehicle["consumption"],
        people=people
    )

    # Toplu taşıma rotası
    public_result = find_public_transport_route(
        start_place["lat"],
        start_place["lon"],
        end_place["lat"],
        end_place["lon"]
    )

    # Başlangıç ve hedef isimlerini düzelt
    if public_result.get("status") == "success":
        for route in public_result.get("routes", []):
            legs = route.get("legs", [])

            if not legs:
                continue

            if legs[0].get("from_stop") == "start":
                legs[0]["from_stop"] = start_place["display_name"]

            if legs[-1].get("to_stop") == "destination":
                legs[-1]["to_stop"] = end_place["display_name"]

        # Toplu taşıma önerileri
    recommendations = {
        "fastest": None,
        "cheapest": None,
        "least_walking": None
    }

    if public_result.get("status") == "success":
        routes = public_result.get("routes", [])

        if routes:
            # En hızlı rota
            recommendations["fastest"] = min(
                routes,
                key=lambda route: route.get(
                    "duration_minutes",
                    float("inf")
                )
            )

            # En ucuz rota
            valid_fee_routes = [
                route
                for route in routes
                if route.get("fee") is not None
            ]

            if valid_fee_routes:
                recommendations["cheapest"] = min(
                    valid_fee_routes,
                    key=lambda route: route.get(
                        "fee",
                        float("inf")
                    )
                )

            # En az yürüme
            recommendations["least_walking"] = min(
                routes,
                key=lambda route: route.get(
                    "walking_distance_m",
                    float("inf")
                )
            )

    return {
        "start": start_place["display_name"],
        "destination": end_place["display_name"],
        "people": people,

        "car": {
            "vehicle": vehicle["name"],
            "fuel_type": vehicle["fuel_type"],
            "fuel_consumption": vehicle["consumption"],
            **route_result,
            **fuel_result
        },

        "public_transport": public_result,

        "recommendations": recommendations
    }
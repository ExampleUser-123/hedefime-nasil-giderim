VEHICLES = {
    "toyota_corolla": {
        "name": "Toyota Corolla",
        "fuel_type": "Benzin",
        "consumption": 7.0
    },
    "fiat_egea": {
        "name": "Fiat Egea",
        "fuel_type": "Motorin",
        "consumption": 5.0
    },
    "renault_clio": {
        "name": "Renault Clio",
        "fuel_type": "Benzin",
        "consumption": 6.0
    }
}


def get_vehicles():
    return VEHICLES


def get_vehicle(vehicle_id: str):
    return VEHICLES.get(vehicle_id)
# Türk piyasasında yaygın araçlar (yaklaşık ortalama tüketimler, L/100 km)

VEHICLES = {
    # ---------------- BENZİN ----------------
    "toyota_corolla": {
        "name": "Toyota Corolla 1.6",
        "brand": "Toyota",
        "fuel_type": "Benzin",
        "consumption": 6.7,
    },
    "toyota_yaris": {
        "name": "Toyota Yaris 1.5",
        "brand": "Toyota",
        "fuel_type": "Benzin",
        "consumption": 5.5,
    },
    "fiat_egea_benzin": {
        "name": "Fiat Egea 1.6 (Benzin)",
        "brand": "Fiat",
        "fuel_type": "Benzin",
        "consumption": 6.8,
    },
    "fiat_egea_cross": {
        "name": "Fiat Egea Cross 1.6",
        "brand": "Fiat",
        "fuel_type": "Benzin",
        "consumption": 7.2,
    },
    "renault_clio_benzin": {
        "name": "Renault Clio 1.0 TCe",
        "brand": "Renault",
        "fuel_type": "Benzin",
        "consumption": 5.6,
    },
    "renault_megane_benzin": {
        "name": "Renault Megane 1.3 TCe",
        "brand": "Renault",
        "fuel_type": "Benzin",
        "consumption": 6.4,
    },
    "renault_symbol": {
        "name": "Renault Symbol 1.6",
        "brand": "Renault",
        "fuel_type": "Benzin",
        "consumption": 6.4,
    },
    "vw_golf": {
        "name": "Volkswagen Golf 1.5 TSI",
        "brand": "Volkswagen",
        "fuel_type": "Benzin",
        "consumption": 6.2,
    },
    "vw_polo": {
        "name": "Volkswagen Polo 1.0 TSI",
        "brand": "Volkswagen",
        "fuel_type": "Benzin",
        "consumption": 5.8,
    },
    "vw_passat_benzin": {
        "name": "Volkswagen Passat 1.5 TSI",
        "brand": "Volkswagen",
        "fuel_type": "Benzin",
        "consumption": 6.9,
    },
    "vw_tiguan": {
        "name": "Volkswagen Tiguan 1.5 TSI",
        "brand": "Volkswagen",
        "fuel_type": "Benzin",
        "consumption": 7.4,
    },
    "opel_astra_benzin": {
        "name": "Opel Astra 1.4 Turbo",
        "brand": "Opel",
        "fuel_type": "Benzin",
        "consumption": 6.5,
    },
    "opel_corsa": {
        "name": "Opel Corsa 1.2",
        "brand": "Opel",
        "fuel_type": "Benzin",
        "consumption": 5.6,
    },
    "ford_focus_benzin": {
        "name": "Ford Focus 1.5 EcoBoost",
        "brand": "Ford",
        "fuel_type": "Benzin",
        "consumption": 6.6,
    },
    "ford_fiesta": {
        "name": "Ford Fiesta 1.1",
        "brand": "Ford",
        "fuel_type": "Benzin",
        "consumption": 5.9,
    },
    "honda_civic_benzin": {
        "name": "Honda Civic 1.6 i-VTEC",
        "brand": "Honda",
        "fuel_type": "Benzin",
        "consumption": 6.8,
    },
    "skoda_octavia_benzin": {
        "name": "Skoda Octavia 1.5 TSI",
        "brand": "Skoda",
        "fuel_type": "Benzin",
        "consumption": 6.4,
    },
    "seat_ibiza": {
        "name": "Seat Ibiza 1.0 TSI",
        "brand": "Seat",
        "fuel_type": "Benzin",
        "consumption": 5.8,
    },
    "peugeot_208_benzin": {
        "name": "Peugeot 208 1.2 PureTech",
        "brand": "Peugeot",
        "fuel_type": "Benzin",
        "consumption": 5.7,
    },
    "peugeot_301_benzin": {
        "name": "Peugeot 301 1.6 VTi",
        "brand": "Peugeot",
        "fuel_type": "Benzin",
        "consumption": 6.5,
    },
    "dacia_sandero_benzin": {
        "name": "Dacia Sandero 1.0 SCe",
        "brand": "Dacia",
        "fuel_type": "Benzin",
        "consumption": 5.8,
    },
    "dacia_duster_benzin": {
        "name": "Dacia Duster 1.3 TCe",
        "brand": "Dacia",
        "fuel_type": "Benzin",
        "consumption": 6.9,
    },
    "hyundai_i20_benzin": {
        "name": "Hyundai i20 1.4 MPI",
        "brand": "Hyundai",
        "fuel_type": "Benzin",
        "consumption": 6.2,
    },
    "nissan_micra": {
        "name": "Nissan Micra 1.0",
        "brand": "Nissan",
        "fuel_type": "Benzin",
        "consumption": 5.7,
    },
    "nissan_qashqai_benzin": {
        "name": "Nissan Qashqai 1.3 DIG-T",
        "brand": "Nissan",
        "fuel_type": "Benzin",
        "consumption": 6.9,
    },

    # ---------------- MOTORİN ----------------
    "fiat_egea": {
        "name": "Fiat Egea 1.3 Multijet",
        "brand": "Fiat",
        "fuel_type": "Motorin",
        "consumption": 4.3,
    },
    "renault_clio_dizel": {
        "name": "Renault Clio 1.5 dCi",
        "brand": "Renault",
        "fuel_type": "Motorin",
        "consumption": 4.2,
    },
    "renault_megane_dizel": {
        "name": "Renault Megane 1.5 dCi",
        "brand": "Renault",
        "fuel_type": "Motorin",
        "consumption": 4.6,
    },
    "vw_passat": {
        "name": "Volkswagen Passat 2.0 TDI",
        "brand": "Volkswagen",
        "fuel_type": "Motorin",
        "consumption": 5.2,
    },
    "vw_golf_dizel": {
        "name": "Volkswagen Golf 2.0 TDI",
        "brand": "Volkswagen",
        "fuel_type": "Motorin",
        "consumption": 5.0,
    },
    "skoda_octavia": {
        "name": "Skoda Octavia 2.0 TDI",
        "brand": "Skoda",
        "fuel_type": "Motorin",
        "consumption": 5.0,
    },
    "opel_astra_dizel": {
        "name": "Opel Astra 1.6 CDTi",
        "brand": "Opel",
        "fuel_type": "Motorin",
        "consumption": 4.8,
    },
    "ford_focus_dizel": {
        "name": "Ford Focus 1.5 TDCi",
        "brand": "Ford",
        "fuel_type": "Motorin",
        "consumption": 4.8,
    },
    "honda_civic_dizel": {
        "name": "Honda Civic 1.6 i-DTEC",
        "brand": "Honda",
        "fuel_type": "Motorin",
        "consumption": 4.9,
    },
    "peugeot_301": {
        "name": "Peugeot 301 1.6 BlueHDi",
        "brand": "Peugeot",
        "fuel_type": "Motorin",
        "consumption": 4.5,
    },
    "citroen_cehlysee": {
        "name": "Citroën C-Elysée 1.6 BlueHDi",
        "brand": "Citroën",
        "fuel_type": "Motorin",
        "consumption": 4.5,
    },
    "dacia_duster_dizel": {
        "name": "Dacia Duster 1.5 dCi",
        "brand": "Dacia",
        "fuel_type": "Motorin",
        "consumption": 5.0,
    },
    "nissan_qashqai_dizel": {
        "name": "Nissan Qashqai 1.5 dCi",
        "brand": "Nissan",
        "fuel_type": "Motorin",
        "consumption": 4.9,
    },
    "audi_a3_dizel": {
        "name": "Audi A3 30 TDI",
        "brand": "Audi",
        "fuel_type": "Motorin",
        "consumption": 4.7,
    },
    "bmw_320d": {
        "name": "BMW 320d",
        "brand": "BMW",
        "fuel_type": "Motorin",
        "consumption": 5.3,
    },
    "mercedes_c200d": {
        "name": "Mercedes-Benz C 200 d",
        "brand": "Mercedes-Benz",
        "fuel_type": "Motorin",
        "consumption": 5.4,
    },

    # ---------------- LPG (fabrika çıkışlı) ----------------
    "fiat_egea_lpg": {
        "name": "Fiat Egea 1.4 LPG",
        "brand": "Fiat",
        "fuel_type": "LPG",
        "consumption": 8.2,
    },
    "renault_clio_lpg": {
        "name": "Renault Clio 1.0 TCe LPG",
        "brand": "Renault",
        "fuel_type": "LPG",
        "consumption": 6.8,
    },
    "dacia_sandero_lpg": {
        "name": "Dacia Sandero 1.0 TCe LPG",
        "brand": "Dacia",
        "fuel_type": "LPG",
        "consumption": 6.9,
    },
    "hyundai_i20_lpg": {
        "name": "Hyundai i20 1.2 LPG",
        "brand": "Hyundai",
        "fuel_type": "LPG",
        "consumption": 7.0,
    },
    "hyundai_tucson_lpg": {
        "name": "Hyundai Tucson 1.6 TGI (LPG)",
        "brand": "Hyundai",
        "fuel_type": "LPG",
        "consumption": 7.6,
    },

    # ---------------- TİCARİ ----------------
    "fiat_doblo": {
        "name": "Fiat Doblo 1.3 Multijet",
        "brand": "Fiat",
        "fuel_type": "Motorin",
        "consumption": 5.4,
    },
    "renault_kangoo": {
        "name": "Renault Kangoo 1.5 dCi",
        "brand": "Renault",
        "fuel_type": "Motorin",
        "consumption": 5.4,
    },
    "vw_caddy": {
        "name": "Volkswagen Caddy 2.0 TDI",
        "brand": "Volkswagen",
        "fuel_type": "Motorin",
        "consumption": 5.8,
    },
    "ford_transit_custom": {
        "name": "Ford Transit Custom",
        "brand": "Ford",
        "fuel_type": "Motorin",
        "consumption": 7.8,
    },
    "ford_transit": {
        "name": "Ford Transit",
        "brand": "Ford",
        "fuel_type": "Motorin",
        "consumption": 8.8,
    },
    "mercedes_sprinter": {
        "name": "Mercedes-Benz Sprinter",
        "brand": "Mercedes-Benz",
        "fuel_type": "Motorin",
        "consumption": 9.2,
    },
    "mercedes_vito": {
        "name": "Mercedes-Benz Vito",
        "brand": "Mercedes-Benz",
        "fuel_type": "Motorin",
        "consumption": 7.4,
    },
}


def get_vehicles():
    return VEHICLES


def get_vehicle(vehicle_id: str):
    return VEHICLES.get(vehicle_id)

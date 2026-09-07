# Eksik marka/model tamamlandigi: yukaridaki VEHICLES/MOTORCYCLES'a
# vehicles.py icinde birlestirilir. Ayrintili aciklama vehicles.py basinda.

NEW_CARS = {
    # ---------------- ALFA ROMEO ----------------
    "alfa_giulietta": {"name": "Alfa Romeo Giulietta 1.4 TB", "brand": "Alfa Romeo", "fuel_type": "Benzin", "consumption": 6.8},
    "alfa_tonale_hybrid": {"name": "Alfa Romeo Tonale 1.5 Hybrid", "brand": "Alfa Romeo", "fuel_type": "Benzin", "consumption": 5.4},
    "alfa_stelvio": {"name": "Alfa Romeo Stelvio 2.0", "brand": "Alfa Romeo", "fuel_type": "Benzin", "consumption": 8.6},
    "alfa_giulia": {"name": "Alfa Romeo Giulia 2.0", "brand": "Alfa Romeo", "fuel_type": "Benzin", "consumption": 8.2},

    # ---------------- LEXUS ----------------
    "lexus_nx_350h": {"name": "Lexus NX 350h", "brand": "Lexus", "fuel_type": "Benzin", "consumption": 5.8},
    "lexus_ux_250h": {"name": "Lexus UX 250h", "brand": "Lexus", "fuel_type": "Benzin", "consumption": 5.0},
    "lexus_es_300h": {"name": "Lexus ES 300h", "brand": "Lexus", "fuel_type": "Benzin", "consumption": 5.2},
    "lexus_rx_500h": {"name": "Lexus RX 500h", "brand": "Lexus", "fuel_type": "Benzin", "consumption": 7.4},
    "lexus_rz_450e": {"name": "Lexus RZ 450e", "brand": "Lexus", "fuel_type": "Elektrik", "consumption": 17.5},

    # ---------------- LAND ROVER ----------------
    "landrover_defender_d250": {"name": "Land Rover Defender D250", "brand": "Land Rover", "fuel_type": "Dizel", "consumption": 8.9},
    "landrover_discovery_sport_d165": {"name": "Land Rover Discovery Sport D165", "brand": "Land Rover", "fuel_type": "Dizel", "consumption": 7.2},
    "landrover_range_evoque_p200": {"name": "Range Rover Evoque P200", "brand": "Land Rover", "fuel_type": "Benzin", "consumption": 8.4},
    "landrover_range_velar_p250": {"name": "Range Rover Velar P250", "brand": "Land Rover", "fuel_type": "Benzin", "consumption": 9.0},

    # ---------------- SSANGYONG / KGM ----------------
    "ssangyong_tivoli_1_5": {"name": "KGM Tivoli 1.5 TGDI", "brand": "SsangYong", "fuel_type": "Benzin", "consumption": 7.8},
    "ssangyong_korando_1_5": {"name": "KGM Korando 1.5 TGDI", "brand": "SsangYong", "fuel_type": "Benzin", "consumption": 8.0},
    "ssangyong_torres_1_5": {"name": "KGM Torres 1.5 TGDI", "brand": "SsangYong", "fuel_type": "Benzin", "consumption": 8.3},
    "ssangyong_musso_d202": {"name": "KGM Musso D202", "brand": "SsangYong", "fuel_type": "Dizel", "consumption": 8.5},
    "ssangyong_reator_s200": {"name": "KGM Rexton S200", "brand": "SsangYong", "fuel_type": "Dizel", "consumption": 9.2},

    # ---------------- ISUZU ----------------
    "isuzu_dmax_1_9": {"name": "Isuzu D-Max 1.9", "brand": "Isuzu", "fuel_type": "Dizel", "consumption": 7.8},
    "isuzu_dmax_1_9_4x4": {"name": "Isuzu D-Max 1.9 4x4", "brand": "Isuzu", "fuel_type": "Dizel", "consumption": 8.4},
    "isuzu_traga_panel": {"name": "Isuzu Traga Panelvan", "brand": "Isuzu", "fuel_type": "Dizel", "consumption": 9.5},

    # ---------------- CHERY ----------------
    "chery_tiggo_4_pro": {"name": "Chery Tiggo 4 Pro 1.5", "brand": "Chery", "fuel_type": "Benzin", "consumption": 7.3},
    "chery_tiggo_7_pro": {"name": "Chery Tiggo 7 Pro 1.6 TGDI", "brand": "Chery", "fuel_type": "Benzin", "consumption": 7.9},
    "chery_tiggo_8_pro": {"name": "Chery Tiggo 8 Pro 1.6 TGDI", "brand": "Chery", "fuel_type": "Benzin", "consumption": 8.4},
    "chery_arrizo_5": {"name": "Chery Arrizo 5 Plus 1.5", "brand": "Chery", "fuel_type": "Benzin", "consumption": 6.9},
    "chery_fulwin_a05": {"name": "Chery Fulwin A05 Hibrit", "brand": "Chery", "fuel_type": "Benzin", "consumption": 4.8},
    "chery_fulwin_t7": {"name": "Chery Fulwin T7 Hibrit", "brand": "Chery", "fuel_type": "Benzin", "consumption": 5.4},

    # ---------------- BYD ----------------
    "byd_dolphin": {"name": "BYD Dolphin", "brand": "BYD", "fuel_type": "Elektrik", "consumption": 16.8},
    "byd_atto_3": {"name": "BYD Atto 3", "brand": "BYD", "fuel_type": "Elektrik", "consumption": 17.5},
    "byd_seal_u": {"name": "BYD Seal U", "brand": "BYD", "fuel_type": "Elektrik", "consumption": 18.2},
    "byd_seal": {"name": "BYD Seal", "brand": "BYD", "fuel_type": "Elektrik", "consumption": 16.5},
    "byd_song_plus_hybrid": {"name": "BYD Song Plus DM-i", "brand": "BYD", "fuel_type": "Benzin", "consumption": 5.0},

    # ---------------- JAC ----------------
    "jac_e_js1": {"name": "JAC e-JS1", "brand": "JAC", "fuel_type": "Elektrik", "consumption": 14.8},
    "jac_e_js4": {"name": "JAC e-JS4", "brand": "JAC", "fuel_type": "Elektrik", "consumption": 16.2},
    "jac_js2_m3": {"name": "JAC JS2 M3", "brand": "JAC", "fuel_type": "Benzin", "consumption": 7.5},
    "jac_sunray_panel": {"name": "JAC Sunray Panelvan", "brand": "JAC", "fuel_type": "Dizel", "consumption": 10.5},

    # ---------------- MAXUS ----------------
    "maxus_t90ev": {"name": "Maxus T90EV Pikap", "brand": "Maxus", "fuel_type": "Elektrik", "consumption": 19.5},
    "maxus_e_deliver_3": {"name": "Maxus e-Deliver 3", "brand": "Maxus", "fuel_type": "Elektrik", "consumption": 21.0},
    "maxus_e_deliver_9": {"name": "Maxus e-Deliver 9", "brand": "Maxus", "fuel_type": "Elektrik", "consumption": 24.5},
    "maxus_mifa_9": {"name": "Maxus Mifa 9", "brand": "Maxus", "fuel_type": "Elektrik", "consumption": 21.5},
    "maxus_deliver_9_dizel": {"name": "Maxus Deliver 9", "brand": "Maxus", "fuel_type": "Dizel", "consumption": 9.8},

    # ---------------- FOTON ----------------
    "foton_tunland_v9": {"name": "Foton Tunland V9", "brand": "Foton", "fuel_type": "Dizel", "consumption": 8.9},
    "foton_aurajken": {"name": "Foton AuRAJKen Panelvan", "brand": "Foton", "fuel_type": "Dizel", "consumption": 9.8},
    "foton_esupernova": {"name": "Foton e-Supernova Panelvan", "brand": "Foton", "fuel_type": "Elektrik", "consumption": 23.0},
}

NEW_MOTORCYCLES = {
    # ---------------- APRILIA ----------------
    "aprilia_rs_457": {"name": "Aprilia RS 457", "brand": "Aprilia", "fuel_type": "Benzin", "consumption": 3.3},
    "aprilia_rs_660": {"name": "Aprilia RS 660", "brand": "Aprilia", "fuel_type": "Benzin", "consumption": 4.8},
    "aprilia_tuono_660": {"name": "Aprilia Tuono 660", "brand": "Aprilia", "fuel_type": "Benzin", "consumption": 5.0},
    "aprilia_sr_125": {"name": "Aprilia SR GT 125", "brand": "Aprilia", "fuel_type": "Benzin", "consumption": 2.6},
    "aprilia_sxr_160": {"name": "Aprilia SXR 160", "brand": "Aprilia", "fuel_type": "Benzin", "consumption": 2.4},

    # ---------------- BENELLI ----------------
    "benelli_leoncino_250": {"name": "Benelli Leoncino 250", "brand": "Benelli", "fuel_type": "Benzin", "consumption": 3.2},
    "benelli_tnt_135": {"name": "Benelli TNT 135", "brand": "Benelli", "fuel_type": "Benzin", "consumption": 2.3},
    "benelli_trk_251": {"name": "Benelli TRK 251", "brand": "Benelli", "fuel_type": "Benzin", "consumption": 3.1},
    "benelli_trk_502": {"name": "Benelli TRK 502", "brand": "Benelli", "fuel_type": "Benzin", "consumption": 4.9},
    "benelli_302s": {"name": "Benelli 302S", "brand": "Benelli", "fuel_type": "Benzin", "consumption": 3.9},
    "benelli_naked_tnt_125": {"name": "Benelli TNT 125", "brand": "Benelli", "fuel_type": "Benzin", "consumption": 2.2},

    # ---------------- TRIUMPH ----------------
    "triumph_speed_400": {"name": "Triumph Speed 400", "brand": "Triumph", "fuel_type": "Benzin", "consumption": 3.3},
    "triumph_scrambler_400x": {"name": "Triumph Scrambler 400 X", "brand": "Triumph", "fuel_type": "Benzin", "consumption": 3.4},
    "triumph_street_triple_765": {"name": "Triumph Street Triple 765", "brand": "Triumph", "fuel_type": "Benzin", "consumption": 5.0},
    "triumph_tiger_sport_660": {"name": "Triumph Tiger Sport 660", "brand": "Triumph", "fuel_type": "Benzin", "consumption": 4.7},
    "triumph_bonneville_t100": {"name": "Triumph Bonneville T100", "brand": "Triumph", "fuel_type": "Benzin", "consumption": 4.5},
    "triumph_rocket_3": {"name": "Triumph Rocket 3", "brand": "Triumph", "fuel_type": "Benzin", "consumption": 7.2},

    # ---------------- HUSQVARNA ----------------
    "husqvarna_svartpilen_250": {"name": "Husqvarna Svartpilen 250", "brand": "Husqvarna", "fuel_type": "Benzin", "consumption": 3.0},
    "husqvarna_svartpilen_401": {"name": "Husqvarna Svartpilen 401", "brand": "Husqvarna", "fuel_type": "Benzin", "consumption": 3.5},
    "husqvarna_vitpilen_401": {"name": "Husqvarna Vitpilen 401", "brand": "Husqvarna", "fuel_type": "Benzin", "consumption": 3.4},
    "husqvarna_norden_901": {"name": "Husqvarna Norden 901", "brand": "Husqvarna", "fuel_type": "Benzin", "consumption": 5.2},

    # ---------------- GASGAS ----------------
    "gasgas_es_700": {"name": "GasGas ES 700", "brand": "GasGas", "fuel_type": "Benzin", "consumption": 4.6},
    "gasgas_sm_700": {"name": "GasGas SM 700", "brand": "GasGas", "fuel_type": "Benzin", "consumption": 4.7},
    "gasgas_mc_125": {"name": "GasGas MC 125", "brand": "GasGas", "fuel_type": "Benzin", "consumption": 3.8},

    # ---------------- QJ MOTOR ----------------
    "qjmotor_srk_400": {"name": "QJ Motor SRK 400", "brand": "QJ Motor", "fuel_type": "Benzin", "consumption": 3.6},
    "qjmotor_srk_600": {"name": "QJ Motor SRK 600", "brand": "QJ Motor", "fuel_type": "Benzin", "consumption": 4.8},
    "qjmotor_srk_700": {"name": "QJ Motor SRK 700", "brand": "QJ Motor", "fuel_type": "Benzin", "consumption": 5.1},
    "qjmotor_scv_250": {"name": "QJ Motor SCV 250", "brand": "QJ Motor", "fuel_type": "Benzin", "consumption": 2.8},
    "qjmotor_moto_guzzi_v100": {"name": "QJ Motor V100S (Moto Guzzi)", "brand": "QJ Motor", "fuel_type": "Benzin", "consumption": 5.4},

    # ---------------- FANTIC ----------------
    "fantic_caballero_500": {"name": "Fantic Caballero 500", "brand": "Fantic", "fuel_type": "Benzin", "consumption": 3.9},
    "fantic_xef_125": {"name": "Fantic XEF 125", "brand": "Fantic", "fuel_type": "Benzin", "consumption": 2.9},
    "fantic_caballero_700": {"name": "Fantic Caballero 700", "brand": "Fantic", "fuel_type": "Benzin", "consumption": 4.6},
}

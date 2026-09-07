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

    # ---------------- RENAULT (ek) ----------------
    "renault_taliant_1_0": {"name": "Renault Taliant 1.0 TCe", "brand": "Renault", "fuel_type": "Benzin", "consumption": 5.9},
    "renault_taliant_dizel": {"name": "Renault Taliant 1.5 Blue dCi", "brand": "Renault", "fuel_type": "Dizel", "consumption": 4.6},
    "renault_megane_sedan_1_3": {"name": "Renault Megane Sedan 1.3 TCe", "brand": "Renault", "fuel_type": "Benzin", "consumption": 6.4},
    "renault_austral_hybrid": {"name": "Renault Austral Hybrid 200", "brand": "Renault", "fuel_type": "Benzin", "consumption": 5.0},
    "renault_kangoo_e": {"name": "Renault Kangoo E-Tech", "brand": "Renault", "fuel_type": "Elektrik", "consumption": 19.5},
    "renault_express": {"name": "Renault Express Van 1.5 Blue dCi", "brand": "Renault", "fuel_type": "Dizel", "consumption": 5.4},

    # ---------------- FIAT (ek) ----------------
    "fiat_fiorino_1_3": {"name": "Fiat Fiorino 1.3 Multijet", "brand": "Fiat", "fuel_type": "Dizel", "consumption": 4.9},
    "fiat_fiorino_1_4_lpg": {"name": "Fiat Fiorino 1.4 LPG", "brand": "Fiat", "fuel_type": "Benzin", "consumption": 6.8},
    "fiat_doblo_maxi": {"name": "Fiat Doblo Maxi 1.5 BlueHDi", "brand": "Fiat", "fuel_type": "Dizel", "consumption": 5.6},
    "fiat_ducato": {"name": "Fiat Ducato 2.2 Multijet", "brand": "Fiat", "fuel_type": "Dizel", "consumption": 8.8},
    "fiat_egea_sedan_1_4": {"name": "Fiat Egea Sedan 1.4 Fire", "brand": "Fiat", "fuel_type": "Benzin", "consumption": 6.3},
    "fiat_egea_1_6_multijet": {"name": "Fiat Egea 1.6 MultiJet", "brand": "Fiat", "fuel_type": "Dizel", "consumption": 4.8},
    "fiat_500_hybrid": {"name": "Fiat 500 1.0 Hybrid", "brand": "Fiat", "fuel_type": "Benzin", "consumption": 4.5},
    "fiat_panda_hybrid": {"name": "Fiat Panda 1.0 Hybrid", "brand": "Fiat", "fuel_type": "Benzin", "consumption": 4.8},

    # ---------------- TOYOTA (ek) ----------------
    "toyota_corolla_cross": {"name": "Toyota Corolla Cross 2.0 Hybrid", "brand": "Toyota", "fuel_type": "Benzin", "consumption": 5.1},
    "toyota_yaris_cross": {"name": "Toyota Yaris Cross 1.5 Hybrid", "brand": "Toyota", "fuel_type": "Benzin", "consumption": 4.5},
    "toyota_camry_hybrid": {"name": "Toyota Camry 2.5 Hybrid", "brand": "Toyota", "fuel_type": "Benzin", "consumption": 5.6},
    "toyota_proace_city": {"name": "Toyota Proace City 1.5 D-4D", "brand": "Toyota", "fuel_type": "Dizel", "consumption": 5.5},
    "toyota_proace_verso": {"name": "Toyota Proace Verso 2.0 D-4D", "brand": "Toyota", "fuel_type": "Dizel", "consumption": 7.0},
    "toyota_rav4_dizel": {"name": "Toyota RAV4 2.0 Valvematic", "brand": "Toyota", "fuel_type": "Benzin", "consumption": 7.4},
    "toyota_hilux_dizel_28": {"name": "Toyota Hilux 2.8 D-4D", "brand": "Toyota", "fuel_type": "Dizel", "consumption": 8.6},

    # ---------------- FORD (ek) ----------------
    "ford_focus_1_0": {"name": "Ford Focus 1.0 EcoBoost", "brand": "Ford", "fuel_type": "Benzin", "consumption": 6.0},
    "ford_tourneo_custom": {"name": "Ford Tourneo Custom 2.0 TDCi", "brand": "Ford", "fuel_type": "Dizel", "consumption": 7.6},
    "ford_kuga_fhev": {"name": "Ford Kuga 2.5 FHEV", "brand": "Ford", "fuel_type": "Benzin", "consumption": 5.6},
    "ford_ranger_raptor": {"name": "Ford Ranger Raptor 3.0 V6", "brand": "Ford", "fuel_type": "Dizel", "consumption": 10.5},
    "ford_transit_2_0": {"name": "Ford Transit 2.0 TDCi", "brand": "Ford", "fuel_type": "Dizel", "consumption": 8.4},

    # ---------------- HYUNDAI (ek) ----------------
    "hyundai_i30_1_4": {"name": "Hyundai i30 1.4 T-GDI", "brand": "Hyundai", "fuel_type": "Benzin", "consumption": 6.4},
    "hyundai_santa_fe": {"name": "Hyundai Santa Fe 2.2 CRDi", "brand": "Hyundai", "fuel_type": "Dizel", "consumption": 7.2},
    "hyundai_creta_1_5": {"name": "Hyundai Creta 1.5 MPI", "brand": "Hyundai", "fuel_type": "Benzin", "consumption": 7.0},
    "hyundai_ioniq_6": {"name": "Hyundai Ioniq 6", "brand": "Hyundai", "fuel_type": "Elektrik", "consumption": 14.8},
    "hyundai_elantra_hybrid": {"name": "Hyundai Elantra 1.6 HEV", "brand": "Hyundai", "fuel_type": "Benzin", "consumption": 4.9},
    "hyundai_bayon_1_0": {"name": "Hyundai Bayon 1.0 T-GDI", "brand": "Hyundai", "fuel_type": "Benzin", "consumption": 6.1},

    # ---------------- KIA (ek) ----------------
    "kia_sportage_hev": {"name": "Kia Sportage 1.6 HEV", "brand": "Kia", "fuel_type": "Benzin", "consumption": 5.4},
    "kia_sorento": {"name": "Kia Sorento 2.2 CRDi", "brand": "Kia", "fuel_type": "Dizel", "consumption": 7.4},
    "kia_ceed_sw": {"name": "Kia Ceed SW 1.6 CRDi", "brand": "Kia", "fuel_type": "Dizel", "consumption": 4.9},
    "kia_picanto_1_2": {"name": "Kia Picanto 1.2 MPI", "brand": "Kia", "fuel_type": "Benzin", "consumption": 5.5},
    "kia_ev9": {"name": "Kia EV9", "brand": "Kia", "fuel_type": "Elektrik", "consumption": 20.5},
    "kia_niro_hybrid": {"name": "Kia Niro 1.6 HEV", "brand": "Kia", "fuel_type": "Benzin", "consumption": 4.8},

    # ---------------- VOLKSWAGEN (ek) ----------------
    "vw_t_cross": {"name": "Volkswagen T-Cross 1.0 TSI", "brand": "Volkswagen", "fuel_type": "Benzin", "consumption": 5.7},
    "vw_taigo": {"name": "Volkswagen Taigo 1.0 TSI", "brand": "Volkswagen", "fuel_type": "Benzin", "consumption": 5.8},
    "vw_amarok": {"name": "Volkswagen Amarok 3.0 V6 TDI", "brand": "Volkswagen", "fuel_type": "Dizel", "consumption": 9.4},
    "vw_crafter": {"name": "Volkswagen Crafter 2.0 TDI", "brand": "Volkswagen", "fuel_type": "Dizel", "consumption": 8.8},
    "vw_id5": {"name": "Volkswagen ID.5", "brand": "Volkswagen", "fuel_type": "Elektrik", "consumption": 17.8},
    "vw_tiguan_allspace": {"name": "Volkswagen Tiguan Allspace 2.0 TDI", "brand": "Volkswagen", "fuel_type": "Dizel", "consumption": 6.9},
    "vw_tiguan_1_4_hybrid": {"name": "Volkswagen Tiguan 1.4 eHybrid", "brand": "Volkswagen", "fuel_type": "Benzin", "consumption": 5.5},

    # ---------------- PEUGEOT (ek) ----------------
    "peugeot_508_1_5": {"name": "Peugeot 508 1.5 BlueHDi", "brand": "Peugeot", "fuel_type": "Dizel", "consumption": 5.0},
    "peugeot_408_1_2": {"name": "Peugeot 408 1.2 PureTech", "brand": "Peugeot", "fuel_type": "Benzin", "consumption": 6.2},
    "peugeot_108_1_0": {"name": "Peugeot 108 1.0 VTi", "brand": "Peugeot", "fuel_type": "Benzin", "consumption": 4.7},
    "peugeot_5008_1_5": {"name": "Peugeot 5008 1.5 BlueHDi", "brand": "Peugeot", "fuel_type": "Dizel", "consumption": 5.6},
    "peugeot_rifter": {"name": "Peugeot Rifter 1.5 BlueHDi", "brand": "Peugeot", "fuel_type": "Dizel", "consumption": 5.5},
    "peugeot_boxer": {"name": "Peugeot Boxer 2.2 BlueHDi", "brand": "Peugeot", "fuel_type": "Dizel", "consumption": 9.0},
    "peugeot_e_2008": {"name": "Peugeot e-2008", "brand": "Peugeot", "fuel_type": "Elektrik", "consumption": 16.5},
    "peugeot_e_partner": {"name": "Peugeot e-Partner", "brand": "Peugeot", "fuel_type": "Elektrik", "consumption": 21.0},

    # ---------------- OPEL (ek) ----------------
    "opel_astra_1_5d": {"name": "Opel Astra 1.5 Diesel", "brand": "Opel", "fuel_type": "Dizel", "consumption": 4.7},
    "opel_combo_life": {"name": "Opel Combo Life 1.5 D", "brand": "Opel", "fuel_type": "Dizel", "consumption": 5.4},
    "opel_zafira_life": {"name": "Opel Zafira Life 2.0 D", "brand": "Opel", "fuel_type": "Dizel", "consumption": 7.0},
    "opel_corsa_e": {"name": "Opel Corsa Electric", "brand": "Opel", "fuel_type": "Elektrik", "consumption": 15.8},
    "opel_movano": {"name": "Opel Movano 2.3 CDTi", "brand": "Opel", "fuel_type": "Dizel", "consumption": 9.2},

    # ---------------- CITROEN (ek) ----------------
    "citroen_c3_aircross": {"name": "Citroën C3 Aircross 1.2 PureTech", "brand": "Citroën", "fuel_type": "Benzin", "consumption": 6.3},
    "citroen_c4_x": {"name": "Citroën C4 X 1.2 PureTech", "brand": "Citroën", "fuel_type": "Benzin", "consumption": 6.0},
    "citroen_jumpy": {"name": "Citroën Jumpy 1.5 BlueHDi", "brand": "Citroën", "fuel_type": "Dizel", "consumption": 6.5},
    "citroen_jumper": {"name": "Citroën Jumper 2.2 BlueHDi", "brand": "Citroën", "fuel_type": "Dizel", "consumption": 9.0},
    "citroen_c3_e": {"name": "Citroën ë-C3", "brand": "Citroën", "fuel_type": "Elektrik", "consumption": 15.5},

    # ---------------- SKODA (ek) ----------------
    "skoda_scala_1_5": {"name": "Skoda Scala 1.5 TSI", "brand": "Skoda", "fuel_type": "Benzin", "consumption": 5.8},
    "skoda_superb_1_5": {"name": "Skoda Superb 1.5 TSI", "brand": "Skoda", "fuel_type": "Benzin", "consumption": 6.4},
    "skoda_rapid_1_6": {"name": "Skoda Rapid 1.6 TDI", "brand": "Skoda", "fuel_type": "Dizel", "consumption": 4.7},
    "skoda_fabia_1_0_mpi": {"name": "Skoda Fabia 1.0 MPI", "brand": "Skoda", "fuel_type": "Benzin", "consumption": 5.6},
    "skoda_kodiaq_2_0": {"name": "Skoda Kodiaq 2.0 TDI", "brand": "Skoda", "fuel_type": "Dizel", "consumption": 6.5},
    "skoda_karoq_1_5": {"name": "Skoda Karoq 1.5 TSI", "brand": "Skoda", "fuel_type": "Benzin", "consumption": 6.6},

    # ---------------- SEAT (ek) ----------------
    "seat_tarraco": {"name": "Seat Tarraco 2.0 TDI", "brand": "Seat", "fuel_type": "Dizel", "consumption": 6.6},
    "seat_ibiza_1_0_mpi": {"name": "Seat Ibiza 1.0 MPI", "brand": "Seat", "fuel_type": "Benzin", "consumption": 5.6},
    "seat_ateca_1_6": {"name": "Seat Ateca 1.6 TDI", "brand": "Seat", "fuel_type": "Dizel", "consumption": 5.0},
    "seat_leon_1_0": {"name": "Seat Leon 1.0 TSI", "brand": "Seat", "fuel_type": "Benzin", "consumption": 5.5},

    # ---------------- AUDI (ek) ----------------
    "audi_a1_30": {"name": "Audi A1 30 TFSI", "brand": "Audi", "fuel_type": "Benzin", "consumption": 5.6},
    "audi_q2_35": {"name": "Audi Q2 35 TFSI", "brand": "Audi", "fuel_type": "Benzin", "consumption": 6.3},
    "audi_q5_40": {"name": "Audi Q5 40 TDI", "brand": "Audi", "fuel_type": "Dizel", "consumption": 6.2},
    "audi_q7_45": {"name": "Audi Q7 45 TDI", "brand": "Audi", "fuel_type": "Dizel", "consumption": 7.8},
    "audi_a6_40": {"name": "Audi A6 40 TDI", "brand": "Audi", "fuel_type": "Dizel", "consumption": 5.8},
    "audi_a5_40": {"name": "Audi A5 40 TFSI", "brand": "Audi", "fuel_type": "Benzin", "consumption": 6.9},
    "audi_etron_55": {"name": "Audi e-tron 55", "brand": "Audi", "fuel_type": "Elektrik", "consumption": 22.0},

    # ---------------- BMW (ek) ----------------
    "bmw_118i": {"name": "BMW 118i", "brand": "BMW", "fuel_type": "Benzin", "consumption": 6.2},
    "bmw_520i": {"name": "BMW 520i", "brand": "BMW", "fuel_type": "Benzin", "consumption": 6.8},
    "bmw_x2_18i": {"name": "BMW X2 sDrive18i", "brand": "BMW", "fuel_type": "Benzin", "consumption": 6.6},
    "bmw_x5_30d": {"name": "BMW X5 xDrive30d", "brand": "BMW", "fuel_type": "Dizel", "consumption": 7.9},
    "bmw_ix1": {"name": "BMW iX1 xDrive30", "brand": "BMW", "fuel_type": "Elektrik", "consumption": 17.5},
    "bmw_ix": {"name": "BMW iX xDrive50", "brand": "BMW", "fuel_type": "Elektrik", "consumption": 20.0},

    # ---------------- MERCEDES (ek) ----------------
    "mb_e200": {"name": "Mercedes-Benz E 200", "brand": "Mercedes-Benz", "fuel_type": "Benzin", "consumption": 7.2},
    "mb_e220d": {"name": "Mercedes-Benz E 220 d", "brand": "Mercedes-Benz", "fuel_type": "Dizel", "consumption": 5.5},
    "mb_glc_220d": {"name": "Mercedes-Benz GLC 220 d", "brand": "Mercedes-Benz", "fuel_type": "Dizel", "consumption": 6.5},
    "mb_gle_300d": {"name": "Mercedes-Benz GLE 300 d", "brand": "Mercedes-Benz", "fuel_type": "Dizel", "consumption": 7.4},
    "mb_b180": {"name": "Mercedes-Benz B 180", "brand": "Mercedes-Benz", "fuel_type": "Benzin", "consumption": 6.4},
    "mb_cla_180": {"name": "Mercedes-Benz CLA 180", "brand": "Mercedes-Benz", "fuel_type": "Benzin", "consumption": 6.2},
    "mb_eqb": {"name": "Mercedes-Benz EQB 300", "brand": "Mercedes-Benz", "fuel_type": "Elektrik", "consumption": 18.5},
    "mb_c180_w206": {"name": "Mercedes-Benz C 180 (Yeni)", "brand": "Mercedes-Benz", "fuel_type": "Benzin", "consumption": 6.7},

    # ---------------- HONDA (ek) ----------------
    "honda_civic_hev": {"name": "Honda Civic e:HEV", "brand": "Honda", "fuel_type": "Benzin", "consumption": 4.7},
    "honda_crv_hev": {"name": "Honda CR-V e:HEV", "brand": "Honda", "fuel_type": "Benzin", "consumption": 6.0},
    "honda_zrv_hev": {"name": "Honda ZR-V e:HEV", "brand": "Honda", "fuel_type": "Benzin", "consumption": 5.8},
    "honda_jazz_hev": {"name": "Honda Jazz e:HEV", "brand": "Honda", "fuel_type": "Benzin", "consumption": 4.5},
    "honda_civic_1_5t": {"name": "Honda Civic 1.5 VTEC Turbo", "brand": "Honda", "fuel_type": "Benzin", "consumption": 6.8},

    # ---------------- MAZDA (ek) ----------------
    "mazda_cx30": {"name": "Mazda CX-30 2.0 Skyactiv-G", "brand": "Mazda", "fuel_type": "Benzin", "consumption": 6.8},
    "mazda_cx60": {"name": "Mazda CX-60 3.3 Skyactiv-D", "brand": "Mazda", "fuel_type": "Dizel", "consumption": 5.8},
    "mazda_6": {"name": "Mazda 6 2.0 Skyactiv-G", "brand": "Mazda", "fuel_type": "Benzin", "consumption": 7.0},
    "mazda_mx5": {"name": "Mazda MX-5 2.0 Skyactiv-G", "brand": "Mazda", "fuel_type": "Benzin", "consumption": 7.4},

    # ---------------- VOLVO (ek) ----------------
    "volvo_xc60_b4": {"name": "Volvo XC60 B4", "brand": "Volvo", "fuel_type": "Dizel", "consumption": 6.2},
    "volvo_xc90_b5": {"name": "Volvo XC90 B5", "brand": "Volvo", "fuel_type": "Dizel", "consumption": 7.8},
    "volvo_c40": {"name": "Volvo C40 Recharge", "brand": "Volvo", "fuel_type": "Elektrik", "consumption": 18.8},
    "volvo_s60_b4": {"name": "Volvo S60 B4", "brand": "Volvo", "fuel_type": "Benzin", "consumption": 7.0},
    "volvo_xc40_b3": {"name": "Volvo XC40 B3", "brand": "Volvo", "fuel_type": "Benzin", "consumption": 7.4},

    # ---------------- SUZUKI (ek) ----------------
    "suzuki_ignis": {"name": "Suzuki Ignis 1.2 Hybrid", "brand": "Suzuki", "fuel_type": "Benzin", "consumption": 4.9},
    "suzuki_baleno": {"name": "Suzuki Baleno 1.2 Dualjet", "brand": "Suzuki", "fuel_type": "Benzin", "consumption": 5.2},
    "suzuki_vitara_hev": {"name": "Suzuki Vitara 1.5 Hybrid", "brand": "Suzuki", "fuel_type": "Benzin", "consumption": 5.4},
    "suzuki_swace": {"name": "Suzuki Swace 1.8 Hybrid", "brand": "Suzuki", "fuel_type": "Benzin", "consumption": 4.8},
    "suzuki_jimny_1_3": {"name": "Suzuki Jimny 1.3", "brand": "Suzuki", "fuel_type": "Benzin", "consumption": 7.6},

    # ---------------- NISSAN (ek) ----------------
    "nissan_qashqai_epower": {"name": "Nissan Qashqai e-POWER", "brand": "Nissan", "fuel_type": "Benzin", "consumption": 5.3},
    "nissan_xtrail_epower": {"name": "Nissan X-Trail e-POWER", "brand": "Nissan", "fuel_type": "Benzin", "consumption": 6.2},
    "nissan_juke_hybrid": {"name": "Nissan Juke Hybrid", "brand": "Nissan", "fuel_type": "Benzin", "consumption": 5.0},
    "nissan_townstar": {"name": "Nissan Townstar 1.3", "brand": "Nissan", "fuel_type": "Benzin", "consumption": 7.0},

    # ---------------- MITSUBISHI (ek) ----------------
    "mitsubishi_outlander_phev": {"name": "Mitsubishi Outlander PHEV", "brand": "Mitsubishi", "fuel_type": "Benzin", "consumption": 6.0},
    "mitsubishi_space_star": {"name": "Mitsubishi Space Star 1.2", "brand": "Mitsubishi", "fuel_type": "Benzin", "consumption": 5.2},

    # ---------------- JEEP (ek) ----------------
    "jeep_avenger": {"name": "Jeep Avenger 1.2 Turbo", "brand": "Jeep", "fuel_type": "Benzin", "consumption": 5.8},
    "jeep_avenger_e": {"name": "Jeep Avenger Electric", "brand": "Jeep", "fuel_type": "Elektrik", "consumption": 16.8},
    "jeep_wrangler_2_0": {"name": "Jeep Wrangler 2.0 Turbo", "brand": "Jeep", "fuel_type": "Benzin", "consumption": 9.8},
    "jeep_grand_cherokee": {"name": "Jeep Grand Cherokee 3.0 V6", "brand": "Jeep", "fuel_type": "Dizel", "consumption": 8.8},

    # ---------------- SUBARU ----------------
    "subaru_forester": {"name": "Subaru Forester 2.0 e-Boxer", "brand": "Subaru", "fuel_type": "Benzin", "consumption": 7.2},
    "subaru_crosstrek": {"name": "Subaru Crosstrek 2.0 e-Boxer", "brand": "Subaru", "fuel_type": "Benzin", "consumption": 7.0},
    "subaru_outback": {"name": "Subaru Outback 2.5", "brand": "Subaru", "fuel_type": "Benzin", "consumption": 8.4},

    # ---------------- MG (ek) ----------------
    "mg_zs_1_5": {"name": "MG ZS 1.5", "brand": "MG", "fuel_type": "Benzin", "consumption": 6.8},
    "mg_hs_1_5": {"name": "MG HS 1.5 T-GDI", "brand": "MG", "fuel_type": "Benzin", "consumption": 7.4},
    "mg_hs_hev": {"name": "MG HS PHEV", "brand": "MG", "fuel_type": "Benzin", "consumption": 6.2},
    "mg_zs_ev": {"name": "MG ZS EV", "brand": "MG", "fuel_type": "Elektrik", "consumption": 17.2},
    "mg5_ev": {"name": "MG 5 Electric Long Range", "brand": "MG", "fuel_type": "Elektrik", "consumption": 16.8},

    # ---------------- CUPRA (ek) ----------------
    "cupra_formentor_1_5": {"name": "Cupra Formentor 1.5 TSI", "brand": "Cupra", "fuel_type": "Benzin", "consumption": 7.0},
    "cupra_formentor_2_0": {"name": "Cupra Formentor 2.0 TSI", "brand": "Cupra", "fuel_type": "Benzin", "consumption": 8.4},
    "cupra_leon_1_5": {"name": "Cupra Leon 1.5 TSI", "brand": "Cupra", "fuel_type": "Benzin", "consumption": 6.4},
    "cupra_tavascan": {"name": "Cupra Tavascan", "brand": "Cupra", "fuel_type": "Elektrik", "consumption": 17.9},

    # ---------------- MINI (ek) ----------------
    "mini_cooper_s": {"name": "Mini Cooper S 2.0", "brand": "Mini", "fuel_type": "Benzin", "consumption": 6.6},
    "mini_countryman_c": {"name": "Mini Countryman C", "brand": "Mini", "fuel_type": "Benzin", "consumption": 7.0},
    "mini_cooper_e": {"name": "Mini Cooper Electric", "brand": "Mini", "fuel_type": "Elektrik", "consumption": 16.0},

    # ---------------- PORSCHE (ek) ----------------
    "porsche_macan": {"name": "Porsche Macan", "brand": "Porsche", "fuel_type": "Benzin", "consumption": 9.8},
    "porsche_macan_e": {"name": "Porsche Macan Electric", "brand": "Porsche", "fuel_type": "Elektrik", "consumption": 21.5},
    "porsche_cayenne": {"name": "Porsche Cayenne", "brand": "Porsche", "fuel_type": "Benzin", "consumption": 11.5},
    "porsche_911_carrera": {"name": "Porsche 911 Carrera", "brand": "Porsche", "fuel_type": "Benzin", "consumption": 10.2},

    # ---------------- LEXUS (ek) ----------------
    "lexus_is_300h": {"name": "Lexus IS 300h", "brand": "Lexus", "fuel_type": "Benzin", "consumption": 6.2},
    "lexus_ux_300e": {"name": "Lexus UX 300e", "brand": "Lexus", "fuel_type": "Elektrik", "consumption": 17.0},

    # ---------------- SMART (ek) ----------------
    "smart_1": {"name": "Smart #1", "brand": "Smart", "fuel_type": "Elektrik", "consumption": 17.8},
    "smart_3": {"name": "Smart #3", "brand": "Smart", "fuel_type": "Elektrik", "consumption": 17.5},
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

    # ---------------- YAMAHA (ek) ----------------
    "yamaha_mt_125": {"name": "Yamaha MT-125", "brand": "Yamaha", "fuel_type": "Benzin", "consumption": 2.6},
    "yamaha_yzf_r125": {"name": "Yamaha YZF-R125", "brand": "Yamaha", "fuel_type": "Benzin", "consumption": 2.5},
    "yamaha_xsr_900": {"name": "Yamaha XSR 900", "brand": "Yamaha", "fuel_type": "Benzin", "consumption": 4.9},

    # ---------------- HONDA (ek) ----------------
    "honda_adv_350": {"name": "Honda ADV 350", "brand": "Honda", "fuel_type": "Benzin", "consumption": 3.1},
    "honda_forza_350": {"name": "Honda Forza 350", "brand": "Honda", "fuel_type": "Benzin", "consumption": 3.0},
    "honda_cb_125f": {"name": "Honda CB 125F", "brand": "Honda", "fuel_type": "Benzin", "consumption": 1.9},
    "honda_cb_500x": {"name": "Honda CB 500X", "brand": "Honda", "fuel_type": "Benzin", "consumption": 3.5},
    "honda_rebel_500": {"name": "Honda Rebel 500", "brand": "Honda", "fuel_type": "Benzin", "consumption": 3.6},

    # ---------------- KAWASAKI (ek) ----------------
    "kawasaki_z900rs": {"name": "Kawasaki Z900RS", "brand": "Kawasaki", "fuel_type": "Benzin", "consumption": 5.2},
    "kawasaki_versys_1000": {"name": "Kawasaki Versys 1000", "brand": "Kawasaki", "fuel_type": "Benzin", "consumption": 5.8},
    "kawasaki_z125": {"name": "Kawasaki Z125", "brand": "Kawasaki", "fuel_type": "Benzin", "consumption": 2.1},

    # ---------------- SUZUKI (ek) ----------------
    "suzuki_sv650": {"name": "Suzuki SV650", "brand": "Suzuki", "fuel_type": "Benzin", "consumption": 4.2},
    "suzuki_dl1050": {"name": "Suzuki V-Strom 1050", "brand": "Suzuki", "fuel_type": "Benzin", "consumption": 5.0},
    "suzuki_gsx_s1000": {"name": "Suzuki GSX-S1000", "brand": "Suzuki", "fuel_type": "Benzin", "consumption": 5.5},

    # ---------------- BENELLI (ek) ----------------
    "benelli_leoncino_500": {"name": "Benelli Leoncino 500", "brand": "Benelli", "fuel_type": "Benzin", "consumption": 4.2},
    "benelli_bj_600": {"name": "Benelli TNT 600", "brand": "Benelli", "fuel_type": "Benzin", "consumption": 5.5},

    # ---------------- KTM (ek) ----------------
    "ktm_1390_super_duke": {"name": "KTM 1390 Super Duke R", "brand": "KTM", "fuel_type": "Benzin", "consumption": 6.0},
    "ktm_390_duke_yeni": {"name": "KTM 390 Duke (Yeni)", "brand": "KTM", "fuel_type": "Benzin", "consumption": 3.4},

    # ---------------- DUCATI (ek) ----------------
    "ducati_multistrada_v4": {"name": "Ducati Multistrada V4", "brand": "Ducati", "fuel_type": "Benzin", "consumption": 5.9},
    "ducati_panigale_v4": {"name": "Ducati Panigale V4", "brand": "Ducati", "fuel_type": "Benzin", "consumption": 6.4},

    # ---------------- ROYAL ENFIELD (ek) ----------------
    "royal_enfield_himalayan_450": {"name": "Royal Enfield Himalayan 450", "brand": "Royal Enfield", "fuel_type": "Benzin", "consumption": 3.4},
    "royal_enfield_shotgun_650": {"name": "Royal Enfield Shotgun 650", "brand": "Royal Enfield", "fuel_type": "Benzin", "consumption": 4.4},

    # ---------------- HARLEY-DAVIDSON (ek) ----------------
    "hd_sportster_s": {"name": "Harley-Davidson Sportster S", "brand": "Harley-Davidson", "fuel_type": "Benzin", "consumption": 5.4},
    "hd_nightster": {"name": "Harley-Davidson Nightster", "brand": "Harley-Davidson", "fuel_type": "Benzin", "consumption": 4.9},

    # ---------------- MONDIAL (ek) ----------------
    "mondial_smx_250": {"name": "Mondial SMX 250", "brand": "Mondial", "fuel_type": "Benzin", "consumption": 2.9},
    "mondial_superleggera_250": {"name": "Mondial Superleggera 250", "brand": "Mondial", "fuel_type": "Benzin", "consumption": 2.7},
}

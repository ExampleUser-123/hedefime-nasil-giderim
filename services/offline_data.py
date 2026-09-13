# -*- coding: utf-8 -*-
import gzip
import json
import os
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

_TURKISH_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def _normalize(city: str) -> str:
    return city.translate(_TURKISH_MAP).lower().strip()


def city_data_path(city: str) -> Optional[str]:
    """Şehir adına karşılık gelen transit veri dosyasını döndürür.

    Not: GTFS tabanlı sehirler (istanbul, izmir, antalya, adana, gaziantep,
    kocaeli, samsun, konya) zip paketidir; cevrimdisi indirme su asamada
    sadece hazir `_transit.json.gz` dosyalarini sunar.
    """
    norm = _normalize(city)
    p = os.path.join(DATA_DIR, f"{norm}_transit.json.gz")
    if os.path.exists(p):
        return p
    return None


def load_city_stops(city: str):
    """Bir şehrin tüm durak listesini JSON olarak döndürür."""
    path = city_data_path(city)
    if not path:
        return None

    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def list_offline_cities():
    """İndirilebilir tüm şehirleri listeler."""
    cities = []
    for fname in os.listdir(DATA_DIR):
        if fname.endswith("_transit.json.gz"):
            cities.append(fname.replace("_transit.json.gz", ""))
    return cities

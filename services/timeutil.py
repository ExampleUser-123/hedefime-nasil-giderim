"""Turkiye yerel saati (Europe/Istanbul) yardimcilari.

Kritik nokta: Render sunuculari UTC'de calisir. `datetime.now()` naive
olarak sistem yerel saatini verir; tarifeler ise Turkiye duvar saatine
goredir. Bu modul tum "simdi" hesaplarini tek noktada Istanbul'a sabitler.

- `now_tr()`: tz-aware Istanbul su ani.
- `as_tr(value)`: naive girdiyi SISTEM yerel saati sayip Istanbul'a cevirir
  (Render UTC -> +3 dogru; TR makinede +03 -> +03 etkisiz). Aware girdi
  `astimezone` ile cevrilir. Boylece cagiran taraf sunucu saat dilimini
  bilmek zorunda kalmaz.
- `to_iso_tr(value)`: API yanitlarindaki `computed_at` alani icin ISO metin.
"""

from __future__ import annotations

from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    ISTANBUL_TZ = ZoneInfo("Europe/Istanbul")
except Exception:  # pragma: no cover - zoneinfo her yerde var
    ISTANBUL_TZ = None


def now_tr() -> datetime:
    """Su anin Istanbul saat diliminde tz-aware karsiligi."""
    if ISTANBUL_TZ is None:
        return datetime.now()
    return datetime.now(ISTANBUL_TZ)


def as_tr(value: datetime | None) -> datetime:
    """Verilen ani Istanbul duvar saatine cevirir.

    Naive degerler sistem yerel saati kabul edilir (saf `datetime.now()`
    cagrilarinin dondurdugu gibi); aware degerler dogrudan cevrilir.
    """
    if value is None:
        return now_tr()
    if ISTANBUL_TZ is None:
        return value
    if value.tzinfo is None:
        local_tz = datetime.now().astimezone().tzinfo
        return value.replace(tzinfo=local_tz).astimezone(ISTANBUL_TZ)
    return value.astimezone(ISTANBUL_TZ)


def to_iso_tr(value: datetime | None = None) -> str:
    """API `computed_at` alani: saniye duyarlikli ISO Istanbul zamani."""
    return as_tr(value).isoformat(timespec="seconds")

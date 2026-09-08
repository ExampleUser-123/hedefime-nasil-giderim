"""Tahmini sefer saati motoru (GTFS olmayan iller için heuristik).

Gerçek zaman çizelgesi verisi olmayan hatlar için, hat numarası + şehir +
durak adına dayalı deterministik (pseudo-random) tahmini kalkış saatleri
üretir. Çıktıdaki "source": "tahmini" etiketi zorunludur — frontend
kullanıcıya bunun bir tahmin olduğunu göstermelidir.
"""

from __future__ import annotations

from datetime import datetime, timedelta

# Varsayılan hizmet penceresi (deterministik ofsetlerle kaydırılır)
FIRST_DEPARTURE_MIN = 6 * 60 + 15   # ~06:15
LAST_DEPARTURE_MIN = 23 * 60 + 30   # ~23:30

PREDICT_WINDOW_START = 6 * 60       # 06:00
PREDICT_WINDOW_END = 24 * 60        # 23:59:59 dahil olur

MAX_RESULTS = 3


def _hash_int(s: str) -> int:
    """Stable hash: PYTHONHASHSEED'den bağımsız deterministik değer."""
    h = 2166136261
    for ch in s.encode("utf-8"):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _base_headway(city: str, line_no: str) -> int:
    """Hat için temel sefer aralığı: 8-25 dk, deterministik."""
    return 8 + _hash_int(f"{city}|{line_no}|base") % 18


def _headway_multiplier(now_dt: datetime) -> float | None:
    """Saate göre aralık çarpanı; gece 01:00-05:59 için None (sefer yok)."""
    h = now_dt.hour
    if 1 <= h <= 5:
        return None
    if (6 <= h < 9) or (17 <= h < 20):
        return 0.8  # yoğun saatler: sık sefer
    if h >= 23:
        return 2.0  # gece: seyrek sefer
    return 1.0


def _is_weekend(now_dt: datetime) -> bool:
    return now_dt.weekday() >= 5


def _clamp_minutes(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def estimate_departures(
    city: str,
    line_no: str,
    stop_name: str,
    now_dt: datetime | None = None,
) -> list[dict]:
    """Sonraki 3 tahmini kalkışı döndürür.

    Dönüş: [{"time": "HH:MM", "source": "tahmini", "minutes_ahead": int}]
    Gece (01:00-05:59) veya pencere dışında boş liste döner.
    """
    if now_dt is None:
        now_dt = datetime.now()

    now_minutes = _clamp_minutes(now_dt)
    if not (PREDICT_WINDOW_START <= now_minutes <= PREDICT_WINDOW_END):
        return []

    mult = _headway_multiplier(now_dt)
    if mult is None:
        return []

    base = _base_headway(city, str(line_no))
    headway = max(1, round(base * mult * (1.1 if _is_weekend(now_dt) else 1.0)))

    # Durak konumu etkisi: bilinmeyen sıra yerine deterministik ±3 dk jitter
    jitter = (_hash_int(f"{city}|{line_no}|{stop_name}|jit") % 7) - 3

    first = FIRST_DEPARTURE_MIN + (_hash_int(f"{city}|{line_no}|first") % 21)
    last = LAST_DEPARTURE_MIN - (_hash_int(f"{city}|{line_no}|last") % 21)

    # İlk kalkıştan itibaren tüm seferleri üret, "şimdi"den sonrakileri seç
    offset = (now_minutes - first) % headway if now_minutes >= first else None
    candidates: list[int] = []
    if now_minutes >= first and offset is not None:
        t = now_minutes + max(1, headway - offset)  # bir sonraki sefer
        # jitter ile kaydırılmış ilk aday; jitter'ı sonrakilere de uygula
        t += jitter
        if t <= now_minutes:
            t += headway
        while t <= last and len(candidates) < MAX_RESULTS:
            if t > now_minutes:
                candidates.append(t)
            t += headway

    # Adaylar pencere dışına taşarsa (23:59 sonrası) düş
    candidates = [t for t in candidates if t <= PREDICT_WINDOW_END]

    return [
        {
            "time": f"{t // 60:02d}:{t % 60:02d}",
            "source": "tahmini",
            "minutes_ahead": t - now_minutes,
        }
        for t in candidates
    ]

"""
GTFS sefer zamanı motoru.

data/gtfs/{il}_gtfs.zip dosyalarından durak + hat bazında kalkış saatlerini
indeksler ve next_departures() ile sonraki kalkışları döner.

Tek public fonksiyon: next_departures(city, line_no, stop_name, lat, lon, now_dt)
"""

import io
import pickle
import zipfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GTFS_DIR = BASE_DIR / "data" / "gtfs"
CACHE_DIR = BASE_DIR / "data" / "gtfs_cache"

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Istanbul")
except Exception:  # pragma: no cover
    TZ = None


# ---------------------------------------------------------------- yardımcılar

def _norm(text) -> str:
    """Durak adı / hat no normalize: küçük harf, Türkçe sadeleştirme, boşluk tekilleştir."""
    if text is None:
        return ""
    s = str(text).strip().lower()
    s = s.replace("ı", "i").replace("İ", "i").replace("̇", "")
    for old, new in (("ş", "s"), ("ğ", "g"), ("ü", "u"), ("ö", "o"), ("ç", "c")):
        s = s.replace(old, new)
    return " ".join(s.split())


def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Metre cinsinden mesafe."""
    import math
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _parse_gtfs_time(value) -> int | None:
    """'HH:MM:SS' (H 24+ olabilir) -> saniye. Hata -> None."""
    try:
        parts = str(value).strip().split(":")
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2] if len(parts) > 2 else 0)
        return h * 3600 + m * 60 + s
    except Exception:
        return None


def _ibb_coord(value, deg_len: int) -> float | None:
    """'410.191.700.005.564' gibi IBB noktali koordinatini dereceye cevirir.

    deg_len: derece hane sayisi (lat=2, lon=3).
    """
    s = str(value).strip()
    if "." not in s:
        return None
    digits = s.replace(".", "")
    if not digits.isdigit() or len(digits) <= deg_len:
        return None
    try:
        return float(f"{digits[:deg_len]}.{digits[deg_len:]}")
    except ValueError:
        return None


def _sec_to_hhmm(sec) -> str:
    """Saniye -> 'HH:MM' (24+ saatler mod 24'e normalize)."""
    h = (sec // 3600) % 24
    m = (sec % 3600) // 60
    return f"{h:02d}:{m:02d}"


def _now_local(now_dt: datetime | None) -> datetime:
    if now_dt is None:
        return datetime.now(TZ) if TZ else datetime.now()
    if now_dt.tzinfo is None:
        return now_dt.replace(tzinfo=TZ) if TZ else now_dt
    return now_dt.astimezone(TZ) if TZ else now_dt


def _csv_rows(zf: zipfile.ZipFile, name: str):
    """Zip içindeki CSV'yi satır-sözlük olarak stream eder (encoding denemeli)."""
    info = None
    for cand in (name, name.lower(), f"google/{name}"):
        try:
            info = zf.getinfo(cand)
            break
        except KeyError:
            continue
    if info is None:
        return None
    raw = zf.open(info)
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            raw.seek(0)
            f = io.TextIOWrapper(raw, encoding=enc, errors="replace")
            first = f.readline().rstrip("\r\n")
            if not first:
                return None
            # Ayraç algıla: İBB gibi kaynaklarda ';' kullanılır
            delim = ";" if first.count(";") > first.count(",") else ","
            header = [h.strip().strip('"') for h in first.split(delim)]
            if not any(header):
                return None
            for line in f:
                line = line.rstrip("\r\n")
                if not line:
                    continue
                vals = next(__import__("csv").reader([line], delimiter=delim))
                if len(vals) < len(header):
                    vals += [""] * (len(header) - len(vals))
                yield dict(zip(header, vals))
            return
        except UnicodeDecodeError:
            continue
        finally:
            pass


# ---------------------------------------------------------------- indeksleme

def _build_index(city: str) -> dict:
    """
    Zip'i stream okuyup {(hat_norm, durak_norm): [(dep_sec, service_id, lat, lon), ...]}
    indeksi oluşturur.
    """
    zip_path = GTFS_DIR / f"{_norm(city)}_gtfs.zip"
    if not zip_path.exists():
        return {}

    stops = {}     # stop_id -> (name_norm, lat, lon)
    routes = {}    # route_id -> route_short_name_norm
    trips = {}     # trip_id -> (route_id, service_id)
    calendar = {}  # service_id -> {weekday: True}, tarih aralığı
    cal_dates_add = set()
    cal_dates_del = set()

    with zipfile.ZipFile(zip_path) as zf:
        for row in _csv_rows(zf, "stops.txt") or ():
            raw_lat = row.get("stop_lat") or ""
            raw_lon = row.get("stop_lon") or ""
            try:
                lat = float(raw_lat)
            except ValueError:
                lat = _ibb_coord(raw_lat, 2)
            try:
                lon = float(raw_lon)
            except ValueError:
                lon = _ibb_coord(raw_lon, 3)
            if lat is None or lon is None:
                continue
            sid = (row.get("stop_id") or "").strip()
            if sid:
                stops[sid] = (_norm(row.get("stop_name")), lat, lon)

        for row in _csv_rows(zf, "routes.txt") or ():
            rid = (row.get("route_id") or "").strip()
            if rid:
                routes[rid] = _norm(row.get("route_short_name") or row.get("route_long_name"))

        for row in _csv_rows(zf, "trips.txt") or ():
            tid = (row.get("trip_id") or "").strip()
            if tid:
                trips[tid] = ((row.get("route_id") or "").strip(),
                              (row.get("service_id") or "").strip())

        for row in _csv_rows(zf, "calendar.txt") or ():
            sid = (row.get("service_id") or "").strip()
            try:
                start = datetime.strptime(row.get("start_date", ""), "%Y%m%d").date()
                end = datetime.strptime(row.get("end_date", ""), "%Y%m%d").date()
            except ValueError:
                continue
            days = {d: row.get(d) == "1" for d in
                    ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")}
            calendar[sid] = (start, end, days)

        for row in _csv_rows(zf, "calendar_dates.txt") or ():
            try:
                d = datetime.strptime(row.get("date", ""), "%Y%m%d").date()
            except ValueError:
                continue
            sid = (row.get("service_id") or "").strip()
            if row.get("exception_type") == "1":
                cal_dates_add.add((sid, d))
            else:
                cal_dates_del.add((sid, d))

        # stop_times.txt: en büyük dosya, stream
        index = {}
        for row in _csv_rows(zf, "stop_times.txt") or ():
            tid = (row.get("trip_id") or "").strip()
            trip = trips.get(tid)
            if not trip:
                continue
            rid, service_id = trip
            route = routes.get(rid)
            if not route:
                continue
            dep = _parse_gtfs_time(row.get("departure_time"))
            if dep is None:
                continue
            stop = stops.get((row.get("stop_id") or "").strip())
            if not stop:
                continue
            name_n, lat, lon = stop
            index.setdefault((route, name_n), []).append((dep, service_id, lat, lon))

    for entries in index.values():
        entries.sort(key=lambda e: e[0])

    index["_meta"] = {"calendar": calendar, "add": cal_dates_add, "del": cal_dates_del}
    return index


def _load_index(city: str) -> dict:
    """Cache'den oku, yoksa kur ve pkl'a yaz."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{_norm(city)}.pkl"
    if cache_file.exists():
        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    index = _build_index(city)
    try:
        with open(cache_file, "wb") as f:
            pickle.dump(index, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass
    return index


# ---------------------------------------------------------------- public API

def next_departures(city: str, line_no: str, stop_name: str, lat: float, lon: float,
                    now_dt: datetime | None = None) -> list[dict]:
    """
    Verilen durak + hat için şimdi/sonraki 3 kalkış.

    Dönüş: [{"time": "HH:MM", "source": "gtfs", "minutes_ahead": int}]
    Veri yoksa [].
    """
    try:
        index = _load_index(city)
        meta = index.get("_meta") or {}
        if not meta or not line_no:
            return []

        now = _now_local(now_dt)
        today = now.date()
        now_sec = now.hour * 3600 + now.minute * 60 + now.second

        # Bugün aktif servisler (basit yaklaşım)
        weekday = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")[today.weekday()]
        active = set()
        for sid, (start, end, days) in meta["calendar"].items():
            if start <= today <= end and days.get(weekday):
                active.add(sid)
        for sid, d in meta["add"]:
            if d == today:
                active.add(sid)
        for sid, d in meta["del"]:
            if d == today:
                active.discard(sid)

        # Bayat besleme gevşetmesi: takvim aralıklarının TAMAMI geçmişse
        # (besleme güncellenmemişse) gün filtrelemeyi atla — sefer saatleri
        # yine gerçek takvimden gelir, etiket 'gtfs' kalır.
        if not active and meta["calendar"]:
            today_ord = today.toordinal()
            if all(end.toordinal() < today_ord for _, end, _d in meta["calendar"].values()):
                active = set(meta["calendar"].keys())
                for sid, d in meta["del"]:
                    if d == today:
                        active.discard(sid)

        route_n = _norm(line_no)
        stop_n = _norm(stop_name)

        entries = None
        for (r, s), lst in index.items():
            if r == "_meta":
                continue
            if r == route_n and (s == stop_n or (not stop_n)):
                entries = lst
                break

        if entries is None:
            return []

        # Koordinat: 150m içinde bir durak varsa sadece onlar; yoksa gevşek (ad eşleşmesi)
        coord_entries = [e for e in entries
                         if _haversine(lat, lon, e[2], e[3]) <= 150.0]
        use = coord_entries if coord_entries else entries

        out = []
        seen = set()
        for dep, service_id, _la, _lo in use:
            if dep < now_sec:
                continue
            if service_id not in active:
                continue
            hhmm = _sec_to_hhmm(dep)
            key = (hhmm, dep // 60)
            if key in seen:
                continue
            seen.add(key)
            out.append({"time": hhmm, "source": "gtfs",
                        "minutes_ahead": max(0, dep // 60 - now_sec // 60)})
            if len(out) >= 3:
                break
        return out
    except Exception:
        return []

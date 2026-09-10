"""Kullanici "bu bilgi yanlis" bildirimleri: data/reports.json"""
import json
import os
import threading
import time

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_PATH = os.path.join(_DATA_DIR, "reports.json")
_lock = threading.Lock()
MAX_REPORTS = 2000


def _load() -> list:
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _save(reports: list) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    tmp = _PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _PATH)


def add_report(message: str, context: str | None = None) -> dict:
    entry = {
        "id": int(time.time() * 1000),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": (message or "")[:500],
        "context": (context or "")[:200],
    }

    with _lock:
        reports = _load()
        reports.append(entry)
        if len(reports) > MAX_REPORTS:
            reports = reports[-MAX_REPORTS:]
        _save(reports)

    return entry


def list_reports(limit: int = 100) -> list:
    with _lock:
        reports = _load()
    return list(reversed(reports[-max(1, min(limit, MAX_REPORTS)):]))

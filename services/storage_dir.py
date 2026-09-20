"""Ortam duyarli yazilabilir veri dizini.

Vercel Serverless'ta proje dosyalari salt-okunurdur; `data/` altina yazmak
OSError verip 500'e yol acar. Vercel algilanirsa (`VERCEL` env) yazmalar
isletim sisteminin gecici dizinine (`/tmp/hng-data`) yonlendirilir
(sicak instance suresince calisir, kalici degildir).
Diger ortamlarda (Render/lokal) repo icindeki `data/` kullanilir.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def is_vercel() -> bool:
    return bool(os.getenv("VERCEL"))


def writable_base_dir() -> Path:
    """Yazilabilir kok dizin (Vercel'de /tmp/hng-data, digerinde repo/data)."""
    if is_vercel():
        path = Path(tempfile.gettempdir()) / "hng-data"
    else:
        path = _REPO_ROOT / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def writable_subdir(name: str) -> str:
    """Yazilabilir alt dizin (olusturulur); dosya yolu kurmak icin str doner."""
    path = writable_base_dir() / name
    path.mkdir(parents=True, exist_ok=True)
    return str(path)

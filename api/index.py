"""Vercel Serverless Python giris noktasi.

Resmi Vercel mimarisi: `vercel.json` tum istekleri buraya yonlendirir.
Tum uygulama mantigi kokteki `main.py`'dedir (Render + testler onu kullanir);
burasi yalnizca `app` objesini disa aktarir, kopya mantik barindirmaz.
"""

from main import app  # noqa: F401

__all__ = ["app"]

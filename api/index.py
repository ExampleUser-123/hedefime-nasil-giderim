"""Vercel Serverless Python giris noktasi.

Resmi Vercel mimarisi: `vercel.json` tum istekleri buraya yonlendirir.
Tum uygulama mantigi kokteki `main.py`'dedir (Render + testler onu kullanir);
burasi yalnizca `app` objesini disa aktarir, kopya mantik barindirmaz.

Neden dosya-yolu ile yukleme: Vercel function calisma dizininde proje koku
her zaman `sys.path`'te olmayabilir; `from main import app` o durumda
ModuleNotFoundError verip "could not import" hatasina yol acar. Asagidaki
yapi kok dizini kendisi ekler ve `main.py`'yi mutlak yoldan yukler; ayni
dosya yerelde de sorunsuz calisir.
"""

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_spec = importlib.util.spec_from_file_location("main", _ROOT / "main.py")
_main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_main)

app = _main.app

__all__ = ["app"]

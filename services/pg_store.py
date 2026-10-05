"""Postgres destekli kullanici deposu (Vercel/Render kaliciligi).

Durum: Vercel sunucusuz dosya sistemi (`/tmp`) soguk baslatmada silinir;
dosya tabanli `user_store` bu yuzden kayitlari kaybeder. `DATABASE_URL`
tanimliysa (Supabase / Neon / Vercel Postgres) kullanici kayitlari burada
tutulur ve deploy/restart sonrasi SIFIRLANMAZ.

Tasarim: `user_store._load/_save` ile AYNI sozlesme (id -> user dict).
Tum tablo tek transaction'da degistirilir; dosya surumuyle davranis
birebirdir. `DATABASE_URL` yoksa bu modul hic devreye girmez (psycopg
kurulu olmasa bile import guvenlidir).
"""

from __future__ import annotations

import json
import os

_TABLE = "hng_users"
_schema_ready = False


def pg_enabled() -> bool:
    """Postgres deposu aktif mi (DATABASE_URL tanimli mi)?"""
    return bool((os.getenv("DATABASE_URL") or "").strip())


def _connect():
    """Kisa omurlu baglanti (serverless uyumlu; her islemde ac/kapat)."""
    import psycopg  # gec import: dosya modunda pakete gerek yok

    return psycopg.connect(
        os.getenv("DATABASE_URL", "").strip(),
        connect_timeout=10,
    )


def _ensure_schema(conn) -> None:
    global _schema_ready
    if _schema_ready:
        return
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {_TABLE} (
            id TEXT PRIMARY KEY,
            email TEXT,
            data JSONB NOT NULL DEFAULT '{{}}'
        )
        """
    )
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS {_TABLE}_email_idx ON {_TABLE} (email)"
    )
    conn.commit()
    _schema_ready = True


def pg_load_all() -> dict:
    """Tum kullanicilar: {id: user_dict} (dosya _load ile ayni sekil)."""
    conn = _connect()
    try:
        _ensure_schema(conn)
        rows = conn.execute(f"SELECT id, email, data FROM {_TABLE}").fetchall()
    finally:
        conn.close()
    users: dict = {}
    for uid, email, data in rows:
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                continue
        if not isinstance(data, dict):
            continue
        row = dict(data)
        row.setdefault("id", uid)
        if email and not row.get("email"):
            row["email"] = email
        users[str(uid)] = row
    return users


def pg_save_all(users: dict) -> None:
    """Tum tabloyu tek transaction'da degistirir (silinenler dahil)."""
    conn = _connect()
    try:
        _ensure_schema(conn)
        with conn.transaction():
            conn.execute(f"DELETE FROM {_TABLE}")
            for uid, user in (users or {}).items():
                data = dict(user) if isinstance(user, dict) else {}
                data["id"] = str(uid)
                email = data.get("email") if isinstance(data.get("email"), str) else None
                conn.execute(
                    f"INSERT INTO {_TABLE} (id, email, data) VALUES (%s, %s, %s)",
                    (str(uid), email, json.dumps(data, ensure_ascii=False)),
                )
    finally:
        conn.close()

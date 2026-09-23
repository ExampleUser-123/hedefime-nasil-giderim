"""Kullanici + favori deposu (JSON dosya, chat_store ile ayni yaklasim).

NOT: Render free tier'da dosya sistemi deploy/restart'larda sifirlanir.
Bu, mevcut chat_sessions davranisiyla aynidir; ileride ucretsiz bir
Postgres'e (orn. Supabase) tasinabilir.
"""

import os
import json
import hashlib
import hmac
import threading
import uuid
from datetime import datetime, timedelta

from .crypto_store import encrypt_data, decrypt_data
from .storage_dir import writable_base_dir


def _data_dir():
    return str(writable_base_dir())


DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)

USERS_FILE = os.path.join(_data_dir(), "users.json")
ENC_USERS_FILE = os.path.join(_data_dir(), "users.enc.db")

MAX_FAVORITES = 50

_lock = threading.Lock()


def _ensure_dir():
    os.makedirs(_data_dir(), exist_ok=True)


def _load() -> dict:
    if os.path.exists(ENC_USERS_FILE):
        try:
            with open(ENC_USERS_FILE, "rb") as f:
                encrypted = f.read()
            raw = decrypt_data(encrypted).decode("utf-8")
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            # Baska anahtarla yazilmis (orn. ephemeral sonrasi restart) ya da
            # bozuk dosya uygulamayi kilitlemesin: yedege tasinip bos baslanir.
            import logging as _logging
            import time as _time
            backup = ENC_USERS_FILE + f".corrupt-{int(_time.time())}"
            try:
                os.replace(ENC_USERS_FILE, backup)
            except OSError:
                backup = "(yedekleme basarisiz)"
            _logging.getLogger("user_store").error(
                "Sifreli kullanici deposu okunamadi (%s); %s konumuna "
                "yedeklendi, bos depoyla devam ediliyor.",
                exc, backup,
            )
            return {}

    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {}

        # Eski duz metin deposunu ilk yazmada sifreli formata tasiriz.
        return data

    except (json.JSONDecodeError, OSError):
        return {}


def _save(users: dict):
    _ensure_dir()

    serialized = json.dumps(users, ensure_ascii=False)

    # AES-256-GCM sifreli tek depo. Duz metin yedegi parola hash'leri ve
    # e-posta adreslerini diske acikta birakacagindan tutulmaz.
    enc_bytes = encrypt_data(serialized.encode("utf-8"))
    tmp_enc = ENC_USERS_FILE + ".tmp"
    with open(tmp_enc, "wb") as f:
        f.write(enc_bytes)
    os.replace(tmp_enc, ENC_USERS_FILE)

    # Onceki surumlerden kalan duz metin depoyu ancak sifreli yazma
    # basariyla tamamlandiktan sonra kaldir.
    if os.path.exists(USERS_FILE):
        os.remove(USERS_FILE)


def upsert_google_user(payload: dict) -> dict:
    """Google payload'indaki kullaniciyi kaydeder/gunceller; user dict doner."""

    user_id = payload["sub"]
    now = datetime.now().isoformat(timespec="seconds")

    with _lock:
        users = _load()

        user = users.get(user_id) or {
            "id": user_id,
            "created_at": now,
            "favorites": [],
            "ai_request_count": 0,
            "is_verified": True,
        }

        user.update({
            "email": payload.get("email"),
            "name": payload.get("name") or "Kullanici",
            "picture": payload.get("picture"),
            "last_login": now,
            "is_verified": True,
        })

        users[user_id] = user
        _save(users)

    return user


def find_user_by_email(email: str) -> dict | None:
    """E-posta ile kullanici arar (e-posta kayitli kullanicilar icin)."""

    email_norm = (email or "").strip().lower()

    if not email_norm:
        return None

    for user in _load().values():
        if (user.get("email") or "").strip().lower() == email_norm:
            return user

    return None


def upsert_email_user(email: str, name: str, password_hash: str, salt: str, is_verified: bool = False) -> dict:
    """E-posta+sifre ile kullanici kaydeder/gunceller; user dict doner."""

    email_norm = email.strip().lower()
    now = datetime.now().isoformat(timespec="seconds")

    with _lock:
        users = _load()

        user = find_user_by_email(email_norm)

        if user is None:
            user_id = "em_" + uuid.uuid4().hex[:16]
            user = {
                "id": user_id,
                "created_at": now,
                "favorites": [],
                "ai_request_count": 0,
                "is_verified": is_verified,
            }
        else:
            user = users.get(user["id"]) or user

        user.update({
            "email": email_norm,
            "name": name or email_norm.split("@")[0],
            "provider": "email",
            "password_hash": password_hash,
            "salt": salt,
            "last_login": now,
        })
        if "is_verified" not in user:
            user["is_verified"] = is_verified

        users[user["id"]] = user
        _save(users)

    return user


def set_verification_code(user_id: str, code: str) -> None:
    """Kullanici icin 15 dakika gecerli 6 haneli dogrulama kodu saklar."""
    now = datetime.now()
    expires_at = (now + timedelta(minutes=15)).isoformat(timespec="seconds")
    now_iso = now.isoformat(timespec="seconds")

    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is not None:
            # OTP'yi duz metin saklama; calinan depoda tekrar kullanilamasin.
            user["verification_code_hash"] = hashlib.sha256(
                str(code).strip().encode("utf-8")
            ).hexdigest()
            user.pop("verification_code", None)
            user["verification_expires_at"] = expires_at
            user["verification_attempts"] = 0
            user["last_code_sent_at"] = now_iso
            users[user_id] = user
            _save(users)


def verify_user_code(email: str, code: str, ignore_verified: bool = False) -> tuple[bool, str, dict | None]:
    """Kullanicinin girdigi dogrulama kodunu denetler.

    ignore_verified: sifre sifirlama gibi akislar icin (kullanici zaten
    dogrulanmis olabilir); kod kontrolu yine de zorunludur.
    """
    email_norm = (email or "").strip().lower()
    code_norm = (code or "").strip()
    now_iso = datetime.now().isoformat(timespec="seconds")

    with _lock:
        users = _load()
        user = None
        for u in users.values():
            if (u.get("email") or "").strip().lower() == email_norm:
                user = u
                break

        if not user:
            return False, "Kayıtlı kullanıcı bulunamadı.", None

        if user.get("is_verified") and not ignore_verified:
            # Guvenlik: dogrulanmis hesaba kod kontrolsuz token uretilmesin.
            # (Aksi halde e-postayi bilen herkes sifresiz oturum acabilirdi.)
            return False, "E-posta adresi zaten doğrulanmış. Lütfen giriş yapın.", None

        stored_code_hash = user.get("verification_code_hash")
        expires_at = user.get("verification_expires_at")
        attempts = int(user.get("verification_attempts") or 0)

        if not stored_code_hash:
            return False, "Aktif bir doğrulama kodu bulunamadı. Lütfen yeni kod isteyin.", None

        if expires_at and now_iso > expires_at:
            return False, "Doğrulama kodunun süresi dolmuş. Lütfen 'Tekrar Kod Gönder'e tıklayın.", None

        if attempts >= 5:
            return False, "Çok fazla hatalı kod denemesi yapıldı. Lütfen yeni kod isteyin.", None

        provided_hash = hashlib.sha256(code_norm.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(str(stored_code_hash), provided_hash):
            user["verification_attempts"] = attempts + 1
            users[user["id"]] = user
            _save(users)
            remaining = 5 - (attempts + 1)
            return False, f"Hatalı doğrulama kodu. Kalan deneme hakkı: {remaining}", None

        # Doğrulama başarılı!
        user["is_verified"] = True
        user["verification_code_hash"] = None
        user["verification_expires_at"] = None
        user["verification_attempts"] = 0
        users[user["id"]] = user
        _save(users)
        return True, "E-posta başarıyla doğrulandı.", user


def can_resend_code(email: str) -> tuple[bool, str, dict | None]:
    """Yeni kod gonderme limiti (60 sn bekleme)."""
    email_norm = (email or "").strip().lower()
    now = datetime.now()

    with _lock:
        users = _load()
        user = None
        for u in users.values():
            if (u.get("email") or "").strip().lower() == email_norm:
                user = u
                break

        if not user:
            return False, "Kullanıcı bulunamadı.", None

        if user.get("is_verified"):
            return False, "E-posta adresi zaten doğrulanmış.", user

        last_sent = user.get("last_code_sent_at")
        if last_sent:
            try:
                last_dt = datetime.fromisoformat(last_sent)
                diff = (now - last_dt).total_seconds()
                if diff < 60:
                    wait_sec = int(60 - diff)
                    return False, f"Yeni kod istemek için lütfen {wait_sec} saniye bekleyin.", None
            except Exception:
                pass

        return True, "", user


def is_user_verified(user: dict | None) -> bool:
    """Kullanicinin e-postasinin dogrulanip dogrulanmadigini kontrol eder."""
    if not user:
        return False
    return bool(user.get("is_verified", False))


def set_verified(user_id: str) -> dict | None:
    """E-postayi dogrulanmis isaretler (mailer kapali ortamlarda kayit akisi)."""

    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is None:
            return None
        user["is_verified"] = True
        user["verification_code_hash"] = None
        user["verification_expires_at"] = None
        user["verification_attempts"] = 0
        users[user_id] = user
        _save(users)
        return user


def set_password(user_id: str, password_hash: str, salt: str) -> dict | None:
    """Sifreyi hash'li sekilde gunceller (sifre sifirlama akisi)."""

    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is None:
            return None
        user["password_hash"] = password_hash
        user["salt"] = salt
        users[user_id] = user
        _save(users)
        return user



def touch_last_login(user_id: str) -> None:
    """Giris anini kaydeder (hata durumunda sessizce gecer)."""

    try:
        with _lock:
            users = _load()
            user = users.get(user_id)

            if user is not None:
                user["last_login"] = datetime.now().isoformat(timespec="seconds")
                _save(users)
    except Exception:
        pass


def get_user(user_id: str) -> dict | None:
    users = _load()
    return users.get(user_id)


def set_pending_invite(user_id: str, referrer_id: str) -> None:
    """Davet kodunu bekleyen olarak isaretler (dogrulamada odullendirilir)."""

    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is None:
            return
        user["pending_invite"] = referrer_id
        _save(users)


def take_pending_invite(user_id: str) -> str | None:
    """Bekleyen daveti tek seferlik alir (okuyup temizler)."""

    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is None:
            return None
        code = user.pop("pending_invite", None)
        _save(users)
        return code or None


def delete_user(user_id: str) -> bool:
    """Kullanici kaydini (favoriler dahil) tamamen siler. Varsa True doner."""

    with _lock:
        users = _load()
        if user_id not in users:
            return False
        del users[user_id]
        _save(users)
        return True


def set_tier(user_id: str, tier: str) -> dict | None:
    """Uyelik katmanini gunceller (free/lite/premium). Admin kullanimi icin."""

    if tier not in ("free", "lite", "premium"):
        return None

    with _lock:
        users = _load()
        user = users.get(user_id)

        if user is None:
            return None

        user["tier"] = tier
        _save(users)
        return user


def get_tier(user: dict | None) -> str:
    """Kullanicinin uyelik katmani (varsayilan free).

    XP Store'dan alinmis gunluk Lite denemesi suruyorsa lite doner.
    """
    if not user:
        return "free"
    perks = user.get("perks") or {}
    lite_until = perks.get("lite_until") or ""
    try:
        if lite_until and lite_until >= datetime.now().isoformat(timespec="seconds")[:10]:
            return "lite"
    except Exception:
        pass
    t = user.get("tier") or "free"
    return t if t in ("free", "lite", "premium") else "free"


def get_perks(user_id: str) -> dict:
    """XP Store haklari: {bonus_routes, bonus_ai, bonus_magic,
    vibe_unlock, lite_until}. Yoksa sifir degerler."""

    user = get_user(user_id) or {}
    perks = (user.get("perks") or {})
    return {
        "bonus_routes": int(perks.get("bonus_routes", 0) or 0),
        "bonus_ai": int(perks.get("bonus_ai", 0) or 0),
        "bonus_magic": int(perks.get("bonus_magic", 0) or 0),
        "vibe_unlock": bool(perks.get("vibe_unlock", False)),
        "lite_until": perks.get("lite_until") or "",
        "night_alert": bool(perks.get("night_alert", False)),
        "offline_pack": bool(perks.get("offline_pack", False)),
        "unlimited_routes_until": perks.get("unlimited_routes_until") or "",
    }


def grant_perk(user_id: str, key: str, value) -> dict | None:
    """Tekil hak tanimlar (vibe_unlock / lite_until); guncel perks doner."""

    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is None:
            return None
        perks = user.setdefault("perks", {})
        perks[key] = value
        _save(users)
        return get_perks(user_id)


def add_bonus(user_id: str, kind: str, amount: int) -> dict | None:
    """Bonus kullanim hakki ekler (bonus_routes/ai/magic)."""

    if kind not in ("bonus_routes", "bonus_ai", "bonus_magic"):
        return None
    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is None:
            return None
        perks = user.setdefault("perks", {})
        perks[kind] = int(perks.get(kind, 0) or 0) + max(0, int(amount or 0))
        _save(users)
        return get_perks(user_id)


def get_or_create_invite_code(user_id: str) -> str | None:
    """Kullanicinin davet kodunu dondurur (yoksa uretir, benzersiz)."""

    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is None:
            return None
        code = (user.get("invite_code") or "").strip()
        if code:
            return code
        taken = {str(u.get("invite_code") or "") for u in users.values()}
        for _ in range(20):
            code = uuid.uuid4().hex[:8]
            if code not in taken:
                break
        user["invite_code"] = code
        _save(users)
        return code


def find_user_by_invite(code: str) -> dict | None:
    """Davet kodundan kullanici bulur."""

    code = (code or "").strip().lower()
    if not code:
        return None
    for user in _load().values():
        if str(user.get("invite_code") or "").strip().lower() == code:
            return user
    return None


def record_referral(referrer_id: str, new_user_id: str) -> bool:
    """Davet odulu bir kez verilsin diye isaretler. Ilk sefer True."""

    with _lock:
        users = _load()
        ref = users.get(referrer_id)
        new_user = users.get(new_user_id)
        if ref is None or new_user is None:
            return False
        awarded = ref.setdefault("referrals_awarded", [])
        if new_user_id in awarded:
            return False
        awarded.append(new_user_id)
        new_user["referred_by"] = referrer_id
        _save(users)
        return True


def public_user(user: dict) -> dict:
    """Istemciye gonderilecek guvenli alanlar (ic sayaclar haric)."""

    return {
        "id": user["id"],
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture"),
        "created_at": user.get("created_at"),
        "tier": get_tier(user),
        "is_verified": is_user_verified(user),
    }


def count_ai_request(user_id: str):
    """Kullanicinin AI istek sayacini artirir."""

    with _lock:
        users = _load()

        user = users.get(user_id)

        if user is None:
            return

        user["ai_request_count"] = user.get("ai_request_count", 0) + 1
        user["last_ai_request"] = datetime.now().isoformat(timespec="seconds")

        _save(users)


# --- Favoriler -------------------------------------------------------------


def list_favorites(user_id: str) -> list:
    user = get_user(user_id)

    if user is None:
        return []

    return user.get("favorites", [])


def add_favorite(user_id: str, item: dict) -> list | None:
    """Favori ekler; limit asilarsa None doner."""

    now = datetime.now().isoformat(timespec="seconds")

    with _lock:
        users = _load()

        user = users.get(user_id)

        if user is None:
            return None

        favorites = user.setdefault("favorites", [])

        # Ayni guzergah (yon ayrimi olmadan) zaten varsa tekrar ekleme
        for existing in favorites:
            if (existing.get("from") == item.get("from")
                    and existing.get("to") == item.get("to")
                    and existing.get("mode") == item.get("mode")):
                return favorites

        if len(favorites) >= MAX_FAVORITES:
            return None

        favorites.append({
            "id": uuid.uuid4().hex[:12],
            "from": item.get("from"),
            "to": item.get("to"),
            "people": item.get("people", 1),
            "mode": item.get("mode", "tumu"),
            "created_at": now,
        })

        _save(users)

    return user["favorites"]


def remove_favorite(user_id: str, favorite_id: str) -> list | None:
    with _lock:
        users = _load()

        user = users.get(user_id)

        if user is None:
            return None

        favorites = user.get("favorites", [])
        new_favorites = [f for f in favorites if f.get("id") != favorite_id]

        if len(new_favorites) == len(favorites):
            return favorites  # bulunamadi; mevcut listeyi dondur

        user["favorites"] = new_favorites
        _save(users)

    return new_favorites


MAX_TARGETS = 50


def get_game(user_id: str) -> dict:
    """Oyun durumu: {xp, badges[], cities[], targets[], counters{}}."""

    with _lock:
        users = _load()
        user = users.get(user_id)
        game = (user or {}).get("game") or {}
        return {
            "xp": int(game.get("xp", 0) or 0),
            "badges": list(game.get("badges", []) or []),
            "cities": list(game.get("cities", []) or []),
            "targets": list(game.get("targets", []) or []),
            "counters": dict(game.get("counters", {}) or {}),
        }


def save_game(user_id: str, game: dict) -> dict | None:
    """Oyun durumunu yazar; guncel durumu doner."""

    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is None:
            return None
        user["game"] = {
            "xp": int(game.get("xp", 0) or 0),
            "badges": list(game.get("badges", []) or []),
            "cities": list(game.get("cities", []) or []),
            "targets": list(game.get("targets", []) or []),
            "counters": dict(game.get("counters", {}) or {}),
        }
        _save(users)
        return dict(user["game"])


def add_target(user_id: str, item: dict) -> list | None:
    """Hedef ekler; guncel hedef listesini doner."""

    now = datetime.now().isoformat(timespec="seconds")

    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is None:
            return None
        game = user.setdefault("game", {})
        targets = game.setdefault("targets", [])
        entry = {
            "id": uuid.uuid4().hex[:12],
            "name": (item.get("name") or "").strip()[:80],
            "address": (item.get("address") or "").strip()[:160],
            "city": (item.get("city") or "").strip()[:60],
            "lat": item.get("lat"),
            "lon": item.get("lon"),
            "created_at": now,
        }
        if len(targets) >= MAX_TARGETS:
            return None
        targets.append(entry)
        _save(users)

    return list(targets)


def remove_target(user_id: str, target_id: str) -> list | None:
    """Hedef siler; guncel hedef listesini doner."""

    with _lock:
        users = _load()
        user = users.get(user_id)
        if user is None:
            return None
        game = user.setdefault("game", {})
        targets = game.get("targets", [])
        remaining = [t for t in targets if t.get("id") != target_id]
        game["targets"] = remaining
        _save(users)

    return list(remaining)


def admin_user_overview() -> list:
    """Kotuye kullanim incelemesi icin ozet: kullanicilar + sohbet istatistikleri."""

    users = _load()

    overview = []

    for user in users.values():
        overview.append({
            "id": user["id"],
            "email": user.get("email"),
            "name": user.get("name"),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login"),
            "ai_request_count": user.get("ai_request_count", 0),
            "last_ai_request": user.get("last_ai_request"),
            "favorite_count": len(user.get("favorites", [])),
        })

    overview.sort(
        key=lambda u: u.get("last_ai_request") or "",
        reverse=True,
    )

    return overview

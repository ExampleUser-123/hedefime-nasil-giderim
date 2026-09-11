"""Google Sign-In dogrulama + kendi JWT'mizin uretimi.

Akis:
1. Uygulama Google'dan ID Token alir (@capawesome/capacitor-google-sign-in).
2. Backend token'i Google'in JWKS anahtarlariyla dogrular
   (imza + audience + issuer + exp).
3. Dogrulanirsa kendi JWT'mizi uretiriz (HS256, 7 gun) —
   sonraki istekler "Authorization: Bearer <jwt>" ile gelir.

Sifre hicbir yerde saklanmaz; hesap guvenligini Google tasir.
"""

import os
import time

import jwt
from jwt import PyJWKClient
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")

TOKEN_TTL_SECONDS = 7 * 24 * 3600  # 7 gun

# Google JWKS anahtarlari surekli degismedigi icin surekli cekmemek adina
# PyJWKClient kendi icinde onbellekler (lifespan: 1 saat).
_jwk_client = PyJWKClient(GOOGLE_JWKS_URL, cache_jwk_set=True, lifespan=3600)

_bearer_scheme = HTTPBearer(auto_error=False)


class AuthError(Exception):
    """Kimlik dogrulama hatalari icin tek tip istisna."""


def _google_client_id() -> str | None:
    """Token'in kime kesildigini dogrulayacagimiz OAuth client ID (env)."""
    return os.getenv("GOOGLE_CLIENT_ID")


# JWT_SECRET env'i yoksa kullanilan gecici anahtar (surec omru boyunca sabit).
# Surec icinde degisir; deploy/restart sonrasi eski tokenlar gecersizlesir.
_EPHEMERAL_SECRET: str | None = None


def _jwt_secret() -> str:
    global _EPHEMERAL_SECRET
    secret = os.getenv("JWT_SECRET")

    if secret:
        return secret

    # Render'da JWT_SECRET tanimli olacak. Tanimli degilse (lokal hizli
    # deneme) SUREC BASINA BIR KEZ uretilir — aksi halde her cagri farkli
    # anahtar uretir ve hicbir token dogrulanamaz.
    if _EPHEMERAL_SECRET is None:
        import logging
        import secrets as _secrets

        logging.getLogger("hng").warning(
            "JWT_SECRET tanimli degil! Gecici anahtar uretildi (surec boyunca "
            "sabit); deploy/restart sonrasi oturumlar sifirlanir."
        )
        _EPHEMERAL_SECRET = _secrets.token_hex(32)

    return _EPHEMERAL_SECRET


# --- E-posta + sifre -------------------------------------------------------

_PBKDF2_ITERATIONS = 200_000


def hash_password(password: str, salt: str) -> str:
    """PBKDF2-SHA256 ile sifreyi hash'ler (karmasiz metin ASLA saklanmaz)."""

    import hashlib

    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        _PBKDF2_ITERATIONS,
    ).hex()


def new_salt() -> str:
    """16 baytlik rastgele tuz (hex)."""

    import secrets as _sec

    return _sec.token_hex(16)


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Sifreyi sabit-zamanli karsilastirmayla dogrular."""

    import hmac

    try:
        return hmac.compare_digest(hash_password(password, salt), expected_hash)
    except (ValueError, TypeError):
        return False


def validate_email_password(email: str, password: str) -> str | None:
    """Girdi kurallari; sorun yoksa None, varsa hata mesaji doner."""

    import re

    email_norm = (email or "").strip().lower()

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]{2,}", email_norm):
        return "Gecerli bir e-posta adresi gir."

    if len(password or "") < 6:
        return "Sifre en az 6 karakter olmali."

    if len(password) > 128:
        return "Sifre cok uzun."

    return None


def verify_google_token(id_token: str) -> dict:
    """Google ID Token'i dogrular; payload (sub, email, name, picture) doner."""

    client_id = _google_client_id()

    if not client_id:
        raise AuthError("Sunucu tarafinda GOOGLE_CLIENT_ID tanimli degil.")

    if not id_token or len(id_token) > 5000:
        raise AuthError("Gecersiz kimlik bilgisi.")

    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(id_token)

        payload = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            options={"require": ["exp", "iat", "aud", "sub"]},
        )

    except jwt.PyJWTError as exc:
        raise AuthError("Google kimlik dogrulamasi basarisiz.") from exc

    issuer = payload.get("iss") or ""

    if issuer not in GOOGLE_ISSUERS:
        raise AuthError("Google kimlik dogrulamasi basarisiz.")

    # email_verified olmayan hesaplar ve tek seferlik token'lar kabul edilmez
    if payload.get("email_verified") is False:
        raise AuthError("Google hesabinin e-postasi dogrulanmamis.")

    return payload


def issue_app_token(user: dict) -> str:
    """Dogrulanmis kullanici icin kendi JWT'mizi uretir."""

    now = int(time.time())

    return jwt.encode(
        {
            "sub": user["id"],
            "email": user.get("email"),
            "name": user.get("name"),
            "picture": user.get("picture"),
            "iat": now,
            "exp": now + TOKEN_TTL_SECONDS,
        },
        _jwt_secret(),
        algorithm="HS256",
    )


def decode_app_token(token: str) -> dict:
    """Kendi JWT'mizi dogrular; payload doner. Gecersizse AuthError."""

    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub"]},
        )

    except jwt.PyJWTError as exc:
        raise AuthError("Oturum gecersiz veya suresi dolmus.") from exc

    if not isinstance(payload.get("sub"), str) or not payload["sub"]:
        raise AuthError("Oturum gecersiz.")

    return payload


def extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if credentials is None or not credentials.credentials:
        raise AuthError("Bu islem icin giris yapmalisin.")

    return credentials.credentials

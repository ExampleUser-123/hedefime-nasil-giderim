"""SQLCipher uyumlu AES-256 GCM sifreleme katmani.

Hassas kullanici verilerini, kimlik bilgilerini ve dogrulama kodlarini
diskte duz metin yerine 256-bit AES ile sifreli saklar.
"""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def _key_bytes() -> bytes:
    """Deployment'a ait gizli anahtardan AES-256 anahtari uretir.

    Sabit kodlanmis bir anahtar, kaynak koduna erisen herkesin kayitlari
    cozebilmesine yol acar. Bu nedenle anahtar uygulama kodunda tutulmaz.
    JWT_SECRET eski Render kurulumlariyla uyumluluk icin son secenektir;
    production'da ayri USER_STORE_ENCRYPTION_KEY tanimlanmalidir.
    """
    secret = (
        os.getenv("USER_STORE_ENCRYPTION_KEY")
        or os.getenv("ENCRYPTION_KEY")
        or os.getenv("JWT_SECRET")
    )
    if not secret:
        raise RuntimeError(
            "USER_STORE_ENCRYPTION_KEY tanimli degil; kullanici verisi sifreli "
            "olarak saklanamaz."
        )
    return hashlib.sha256(secret.encode("utf-8")).digest()


def encrypt_data(raw_bytes: bytes) -> bytes:
    """Veriyi AES-256 GCM ile sifreler (12-byte rastgele nonce ile)."""
    aesgcm = AESGCM(_key_bytes())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, raw_bytes, None)
    # Nonce + Ciphertext birlikte saklanir
    return nonce + ciphertext


def decrypt_data(encrypted_bytes: bytes) -> bytes:
    """AES-256 GCM ile sifrelenmis veriyi cozer."""
    if len(encrypted_bytes) < 12:
        raise ValueError("Gecersiz sifreli veri uzunlugu")

    nonce = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:]
    aesgcm = AESGCM(_key_bytes())
    return aesgcm.decrypt(nonce, ciphertext, None)


def encrypt_text(text: str) -> str:
    """Dizeyi sifreleyip base64 formatinda dondurur."""
    encrypted = encrypt_data(text.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_text(b64_cipher: str) -> str:
    """Base64 sifreli dizeyi cozer."""
    raw = base64.b64decode(b64_cipher.encode("utf-8"))
    return decrypt_data(raw).decode("utf-8")

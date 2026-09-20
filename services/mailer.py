"""E-posta dogrulama ve bildirim servisi (SMTP / Gmail).

Kullanici kayitlarinda 6 haneli tek kullanimlik guvenlik kodlari (OTP) uretir
ve SMTP uzerinden gonderir. Dogrulama kodlari loglara yazilmaz.
"""

import os
import smtplib
import secrets
import logging
from email.message import EmailMessage
from email.utils import formatdate
import threading

logger = logging.getLogger("mailer")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
smtp_port_env = os.getenv("SMTP_PORT")
SMTP_PORT = int(smtp_port_env) if smtp_port_env and smtp_port_env.strip() else 587
SMTP_USER = os.getenv("SMTP_USER", "hedefimenasilgiderim@gmail.com")
# Google uygulama sifresi "xxxx xxxx xxxx xxxx" formatinda bosluklu verilir;
# yapistirirken kalan bosluklar SMTP login'i patlatir, temizle.
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "")

# Resend: varsa birincil gonderim kanali. Anahtar yoksa SMTP'ye dusulur.
# Domain dogrulanmadan onboarding adresi SADECE Resend hesap e-postasina gonderir.
RESEND_FROM_DEFAULT = "Hedefime Nasıl Giderim <onboarding@resend.dev>"
APP_NAME = "Hedefime Nasıl Giderim"


def _resend_api_key() -> str:
    return (os.getenv("RESEND_API_KEY") or "").strip()


def _resend_from() -> str:
    return (os.getenv("RESEND_FROM") or "").strip() or RESEND_FROM_DEFAULT


def is_configured() -> bool:
    """Gercek e-posta gonderimi mumkun mu (Resend anahtari veya SMTP parolasi)?"""
    return bool(_resend_api_key() or SMTP_PASSWORD)


if not _resend_api_key() and not SMTP_PASSWORD:
    # Import aninda tek seferlik uyari: Vercel logunda gorunur, kayit akisi
    # fail-soft calismaya devam eder (dogrulamasiz kayit).
    logger.warning(
        "E-posta gonderimi yapilandirilmamis (RESEND_API_KEY / SMTP_PASSWORD yok); "
        "kayitlar dogrulama kodu gonderilmeden tamamlanacak."
    )


def generate_verification_code() -> str:
    """6 haneli guvenli rastgele dogrulama kodu uretir."""
    return f"{secrets.randbelow(900000) + 100000}"


def _build_html_body(code: str, name: str | None = None) -> str:
    user_greeting = f"Merhaba {name}," if name else "Merhaba,"
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>E-posta Doğrulama Kodu</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f1f5f9;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="min-height: 100vh; padding: 32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 480px; background-color: #1e293b; border-radius: 20px; border: 1px solid #334155; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.5);">
          <!-- Header -->
          <tr>
            <td style="padding: 32px 32px 20px; text-align: center; background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(59,130,246,0.15)); border-bottom: 1px solid #334155;">
              <h1 style="margin: 0; font-size: 22px; font-weight: 800; color: #38bdf8; letter-spacing: -0.5px;">
                🚀 {APP_NAME}
              </h1>
              <p style="margin: 6px 0 0; font-size: 13px; color: #94a3b8;">
                Hesap Güvenliği ve Doğrulama
              </p>
            </td>
          </tr>

          <!-- Content -->
          <tr>
            <td style="padding: 32px;">
              <p style="margin: 0 0 16px; font-size: 15px; color: #cbd5e1; line-height: 1.5;">
                {user_greeting}
              </p>
              <p style="margin: 0 0 24px; font-size: 14px; color: #94a3b8; line-height: 1.6;">
                <strong>{APP_NAME}</strong> hesabınızı aktifleştirmek için aşağıdaki 6 haneli güvenlik kodunu uygulamadaki ekrana girin:
              </p>

              <!-- Code Box -->
              <div style="background-color: #0f172a; border: 2px dashed #0284c7; border-radius: 14px; padding: 20px; text-align: center; margin: 0 0 24px;">
                <span style="font-family: 'Courier New', Courier, monospace; font-size: 34px; font-weight: 900; letter-spacing: 8px; color: #38bdf8; display: inline-block;">
                  {code}
                </span>
                <p style="margin: 8px 0 0; font-size: 11px; color: #64748b;">
                  ⏱ Bu kod 15 dakika boyunca geçerlidir.
                </p>
              </div>

              <p style="margin: 0 0 8px; font-size: 12px; color: #64748b; line-height: 1.5;">
                • Bu işlemi siz yapmadıysanız, bu e-postayı güvenle yok sayabilirsiniz.<br>
                • Kodunuzu asla başkalarıyla paylaşmayın.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 32px; background-color: #0f172a; border-top: 1px solid #1e293b; text-align: center;">
              <p style="margin: 0; font-size: 11px; color: #475569;">
                © 2026 {APP_NAME} • Türkiye Geneli Akıllı Rota ve Toplu Taşıma
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _send_via_resend(to_email: str, code: str, name: str | None = None) -> bool:
    """Resend API ile gonderim dener. Basariliysa True doner.

    Anahtar asla loglanmaz; hata durumunda sadece hata turu kaydedilir.
    """
    api_key = _resend_api_key()
    if not api_key:
        return False

    try:
        import resend
    except ImportError:
        logger.error("resend paketi kurulu degil; Resend gonderimi atlandi.")
        return False

    resend.api_key = api_key
    from_addr = _resend_from()
    if "onboarding@resend.dev" in from_addr:
        # Ucretsiz/test gonderici: SADECE Resend hesap e-postasina iletilir.
        # Baska aliciya gonderim API'den 403 ile reddedilir (asagida loglanir).
        logger.warning(
            "Resend gonderici onboarding@resend.dev; domain dogrulanmadan "
            "yalnizca Resend hesap e-postasina iletim yapilir."
        )
    params = {
        "from": from_addr,
        "to": [to_email],
        "subject": f"{code} — {APP_NAME} Doğrulama Kodunuz",
        "html": _build_html_body(code, name),
    }
    try:
        result = resend.Emails.send(params)
        email_id = (result or {}).get("id") if isinstance(result, dict) else None
        logger.info("Resend ile dogrulama e-postasi gonderildi (id=%s).", email_id)
        return True
    except Exception as exc:
        # ResendError veya ag hatasi. API key ve alici loga yazilmaz; SDK'nin
        # dondurdugu hata mesaji (status/reason, orn. 403 test-modu kisiti)
        # teshis icin kaydedilir.
        logger.error(
            "Resend gonderimi basarisiz oldu (%s): %s",
            type(exc).__name__, str(exc)[:300],
        )
        return False


def _send_smtp_worker(to_email: str, code: str, name: str | None = None):
    """Arka plan thread'inde gercek SMTP gonderimi yapar."""
    if _send_via_resend(to_email, code, name):
        return

    if _resend_api_key():
        # Resend varken SMTP'ye dusme: cift e-posta gitmesin, hata dondur.
        logger.error("Resend basarisiz oldu; SMTP yedegine dusulmedi (cift gonderim onlendi).")
        return

    if not SMTP_PASSWORD:
        logger.error("SMTP_PASSWORD ayarlanmamis; dogrulama e-postasi gonderilmedi.")
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = f"{code} — {APP_NAME} Doğrulama Kodunuz"
        msg["From"] = f"{APP_NAME} <{SMTP_USER}>"
        msg["To"] = to_email
        msg["Date"] = formatdate(localtime=True)

        plain_text = f"Merhaba,\n\n{APP_NAME} hesabınızı doğrulamak için kodunuz: {code}\nBu kod 15 dakika geçerlidir.\n"
        msg.set_content(plain_text)

        html_body = _build_html_body(code, name)
        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Dogrulama e-postasi basariyla gonderildi.")

    except Exception:
        logger.exception("E-posta gonderilirken hata olustu.")


def send_verification_email_async(to_email: str, code: str, name: str | None = None):
    """FastAPI'yi bloklamadan arka planda e-posta gonderir."""
    thread = threading.Thread(
        target=_send_smtp_worker,
        args=(to_email, code, name),
        daemon=True,
    )
    thread.start()

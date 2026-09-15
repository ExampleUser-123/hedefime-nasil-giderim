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
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "hedefimenasilgiderim@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
APP_NAME = "Hedefime Nasıl Giderim"


def is_configured() -> bool:
    """Gercek e-posta gonderimi icin gereken SMTP parolasi tanimli mi?"""
    return bool(SMTP_PASSWORD)


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


def _send_smtp_worker(to_email: str, code: str, name: str | None = None):
    """Arka plan thread'inde gercek SMTP gonderimi yapar."""
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

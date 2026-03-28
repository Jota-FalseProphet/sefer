"""
Email sending via Resend for verification codes.
"""

import resend
from src.config import settings
from src.core.logging import server_log


def send_verification_email(to_email: str, code: str):
    resend.api_key = settings.resend_api_key

    html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 420px; margin: 0 auto;
                background: #1a1a1a; color: #e0e0e0; padding: 40px; border-radius: 12px;">
        <h1 style="color: #c084fc; font-size: 1.4rem; margin-bottom: 8px;">Sefer</h1>
        <p style="color: #888; font-size: 0.9rem; margin-bottom: 24px;">Verificacion de cuenta</p>
        <p style="margin-bottom: 24px;">Tu codigo de verificacion es:</p>
        <div style="background: #252525; border: 1px solid #333; border-radius: 8px;
                    padding: 20px; text-align: center; margin-bottom: 24px;">
            <span style="font-size: 2rem; font-weight: bold; letter-spacing: 8px; color: #c084fc;">
                {code}
            </span>
        </div>
        <p style="color: #888; font-size: 0.8rem;">
            Este codigo expira en 10 minutos. Si no has solicitado este codigo, ignora este email.
        </p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": "Sefer <noreply@yostesis.online>",
            "to": [to_email],
            "subject": "Sefer - Codigo de verificacion",
            "html": html,
        })
        server_log.info("Verification email sent to %s", to_email)
    except Exception as e:
        server_log.error("Failed to send email to %s: %s", to_email, str(e))
        raise

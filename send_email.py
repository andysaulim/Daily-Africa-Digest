"""
Africa Daily Brief — Email Sender

Gmail SMTP with TLS + app password. Reads recipient list from DIGEST_TO
environment variable (comma-separated).
"""

import os
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

def send_digest(
    html: str,
    subject: str,
    sender: str | None = None,
    recipients: list[str] | None = None,
    app_password: str | None = None,
    max_retries: int = 3,
) -> bool:
    """Send the rendered digest. Returns True on success."""
    sender       = sender       or os.environ.get("GMAIL_USER")
    app_password = app_password or os.environ.get("GMAIL_APP_PASS")
    if not recipients:
        recip_str = os.environ.get("DIGEST_TO", "")
        recipients = [r.strip() for r in recip_str.split(",") if r.strip()]

    if not sender or not app_password:
        raise RuntimeError("GMAIL_USER and GMAIL_APP_PASS must be set")
    if not recipients:
        raise RuntimeError("DIGEST_TO must list at least one recipient")

    msg = MIMEMultipart("alternative")
    msg["From"]    = sender
    msg["To"]      = ", ".join(recipients)
    msg["Subject"] = subject

    # Minimal plain-text fallback
    plain = "View the CSIS Daily Africa Brief in an HTML-capable mail client."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            ctx = ssl.create_default_context()
            with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=30) as smtp:
                smtp.starttls(context=ctx)
                smtp.login(sender, app_password)
                smtp.send_message(msg)
            print(f"[email] Sent to {len(recipients)} recipient(s) on attempt {attempt}")
            return True
        except (smtplib.SMTPException, ssl.SSLError, OSError) as exc:
            last_err = exc
            print(f"[email] Attempt {attempt} failed: {exc}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # 2, 4, 8s
    print(f"[email] All {max_retries} attempts failed. Last error: {last_err}")
    return False


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--html",    default="preview.html")
    p.add_argument("--subject", default="CSIS Daily Africa Brief")
    args = p.parse_args()
    with open(args.html) as f:
        html = f.read()
    ok = send_digest(html, args.subject)
    raise SystemExit(0 if ok else 1)

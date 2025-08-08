# app/services/email_service.py
import os
import requests
import jwt
from uuid import UUID
from datetime import datetime, timedelta
from pathlib import Path

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_VERIFY_SECRET = os.getenv("EMAIL_VERIFY_SECRET", "change-me")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Neuvi <no-reply@example.com>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"

def send_verification_email(email: str, profile_id: UUID, first_name: str = None, base_url: str = None):
    token = jwt.encode(
        {"profile_id": str(profile_id), "exp": datetime.utcnow() + timedelta(days=1)},
        EMAIL_VERIFY_SECRET,
        algorithm="HS256",
    )
    verify_link = f"{base_url or FRONTEND_URL}/verify?token={token}"
    subject = "Verify your email for Neuvi"
    preheader = "Confirm your email to continue your Neuvi signup."
    greeting = f"Hey {first_name}," if first_name else "Hey there,"

    html = _render_template(
        "verify_email.html",
        subject=subject,
        preheader=preheader,
        greeting=greeting,
        verify_link=verify_link,
    )
    _send_email(email, subject, html)

def send_welcome_email(email: str, first_name: str | None):
    """Send the branded welcome email using the HTML template."""
    subject = "Welcome to Neuvi!"
    preheader = "Thanks for joining Neuvi — we’ll let you in soon."
    greeting = f"Hey {first_name}!" if first_name else "Hey there!"
    # CTA can lead back to your site; update path later if you want a dashboard/waitlist page
    cta_link = f"{FRONTEND_URL}/"
    cta_text = "Visit Neuvi"

    html = _render_template(
        "welcome_email.html",
        subject=subject,
        preheader=preheader,
        greeting=greeting,
        cta_link=cta_link,
        cta_text=cta_text,
    )
    _send_email(email, subject, html)

def _send_email(to_email: str, subject: str, html: str):
    if not RESEND_API_KEY:
        print("RESEND_API_KEY not set")
        return
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html,
        },
        timeout=10,
    )
    if resp.status_code >= 400:
        print("Failed to send email:", resp.text)

def _render_template(template_name: str, **kwargs) -> str:
    template_path = TEMPLATES_DIR / template_name
    html = template_path.read_text(encoding="utf-8")
    for key, value in kwargs.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))
    return html

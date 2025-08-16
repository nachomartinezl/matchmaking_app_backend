# app/services/email_service.py
import os
import httpx
import jwt
from uuid import UUID
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --- Configuration ---
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_VERIFY_SECRET = os.getenv("EMAIL_VERIFY_SECRET", "change-me")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Neuvi <no-reply@example.com>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"
RESEND_API_URL = "https://api.resend.com/emails"

# --- Main Service Functions ---

async def send_verification_email(email: str, profile_id: UUID, first_name: str = None):
    """Asynchronously sends a verification email."""
    token = jwt.encode(
        {"profile_id": str(profile_id), "exp": datetime.now(timezone.utc) + timedelta(days=1)},
        EMAIL_VERIFY_SECRET,
        algorithm="HS256",
    )
    verify_link = f"{FRONTEND_URL}/verify?token={token}"
    subject = "Verify your email for Neuvi"
    greeting = f"Hey {first_name}," if first_name else "Hey there,"

    html = _render_template(
        "verify_email.html",
        subject=subject,
        preheader="Confirm your email to continue your Neuvi signup.",
        greeting=greeting,
        verify_link=verify_link,
    )
    await _send_email(email, subject, html)


async def send_welcome_email(email: str, first_name: str | None):
    """Asynchronously sends the branded welcome email."""
    subject = "Welcome to Neuvi!"
    greeting = f"Hey {first_name}!" if first_name else "Hey there!"

    html = _render_template(
        "welcome_email.html",
        subject=subject,
        preheader="Thanks for joining Neuvi — we’ll let you in soon.",
        greeting=greeting,
        cta_link=f"{FRONTEND_URL}/",
        cta_text="Visit Neuvi",
    )
    await _send_email(email, subject, html)


async def _send_email(to_email: str, subject: str, html: str):
    """Sends an email using the Resend API with httpx."""
    if not RESEND_API_KEY:
        print("RESEND_API_KEY not set, skipping email.")
        return

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": EMAIL_FROM,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(RESEND_API_URL, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
            print(f"Email sent to {to_email} with status: {resp.status_code}")
        except httpx.HTTPStatusError as e:
            print(f"Failed to send email. Status: {e.response.status_code}, Body: {e.response.text}")
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}: {e}")

def _render_template(template_name: str, **kwargs) -> str:
    template_path = TEMPLATES_DIR / template_name
    html = template_path.read_text(encoding="utf-8")
    for key, value in kwargs.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))
    return html

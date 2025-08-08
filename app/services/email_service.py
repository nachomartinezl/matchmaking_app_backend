# app/services/email_service.py
import os
import requests
import jwt
from uuid import UUID
from datetime import datetime, timedelta

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_VERIFY_SECRET = os.getenv("EMAIL_VERIFY_SECRET", "change-me")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Neuvi <no-reply@example.com>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")  # 👈 Now points to frontend

def send_verification_email(email: str, profile_id: UUID, base_url: str = None):
    """
    Sends a verification email with a link pointing to the frontend.
    `base_url` can override FRONTEND_URL (useful for tests).
    """
    token = jwt.encode(
        {"profile_id": str(profile_id), "exp": datetime.utcnow() + timedelta(days=1)},
        EMAIL_VERIFY_SECRET,
        algorithm="HS256",
    )
    verify_link = f"{base_url or FRONTEND_URL}/verify?token={token}"
    _send_email(
        email,
        "Verify your email",
        f"<p>Click to verify: <a href='{verify_link}'>Verify Email</a></p>",
    )

def send_welcome_email(email: str, first_name: str):
    _send_email(
        email,
        "Welcome to Neuvi!",
        f"<h1>Hey {first_name}!</h1><p>Welcome aboard 🎉</p>"
    )

def _send_email(to_email: str, subject: str, html: str):
    if not RESEND_API_KEY:
        print("RESEND_API_KEY not set")
        return
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html
        },
        timeout=10,
    )
    if resp.status_code >= 400:
        print("Failed to send email:", resp.text)

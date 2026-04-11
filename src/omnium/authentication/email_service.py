"""
Email Verification Service — sends verification codes via Gmail SMTP.

Requires OMNIUM_EMAIL_ADDRESS and OMNIUM_EMAIL_PASSWORD in .env.
Use a Gmail App Password (not your regular password) for OMNIUM_EMAIL_PASSWORD.
"""

from __future__ import annotations

import logging
import os
import random
import smtplib
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Tuple

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

# In-memory store of pending verification codes: {username: (code, email, expires_at)}
_pending_verifications: dict[str, tuple[str, str, datetime]] = {}

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
CODE_LENGTH = 6
CODE_EXPIRY_MINUTES = 10


def _generate_code() -> str:
    """Generate a random 6-digit verification code."""
    return "".join(random.choices(string.digits, k=CODE_LENGTH))


def send_verification_email(username: str, email: str) -> Tuple[bool, str]:
    """
    Generate a verification code and send it to the user's email.

    Returns:
        Tuple of (success, message)
    """
    sender_address = os.getenv("OMNIUM_EMAIL_ADDRESS", "")
    sender_password = os.getenv("OMNIUM_EMAIL_PASSWORD", "")

    if not sender_address or not sender_password:
        log.warning("Email credentials not configured — skipping email send")
        # In development, still generate a code so verification flow works
        code = _generate_code()
        expires = datetime.now() + timedelta(minutes=CODE_EXPIRY_MINUTES)
        _pending_verifications[username.lower()] = (code, email, expires)
        log.info("Dev mode: verification code for %s is %s", username, code)
        return True, f"Verification code generated (dev mode: {code})"

    code = _generate_code()
    expires = datetime.now() + timedelta(minutes=CODE_EXPIRY_MINUTES)
    _pending_verifications[username.lower()] = (code, email, expires)

    msg = MIMEText(
        f"Your Omnium verification code is: {code}\n\n"
        f"This code expires in {CODE_EXPIRY_MINUTES} minutes.\n\n"
        f"If you did not request this, please ignore this email."
    )
    msg["Subject"] = "Omnium — Email Verification Code"
    msg["From"] = sender_address
    msg["To"] = email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(sender_address, sender_password)
            server.send_message(msg)
        log.info("Verification email sent to %s for user %s", email, username)
        return True, "Verification email sent"
    except Exception as e:
        log.error("Failed to send verification email: %s", e)
        return False, f"Failed to send email: {e}"


def verify_code(username: str, code: str) -> Tuple[bool, str]:
    """
    Verify a user's email verification code.

    Returns:
        Tuple of (success, message)
    """
    key = username.lower()
    if key not in _pending_verifications:
        return False, "No verification pending for this user"

    stored_code, email, expires = _pending_verifications[key]

    if datetime.now() > expires:
        del _pending_verifications[key]
        return False, "Verification code expired — request a new one"

    if code != stored_code:
        return False, "Invalid verification code"

    # Code is valid — remove from pending
    del _pending_verifications[key]
    log.info("Email verified for user %s (%s)", username, email)
    return True, "Email verified successfully"


def has_pending_verification(username: str) -> bool:
    """Check if a user has a pending verification."""
    key = username.lower()
    if key not in _pending_verifications:
        return False
    _, _, expires = _pending_verifications[key]
    if datetime.now() > expires:
        del _pending_verifications[key]
        return False
    return True

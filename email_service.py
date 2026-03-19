# email.py

import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple


class EmailService:
    GMAIL_ADDRESS = "omniumverify@gmail.com"
    GMAIL_APP_PASSWORD = "ljql utkt drxx bpbx"

    def __init__(self):
        """Initialize Gmail email service."""
        self.sender_email = self.GMAIL_ADDRESS
        self.sender_password = self.GMAIL_APP_PASSWORD
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_verification_code(self, recipient_email: str, verification_code: str) -> Tuple[bool, str]:
        """
        Send verification code to recipient email via Gmail.

        Args:
            recipient_email: User's email address (where code is sent TO)
            verification_code: 5-digit code to send

        Returns:
            Tuple of (success, message)
        """
        try:
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = "Omnium Trading - Email Verification Code"

            body = f"""
Hello,

Your Omnium Trading email verification code is:

{verification_code}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

Best regards,
Omnium Trading Team
            """

            message.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            return True, "Verification code sent to email"

        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed. Check Gmail address and app password."
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Error sending email: {str(e)}"
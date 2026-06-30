"""Email notification sender via SMTP."""

from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from typing import Any


class EmailSender:
    """SMTP email sender reading credentials from env vars or config dict."""

    def __init__(self, cfg: dict[str, Any] | None = None) -> None:
        # prefer explicit config dict, fall back to env vars
        sender = os.environ.get("SMTP_SENDER_EMAIL") or (cfg or {}).get("SENDER_EMAIL", "")
        pwd = os.environ.get("SMTP_SENDER_PASSWORD") or (cfg or {}).get("SENDER_PASSWORD", "")
        receiver = os.environ.get("SMTP_RECEIVER_EMAIL") or (cfg or {}).get("RECEIVER_EMAIL", "")

        self.sender = sender
        self.password = pwd
        self.receiver = receiver
        self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    def send(self, subject: str, body: str) -> tuple[bool, str | None]:
        """Send an email. Returns (ok, err_msg)."""
        if not self.sender or not self.password or not self.receiver:
            return False, "Email credentials not configured"

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = self.receiver

        try:
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()
            return True, None
        except Exception as exc:
            return False, str(exc)

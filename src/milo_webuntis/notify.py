from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

import requests

from .config import EmailConfig, TwilioConfig


class Notifier:
    def __init__(self, email: EmailConfig, twilio: TwilioConfig, webhook_url: str) -> None:
        self.email = email
        self.twilio = twilio
        self.webhook_url = webhook_url

    def send(
        self,
        subject: str,
        body: str,
        metadata: dict[str, Any],
        html_body: str | None = None,
    ) -> list[str]:
        delivered: list[str] = []
        if self.email.enabled:
            self._send_email(subject, body, html_body=html_body)
            delivered.append("email")
        if self.twilio.enabled:
            self._send_twilio_whatsapp(body)
            delivered.append("whatsapp")
        if self.webhook_url:
            self._send_webhook(subject, body, metadata)
            delivered.append("webhook")
        return delivered

    def send_email_to(self, recipient: str, subject: str, body: str) -> None:
        if not (self.email.host and self.email.sender):
            raise ValueError("E-Mail-Versand ist nicht konfiguriert.")
        self._send_email(subject, body, recipients=[recipient])

    def send_email(self, subject: str, body: str, html_body: str | None = None) -> bool:
        if not self.email.enabled:
            return False
        self._send_email(subject, body, html_body=html_body)
        return True

    def _send_email(
        self,
        subject: str,
        body: str,
        recipients: list[str] | None = None,
        html_body: str | None = None,
    ) -> None:
        email_recipients = recipients or self.email.recipients
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.email.sender
        message["To"] = ", ".join(email_recipients)
        if self.email.reply_to:
            message["Reply-To"] = self.email.reply_to
        message.set_content(body)
        if html_body:
            message.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(self.email.host, self.email.port, timeout=30) as smtp:
            if self.email.use_tls:
                smtp.starttls()
            if self.email.username:
                smtp.login(self.email.username, self.email.password)
            smtp.send_message(message)

    def _send_twilio_whatsapp(self, body: str) -> None:
        url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{self.twilio.account_sid}/Messages.json"
        )
        for recipient in self.twilio.recipients:
            requests.post(
                url,
                data={
                    "From": self.twilio.whatsapp_from,
                    "To": _whatsapp_address(recipient),
                    "Body": body[:1500],
                },
                auth=(self.twilio.account_sid, self.twilio.auth_token),
                timeout=30,
            ).raise_for_status()

    def _send_webhook(self, subject: str, body: str, metadata: dict[str, Any]) -> None:
        requests.post(
            self.webhook_url,
            json={"subject": subject, "body": body, "metadata": metadata},
            timeout=30,
        ).raise_for_status()


def _whatsapp_address(value: str) -> str:
    if value.startswith("whatsapp:"):
        return value
    return f"whatsapp:{value}"

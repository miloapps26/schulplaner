from __future__ import annotations

import argparse
import json
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .config import load_config
from .notify import Notifier
from .service import MonitorService
from .webuntis_client import WebUntisClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Schulplaner connections.")
    parser.add_argument("--webuntis", action="store_true", help="Check WebUntis login and timetable.")
    parser.add_argument("--webuntis-rest", action="store_true", help="Check WebUntis web timetable REST endpoint.")
    parser.add_argument("--email-to", help="Send a Gmail/SMTP test email to this address.")
    parser.add_argument("--run-once", action="store_true", help="Run one timetable check.")
    parser.add_argument(
        "--force-notify",
        action="store_true",
        help="Send notifications on a detected change even on the first/baseline run.",
    )
    parser.add_argument(
        "--webhook",
        action="store_true",
        help="Send a test notification to NOTIFICATION_WEBHOOK_URL.",
    )
    parser.add_argument("--webhook-url", help="Override NOTIFICATION_WEBHOOK_URL for the webhook test.")
    args = parser.parse_args()

    config = load_config(PROJECT_ROOT)
    results = {}

    if args.webuntis:
        results["webuntis"] = check_webuntis(config)
    if args.webuntis_rest:
        results["webuntis_rest"] = check_webuntis_rest(config)
    if args.email_to:
        results["email"] = send_test_email(config, args.email_to)
    if args.run_once:
        results["run_once"] = MonitorService(config).run_once(force_notify=args.force_notify).__dict__
    if args.webhook:
        results["webhook"] = send_test_webhook(config, args.webhook_url)

    print(json.dumps(results, ensure_ascii=False, indent=2))


def check_webuntis(config):
    if not config.webuntis.is_complete:
        return {"ok": False, "message": "WebUntis-Konfiguration unvollständig."}

    now = _now(config.timezone)
    try:
        with WebUntisClient(config.webuntis) as client:
            lessons = client.timetable(now.date(), now.date() + timedelta(days=7))
        return {
            "ok": True,
            "message": "Login und Stundenplanabruf erfolgreich.",
            "lesson_count": len(lessons),
            "element_type": config.webuntis.element_type,
            "element_id": config.webuntis.element_id,
        }
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def send_test_email(config, recipient: str):
    if not config.email.enabled:
        return {"ok": False, "message": "SMTP-Konfiguration unvollständig."}

    test_email = replace(config.email, recipients=[recipient])
    notifier = Notifier(test_email, config.twilio, "")
    now = _now(config.timezone)
    subject = "Schulplaner Testmail"
    body = (
        "Das ist eine Testmail vom Schulplaner.\n\n"
        f"Zeitpunkt: {now.isoformat()}\n"
        "Wenn diese Mail angekommen ist, funktioniert der SMTP-Versand."
    )
    try:
        channels = notifier.send(subject, body, {"kind": "smtp_test"})
        return {"ok": True, "message": "Testmail versendet.", "channels": channels}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def send_test_webhook(config, webhook_url: str | None):
    url = webhook_url or config.webhook_url
    if not url:
        return {"ok": False, "message": "NOTIFICATION_WEBHOOK_URL fehlt."}

    notifier = Notifier(config.email, config.twilio, url)
    now = _now(config.timezone)
    subject = "Schulplaner Webhook-Test"
    body = (
        "Das ist ein Webhook-Test vom Schulplaner.\n\n"
        f"Zeitpunkt: {now.isoformat()}\n"
        "Wenn diese Mail angekommen ist, funktioniert Make + Gmail."
    )
    try:
        channels = notifier.send(
            subject,
            body,
            {
                "kind": "webhook_test",
                "sent_at": now.isoformat(),
                "timetable_url": "http://127.0.0.1:8000",
            },
        )
        return {"ok": True, "message": "Webhook-Test versendet.", "channels": channels}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def check_webuntis_rest(config):
    if not config.webuntis.is_complete:
        return {"ok": False, "message": "WebUntis-Konfiguration unvollständig."}

    base = config.webuntis.server.rstrip("/")
    if not base.startswith(("http://", "https://")):
        base = f"https://{base}"

    try:
        with WebUntisClient(config.webuntis) as client:
            token_response = client.session.get(f"{base}/WebUntis/api/token/new", timeout=30)
            token_response.raise_for_status()
            token = token_response.text.strip().strip('"')
            if not token:
                return {"ok": False, "message": "Kein Bearer-Token erhalten."}

            response = client.session.get(
                f"{base}/WebUntis/api/rest/view/v1/timetable/entries",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "start": "2026-08-31",
                    "end": "2026-09-06",
                    "format": "1",
                    "resourceType": "STUDENT",
                    "resources": str(config.webuntis.element_id),
                    "periodTypes": "",
                    "timetableType": "MY_TIMETABLE",
                    "layout": "START_TIME",
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        lessons = data.get("elements") or data.get("entries") or data if isinstance(data, dict) else data
        sample = _sample_teacher_fields(lessons)
        return {
            "ok": True,
            "message": "REST-Stundenplanabruf erfolgreich.",
            "top_level": list(data.keys()) if isinstance(data, dict) else "list",
            "entry_count": len(lessons) if isinstance(lessons, list) else None,
            "sample_teacher_fields": sample,
        }
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def _sample_teacher_fields(value):
    if not isinstance(value, list):
        return []
    samples = []
    for item in value[:8]:
        if not isinstance(item, dict):
            continue
        samples.append(
            {
                key: item.get(key)
                for key in item.keys()
                if "teacher" in key.lower() or key.lower() in {"te", "teachers"}
            }
        )
    return samples


def _now(timezone_name: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError:
        return datetime.now().astimezone()


if __name__ == "__main__":
    main()

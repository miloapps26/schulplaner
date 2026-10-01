import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milo_webuntis.config import EmailConfig, IServConfig, load_config
from milo_webuntis.iserv_client import normalize_exam_plan
from milo_webuntis.service import MonitorService


class ExamPlanTests(unittest.TestCase):
    def test_normalize_exam_plan_maps_iserv_plugin_response(self):
        result = normalize_exam_plan(
            [
                {
                    "id": "exam-plan-exam-9481",
                    "title": "Englischarbeit Nr. 1 (Klausur) - Klasse 5d",
                    "start": "2026-09-28T09:55:00+02:00",
                    "end": "2026-09-28T10:40:00+02:00",
                    "allDay": False,
                    "plugin": "exam-plan",
                    "displayFields": [
                        {"text": "Klasse 5d", "label": "Gruppen"},
                        {"text": "ja", "label": "Sichtbar"},
                        {"text": None, "label": "Beschreibung"},
                    ],
                }
            ]
        )

        self.assertEqual(result[0]["id"], "exam-plan-exam-9481")
        self.assertEqual(result[0]["group"], "Klasse 5d")
        self.assertEqual(result[0]["visible"], "ja")
        self.assertEqual(result[0]["description"], "")

    def test_exam_refresh_creates_baseline_without_mail_then_notifies_new_item(self):
        with tempfile.TemporaryDirectory() as directory:
            config = load_config(Path.cwd())
            tenant = replace(
                config.tenants[0],
                data_dir=Path(directory),
                iserv=IServConfig(
                    base_url="https://example.test",
                    username="user",
                    password="secret",
                    enabled=True,
                ),
                email=EmailConfig(
                    host="smtp.example.test",
                    port=587,
                    username="",
                    password="",
                    sender="Schulplaner <noreply@example.test>",
                    reply_to="",
                    recipients=["parent@example.test"],
                    use_tls=True,
                ),
            )
            service = MonitorService(replace(config, data_dir=Path(directory), tenants=(tenant,)))
            sent = []

            class FakeClient:
                calls = 0

                def __init__(self, _config):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *_exc):
                    return None

                def exam_plan(self, _start, _end):
                    FakeClient.calls += 1
                    items = [
                        {
                            "id": "exam-1",
                            "title": "Englischarbeit",
                            "start": "2026-09-28T09:55:00+02:00",
                            "end": "2026-09-28T10:40:00+02:00",
                            "group": "Klasse 5d",
                        }
                    ]
                    if FakeClient.calls > 1:
                        items.append(
                            {
                                "id": "exam-2",
                                "title": "Mathearbeit",
                                "start": "2026-10-02T08:00:00+02:00",
                                "end": "2026-10-02T08:45:00+02:00",
                                "group": "Klasse 5d",
                            }
                        )
                    return items

            class FakeNotifier:
                def send_email(self, subject, body, html_body=None):
                    sent.append((subject, body, html_body))
                    return True

            service.iserv_client_factory = FakeClient
            service.notifiers[tenant.id] = FakeNotifier()
            now = datetime.fromisoformat("2026-09-21T12:00:00+02:00")

            self.assertEqual(service._refresh_exams_and_notify(tenant, now), [])
            self.assertEqual(sent, [])

            self.assertEqual(service._refresh_exams_and_notify(tenant, now), ["email"])
            self.assertEqual(len(sent), 1)
            self.assertIn("Mathearbeit", sent[0][1])


if __name__ == "__main__":
    unittest.main()

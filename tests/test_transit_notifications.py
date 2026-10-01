import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milo_webuntis.service import (
    MonitorService,
    _freeze_departed_recommendations,
    _transit_recommendation_snapshot,
    build_transit_notification,
    build_transit_notification_html,
)
from milo_webuntis.snapshot import SnapshotStore


def _connection(*, delay_seconds=0, vehicle_longitude=10.0):
    return {
        "line": "5402 → 5404",
        "departure": "13:25",
        "arrival": "14:31",
        "planned_departure": "13:25",
        "planned_arrival": "14:31",
        "duration_minutes": 66,
        "from": {"id": "A", "name": "Lüneburg, Herderschule", "coordinate": {"x": 10.1, "y": 53.2}},
        "to": {"id": "B", "name": "Wittorf, Birkenweg", "coordinate": {"x": 10.2, "y": 53.3}},
        "headsign": "Bardowick",
        "cancelled": False,
        "realtime": True,
        "delay_seconds": delay_seconds,
        "platform": "2",
        "legs": [],
        "announcements": [],
        "vehicle": {
            "status": "available",
            "position": {"longitude": vehicle_longitude, "latitude": 53.2},
        },
    }


class TransitNotificationTests(unittest.TestCase):
    def test_snapshot_ignores_moving_vehicle_position(self):
        first = _transit_recommendation_snapshot(
            {"date": "2026-09-17", "recommendation": {"outbound": None, "return": _connection(vehicle_longitude=10.1)}}
        )
        second = _transit_recommendation_snapshot(
            {"date": "2026-09-17", "recommendation": {"outbound": None, "return": _connection(vehicle_longitude=10.2)}}
        )

        self.assertEqual(first, second)

    def test_snapshot_detects_recommendation_delay_change(self):
        first = _transit_recommendation_snapshot(
            {"date": "2026-09-17", "recommendation": {"outbound": None, "return": _connection(delay_seconds=0)}}
        )
        second = _transit_recommendation_snapshot(
            {"date": "2026-09-17", "recommendation": {"outbound": None, "return": _connection(delay_seconds=300)}}
        )

        self.assertNotEqual(first, second)
        subject, body = build_transit_notification(first, second)
        self.assertEqual(subject, "Dein Bus fährt anders: 17.09.2026")
        self.assertIn("Fahrt nach Hause:", body)
        self.assertIn("Verspätung: Pünktlich → +5 Min", body)
        self.assertIn("Bitte nutze die Angaben unter „Jetzt“.", body)
        self.assertNotIn("Fahrt zur Schule:", body)
        self.assertNotIn("Echtzeit", body)
        html_body = build_transit_notification_html(first, second, "https://example.test/app")
        self.assertIn("Das ist neu", html_body)
        self.assertIn("Jetzt: +5 Min", html_body)
        self.assertIn("background:#3a2a0a", html_body)
        self.assertIn("https://example.test/app", html_body)

    def test_snapshot_ignores_delay_changes_within_same_visible_minute(self):
        first = _transit_recommendation_snapshot(
            {"date": "2026-09-17", "recommendation": {"outbound": None, "return": _connection(delay_seconds=241)}}
        )
        second = _transit_recommendation_snapshot(
            {"date": "2026-09-17", "recommendation": {"outbound": None, "return": _connection(delay_seconds=254)}}
        )

        self.assertEqual(first, second)

    def test_departed_connection_is_frozen_to_avoid_late_noise(self):
        previous = _transit_recommendation_snapshot(
            {"date": "2026-09-17", "recommendation": {"outbound": _connection(delay_seconds=0), "return": None}}
        )
        current = _transit_recommendation_snapshot(
            {"date": "2026-09-17", "recommendation": {"outbound": _connection(delay_seconds=300), "return": None}}
        )

        frozen = _freeze_departed_recommendations(
            current,
            previous,
            datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(frozen, previous)

    def test_snapshot_store_persists_transit_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SnapshotStore(Path(directory))
            payload = {
                "date": "2026-09-17",
                "recommendation": {"outbound": None, "return": _connection()},
            }

            store.save_transit_recommendation(payload)

            self.assertEqual(store.load_transit_recommendation(), payload)

    def test_monitor_sends_email_only_after_baseline_changes(self):
        class _Notifier:
            def __init__(self):
                self.messages = []

            def send_email(self, subject, body, html_body=None):
                self.messages.append((subject, body, html_body))
                return True

        with tempfile.TemporaryDirectory() as directory:
            store = SnapshotStore(Path(directory))
            notifier = _Notifier()
            tenant = SimpleNamespace(
                id="tenant-1",
                name="Testprofil",
                email=SimpleNamespace(enabled=True),
            )
            service = object.__new__(MonitorService)
            service.config = SimpleNamespace(public_timetable_url="")
            service.stores = {tenant.id: store}
            service.notifiers = {tenant.id: notifier}
            now = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
            baseline = {
                "date": "2026-09-17",
                "recommendation": {"outbound": None, "return": _connection(delay_seconds=0)},
            }
            changed = {
                "date": "2026-09-17",
                "recommendation": {"outbound": None, "return": _connection(delay_seconds=300)},
            }

            service._notify_transit_recommendation_change(tenant, baseline, now)
            self.assertEqual(notifier.messages, [])

            service._notify_transit_recommendation_change(tenant, changed, now)
            self.assertEqual(len(notifier.messages), 1)
            self.assertEqual(
                store.load_transit_recommendation()["recommendation"],
                _transit_recommendation_snapshot(changed)["recommendation"],
            )

    def test_monitor_does_not_repeat_identical_notification_after_oscillation(self):
        class _Notifier:
            def __init__(self):
                self.messages = []

            def send_email(self, subject, body, html_body=None):
                self.messages.append((subject, body, html_body))
                return True

        with tempfile.TemporaryDirectory() as directory:
            store = SnapshotStore(Path(directory))
            notifier = _Notifier()
            tenant = SimpleNamespace(
                id="tenant-1",
                name="Testprofil",
                email=SimpleNamespace(enabled=True),
            )
            service = object.__new__(MonitorService)
            service.config = SimpleNamespace(public_timetable_url="")
            service.stores = {tenant.id: store}
            service.notifiers = {tenant.id: notifier}
            service._transit_notification_locks = {}
            now = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
            baseline = {
                "date": "2026-09-17",
                "recommendation": {"outbound": None, "return": _connection(delay_seconds=0)},
            }
            changed = {
                "date": "2026-09-17",
                "recommendation": {"outbound": None, "return": _connection(delay_seconds=300)},
            }

            service._notify_transit_recommendation_change(tenant, baseline, now)
            service._notify_transit_recommendation_change(tenant, changed, now)
            service._notify_transit_recommendation_change(tenant, baseline, now)
            service._notify_transit_recommendation_change(tenant, changed, now)

            self.assertEqual(len(notifier.messages), 2)
            self.assertNotEqual(notifier.messages[0], notifier.messages[1])

    def test_parallel_monitor_checks_send_changed_email_once(self):
        class _Notifier:
            def __init__(self):
                self.messages = []

            def send_email(self, subject, body, html_body=None):
                time.sleep(0.05)
                self.messages.append((subject, body, html_body))
                return True

        with tempfile.TemporaryDirectory() as directory:
            store = SnapshotStore(Path(directory))
            notifier = _Notifier()
            tenant = SimpleNamespace(
                id="tenant-1",
                name="Testprofil",
                email=SimpleNamespace(enabled=True),
            )
            service = object.__new__(MonitorService)
            service.config = SimpleNamespace(public_timetable_url="")
            service.stores = {tenant.id: store}
            service.notifiers = {tenant.id: notifier}
            service._transit_notification_locks = {}
            now = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
            baseline = {
                "date": "2026-09-17",
                "recommendation": {"outbound": None, "return": _connection(delay_seconds=0)},
            }
            changed = {
                "date": "2026-09-17",
                "recommendation": {"outbound": None, "return": _connection(delay_seconds=300)},
            }
            service._notify_transit_recommendation_change(tenant, baseline, now)

            threads = [
                threading.Thread(
                    target=service._notify_transit_recommendation_change,
                    args=(tenant, changed, now),
                )
                for _ in range(2)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            self.assertEqual(len(notifier.messages), 1)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milo_webuntis.diff import build_notification, build_notification_html, diff_lessons, group_by_date
from milo_webuntis.service import _comparison_dates, monitor_window


def lesson(uid, day="2026-08-28", subject="Mathe", room="101", status="regular"):
    return {
        "uid": uid,
        "date": day,
        "start": "08:00",
        "end": "08:45",
        "subject": [subject],
        "teacher": ["Meyer"],
        "room": [room],
        "status": status,
        "lesson_text": "",
        "substitution_text": "",
        "info": "",
    }


class DiffTests(unittest.TestCase):
    def test_diff_detects_changed_lesson(self):
        changes = diff_lessons([lesson("1")], [lesson("1", room="203", status="changed")])

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].kind, "changed")
        self.assertEqual(changes[0].before["room"], ["101"])
        self.assertEqual(changes[0].after["room"], ["203"])


    def test_diff_detects_added_and_removed_lessons(self):
        changes = diff_lessons([lesson("1")], [lesson("2", subject="Deutsch")])

        self.assertEqual([change.kind for change in changes], ["removed", "added"])


    def test_diff_ignores_week_window_rollover_outside_overlap(self):
        comparable_dates = {
            "2026-08-31",
            "2026-09-01",
            "2026-09-02",
            "2026-09-03",
            "2026-09-04",
        }
        previous = [
            lesson("old-week", day="2026-08-28", subject="Deutsch"),
            lesson("changed", day="2026-09-01", room="101"),
            lesson("removed-inside", day="2026-09-02", subject="Musik"),
        ]
        current = [
            lesson("changed", day="2026-09-01", room="203", status="changed"),
            lesson("new-week", day="2026-09-07", subject="Englisch"),
        ]

        changes = diff_lessons(previous, current, comparable_dates=comparable_dates)

        self.assertEqual([change.kind for change in changes], ["changed", "removed"])
        self.assertEqual([change.date for change in changes], ["2026-09-01", "2026-09-02"])


    def test_comparison_dates_use_only_overlapping_monitor_windows(self):
        previous_payload = {"timestamp": "2026-08-28T12:00:00+02:00", "lessons": []}

        dates = _comparison_dates(previous_payload, date(2026, 8, 31))

        self.assertEqual(
            dates,
            {
                "2026-08-31",
                "2026-09-01",
                "2026-09-02",
                "2026-09-03",
                "2026-09-04",
            },
        )


    def test_group_by_date_sorts_lessons(self):
        later = lesson("2")
        later["start"] = "10:00"
        earlier = lesson("1")
        earlier["start"] = "08:00"

        grouped = group_by_date([later, earlier])

        self.assertEqual(grouped["2026-08-28"][0]["uid"], "1")


    def test_notification_contains_changed_day_schedule(self):
        changes = diff_lessons([lesson("1")], [lesson("1", room="203", status="changed")])

        subject, body = build_notification(
            changes,
            [lesson("1", room="203", status="changed")],
            today=date(2026, 8, 28),
        )

        self.assertEqual(subject, "Dein Stundenplan hat sich geändert: 28.08.2026")
        self.assertIn("Freitag, 28.08.2026", body)
        self.assertIn("Raum: 101 → 203", body)
        self.assertNotIn("[changed]", body)
        html_body = build_notification_html(changes, "https://example.test/app")
        self.assertIn("Das ist neu", html_body)
        self.assertIn("Raum", html_body)
        self.assertIn("203", html_body)
        self.assertIn("vorher 101", html_body)
        self.assertIn("https://example.test/app", html_body)


    def test_notification_explains_cancelled_lesson_in_simple_words(self):
        cancelled = lesson("1", status="cancelled")
        changes = diff_lessons([lesson("1")], [cancelled])

        _subject, body = build_notification(changes, [cancelled], today=date(2026, 8, 28))

        self.assertIn("FÄLLT AUS: Mathe, 08:00–08:45 Uhr", body)
        self.assertNotIn("Entfällt", body)
        html_body = build_notification_html(changes)
        self.assertIn("Fällt aus", html_body)
        self.assertIn("#ef4444", html_body)


    def test_monitor_window_covers_current_and_next_school_week(self):
        start, end = monitor_window(date(2026, 8, 29))

        self.assertEqual(start.isoformat(), "2026-08-24")
        self.assertEqual(end.isoformat(), "2026-09-04")


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milo_webuntis.service import (
    _cleanup_completed_homework_state,
    _homework_completed_retention_expired,
    _next_subject_due_date,
    _resolve_homework_due_date,
    _with_homework_status,
    _with_local_completion,
)
from milo_webuntis.webuntis_client import normalize_homeworks, normalize_rest_entry


class HomeworkTests(unittest.TestCase):
    def test_normalize_homeworks_maps_lesson_subject_teacher_and_due_date(self):
        data = {
            "homeworks": [
                {
                    "id": 1001,
                    "lessonId": 55,
                    "date": 20260907,
                    "dueDate": 20260910,
                    "text": "S. 12 Nr. 1",
                    "completed": False,
                }
            ],
            "lessons": [
                {"id": 55, "subject": {"displayName": "Mathematik"}}
            ],
            "records": [
                {"homeworkId": 1001, "teacherId": 9}
            ],
            "teachers": [
                {"id": 9, "displayName": "Conrads"}
            ],
        }

        result = normalize_homeworks(data)

        self.assertEqual(result[0]["id"], "webuntis:1001")
        self.assertEqual(result[0]["source"], "webuntis")
        self.assertEqual(result[0]["subject"], ["Mathematik"])
        self.assertEqual(result[0]["teacher"], ["Conrads"])
        self.assertEqual(result[0]["due_date"], "2026-09-10")

    def test_local_completion_overrides_webuntis_state(self):
        item = {"id": "webuntis:1001", "completed": False}
        state = {"webuntis:1001": {"completed": True, "completed_at": "2026-09-09T10:00:00"}}

        result = _with_local_completion(item, state)

        self.assertTrue(result["completed"])
        self.assertEqual(result["completed_at"], "2026-09-09T10:00:00")

    def test_homework_status_marks_past_due_open_item_as_expired(self):
        item = {"id": "webuntis:1001", "completed": False, "due_date": "2026-09-08"}

        result = _with_homework_status(item, {}, date(2026, 9, 9))

        self.assertFalse(result["completed"])
        self.assertTrue(result["is_expired"])

    def test_completed_homework_retention_keeps_item_for_six_days_after_due_date(self):
        item = {"id": "manual:1", "completed": True, "due_date": "2026-09-10"}

        self.assertFalse(_homework_completed_retention_expired(item, date(2026, 9, 16)))

    def test_completed_homework_retention_removes_item_after_seven_days_after_due_date(self):
        item = {"id": "manual:1", "completed": True, "due_date": "2026-09-10"}

        self.assertTrue(_homework_completed_retention_expired(item, date(2026, 9, 17)))

    def test_cleanup_removes_completed_manual_homework_and_completion_state(self):
        manual_item = {
            "id": "manual:1",
            "source": "manual",
            "completed": True,
            "due_date": "2026-09-10",
        }
        state = {
            "manual": [manual_item, {"id": "manual:2", "source": "manual", "due_date": "2026-09-18"}],
            "completed": {"manual:1": {"completed": True}, "webuntis:1": {"completed": True}},
        }

        cleaned_state, visible_items, changed = _cleanup_completed_homework_state(
            state,
            [manual_item, {"id": "manual:2", "source": "manual", "completed": False, "due_date": "2026-09-18"}],
            date(2026, 9, 17),
        )

        self.assertTrue(changed)
        self.assertEqual([item["id"] for item in cleaned_state["manual"]], ["manual:2"])
        self.assertNotIn("manual:1", cleaned_state["completed"])
        self.assertEqual([item["id"] for item in visible_items], ["manual:2"])

    def test_cleanup_hides_old_completed_webuntis_homework_from_response(self):
        webuntis_item = {
            "id": "webuntis:1",
            "source": "webuntis",
            "completed": True,
            "due_date": "2026-09-10",
        }
        state = {"manual": [], "completed": {}}

        cleaned_state, visible_items, changed = _cleanup_completed_homework_state(
            state,
            [webuntis_item],
            date(2026, 9, 17),
        )

        self.assertFalse(changed)
        self.assertEqual(cleaned_state, state)
        self.assertEqual(visible_items, [])

    def test_missing_due_date_uses_next_matching_subject_lesson(self):
        lessons = [
            {"date": "2026-09-08", "subject": ["Englisch"]},
            {"date": "2026-09-11", "subject": ["Mathematik (Ma)"]},
            {"date": "2026-09-14", "subject": ["Mathematik (Ma)"]},
        ]

        result = _next_subject_due_date("Mathematik", lessons, date(2026, 9, 9))

        self.assertEqual(result, "2026-09-11")

    def test_resolve_homework_due_date_uses_subject_fallback(self):
        homework = {"id": "manual:test", "subject": ["Englisch"], "due_date": ""}
        lessons = [{"date": "2026-09-10", "subject": ["Englisch (En)"]}]

        result = _resolve_homework_due_date(homework, lessons, date(2026, 9, 9))

        self.assertEqual(result["due_date"], "2026-09-10")

    def test_normalize_rest_entry_still_returns_timetable_lesson(self):
        entry = {
            "duration": {
                "start": "2026-09-09T08:00:00",
                "end": "2026-09-09T08:45:00",
            },
            "position1": [{"current": {"displayName": "Deutsch"}}],
            "position2": [{"current": {"displayName": "Meyer"}}],
            "position3": [{"current": {"displayName": "A18"}}],
            "ids": [1],
            "status": "REGULAR",
        }

        result = normalize_rest_entry("2026-09-09", entry)

        self.assertIsNotNone(result)
        self.assertEqual(result["subject"], ["Deutsch"])


if __name__ == "__main__":
    unittest.main()

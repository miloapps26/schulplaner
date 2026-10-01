from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class SnapshotStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.snapshots_dir = data_dir / "snapshots"
        self.runs_path = data_dir / "runs.jsonl"
        self.latest_path = self.snapshots_dir / "latest.json"
        self.homework_path = data_dir / "homework.json"
        self.exams_path = data_dir / "exams.json"
        self.manual_lessons_path = data_dir / "manual_lessons.json"
        self.pending_notification_path = data_dir / "pending_notification.json"
        self.transit_recommendation_path = data_dir / "transit_recommendation.json"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def load_latest(self) -> list[dict[str, Any]] | None:
        if not self.latest_path.exists():
            return None
        payload = json.loads(self.latest_path.read_text(encoding="utf-8"))
        return payload.get("lessons", [])

    def load_latest_payload(self) -> dict[str, Any] | None:
        if not self.latest_path.exists():
            return None
        return json.loads(self.latest_path.read_text(encoding="utf-8"))

    def save_latest(self, lessons: list[dict[str, Any]], timestamp: datetime) -> None:
        payload = {"timestamp": timestamp.isoformat(), "lessons": lessons}
        self.latest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        history_path = self.snapshots_dir / f"{timestamp.strftime('%Y%m%d-%H%M%S')}.json"
        history_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def append_run(self, payload: dict[str, Any]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with self.runs_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def load_pending_notification(self) -> dict[str, Any] | None:
        if not self.pending_notification_path.exists():
            return None
        return json.loads(self.pending_notification_path.read_text(encoding="utf-8"))

    def save_pending_notification(self, payload: dict[str, Any]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.pending_notification_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear_pending_notification(self) -> None:
        if self.pending_notification_path.exists():
            self.pending_notification_path.unlink()

    def load_transit_recommendation(self) -> dict[str, Any] | None:
        if not self.transit_recommendation_path.exists():
            return None
        try:
            payload = json.loads(self.transit_recommendation_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def save_transit_recommendation(self, payload: dict[str, Any]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.transit_recommendation_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_homework_state(self) -> dict[str, Any]:
        if not self.homework_path.exists():
            return {"manual": [], "completed": {}}
        try:
            payload = json.loads(self.homework_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"manual": [], "completed": {}}
        return {
            "manual": payload.get("manual") if isinstance(payload.get("manual"), list) else [],
            "completed": payload.get("completed") if isinstance(payload.get("completed"), dict) else {},
        }

    def save_homework_state(self, payload: dict[str, Any]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.homework_path.write_text(
            json.dumps(
                {
                    "manual": payload.get("manual") if isinstance(payload.get("manual"), list) else [],
                    "completed": payload.get("completed") if isinstance(payload.get("completed"), dict) else {},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load_exam_state(self) -> dict[str, Any]:
        if not self.exams_path.exists():
            return {"items": [], "known_ids": [], "notified_ids": [], "timestamp": ""}
        try:
            payload = json.loads(self.exams_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"items": [], "known_ids": [], "notified_ids": [], "timestamp": ""}
        return {
            "items": payload.get("items") if isinstance(payload.get("items"), list) else [],
            "known_ids": payload.get("known_ids") if isinstance(payload.get("known_ids"), list) else [],
            "notified_ids": payload.get("notified_ids") if isinstance(payload.get("notified_ids"), list) else [],
            "timestamp": str(payload.get("timestamp") or ""),
            "source_error": str(payload.get("source_error") or ""),
        }

    def save_exam_state(self, payload: dict[str, Any]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.exams_path.write_text(
            json.dumps(
                {
                    "items": payload.get("items") if isinstance(payload.get("items"), list) else [],
                    "known_ids": payload.get("known_ids") if isinstance(payload.get("known_ids"), list) else [],
                    "notified_ids": payload.get("notified_ids") if isinstance(payload.get("notified_ids"), list) else [],
                    "timestamp": str(payload.get("timestamp") or ""),
                    "source_error": str(payload.get("source_error") or ""),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load_manual_lessons_state(self) -> dict[str, Any]:
        if not self.manual_lessons_path.exists():
            return {"items": []}
        try:
            payload = json.loads(self.manual_lessons_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"items": []}
        return {
            "items": payload.get("items") if isinstance(payload.get("items"), list) else [],
        }

    def save_manual_lessons_state(self, payload: dict[str, Any]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.manual_lessons_path.write_text(
            json.dumps(
                {
                    "items": payload.get("items") if isinstance(payload.get("items"), list) else [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def runs(self, limit: int = 25) -> list[dict[str, Any]]:
        if not self.runs_path.exists():
            return []
        lines = self.runs_path.read_text(encoding="utf-8").splitlines()[-limit:]
        items = []
        for line in lines:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(items))

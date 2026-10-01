from __future__ import annotations

import base64
import hashlib
import hmac
import struct
from datetime import date
import time
from typing import Any
from urllib.parse import quote

import requests

from .config import WebUntisConfig


class WebUntisError(RuntimeError):
    pass


class WebUntisClient:
    def __init__(self, config: WebUntisConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/138.0.0.0 Safari/537.36"
                ),
            }
        )
        self._request_id = 0
        self._session_id: str | None = None

    @property
    def endpoint(self) -> str:
        server = self.config.server.rstrip("/")
        if not server.startswith(("http://", "https://")):
            server = f"https://{server}"
        school = quote(self.config.school)
        return f"{server}/WebUntis/jsonrpc.do?school={school}"

    def __enter__(self) -> "WebUntisClient":
        self.login()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.logout()

    def _call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        self._request_id += 1
        payload = {
            "id": str(self._request_id),
            "method": method,
            "params": params or {},
            "jsonrpc": "2.0",
        }
        response = self.session.post(self.endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            error = data["error"]
            message = error.get("message") or error.get("data") or str(error)
            raise WebUntisError(f"{method}: {message}")
        return data.get("result")

    def login(self) -> None:
        if self.config.app_secret:
            self._login_with_app_secret()
            return

        result = self._call(
            "authenticate",
            {
                "user": self.config.username,
                "password": self.config.password,
                "client": "Schulplaner",
            },
        )
        self._session_id = result.get("sessionId") if isinstance(result, dict) else None
        if self._session_id:
            self.session.cookies.set("JSESSIONID", self._session_id)

    def _login_with_app_secret(self) -> None:
        server = self.config.server.rstrip("/")
        if not server.startswith(("http://", "https://")):
            server = f"https://{server}"

        last_message = "App-Schlüssel-Login fehlgeschlagen."
        for offset in (-1, 0, 1):
            token = _totp(self.config.app_secret, offset=offset)
            response = self.session.post(
                f"{server}/WebUntis/jsonrpc_intern.do",
                params={"m": "getUserData2017", "school": self.config.school, "v": "i2.2"},
                json={
                    "id": "Schulplaner",
                    "method": "getUserData2017",
                    "params": [
                        {
                            "auth": {
                                "clientTime": int(time.time() * 1000),
                                "user": self.config.username,
                                "otp": token,
                            }
                        }
                    ],
                    "jsonrpc": "2.0",
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("error"):
                error = data["error"]
                last_message = error.get("message") or error.get("data") or str(error)
                continue

            self._session_id = self.session.cookies.get("JSESSIONID")
            if self._session_id:
                return

        raise WebUntisError(f"getUserData2017: {last_message}")

    def logout(self) -> None:
        try:
            self._call("logout")
        except Exception:
            pass

    def classes(self) -> list[dict[str, Any]]:
        result = self._call("getKlassen")
        return result if isinstance(result, list) else []

    def subjects(self) -> dict[int, dict[str, Any]]:
        return self._by_id(self._call("getSubjects"))

    def teachers(self) -> dict[int, dict[str, Any]]:
        return self._by_id(self._call("getTeachers"))

    def rooms(self) -> dict[int, dict[str, Any]]:
        return self._by_id(self._call("getRooms"))

    def resolve_element_id(self) -> int:
        if self.config.element_id is not None:
            return self.config.element_id
        wanted = self.config.class_name.strip().lower()
        for item in self.classes():
            names = {
                str(item.get("name", "")).strip().lower(),
                str(item.get("longName", "")).strip().lower(),
                str(item.get("displayname", "")).strip().lower(),
            }
            if wanted in names:
                return int(item["id"])
        raise WebUntisError(f"Klasse nicht gefunden: {self.config.class_name}")

    def timetable(self, start: date, end: date) -> list[dict[str, Any]]:
        if self.config.app_secret:
            return self._rest_timetable(start, end)

        element_id = self.resolve_element_id()
        result = self._call(
            "getTimetable",
            {
                "options": {
                    "element": {"id": element_id, "type": self.config.element_type},
                    "startDate": int(start.strftime("%Y%m%d")),
                    "endDate": int(end.strftime("%Y%m%d")),
                    "showBooking": True,
                    "showInfo": True,
                    "showSubstText": True,
                    "showLsText": True,
                }
            },
        )
        lessons = result if isinstance(result, list) else []
        refs = {
            "subjects": self.subjects(),
            "teachers": self.teachers(),
            "rooms": self.rooms(),
        }
        return [normalize_lesson(lesson, refs) for lesson in lessons]

    def homeworks(self, start: date, end: date) -> list[dict[str, Any]]:
        base = self.config.server.rstrip("/")
        if not base.startswith(("http://", "https://")):
            base = f"https://{base}"

        self.session.cookies.set(
            "schoolname",
            f"_{base64.b64encode(self.config.school.encode('utf-8')).decode('ascii')}",
        )
        response = self.session.get(
            f"{base}/WebUntis/api/homeworks/lessons",
            params={
                "startDate": start.strftime("%Y%m%d"),
                "endDate": end.strftime("%Y%m%d"),
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else {}
        return normalize_homeworks(data if isinstance(data, dict) else {})

    def _rest_timetable(self, start: date, end: date) -> list[dict[str, Any]]:
        base = self.config.server.rstrip("/")
        if not base.startswith(("http://", "https://")):
            base = f"https://{base}"

        token_response = self.session.get(f"{base}/WebUntis/api/token/new", timeout=30)
        token_response.raise_for_status()
        token = token_response.text.strip().strip('"')
        if not token:
            raise WebUntisError("Kein Bearer-Token für WebUntis-REST erhalten.")

        response = self.session.get(
            f"{base}/WebUntis/api/rest/view/v1/timetable/entries",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "start": start.isoformat(),
                "end": end.isoformat(),
                "format": "1",
                "resourceType": _resource_type(self.config.element_type),
                "resources": str(self.resolve_element_id()),
                "periodTypes": "",
                "timetableType": "MY_TIMETABLE",
                "layout": "START_TIME",
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        lessons = normalize_rest_timetable(data)

        cancelled = [
            item
            for item in self._legacy_timetable(start, end)
            if item.get("status") == "cancelled"
            and not _has_matching_cancelled_source(item, lessons)
        ]
        return sorted(lessons + cancelled, key=lambda item: (item["date"], item["start"], item["end"], item["uid"]))

    def _legacy_timetable(self, start: date, end: date) -> list[dict[str, Any]]:
        element_id = self.resolve_element_id()
        result = self._call(
            "getTimetable",
            {
                "options": {
                    "element": {"id": element_id, "type": self.config.element_type},
                    "startDate": int(start.strftime("%Y%m%d")),
                    "endDate": int(end.strftime("%Y%m%d")),
                    "showBooking": True,
                    "showInfo": True,
                    "showSubstText": True,
                    "showLsText": True,
                }
            },
        )
        lessons = result if isinstance(result, list) else []
        refs = {
            "subjects": self.subjects(),
            "teachers": self.teachers(),
            "rooms": self.rooms(),
        }
        return [normalize_lesson(lesson, refs) for lesson in lessons]

    @staticmethod
    def _by_id(items: Any) -> dict[int, dict[str, Any]]:
        if not isinstance(items, list):
            return {}
        mapped = {}
        for item in items:
            if isinstance(item, dict) and "id" in item:
                try:
                    mapped[int(item["id"])] = item
                except (TypeError, ValueError):
                    continue
        return mapped


def normalize_lesson(
    lesson: dict[str, Any], refs: dict[str, dict[int, dict[str, Any]]]
) -> dict[str, Any]:
    subject = _entity_names(lesson.get("su"), refs["subjects"])
    teacher = _entity_names(lesson.get("te"), refs["teachers"])
    room = _entity_names(lesson.get("ro"), refs["rooms"])
    class_names = _entity_names(lesson.get("kl"), {})

    raw_code = str(lesson.get("code") or "").lower()
    raw_type = str(lesson.get("lstype") or "").lower()
    if "cancel" in raw_code:
        status = "cancelled"
    elif raw_code or raw_type in {"subst", "irregular"}:
        status = "changed"
    else:
        status = "regular"

    return {
        "uid": str(lesson.get("id") or _fallback_uid(lesson, subject, teacher, room)),
        "date": _format_date(lesson.get("date")),
        "start": _format_time(lesson.get("startTime")),
        "end": _format_time(lesson.get("endTime")),
        "subject": subject,
        "teacher": teacher,
        "room": room,
        "class": class_names,
        "status": status,
        "code": raw_code,
        "type": raw_type,
        "lesson_text": str(lesson.get("lstext") or "").strip(),
        "substitution_text": str(lesson.get("substText") or "").strip(),
        "info": str(lesson.get("info") or "").strip(),
    }


def normalize_rest_timetable(data: dict[str, Any]) -> list[dict[str, Any]]:
    lessons: list[dict[str, Any]] = []
    for day in data.get("days") or []:
        for entry in day.get("gridEntries") or []:
            lesson = normalize_rest_entry(day.get("date", ""), entry)
            if lesson:
                lessons.append(lesson)
    return lessons


def normalize_rest_entry(day: str, entry: dict[str, Any]) -> dict[str, Any] | None:
    duration = entry.get("duration") or {}
    start = _time_from_iso(duration.get("start"))
    end = _time_from_iso(duration.get("end"))
    if not day or not start or not end:
        return None

    subjects = _rest_position_names(entry.get("position1"))
    teachers = _rest_position_names(entry.get("position2"))
    rooms = _rest_position_names(entry.get("position3"))
    removed = {
        "subject": _rest_position_names(entry.get("position1"), field="removed"),
        "teacher": _rest_position_names(entry.get("position2"), field="removed"),
        "room": _rest_position_names(entry.get("position3"), field="removed"),
    }

    status = _rest_status(entry)
    lesson_text = str(entry.get("lessonText") or entry.get("name") or "").strip()
    substitution_text = str(entry.get("substitutionText") or entry.get("notesAll") or "").strip()
    ids = entry.get("ids") if isinstance(entry.get("ids"), list) else []
    uid = "rest:" + "-".join(str(item) for item in ids) if ids else f"rest:{day}:{start}:{end}:{subjects}:{teachers}:{rooms}"

    return {
        "uid": uid,
        "date": day,
        "start": start,
        "end": end,
        "subject": subjects,
        "teacher": teachers,
        "room": rooms,
        "removed": removed,
        "class": [],
        "status": status,
        "code": str(entry.get("status") or "").lower(),
        "type": str(entry.get("type") or "").lower(),
        "lesson_text": lesson_text,
        "substitution_text": substitution_text,
        "info": str(entry.get("lessonInfo") or "").strip(),
    }


def normalize_homeworks(data: dict[str, Any]) -> list[dict[str, Any]]:
    lessons = _items_by_id(data.get("lessons"))
    records_by_homework = _records_by_homework(data.get("records"))
    teachers = _items_by_id(data.get("teachers"))
    normalized: list[dict[str, Any]] = []

    for item in data.get("homeworks") or []:
        if not isinstance(item, dict) or item.get("id") is None:
            continue
        external_id = str(item["id"])
        lesson_id = item.get("lessonId")
        lesson = lessons.get(str(lesson_id), {})
        record = records_by_homework.get(external_id, {})
        teacher = teachers.get(str(record.get("teacherId")), {})
        text = str(item.get("text") or "").strip()
        remark = str(item.get("remark") or "").strip()
        if not text and not remark:
            continue

        normalized.append(
            {
                "id": f"webuntis:{external_id}",
                "source": "webuntis",
                "external_id": external_id,
                "text": text,
                "remark": remark,
                "assigned_date": _format_date(item.get("date")),
                "due_date": _format_date(item.get("dueDate")),
                "lesson_id": str(lesson_id) if lesson_id is not None else "",
                "subject": _homework_subjects(lesson),
                "teacher": _homework_teacher(teacher),
                "attachments": item.get("attachments") if isinstance(item.get("attachments"), list) else [],
                "completed": bool(item.get("completed")),
            }
        )

    return sorted(
        normalized,
        key=lambda homework: (
            homework.get("due_date") or "9999-12-31",
            ", ".join(homework.get("subject") or []),
            homework.get("text") or "",
        ),
    )


def _entity_names(values: Any, reference: dict[int, dict[str, Any]]) -> list[str]:
    if not isinstance(values, list):
        return []

    names: list[str] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        ref = None
        try:
            ref = reference.get(int(value.get("id"))) if value.get("id") is not None else None
        except (TypeError, ValueError):
            ref = None

        source = ref or value
        name = (
            source.get("displayname")
            or source.get("longName")
            or source.get("name")
            or value.get("name")
            or value.get("longname")
        )
        if name:
            names.append(str(name))
    return names


def _items_by_id(items: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        return {}
    mapped = {}
    for item in items:
        if isinstance(item, dict) and item.get("id") is not None:
            mapped[str(item["id"])] = item
    return mapped


def _records_by_homework(items: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        return {}
    mapped = {}
    for item in items:
        if isinstance(item, dict) and item.get("homeworkId") is not None:
            mapped[str(item["homeworkId"])] = item
    return mapped


def _homework_subjects(lesson: dict[str, Any]) -> list[str]:
    subject = lesson.get("subject") if isinstance(lesson, dict) else None
    if isinstance(subject, list):
        return unique_names(subject)
    if isinstance(subject, dict):
        return unique_names([subject])
    if subject:
        return [str(subject)]

    candidates = lesson.get("subjects") if isinstance(lesson, dict) else None
    if isinstance(candidates, list):
        return unique_names(candidates)
    return []


def _homework_teacher(teacher: dict[str, Any]) -> list[str]:
    if not teacher:
        return []
    return unique_names([teacher])


def unique_names(items: list[Any]) -> list[str]:
    names: list[str] = []
    for item in items:
        if isinstance(item, dict):
            name = (
                item.get("displayName")
                or item.get("displayname")
                or item.get("longName")
                or item.get("shortName")
                or item.get("name")
            )
        else:
            name = item
        if name and str(name) not in names:
            names.append(str(name))
    return names


def _rest_position_names(values: Any, field: str = "current") -> list[str]:
    if not isinstance(values, list):
        return []
    names: list[str] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        item = value.get(field)
        if not isinstance(item, dict):
            continue
        name = item.get("displayName") or item.get("longName") or item.get("shortName")
        if name:
            names.append(str(name))
    return names


def _rest_status(entry: dict[str, Any]) -> str:
    raw_status = str(entry.get("status") or "").upper()
    raw_type = str(entry.get("type") or "").upper()
    positions = [
        entry.get("position1"),
        entry.get("position2"),
        entry.get("position3"),
    ]
    has_removed = any(_rest_position_names(position, field="removed") for position in positions)
    if raw_status in {"CANCELLED", "CANCELED"}:
        return "cancelled"
    if raw_status in {"CHANGED", "ADDITIONAL"} or raw_type in {"EVENT", "ADDITIONAL_PERIOD"} or has_removed:
        return "changed"
    return "regular"


def _time_from_iso(value: Any) -> str:
    text = str(value or "")
    if "T" not in text:
        return ""
    return text.split("T", 1)[1][:5]


def _resource_type(element_type: int) -> str:
    return {
        1: "CLASS",
        2: "TEACHER",
        3: "SUBJECT",
        4: "ROOM",
        5: "STUDENT",
    }.get(element_type, "STUDENT")


def _has_matching_cancelled_source(
    cancelled: dict[str, Any], lessons: list[dict[str, Any]]
) -> bool:
    cancelled_subjects = set(cancelled.get("subject") or [])
    for lesson in lessons:
        if lesson.get("date") != cancelled.get("date"):
            continue
        if not lesson.get("start") <= cancelled.get("start", "") < lesson.get("end"):
            continue
        removed_subjects = set((lesson.get("removed") or {}).get("subject") or [])
        if cancelled_subjects & removed_subjects:
            return True
    return False


def _format_date(value: Any) -> str:
    text = str(value or "")
    if len(text) == 8:
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text


def _format_time(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return ""
    return f"{number // 100:02d}:{number % 100:02d}"


def _fallback_uid(
    lesson: dict[str, Any], subject: list[str], teacher: list[str], room: list[str]
) -> str:
    parts = [
        str(lesson.get("date", "")),
        str(lesson.get("startTime", "")),
        str(lesson.get("endTime", "")),
        "|".join(subject),
        "|".join(teacher),
        "|".join(room),
    ]
    return "::".join(parts)


def _totp(secret: str, offset: int = 0, step: int = 30, digits: int = 6) -> str:
    normalized = "".join(secret.split()).upper()
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    try:
        key = base64.b32decode(normalized + padding, casefold=True)
    except Exception as exc:
        raise WebUntisError("WEBUNTIS_APP_SECRET ist kein gültiger QR-/App-Schlüssel.") from exc

    counter = int(time.time() / step) + offset
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    index = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[index : index + 4])[0] & 0x7FFFFFFF
    return str(code % (10**digits)).zfill(digits)

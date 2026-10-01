from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Change:
    date: str
    kind: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "kind": self.kind,
            "before": self.before,
            "after": self.after,
        }


def group_by_date(lessons: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for lesson in lessons:
        grouped.setdefault(lesson.get("date", ""), []).append(lesson)
    for items in grouped.values():
        items.sort(key=lambda item: (item.get("start", ""), item.get("end", ""), item.get("uid", "")))
    return dict(sorted(grouped.items()))


def diff_lessons(
    previous: list[dict[str, Any]],
    current: list[dict[str, Any]],
    comparable_dates: set[str] | None = None,
) -> list[Change]:
    old = {
        item["uid"]: item
        for item in previous
        if _is_comparable_date(item, comparable_dates)
    }
    new = {
        item["uid"]: item
        for item in current
        if _is_comparable_date(item, comparable_dates)
    }

    changes: list[Change] = []
    for uid in sorted(set(old) - set(new)):
        changes.append(Change(date=old[uid].get("date", ""), kind="removed", before=old[uid], after=None))
    for uid in sorted(set(new) - set(old)):
        changes.append(Change(date=new[uid].get("date", ""), kind="added", before=None, after=new[uid]))
    for uid in sorted(set(old) & set(new)):
        if _stable_json(old[uid]) != _stable_json(new[uid]):
            changes.append(Change(date=new[uid].get("date", ""), kind="changed", before=old[uid], after=new[uid]))

    kind_order = {"removed": 0, "changed": 1, "added": 2}
    return sorted(
        changes,
        key=lambda item: (item.date, _change_time(item), kind_order.get(item.kind, 99)),
    )


def build_notification(
    changes: list[Change], current: list[dict[str, Any]], today: date | None = None
) -> tuple[str, str]:
    affected_dates = sorted({change.date for change in changes if change.date})
    title_date = ", ".join(_display_date(day) for day in affected_dates[:3])
    if len(affected_dates) > 3:
        title_date += f" +{len(affected_dates) - 3}"
    subject = f"Dein Stundenplan hat sich geändert: {title_date}".strip()

    lines = [
        "Hallo,",
        "",
        "das ist in deinem Stundenplan neu:",
        "",
    ]

    for day in affected_dates:
        lines.append(_display_day(day))
        for change in [item for item in changes if item.date == day]:
            lines.append(_format_change(change))
        lines.append("")

    return subject, "\n".join(lines).strip()


def build_notification_html(
    changes: list[Change],
    timetable_url: str = "",
) -> str:
    affected_dates = sorted({change.date for change in changes if change.date})
    day_sections: list[str] = []
    for day in affected_dates:
        cards = "".join(_format_change_html(change) for change in changes if change.date == day)
        day_sections.append(
            f'<section style="margin-top:18px">'
            f'<h2 style="margin:0 0 8px;color:#f8fafc;font-size:18px">{html.escape(_display_day(day))}</h2>'
            f'{cards}</section>'
        )
    link = (
        f'<p style="margin:20px 0 0"><a href="{html.escape(timetable_url, quote=True)}" '
        'style="display:inline-block;padding:10px 14px;border-radius:6px;background:#2dd4bf;color:#07151c;font-weight:800;text-decoration:none">Stundenplan öffnen</a></p>'
        if timetable_url
        else ""
    )
    return f"""<!doctype html>
<html lang="de">
  <body style="margin:0;padding:18px;background:#0b1220;color:#f8fafc;font-family:Arial,sans-serif">
    <main style="max-width:620px;margin:0 auto;padding:20px;border:1px solid #273449;border-radius:8px;background:#111827">
      <p style="margin:0 0 6px;color:#2dd4bf;font-size:13px;font-weight:800;text-transform:uppercase">Stundenplanänderung</p>
      <h1 style="margin:0;font-size:24px">Das ist neu</h1>
      {''.join(day_sections)}
      {link}
    </main>
  </body>
</html>"""


def _stable_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _is_comparable_date(item: dict[str, Any], comparable_dates: set[str] | None) -> bool:
    return comparable_dates is None or str(item.get("date", "")) in comparable_dates


def _change_time(change: Change) -> str:
    item = change.after or change.before or {}
    return str(item.get("start", ""))


def _display_date(value: str) -> str:
    try:
        year, month, day = value.split("-")
        return f"{day}.{month}.{year}"
    except ValueError:
        return value


def _display_day(value: str) -> str:
    weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return _display_date(value)
    return f"{weekdays[parsed.weekday()]}, {_display_date(value)}"


def _format_change(change: Change) -> str:
    after = change.after or {}
    before = change.before or {}
    lesson = after or before
    if lesson.get("status") == "cancelled":
        return f"- FÄLLT AUS: {_lesson_name(lesson)}, {_lesson_time_short(lesson)}"
    if change.kind == "added":
        return f"- NEU: {_lesson_name(after)}, {_lesson_time_short(after)}{_short_place(after)}"
    if change.kind == "removed":
        return f"- NICHT MEHR IM PLAN: {_lesson_name(before)}, {_lesson_time_short(before)}"
    details = _format_change_details(before, after)
    if not details:
        return f"- GEÄNDERT: {_lesson_name(after)}, {_lesson_time_short(after)}"
    return "\n".join(
        [f"- {_lesson_name(after)}, {_lesson_time_short(after)}:"]
        + [f"  {detail}" for detail in details]
    )


def _format_change_html(change: Change) -> str:
    before = change.before or {}
    after = change.after or {}
    lesson = after or before
    cancelled = lesson.get("status") == "cancelled" or change.kind == "removed"
    added = change.kind == "added" and not cancelled
    accent = "#ef4444" if cancelled else "#2dd4bf" if added else "#fbbf24"
    background = "#3b1118" if cancelled else "#0c302d" if added else "#3a2a0a"
    if cancelled:
        status = "Fällt aus"
        rows = []
    elif added:
        status = "Neu"
        rows = [("Jetzt", f"{_lesson_time_short(after)}{_short_place(after)}")]
    else:
        status = "Geändert"
        rows = _change_fields(before, after)
    if not rows and not cancelled:
        rows = [("Jetzt", "Diese Stunde wurde aktualisiert.")]
    row_html = "".join(
        f'<div style="margin-top:7px;color:#f8fafc"><span style="color:#cbd5e1">{html.escape(label)}:</span> '
        f'<strong style="color:{accent}">{html.escape(new)}</strong>'
        f'{f" <span style=\"color:#94a3b8\">(vorher {html.escape(old)})</span>" if old else ""}</div>'
        for label, old, new in rows
    )
    return (
        f'<article style="margin-top:8px;padding:13px;border:1px solid {accent};border-left:5px solid {accent};border-radius:6px;background:{background}">'
        f'<div style="display:flex;justify-content:space-between;gap:10px;align-items:baseline">'
        f'<strong style="font-size:17px;color:#f8fafc">{html.escape(_lesson_name(lesson))}</strong>'
        f'<strong style="color:{accent};white-space:nowrap">{html.escape(status)}</strong></div>'
        f'<div style="margin-top:4px;color:#cbd5e1">{html.escape(_lesson_time_short(lesson))}</div>'
        f'{row_html}</article>'
    )


def _format_lesson(lesson: dict[str, Any], *, sentence_start: bool = False) -> str:
    subject = _lesson_name(lesson)
    if sentence_start:
        subject = subject[:1].upper() + subject[1:]
    teacher = ", ".join(lesson.get("teacher") or [])
    room = ", ".join(lesson.get("room") or [])
    detail_parts = [
        lesson.get("substitution_text", ""),
        lesson.get("lesson_text", ""),
        lesson.get("info", ""),
    ]
    extras = []
    if room:
        extras.append(f"in Raum {room}")
    if teacher:
        extras.append(f"bei {teacher}")
    details = "; ".join(str(part).strip() for part in detail_parts if str(part).strip())
    if details:
        extras.append(f"Hinweis: {details}")
    suffix = f", {', '.join(extras)}" if extras else ""
    return f"{subject} von {_lesson_time(lesson)}{suffix}."


def _lesson_name(lesson: dict[str, Any]) -> str:
    return ", ".join(lesson.get("subject") or []) or "eine Unterrichtsstunde"


def _lesson_time(lesson: dict[str, Any]) -> str:
    start = str(lesson.get("start") or "").strip()
    end = str(lesson.get("end") or "").strip()
    if start and end:
        return f"{start} bis {end} Uhr"
    if start:
        return f"{start} Uhr"
    return "einer noch unbekannten Uhrzeit"


def _lesson_time_short(lesson: dict[str, Any]) -> str:
    start = str(lesson.get("start") or "").strip()
    end = str(lesson.get("end") or "").strip()
    if start and end:
        return f"{start}–{end} Uhr"
    return f"{start or end} Uhr" if start or end else "Zeit noch offen"


def _short_place(lesson: dict[str, Any]) -> str:
    room = _list_value(lesson, "room")
    return f", Raum {room}" if room else ""


def _format_change_details(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    return [
        f"{label}: {old} → {new}" if old and new
        else f"{label}: jetzt {new}" if new
        else f"{label}: {old} gilt nicht mehr"
        for label, old, new in _change_fields(before, after)
    ]


def _change_fields(before: dict[str, Any], after: dict[str, Any]) -> list[tuple[str, str, str]]:
    details: list[tuple[str, str, str]] = []
    pairs = [
        ("Zeit", _time_value(before), _time_value(after)),
        ("Fach", _list_value(before, "subject"), _list_value(after, "subject")),
        ("Raum", _list_value(before, "room"), _list_value(after, "room")),
        ("Lehrer oder Lehrerin", _list_value(before, "teacher"), _list_value(after, "teacher")),
        ("Hinweis", _lesson_details(before), _lesson_details(after)),
    ]
    for label, old, new in pairs:
        if old == new:
            continue
        details.append((label, old, new))
    return details


def _list_value(lesson: dict[str, Any], key: str) -> str:
    return ", ".join(str(item) for item in lesson.get(key) or [] if str(item).strip())


def _time_value(lesson: dict[str, Any]) -> str:
    start = str(lesson.get("start") or "").strip()
    end = str(lesson.get("end") or "").strip()
    return f"{start}-{end} Uhr" if start and end else start or end


def _lesson_details(lesson: dict[str, Any]) -> str:
    return "; ".join(
        str(lesson.get(key) or "").strip()
        for key in ("substitution_text", "lesson_text", "info")
        if str(lesson.get(key) or "").strip()
    )

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .diff import group_by_date


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    snapshot_path = PROJECT_ROOT / "data" / "snapshots" / "latest.json"
    output_dir = PROJECT_ROOT / "preview"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "timetable.html"

    if not snapshot_path.exists():
        raise SystemExit("Kein Snapshot gefunden. Starte zuerst die App und warte auf einen erfolgreichen WebUntis-Abruf.")

    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    lessons = payload.get("lessons", [])
    grouped = group_by_date(lessons)
    output_path.write_text(render(grouped, payload.get("timestamp", "")), encoding="utf-8")
    print(output_path)


def render(grouped: dict[str, list[dict[str, Any]]], timestamp: str) -> str:
    days = "\n".join(render_day(day, lessons) for day, lessons in grouped.items())
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Schulplaner Vorschau</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #0d1117;
      background: #f4f7f8;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 10;
      padding: 16px;
      color: #fff;
      background: #0d1117;
      border-bottom: 3px solid #2dd4bf;
    }}
    h1 {{ margin: 0; font-size: 20px; line-height: 1.2; }}
    .sub {{ margin: 4px 0 0; color: #dce7e1; font-size: 13px; }}
    main {{ display: grid; gap: 14px; padding: 14px; }}
    section {{ background: #fff; border: 1px solid #dce4e8; border-radius: 8px; overflow: hidden; }}
    h2 {{
      margin: 0;
      padding: 14px;
      font-size: 17px;
      border-bottom: 1px solid #dce4e8;
      background: #f7fafb;
    }}
    .lesson {{
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr);
      gap: 12px;
      padding: 12px 14px;
      border-bottom: 1px solid #dce4e8;
    }}
    .lesson:last-child {{ border-bottom: 0; }}
    .time {{ color: #3b82f6; font-size: 13px; font-weight: 800; }}
    .subject {{ display: block; font-weight: 800; overflow-wrap: anywhere; }}
    .meta {{ margin-top: 4px; color: #60727c; font-size: 13px; overflow-wrap: anywhere; }}
    .badge {{
      display: inline-flex;
      margin-top: 8px;
      min-height: 24px;
      align-items: center;
      padding: 0 8px;
      border: 1px solid #dce4e8;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      background: #f7fafb;
    }}
    .changed .badge {{ color: #a15c00; background: #fff3d6; border-color: #f0d69d; }}
    .cancelled .badge {{ color: #b42318; background: #fff0ed; border-color: #f2b8b5; }}
    .regular .badge {{ color: #0f8a5f; background: #e8f8f0; border-color: #bce8d1; }}
    @media (max-width: 560px) {{
      main {{ padding: 10px; }}
      .lesson {{ grid-template-columns: 1fr; gap: 6px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Schulplaner</h1>
    <p class="sub">Stundenplan-Vorschau · Stand {escape(timestamp)}</p>
  </header>
  <main>
    {days or '<section><h2>Keine Daten</h2></section>'}
  </main>
</body>
</html>
"""


def render_day(day: str, lessons: list[dict[str, Any]]) -> str:
    items = "\n".join(render_lesson(lesson) for lesson in lessons)
    return f"""<section>
  <h2>{escape(display_date(day))}</h2>
  {items}
</section>"""


def render_lesson(lesson: dict[str, Any]) -> str:
    status = lesson.get("status") or "regular"
    details = " | ".join(
        item
        for item in [
            join_or(lesson.get("teacher"), ""),
            join_or(lesson.get("room"), ""),
            lesson.get("substitution_text", ""),
            lesson.get("lesson_text", ""),
            lesson.get("info", ""),
        ]
        if item
    )
    return f"""<article class="lesson {escape(status)}">
  <div class="time">{escape(lesson.get("start", ""))}-{escape(lesson.get("end", ""))}</div>
  <div>
    <span class="subject">{escape(join_or(lesson.get("subject"), lesson.get("lesson_text") or "Termin"))}</span>
    <div class="meta">{escape(details)}</div>
    <span class="badge">{escape(status_label(status))}</span>
  </div>
</article>"""


def display_date(value: str) -> str:
    try:
        year, month, day = value.split("-")
        return f"{day}.{month}.{year}"
    except ValueError:
        return value


def status_label(value: str) -> str:
    return {"regular": "planmäßig", "changed": "geändert", "cancelled": "entfällt"}.get(value, value)


def join_or(value: Any, fallback: str) -> str:
    return ", ".join(value) if isinstance(value, list) and value else fallback


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


if __name__ == "__main__":
    main()

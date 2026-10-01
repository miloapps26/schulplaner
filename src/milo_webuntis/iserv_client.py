from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests

from .config import IServConfig


class IServClient:
    def __init__(self, config: IServConfig, timeout: int = 30) -> None:
        self.config = config
        self.timeout = timeout
        self.session = requests.Session()

    def __enter__(self) -> "IServClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.session.close()

    def exam_plan(self, start: datetime, end: datetime) -> list[dict[str, Any]]:
        if not self.config.is_complete:
            raise ValueError("IServ-Klausurplan ist nicht vollständig konfiguriert.")
        self._login()
        response = self.session.get(
            self._url("/iserv/calendar4/plugin"),
            params={
                "plugin": "exam-plan",
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": self._url("/iserv/calendar"),
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            return []
        return normalize_exam_plan(payload)

    def _login(self) -> None:
        login_url = self._url("/iserv/calendar")
        response = self.session.get(login_url, timeout=self.timeout)
        response.raise_for_status()
        if _looks_authenticated(response.text):
            return

        response = self.session.post(
            response.url,
            data={
                "_username": self.config.username,
                "_password": self.config.password,
            },
            timeout=self.timeout,
            allow_redirects=False,
        )
        self._follow_iserv_redirects(response)

    def _follow_iserv_redirects(self, response: requests.Response) -> None:
        current = response
        for _ in range(8):
            if current.is_redirect or current.is_permanent_redirect:
                location = current.headers.get("Location", "")
                if not location:
                    break
                current = self.session.get(
                    urljoin(current.url, location),
                    timeout=self.timeout,
                    allow_redirects=False,
                )
                continue

            refresh_url = _meta_refresh_url(current.text)
            if refresh_url:
                current = self.session.get(
                    urljoin(current.url, refresh_url),
                    timeout=self.timeout,
                    allow_redirects=False,
                )
                continue
            current.raise_for_status()
            return
        current.raise_for_status()

    def _url(self, path: str) -> str:
        return urljoin(f"{self.config.base_url.rstrip('/')}/", path.lstrip("/"))


def normalize_exam_plan(items: list[Any]) -> list[dict[str, Any]]:
    exams: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        external_id = str(item.get("id") or "").strip()
        title = str(item.get("title") or "").strip()
        start = str(item.get("start") or "").strip()
        end = str(item.get("end") or "").strip()
        if not external_id or not title or not start:
            continue
        fields = _display_fields(item.get("displayFields"))
        exams.append(
            {
                "id": external_id,
                "title": title,
                "start": start,
                "end": end,
                "all_day": bool(item.get("allDay")),
                "plugin": str(item.get("plugin") or "exam-plan"),
                "group": fields.get("Gruppen", ""),
                "visible": fields.get("Sichtbar", ""),
                "description": fields.get("Beschreibung", ""),
            }
        )
    return sorted(exams, key=lambda exam: (exam.get("start") or "", exam.get("title") or ""))


def _display_fields(items: Any) -> dict[str, str]:
    fields: dict[str, str] = {}
    if not isinstance(items, list):
        return fields
    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        text = item.get("text")
        if label and text is not None:
            fields[label] = str(text).strip()
    return fields


def _looks_authenticated(body: str) -> bool:
    return "/iserv/calendar4/" in body or "Neuer Termin" in body or "calendar4" in body


def _meta_refresh_url(body: str) -> str:
    match = re.search(
        r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\'][^"\']*url=([^"\']+)["\']',
        body,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    return html.unescape(match.group(1).strip())

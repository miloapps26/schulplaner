from __future__ import annotations

import hashlib
import html
import json
import secrets
import threading
import time
from dataclasses import dataclass
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .accounts import AccountStore, normalize_email
from .config import AppConfig, TenantConfig, TransitSettings
from .diff import build_notification, build_notification_html, diff_lessons, group_by_date
from .iserv_client import IServClient
from .notify import Notifier
from .snapshot import SnapshotStore
from .transit import TransitPlanner
from .webuntis_client import WebUntisClient


HOMEWORK_COMPLETED_RETENTION_DAYS = 7
EXAM_LOOKAHEAD_DAYS = 180


@dataclass(frozen=True)
class RunResult:
    status: str
    timestamp: str
    changes: list[dict[str, Any]]
    notified_channels: list[str]
    message: str
    notification_error: str = ""


class MonitorService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.stores = {
            tenant.id: SnapshotStore(tenant.data_dir)
            for tenant in config.tenants
        }
        self.notifiers = {
            tenant.id: Notifier(tenant.email, config.twilio, config.webhook_url)
            for tenant in config.tenants
        }
        self.accounts = AccountStore(config.data_dir)
        self.transit_planner = TransitPlanner(config.gtfs, config.geofox)
        self.iserv_client_factory = IServClient
        self._transit_cache: dict[str, dict[str, Any]] = {}
        self._transit_latest: dict[tuple[str, str, bool], dict[str, Any]] = {}
        self._transit_refresh_locks: dict[tuple[str, str, bool], threading.Lock] = {}
        self._transit_notification_locks: dict[str, threading.Lock] = {}
        self._transit_cache_lock = threading.Lock()
        self.store = self.stores[self.default_tenant.id]
        self.notifier = self.notifiers[self.default_tenant.id]
        self.lock = threading.Lock()

    @property
    def default_tenant(self) -> TenantConfig:
        active = [tenant for tenant in self.config.tenants if tenant.active]
        return active[0] if active else self.config.tenants[0]

    def tenant(self, tenant_id: str | None = None) -> TenantConfig:
        wanted = tenant_id or self.default_tenant.id
        for tenant in self.config.tenants:
            if tenant.id == wanted or tenant.public_id == wanted:
                return tenant
        raise ValueError(f"Tenant nicht gefunden: {wanted}")

    def store_for(self, tenant_id: str | None = None) -> SnapshotStore:
        return self.stores[self.tenant(tenant_id).id]

    def run_once(self, force_notify: bool = False, tenant_id: str | None = None) -> RunResult:
        with self.lock:
            if tenant_id:
                return self._run_tenant(self.tenant(tenant_id), force_notify=force_notify)

            active_tenants = [tenant for tenant in self.config.tenants if tenant.active]
            results = [
                self._run_tenant(tenant, force_notify=force_notify)
                for tenant in active_tenants
            ]
            if not results:
                now = _now(self.config.timezone)
                return RunResult(
                    status="inactive",
                    timestamp=now.isoformat(),
                    changes=[],
                    notified_channels=[],
                    message="Keine aktiven Profile konfiguriert.",
                )
            if len(results) == 1:
                return results[0]
            now = _now(self.config.timezone)
            changes = [change for result in results for change in result.changes]
            notified_channels = sorted({
                channel for result in results for channel in result.notified_channels
            })
            errors = [result.notification_error for result in results if result.notification_error]
            status = "changed" if changes else "unchanged"
            if errors:
                status = "notify_error"
            return RunResult(
                status=status,
                timestamp=now.isoformat(),
                changes=changes,
                notified_channels=notified_channels,
                message=f"{len(results)} Profile geprüft, {len(changes)} Änderung(en) erkannt.",
                notification_error=" | ".join(errors),
            )

    def _run_tenant(self, tenant: TenantConfig, force_notify: bool = False) -> RunResult:
        now = _now(self.config.timezone)
        store = self.stores[tenant.id]
        notifier = self.notifiers[tenant.id]
        if not tenant.active:
            return self._record(
                tenant,
                now,
                "inactive",
                [],
                [],
                "Profil ist deaktiviert.",
            )
        if not tenant.webuntis.is_complete:
            return self._record(
                tenant,
                now,
                "config_missing",
                [],
                [],
                "WebUntis-Konfiguration unvollständig.",
            )

        start, end = monitor_window(now.date())
        with WebUntisClient(tenant.webuntis) as client:
            current = client.timetable(start=start, end=end)

        previous_payload = store.load_latest_payload()
        previous = None if previous_payload is None else previous_payload.get("lessons", [])
        comparable_dates = _comparison_dates(previous_payload, now.date())
        changes = [] if previous is None else diff_lessons(
            previous,
            current,
            comparable_dates=comparable_dates,
        )
        store.save_latest(current, now)

        should_notify = bool(changes) and (
            previous is not None or self.config.notify_on_first_run or force_notify
        )
        notified_channels: list[str] = []
        notification_error = ""
        pending_sent = False
        pending = store.load_pending_notification()
        if pending:
            try:
                notified_channels.extend(
                    notifier.send(
                        pending.get("subject", "Schulplaner"),
                        pending.get("body", ""),
                        pending.get("metadata", {}),
                        html_body=pending.get("html_body") or None,
                    )
                )
                store.clear_pending_notification()
                pending_sent = True
            except Exception as exc:
                notification_error = str(exc)

        if should_notify:
            subject, body = build_notification(changes, current, today=now.date())
            timetable_url = _timetable_url(
                _app_url(self.config.public_timetable_url),
                _week_for_changes(changes, now.date()),
            )
            if timetable_url:
                body = f"{body}\n\nHier kannst du deinen ganzen Stundenplan ansehen:\n{timetable_url}"
            body = f"{body}\n\nViele Grüße\nSchulplaner"
            html_body = build_notification_html(changes, timetable_url=timetable_url)
            try:
                notified_channels = notifier.send(
                    subject,
                    body,
                    {"tenant_id": tenant.id, "changes": [change.to_dict() for change in changes]},
                    html_body=html_body,
                )
                store.clear_pending_notification()
            except Exception as exc:
                notification_error = str(exc)
                store.save_pending_notification(
                    {
                        "subject": subject,
                        "body": body,
                        "html_body": html_body,
                        "metadata": {
                            "tenant_id": tenant.id,
                            "changes": [change.to_dict() for change in changes],
                        },
                        "created_at": now.isoformat(),
                    }
                )

        exam_channels: list[str] = []
        try:
            exam_channels = self._refresh_exams_and_notify(tenant, now, force_notify=force_notify)
        except Exception as exc:
            store.append_run(
                {
                    "timestamp": now.isoformat(),
                    "tenant_id": tenant.id,
                    "tenant_name": tenant.name,
                    "status": "exam_error",
                    "changes_count": 0,
                    "notified_channels": [],
                    "message": "Klassenarbeiten konnten nicht geprüft werden.",
                    "notification_error": str(exc),
                }
            )
        notified_channels.extend(exam_channels)
        notified_channels = sorted(set(notified_channels))

        if previous is None:
            status = "baseline"
            message = "Erster Snapshot gespeichert."
        elif changes and notification_error:
            status = "notify_error"
            message = f"{len(changes)} Änderung(en) erkannt, Benachrichtigung fehlgeschlagen."
        elif changes:
            status = "changed"
            message = f"{len(changes)} Änderung(en) erkannt."
        elif notification_error:
            status = "notify_error"
            message = "Ausstehende Benachrichtigung konnte nicht versendet werden."
        elif pending_sent:
            status = "unchanged"
            message = "Keine Änderungen erkannt. Ausstehende Benachrichtigung versendet."
        else:
            status = "unchanged"
            message = "Keine Änderungen erkannt."

        return self._record(
            tenant,
            now,
            status,
            [change.to_dict() for change in changes],
            notified_channels,
            message,
            notification_error,
        )

    def _refresh_exams_and_notify(
        self,
        tenant: TenantConfig,
        now: datetime,
        *,
        force_notify: bool = False,
    ) -> list[str]:
        if not tenant.iserv.is_complete:
            return []
        store = self.stores[tenant.id]
        previous_state = store.load_exam_state()
        previous_ids = {
            str(item)
            for item in previous_state.get("known_ids") or []
            if str(item)
        }
        items = self._fetch_exam_items(tenant, now)
        current_ids = {str(item.get("id") or "") for item in items if item.get("id")}
        is_baseline = not previous_state.get("timestamp") and not previous_ids
        new_items = [
            item for item in items
            if str(item.get("id") or "") not in previous_ids
        ]
        notified_ids = {
            str(item)
            for item in previous_state.get("notified_ids") or []
            if str(item)
        }
        channels: list[str] = []
        should_notify = bool(new_items) and (not is_baseline or force_notify)
        if should_notify:
            channels = self._notify_new_exams(tenant, new_items, now)
            notified_ids.update(str(item.get("id") or "") for item in new_items if item.get("id"))
        store.save_exam_state(
            {
                "items": items,
                "known_ids": sorted(current_ids),
                "notified_ids": sorted(notified_ids.intersection(current_ids)),
                "timestamp": now.isoformat(),
                "source_error": "",
            }
        )
        if new_items and channels:
            store.append_run(
                {
                    "timestamp": now.isoformat(),
                    "tenant_id": tenant.id,
                    "tenant_name": tenant.name,
                    "status": "exam_changed",
                    "changes_count": len(new_items),
                    "notified_channels": channels,
                    "message": f"{len(new_items)} neue Klassenarbeit(en) erkannt und per E-Mail versendet.",
                    "notification_error": "",
                }
            )
        elif new_items and should_notify and not channels:
            store.append_run(
                {
                    "timestamp": now.isoformat(),
                    "tenant_id": tenant.id,
                    "tenant_name": tenant.name,
                    "status": "exam_notify_skipped",
                    "changes_count": len(new_items),
                    "notified_channels": [],
                    "message": f"{len(new_items)} neue Klassenarbeit(en) erkannt, E-Mail nicht konfiguriert.",
                    "notification_error": "",
                }
            )
        return channels

    def _fetch_exam_items(self, tenant: TenantConfig, now: datetime) -> list[dict[str, Any]]:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=EXAM_LOOKAHEAD_DAYS)
        with self.iserv_client_factory(tenant.iserv) as client:
            return client.exam_plan(start, end)

    def _notify_new_exams(
        self,
        tenant: TenantConfig,
        items: list[dict[str, Any]],
        now: datetime,
    ) -> list[str]:
        if not tenant.email.enabled:
            return []
        count = len(items)
        subject = "Neue Klassenarbeit im Schulplaner"
        if count == 1:
            subject = f"Neue Klassenarbeit: {items[0].get('title') or 'Termin'}"
        body_lines = [
            "Hallo,",
            "",
            "es wurde eine neue Klassenarbeit gefunden:",
            "",
        ]
        for item in items:
            body_lines.append(f"- {_exam_label(item)}")
        app_url = _app_url(self.config.public_timetable_url)
        if app_url:
            body_lines.extend(["", f"Hier kannst du die Übersicht ansehen: {app_url}"])
        body_lines.extend(["", "Viele Grüße", "Schulplaner"])
        html_items = "".join(f"<li>{html.escape(_exam_label(item))}</li>" for item in items)
        html_body = (
            "<p>Hallo,</p>"
            "<p>es wurde eine neue Klassenarbeit gefunden:</p>"
            f"<ul>{html_items}</ul>"
        )
        if app_url:
            html_body += f'<p><a href="{html.escape(app_url)}">Zur Übersicht</a></p>'
        html_body += "<p>Viele Grüße<br>Schulplaner</p>"
        self.notifiers[tenant.id].send_email(subject, "\n".join(body_lines), html_body=html_body)
        return ["email"]

    def exams(self, tenant_id: str | None = None, force_refresh: bool = False) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        store = self.stores[tenant.id]
        now = _now(self.config.timezone)
        state = store.load_exam_state()
        source_error = ""
        if force_refresh or not state.get("timestamp"):
            try:
                items = self._fetch_exam_items(tenant, now)
                state = {
                    "items": items,
                    "known_ids": [str(item.get("id") or "") for item in items if item.get("id")],
                    "notified_ids": state.get("notified_ids", []),
                    "timestamp": now.isoformat(),
                    "source_error": "",
                }
                store.save_exam_state(state)
            except Exception as exc:
                source_error = str(exc)
                state = {
                    **state,
                    "source_error": source_error,
                }
                store.save_exam_state(state)
        items = [
            item for item in state.get("items", [])
            if isinstance(item, dict) and _exam_not_past(item, now)
        ]
        return {
            "timestamp": state.get("timestamp") or "",
            "items": sorted(items, key=lambda item: (item.get("start") or "", item.get("title") or "")),
            "count": len(items),
            "source_error": source_error or state.get("source_error") or "",
            "tenant_id": tenant.id,
            "tenant_name": tenant.name,
            "profile": _public_profile(tenant),
            "iserv_ready": tenant.iserv.is_complete,
        }

    def status(self, tenant_id: str | None = None) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        store = self.stores[tenant.id]
        latest_payload = store.load_latest_payload() or {}
        latest = latest_payload.get("lessons", [])
        window_start, window_end = monitor_window(_now(self.config.timezone).date())
        return {
            "tenant_id": tenant.id,
            "tenant_name": tenant.name,
            "tenants": self._tenant_summaries(),
            "profile": _public_profile(tenant),
            "webuntis_ready": tenant.webuntis.is_complete,
            "missing_fields": tenant.webuntis.missing_fields,
            "channels": self._notification_channels(tenant),
            "email_recipients": tenant.email.recipients,
            "auth_mode": "app_secret" if tenant.webuntis.app_secret else "password",
            "element_type": tenant.webuntis.element_type,
            "element_id": tenant.webuntis.element_id,
            "poll_interval_minutes": self.config.poll_interval_minutes,
            "transit_poll_interval_minutes": self.config.transit_poll_interval_minutes,
            "days_back": self.config.days_back,
            "days_ahead": self.config.days_ahead,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "snapshot_timestamp": latest_payload.get("timestamp"),
            "lesson_count": len(latest),
            "runs": store.runs(limit=10),
            "auth_required": self.config.auth.required,
            "auth_users_count": len(self.config.auth.users),
        }

    def schedule(self, tenant_id: str | None = None) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        latest_payload = self.store_for(tenant.id).load_latest_payload() or {}
        latest = latest_payload.get("lessons", [])
        now = _now(self.config.timezone)
        window_start, window_end = monitor_window(now.date())
        manual_lessons = self.store_for(tenant.id).load_manual_lessons_state().get("items", [])
        merged = [
            *latest,
            *_manual_lesson_occurrences(manual_lessons, window_start, window_end),
        ]
        return {
            "timestamp": latest_payload.get("timestamp"),
            "days": group_by_date(merged),
            "manual_lessons": manual_lessons,
            "profile": _public_profile(tenant),
        }

    def transit(
        self,
        target_date: date | None = None,
        tenant_id: str | None = None,
        force_refresh: bool = False,
        include_full_day: bool = False,
    ) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        now = _now(self.config.timezone)
        selected_date = target_date or now.date()
        store = self.store_for(tenant.id)
        latest_payload = store.load_latest_payload() or {}
        latest = latest_payload.get("lessons", [])
        window_start, window_end = monitor_window(now.date())
        manual_lessons = store.load_manual_lessons_state().get("items", [])
        lessons = [
            *latest,
            *_manual_lesson_occurrences(manual_lessons, window_start, window_end),
        ]
        cache_key = self._transit_cache_key(
            tenant,
            selected_date,
            latest_payload.get("timestamp"),
            manual_lessons,
            include_full_day,
        )
        logical_key = (tenant.id, selected_date.isoformat(), include_full_day)
        with self._transit_cache_lock:
            latest_entry = self._transit_latest.get(logical_key)
            initial_refresh_marker = float(
                (latest_entry or {}).get("refreshed_monotonic") or 0
            )
            refresh_lock = self._transit_refresh_locks.setdefault(logical_key, threading.Lock())
        if latest_entry and not force_refresh:
            return self._transit_cache_response(latest_entry, tenant, now, cached=True)

        with refresh_lock:
            with self._transit_cache_lock:
                latest_entry = self._transit_latest.get(logical_key)
                if latest_entry and (
                    not force_refresh
                    or float(latest_entry.get("refreshed_monotonic") or 0)
                    > initial_refresh_marker
                ):
                    return self._transit_cache_response(latest_entry, tenant, now, cached=True)
                exact_cached = self._transit_cache.get(cache_key)
            if exact_cached and not force_refresh:
                entry = self._new_transit_cache_entry(exact_cached, cache_key, now)
                with self._transit_cache_lock:
                    self._transit_latest[logical_key] = entry
                return self._transit_cache_response(entry, tenant, now, cached=True)

            plan = self.transit_planner.day_plan(
                tenant.transit,
                lessons,
                selected_date,
                force_refresh=force_refresh,
                include_full_day=include_full_day,
            )
            if not _transit_plan_successful(plan) and latest_entry:
                response = self._transit_cache_response(latest_entry, tenant, now, cached=True)
                response["stale"] = True
                response["refresh_error"] = str(
                    (plan.get("feed") or {}).get("error")
                    or "Busdaten konnten nicht aktualisiert werden."
                )
                return response

            entry = self._new_transit_cache_entry(plan, cache_key, now)
            with self._transit_cache_lock:
                self._transit_cache[cache_key] = plan
                self._transit_latest[logical_key] = entry
                while len(self._transit_cache) > 256:
                    self._transit_cache.pop(next(iter(self._transit_cache)))
            return self._transit_cache_response(entry, tenant, now, cached=False)

    def _new_transit_cache_entry(
        self,
        plan: dict[str, Any],
        cache_key: str,
        now: datetime,
    ) -> dict[str, Any]:
        return {
            "plan": plan,
            "cache_key": cache_key,
            "updated_at": now.isoformat(),
            "refreshed_monotonic": time.monotonic(),
        }

    def _transit_cache_response(
        self,
        entry: dict[str, Any],
        tenant: TenantConfig,
        now: datetime,
        *,
        cached: bool,
    ) -> dict[str, Any]:
        refreshed_at = float(entry.get("refreshed_monotonic") or time.monotonic())
        age_seconds = max(0, round(time.monotonic() - refreshed_at))
        stale_after = max(180, self.config.transit_poll_interval_minutes * 120)
        plan = entry["plan"]
        if plan.get("full_day") and plan.get("date"):
            quick_key = (tenant.id, str(plan["date"]), False)
            with self._transit_cache_lock:
                quick_entry = self._transit_latest.get(quick_key)
            if quick_entry:
                quick_plan = quick_entry["plan"]
                plan = {
                    **plan,
                    "day": quick_plan.get("day", plan.get("day", {})),
                    "recommendation": quick_plan.get(
                        "recommendation",
                        plan.get("recommendation", {}),
                    ),
                }
        return {
            **plan,
            "timestamp": now.isoformat(),
            "cached": cached,
            "cache_updated_at": entry.get("updated_at"),
            "cache_age_seconds": age_seconds,
            "stale": age_seconds > stale_after,
            "profile": _public_profile(tenant),
        }

    def _transit_cache_key(
        self,
        tenant: TenantConfig,
        selected_date: date,
        snapshot_timestamp: Any,
        manual_lessons: list[dict[str, Any]],
        include_full_day: bool,
    ) -> str:
        payload = {
            "tenant_id": tenant.id,
            "date": selected_date.isoformat(),
            "feed": self.transit_planner.cache_key(),
            "snapshot_timestamp": snapshot_timestamp or "",
            "manual_lessons": manual_lessons,
            "include_full_day": include_full_day,
            "settings": _public_transit_settings(tenant.transit),
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def warm_transit_cache(
        self,
        *,
        notify_changes: bool = False,
        include_full_day: bool = False,
        force_refresh: bool = True,
        target_dates: list[date] | tuple[date, ...] | None = None,
    ) -> None:
        now = _now(self.config.timezone)
        today = now.date()
        dates = list(dict.fromkeys(target_dates or [today]))
        for tenant in self.config.tenants:
            if tenant.active and tenant.transit.enabled:
                for target_date in dates:
                    try:
                        plan = self.transit(
                            target_date,
                            tenant.id,
                            force_refresh=force_refresh,
                            include_full_day=include_full_day,
                        )
                        if notify_changes and target_date == today:
                            self._notify_transit_recommendation_change(tenant, plan, now)
                    except Exception as exc:
                        self.stores[tenant.id].append_run(
                            {
                                "timestamp": now.isoformat(),
                                "tenant_id": tenant.id,
                                "tenant_name": tenant.name,
                                "status": "transit_error",
                                "changes_count": 0,
                                "notified_channels": [],
                                "message": (
                                    "Busverbindung für "
                                    f"{target_date.isoformat()} konnte nicht geprüft werden: {exc}"
                                ),
                                "notification_error": "",
                            }
                        )

    def _notify_transit_recommendation_change(
        self,
        tenant: TenantConfig,
        plan: dict[str, Any],
        now: datetime,
    ) -> None:
        notification_locks = getattr(self, "_transit_notification_locks", None)
        if notification_locks is None:
            notification_locks = {}
            self._transit_notification_locks = notification_locks
        lock = notification_locks.setdefault(tenant.id, threading.Lock())
        with lock:
            self._notify_transit_recommendation_change_locked(tenant, plan, now)

    def _notify_transit_recommendation_change_locked(
        self,
        tenant: TenantConfig,
        plan: dict[str, Any],
        now: datetime,
    ) -> None:
        store = self.stores[tenant.id]
        current = _transit_recommendation_snapshot(plan)
        previous = store.load_transit_recommendation()
        current = _freeze_departed_recommendations(current, previous, now)
        if (
            previous is None
            or previous.get("date") != current.get("date")
            or previous.get("schema") != current.get("schema")
        ):
            store.save_transit_recommendation(current)
            return
        if previous.get("recommendation") == current.get("recommendation"):
            return
        notified_fingerprints = [
            str(value)
            for value in previous.get("notified_fingerprints") or []
            if str(value)
        ]
        if not tenant.email.enabled:
            store.save_transit_recommendation({
                **current,
                "notified_fingerprints": notified_fingerprints,
            })
            return

        subject, body = build_transit_notification(previous, current)
        fingerprint = _transit_notification_fingerprint(subject, body)
        if fingerprint in notified_fingerprints:
            store.save_transit_recommendation({
                **current,
                "notified_fingerprints": notified_fingerprints,
            })
            return
        transit_url = _app_url(self.config.public_timetable_url) if self.config.public_timetable_url else ""
        html_body = build_transit_notification_html(previous, current, transit_url)
        if transit_url:
            body = f"{body}\n\nHier kannst du deinen Busfahrplan ansehen:\n{transit_url}"
        body = f"{body}\n\nViele Grüße\nSchulplaner"
        try:
            self.notifiers[tenant.id].send_email(subject, body, html_body=html_body)
        except Exception as exc:
            store.append_run(
                {
                    "timestamp": now.isoformat(),
                    "tenant_id": tenant.id,
                    "tenant_name": tenant.name,
                    "status": "transit_notify_error",
                    "changes_count": 1,
                    "notified_channels": [],
                    "message": "Geänderte Busverbindung erkannt, E-Mail-Versand fehlgeschlagen.",
                    "notification_error": str(exc),
                }
            )
            return

        store.save_transit_recommendation({
            **current,
            "notified_fingerprints": [
                *notified_fingerprints[-49:],
                fingerprint,
            ],
        })
        store.append_run(
            {
                "timestamp": now.isoformat(),
                "tenant_id": tenant.id,
                "tenant_name": tenant.name,
                "status": "transit_changed",
                "changes_count": 1,
                "notified_channels": ["email"],
                "message": "Geänderte Busverbindung erkannt und per E-Mail versendet.",
                "notification_error": "",
            }
        )

    def homework(self, tenant_id: str | None = None) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        store = self.stores[tenant.id]
        now = _now(self.config.timezone)
        state = store.load_homework_state()
        external: list[dict[str, Any]] = []
        source_error = ""
        if tenant.webuntis.is_complete:
            start, end = monitor_window(now.date())
            try:
                with WebUntisClient(tenant.webuntis) as client:
                    external = client.homeworks(start=start, end=end)
            except Exception as exc:
                source_error = str(exc)

        latest_payload = store.load_latest_payload() or {}
        lessons = latest_payload.get("lessons", [])
        manual = [
            _resolve_homework_due_date(item, lessons, now.date())
            for item in state.get("manual", [])
            if isinstance(item, dict)
        ]
        items = [
            _resolve_homework_due_date(item, lessons, now.date())
            for item in [*external, *manual]
        ]
        completed_state = state.get("completed", {})
        items = [_with_homework_status(item, completed_state, now.date()) for item in items]
        state, items, homework_state_changed = _cleanup_completed_homework_state(state, items, now.date())
        if homework_state_changed:
            store.save_homework_state(state)
        items.sort(key=_homework_sort_key)
        open_items = [item for item in items if not item.get("completed")]
        completed_items = [item for item in items if item.get("completed")]
        webuntis_count = len([item for item in items if item.get("source") == "webuntis"])
        manual_count = len([item for item in items if item.get("source") == "manual"])
        return {
            "timestamp": now.isoformat(),
            "items": items,
            "open": open_items,
            "completed": completed_items,
            "webuntis_count": webuntis_count,
            "manual_count": manual_count,
            "webuntis_total_count": len(external),
            "manual_total_count": len(manual),
            "expired_count": len([item for item in items if item.get("is_expired")]),
            "source_error": source_error,
            "tenant_id": tenant.id,
            "tenant_name": tenant.name,
            "profile": _public_profile(tenant),
        }

    def tenant_admin(self) -> dict[str, Any]:
        return {
            "tenants": [self._tenant_admin_item(tenant) for tenant in self.config.tenants],
            "parents": [self._public_parent(parent) for parent in self.accounts.parents()],
            "invitations": [self._public_invitation(invitation) for invitation in self.accounts.invitations()],
        }

    def create_tenant(self, payload: dict[str, Any]) -> dict[str, Any]:
        tenant_id = _new_identifier("tenant")
        public_id = _new_identifier("view")
        tenant = self._tenant_from_admin_payload(
            payload,
            tenant_id=tenant_id,
            public_id=public_id,
            existing=None,
        )
        self.config = replace(self.config, tenants=(*self.config.tenants, tenant))
        self._refresh_tenant_runtime()
        self._save_tenants()
        return self.tenant_admin()

    def update_tenant(self, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.tenant(tenant_id)
        tenant = self._tenant_from_admin_payload(
            payload,
            tenant_id=existing.id,
            public_id=existing.public_id,
            existing=existing,
        )
        self.config = replace(
            self.config,
            tenants=tuple(tenant if item.id == existing.id else item for item in self.config.tenants),
        )
        self._refresh_tenant_runtime()
        self._save_tenants()
        return self.tenant_admin()

    def create_parent_invitation(self, tenant_id: str) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        parent_email = normalize_email(
            tenant.parent_email or (tenant.email.recipients[0] if tenant.email.recipients else "")
        )
        if not parent_email:
            raise ValueError("Bitte zuerst eine Eltern-E-Mail am Profil hinterlegen.")
        now = _now(self.config.timezone)
        token, invitation = self.accounts.create_invitation(parent_email, tenant.id, now)
        setup_url = _setup_url(self.config.public_timetable_url, token)
        subject = "Schulplaner Zugang einrichten"
        body = "\n".join(
            [
                "Hallo,",
                "",
                "für den Schulplaner wurde ein Zugang vorbereitet.",
                "Bitte hinterlege über diesen Link deinen bestehenden WebUntis-Zugang:",
                setup_url,
                "",
                "Dieser Zugang wird danach für die Anmeldung und die Stundenplanabfrage genutzt.",
                "Der Link ist einmalig gültig.",
                "",
                "Viele Grüße",
                "Schulplaner",
            ]
        )
        try:
            self.notifiers[tenant.id].send_email_to(parent_email, subject, body)
            self.accounts.mark_invitation_sent(invitation["id"], now)
            sent = True
            error = ""
        except Exception as exc:
            sent = False
            error = str(exc)
        return {
            **self.tenant_admin(),
            "invite": {
                "sent": sent,
                "error": error,
                "setup_url": setup_url,
            },
        }

    def setup_context(self, token: str) -> dict[str, Any]:
        invitation = self.accounts.invitation_for_token(token, _now(self.config.timezone))
        if not invitation:
            raise ValueError("Einladung ist ungültig oder abgelaufen.")
        tenant = self.tenant(str(invitation.get("tenant_id") or ""))
        return {
            "email": invitation.get("email"),
            "profile": _public_profile(tenant),
        }

    def accept_parent_invitation(self, token: str, username: str, password: str) -> dict[str, Any]:
        now = _now(self.config.timezone)
        invitation = self.accounts.invitation_for_token(token, now)
        if not invitation:
            raise ValueError("Einladung ist ungültig oder abgelaufen.")
        tenant_id = str(invitation.get("tenant_id") or "")
        tenant = self._tenant_with_webuntis_login(self.tenant(tenant_id), username, password)
        parent = self.accounts.accept_invitation(
            token,
            username,
            password,
            now,
            store_password=True,
        )
        self._replace_tenant(tenant)
        return self.parent_profile(str(parent.get("id") or ""), tenant_id)

    def parent_by_login(self, username: str, password: str) -> dict[str, Any] | None:
        return self.accounts.authenticate_parent(username, password)

    def parent_by_oidc_identity(self, email: str, username: str, subject: str) -> dict[str, Any] | None:
        parent = self.accounts.parent_by_oidc_identity(email=email, username=username, subject=subject)
        if parent and parent.get("active", True):
            return parent
        tenant_ids = [
            tenant.id
            for tenant in self.config.tenants
            if normalize_email(tenant.parent_email) == normalize_email(email)
        ]
        if not tenant_ids:
            return None
        return self.accounts.ensure_oidc_parent(
            email=email,
            username=username or email,
            subject=subject,
            tenant_ids=tenant_ids,
            now=_now(self.config.timezone),
        )

    def parent_by_id(self, parent_id: str) -> dict[str, Any] | None:
        return self.accounts.parent_by_id(parent_id)

    def tenant_for_parent(self, parent: dict[str, Any], tenant_id: str | None = None) -> TenantConfig:
        tenant_ids = [str(item) for item in parent.get("tenant_ids", []) if item]
        wanted = tenant_id or (tenant_ids[0] if tenant_ids else "")
        if not wanted:
            raise ValueError("Kein Profil für diesen Zugang vorhanden.")
        if wanted not in tenant_ids:
            raise PermissionError("Kein Zugriff auf dieses Profil.")
        return self.tenant(wanted)

    def parent_profile(self, parent_id: str, tenant_id: str | None = None) -> dict[str, Any]:
        parent = self.accounts.parent_by_id(parent_id)
        if not parent:
            raise ValueError("Elternzugang nicht gefunden.")
        tenant = self.tenant_for_parent(parent, tenant_id)
        return {
            "parent": {
                "id": parent.get("id"),
                "username": parent.get("username"),
                "email": parent.get("email"),
            },
            "profiles": [self._tenant_parent_item(self.tenant(item)) for item in parent.get("tenant_ids", [])],
            "tenant": self._tenant_parent_item(tenant),
        }

    def transit_stop_suggestions(self, query: str, limit: int = 8) -> dict[str, Any]:
        return self.transit_planner.stop_suggestions(query, limit=limit)

    def update_parent_profile(
        self,
        parent_id: str,
        payload: dict[str, Any],
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        parent = self.accounts.parent_by_id(parent_id)
        if not parent:
            raise ValueError("Elternzugang nicht gefunden.")
        existing = self.tenant_for_parent(parent, tenant_id)
        webuntis = payload.get("webuntis") if isinstance(payload.get("webuntis"), dict) else {}
        transit = payload.get("transit") if isinstance(payload.get("transit"), dict) else {}
        source = existing.webuntis
        webuntis_username = str(webuntis.get("username") or source.username).strip()
        webuntis_password = str(webuntis.get("password") or "").strip()
        tenant = replace(
            existing,
            webuntis=replace(
                source,
                server=str(webuntis.get("server") or source.server).strip(),
                school=str(webuntis.get("school") or source.school).strip(),
                username=webuntis_username,
                password=webuntis_password or source.password,
                app_secret=str(webuntis.get("app_secret") or "").strip() or source.app_secret,
                school_number=str(webuntis.get("school_number") or source.school_number).strip(),
                element_type=_optional_int(webuntis.get("element_type"), source.element_type) or 5,
                element_id=_optional_int(webuntis.get("element_id"), source.element_id),
                class_name=str(webuntis.get("class_name") or source.class_name).strip(),
            ),
            iserv=replace(
                existing.iserv,
                username=webuntis_username or existing.iserv.username,
                password=webuntis_password or existing.iserv.password,
            ),
            transit=_transit_from_payload(transit, existing.transit),
        )
        if webuntis_username or webuntis_password:
            self.accounts.update_parent_login(
                parent_id,
                username=webuntis_username or None,
                password=webuntis_password or None,
                now=_now(self.config.timezone),
            )
        self.config = replace(
            self.config,
            tenants=tuple(tenant if item.id == existing.id else item for item in self.config.tenants),
        )
        self._refresh_tenant_runtime()
        self._save_tenants()
        return self.parent_profile(parent_id, tenant.id)

    def add_manual_homework(
        self,
        text: str,
        subject: str | None = None,
        due_date: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        store = self.stores[tenant.id]
        clean_text = text.strip()
        clean_subject = (subject or "").strip()
        clean_due_date = _normalize_date_input(due_date)
        if not clean_text:
            raise ValueError("Text ist erforderlich.")

        latest_payload = store.load_latest_payload() or {}
        lessons = latest_payload.get("lessons", [])
        if not clean_due_date and clean_subject:
            clean_due_date = _next_subject_due_date(clean_subject, lessons, _now(self.config.timezone).date())
        if not clean_due_date:
            raise ValueError("Bitte Fach oder Fälligkeitsdatum angeben.")

        now = _now(self.config.timezone)
        item = {
            "id": f"manual:{secrets.token_urlsafe(8)}",
            "source": "manual",
            "external_id": "",
            "text": clean_text,
            "remark": "",
            "assigned_date": now.date().isoformat(),
            "due_date": clean_due_date,
            "lesson_id": "",
            "subject": [clean_subject] if clean_subject else [],
            "teacher": [],
            "attachments": [],
            "completed": False,
            "created_at": now.isoformat(),
        }
        state = store.load_homework_state()
        manual = state.get("manual", []) if isinstance(state.get("manual"), list) else []
        manual.append(item)
        state["manual"] = manual
        store.save_homework_state(state)
        return self.homework(tenant.id)

    def set_homework_completed(
        self,
        homework_id: str,
        completed: bool = True,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        store = self.stores[tenant.id]
        state = store.load_homework_state()
        completed_state = state.get("completed", {}) if isinstance(state.get("completed"), dict) else {}
        completed_state[homework_id] = {
            "completed": bool(completed),
            "completed_at": _now(self.config.timezone).isoformat() if completed else "",
        }
        state["completed"] = completed_state
        store.save_homework_state(state)
        return self.homework(tenant.id)

    def delete_manual_homework(self, homework_id: str, tenant_id: str | None = None) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        store = self.stores[tenant.id]
        if not homework_id.startswith("manual:"):
            raise ValueError("Nur eigene Hausaufgaben können gelöscht werden.")
        state = store.load_homework_state()
        manual = state.get("manual", []) if isinstance(state.get("manual"), list) else []
        state["manual"] = [
            item for item in manual
            if not (isinstance(item, dict) and item.get("id") == homework_id)
        ]
        completed_state = state.get("completed", {}) if isinstance(state.get("completed"), dict) else {}
        completed_state.pop(homework_id, None)
        state["completed"] = completed_state
        store.save_homework_state(state)
        return self.homework(tenant.id)

    def manual_lessons(self, tenant_id: str | None = None) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        state = self.stores[tenant.id].load_manual_lessons_state()
        items = [
            _public_manual_lesson(item)
            for item in state.get("items", [])
            if isinstance(item, dict)
        ]
        items.sort(key=_manual_lesson_sort_key)
        return {"items": items, "tenant_id": tenant.id}

    def add_manual_lesson(self, payload: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        store = self.stores[tenant.id]
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("Titel ist erforderlich.")
        start_time = _normalize_time_input(payload.get("start"))
        end_time = _normalize_time_input(payload.get("end"))
        if minutes_of_day(start_time) >= minutes_of_day(end_time):
            raise ValueError("Ende muss nach Start liegen.")

        recurring = bool(payload.get("recurring", True))
        clean_date = ""
        weekday: int | None = None
        if recurring:
            weekday = _optional_int(payload.get("weekday"), None)
            if weekday is None or weekday < 0 or weekday > 4:
                raise ValueError("Bitte einen Wochentag von Montag bis Freitag wählen.")
        else:
            clean_date = _normalize_date_input(payload.get("date"))
            if not clean_date:
                raise ValueError("Bitte ein Datum angeben.")
            if date.fromisoformat(clean_date).weekday() > 4:
                raise ValueError("Eigene Termine sind auf Montag bis Freitag begrenzt.")

        now = _now(self.config.timezone)
        item = {
            "id": f"lesson:{secrets.token_urlsafe(8)}",
            "source": "manual",
            "title": title,
            "recurring": recurring,
            "weekday": weekday,
            "date": clean_date,
            "start": start_time,
            "end": end_time,
            "room": str(payload.get("room") or "").strip(),
            "note": str(payload.get("note") or "").strip(),
            "created_at": now.isoformat(),
        }
        state = store.load_manual_lessons_state()
        items = state.get("items", []) if isinstance(state.get("items"), list) else []
        items.append(item)
        state["items"] = items
        store.save_manual_lessons_state(state)
        return self.manual_lessons(tenant.id)

    def delete_manual_lesson(self, manual_lesson_id: str, tenant_id: str | None = None) -> dict[str, Any]:
        tenant = self.tenant(tenant_id)
        store = self.stores[tenant.id]
        if not manual_lesson_id.startswith("lesson:"):
            raise ValueError("Nur eigene Termine können gelöscht werden.")
        state = store.load_manual_lessons_state()
        items = state.get("items", []) if isinstance(state.get("items"), list) else []
        state["items"] = [
            item for item in items
            if not (isinstance(item, dict) and item.get("id") == manual_lesson_id)
        ]
        store.save_manual_lessons_state(state)
        return self.manual_lessons(tenant.id)

    def update_poll_interval(self, minutes: int) -> int:
        sanitized = min(1440, max(1, int(minutes)))
        self.config = replace(self.config, poll_interval_minutes=sanitized)
        _update_env_value("POLL_INTERVAL_MINUTES", str(sanitized))
        return sanitized

    def update_settings(
        self,
        poll_interval_minutes: int | None = None,
        transit_poll_interval_minutes: int | None = None,
        email_recipients: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        tenant = self.tenant(tenant_id)
        if poll_interval_minutes is not None:
            updates["poll_interval_minutes"] = min(1440, max(1, int(poll_interval_minutes)))
            _update_env_value("POLL_INTERVAL_MINUTES", str(updates["poll_interval_minutes"]))
        if transit_poll_interval_minutes is not None:
            updates["transit_poll_interval_minutes"] = min(
                1440,
                max(1, int(transit_poll_interval_minutes)),
            )
            _update_env_value(
                "TRANSIT_POLL_INTERVAL_MINUTES",
                str(updates["transit_poll_interval_minutes"]),
            )
        if email_recipients is not None:
            recipients = _parse_list(email_recipients)
            updated_email = replace(tenant.email, recipients=recipients)
            updated_tenant = replace(tenant, email=updated_email)
            self.config = replace(
                self.config,
                tenants=tuple(
                    updated_tenant if item.id == tenant.id else item
                    for item in self.config.tenants
                ),
            )
            self.notifiers[tenant.id] = Notifier(updated_email, self.config.twilio, self.config.webhook_url)
            if tenant.id == self.default_tenant.id:
                updates["email"] = updated_email
                _update_env_value("EMAIL_TO", ", ".join(recipients))

        if updates:
            self.config = replace(self.config, **updates)
            self.notifier = Notifier(self.config.email, self.config.twilio, self.config.webhook_url)
            default_tenant = replace(self.default_tenant, email=self.config.email)
            self.config = replace(
                self.config,
                tenants=(default_tenant, *self.config.tenants[1:]),
            )
            self.notifiers[default_tenant.id] = self.notifier
        return {
            "poll_interval_minutes": self.config.poll_interval_minutes,
            "transit_poll_interval_minutes": self.config.transit_poll_interval_minutes,
            "email_recipients": self.tenant(tenant.id).email.recipients,
        }

    def _record(
        self,
        tenant: TenantConfig,
        now: datetime,
        status: str,
        changes: list[dict[str, Any]],
        notified_channels: list[str],
        message: str,
        notification_error: str = "",
    ) -> RunResult:
        payload = {
            "timestamp": now.isoformat(),
            "tenant_id": tenant.id,
            "tenant_name": tenant.name,
            "status": status,
            "changes_count": len(changes),
            "notified_channels": notified_channels,
            "message": message,
            "notification_error": notification_error,
        }
        self.stores[tenant.id].append_run(payload)
        return RunResult(
            status=status,
            timestamp=payload["timestamp"],
            changes=changes,
            notified_channels=notified_channels,
            message=message,
            notification_error=notification_error,
        )

    def _notification_channels(self, tenant: TenantConfig) -> list[str]:
        channels = []
        if tenant.email.enabled:
            channels.append("email")
        if self.config.twilio.enabled:
            channels.append("whatsapp")
        if self.config.webhook_url:
            channels.append("webhook")
        return channels

    def _tenant_summaries(self) -> list[dict[str, Any]]:
        summaries = []
        for tenant in self.config.tenants:
            latest_payload = self.stores[tenant.id].load_latest_payload() or {}
            latest = latest_payload.get("lessons", [])
            summaries.append(
                {
                    "id": tenant.id,
                    "name": tenant.name,
                    "active": tenant.active,
                    "profile": _public_profile(tenant),
                    "webuntis_ready": tenant.webuntis.is_complete,
                    "channels": self._notification_channels(tenant),
                    "snapshot_timestamp": latest_payload.get("timestamp"),
                    "lesson_count": len(latest),
                }
            )
        return summaries

    def _tenant_admin_item(self, tenant: TenantConfig) -> dict[str, Any]:
        return {
            "id": tenant.id,
            "name": tenant.name,
            "active": tenant.active,
            "parent_email": tenant.parent_email,
            "app_url": _app_url(self.config.public_timetable_url),
            "display": _public_profile(tenant),
            "display_admin": {
                "student_first_name": tenant.student_first_name,
                "student_last_name": tenant.student_last_initial,
                "student_last_initial": tenant.student_last_initial,
                "school": tenant.school_label,
                "class": tenant.class_label,
            },
            "webuntis": {
                "server": tenant.webuntis.server,
                "school": tenant.webuntis.school,
                "username": tenant.webuntis.username,
                "has_password": bool(tenant.webuntis.password),
                "has_app_secret": bool(tenant.webuntis.app_secret),
                "school_number": tenant.webuntis.school_number,
                "element_type": tenant.webuntis.element_type,
                "element_id": tenant.webuntis.element_id,
                "class_name": tenant.webuntis.class_name,
            },
            "iserv": {
                "base_url": tenant.iserv.base_url,
                "enabled": tenant.iserv.enabled,
                "ready": tenant.iserv.is_complete,
            },
            "email_recipients": tenant.email.recipients,
            "transit": _public_transit_settings(tenant.transit),
            "data_dir": str(tenant.data_dir),
        }

    def _tenant_parent_item(self, tenant: TenantConfig) -> dict[str, Any]:
        return {
            "id": tenant.id,
            "name": tenant.name,
            "active": tenant.active,
            "display": _public_profile(tenant),
            "webuntis": {
                "server": tenant.webuntis.server,
                "school": tenant.webuntis.school,
                "username": tenant.webuntis.username,
                "has_password": bool(tenant.webuntis.password),
                "has_app_secret": bool(tenant.webuntis.app_secret),
                "school_number": tenant.webuntis.school_number,
                "element_type": tenant.webuntis.element_type,
                "element_id": tenant.webuntis.element_id,
                "class_name": tenant.webuntis.class_name,
            },
            "iserv": {
                "base_url": tenant.iserv.base_url,
                "enabled": tenant.iserv.enabled,
                "ready": tenant.iserv.is_complete,
            },
            "transit": {
                **_public_transit_settings(tenant.transit),
                "validation": self.transit_planner.validate_stops(tenant.transit)
                if tenant.transit.enabled
                else {"feed": {"status": "not_configured"}, "groups": {}, "ready": False},
            },
            "webuntis_ready": tenant.webuntis.is_complete,
            "missing_fields": tenant.webuntis.missing_fields,
        }

    def _public_parent(self, parent: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": parent.get("id"),
            "username": parent.get("username"),
            "email": parent.get("email"),
            "tenant_ids": parent.get("tenant_ids") if isinstance(parent.get("tenant_ids"), list) else [],
            "active": bool(parent.get("active", True)),
            "created_at": parent.get("created_at"),
            "updated_at": parent.get("updated_at"),
        }

    def _public_invitation(self, invitation: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": invitation.get("id"),
            "email": invitation.get("email"),
            "tenant_id": invitation.get("tenant_id"),
            "created_at": invitation.get("created_at"),
            "expires_at": invitation.get("expires_at"),
            "accepted_at": invitation.get("accepted_at"),
            "sent_at": invitation.get("sent_at"),
        }

    def _tenant_from_admin_payload(
        self,
        payload: dict[str, Any],
        tenant_id: str,
        public_id: str,
        existing: TenantConfig | None,
    ) -> TenantConfig:
        webuntis = payload.get("webuntis") if isinstance(payload.get("webuntis"), dict) else {}
        display = payload.get("display") if isinstance(payload.get("display"), dict) else {}
        email = payload.get("email") if isinstance(payload.get("email"), dict) else {}
        source = existing or self.default_tenant
        element_id = _optional_int(webuntis.get("element_id"), source.webuntis.element_id)
        username = source.webuntis.username if existing else ""
        password = source.webuntis.password if existing else ""
        app_secret = source.webuntis.app_secret if existing else ""
        class_label = (
            str(display.get("class") or display.get("class_name") or "").strip()
            or str(webuntis.get("class_name") or "").strip()
        )
        return TenantConfig(
            id=tenant_id,
            name=str(payload.get("name") or display.get("student_first_name") or source.name).strip(),
            public_id=public_id,
            parent_email=normalize_email(payload.get("parent_email") or source.parent_email),
            student_first_name=str(display.get("student_first_name") or source.student_first_name).strip(),
            student_last_initial=str(
                display.get("student_last_name")
                or display.get("student_last_initial")
                or source.student_last_initial
            ).strip(),
            school_label=str(display.get("school") or source.school_label).strip(),
            class_label=class_label or source.class_label,
            active=bool(payload.get("active", source.active)),
            webuntis=replace(
                source.webuntis,
                server=str(webuntis.get("server") or source.webuntis.server).strip(),
                school=str(webuntis.get("school") or source.webuntis.school).strip(),
                username=username,
                password=password,
                app_secret=app_secret,
                school_number=str(webuntis.get("school_number") or source.webuntis.school_number).strip(),
                element_type=_optional_int(webuntis.get("element_type"), source.webuntis.element_type) or 5,
                element_id=element_id,
                class_name=str(webuntis.get("class_name") or source.webuntis.class_name).strip(),
            ),
            iserv=replace(
                source.iserv,
                username=username or source.iserv.username,
                password=password or source.iserv.password,
            ),
            email=replace(
                source.email,
                recipients=_parse_list(str(email.get("recipients") or "")) or source.email.recipients,
            ),
            transit=source.transit,
            public_timetable_url=_app_url(self.config.public_timetable_url),
            data_dir=source.data_dir if existing else self.config.data_dir / "tenants" / tenant_id,
        )

    def _refresh_tenant_runtime(self) -> None:
        self.stores = {
            tenant.id: self.stores.get(tenant.id, SnapshotStore(tenant.data_dir))
            for tenant in self.config.tenants
        }
        self.notifiers = {
            tenant.id: Notifier(tenant.email, self.config.twilio, self.config.webhook_url)
            for tenant in self.config.tenants
        }
        self.store = self.stores[self.default_tenant.id]
        self.notifier = self.notifiers[self.default_tenant.id]
        with self._transit_cache_lock:
            self._transit_cache.clear()
            self._transit_latest.clear()

    def _save_tenants(self) -> None:
        self.config.tenants_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "tenants": [
                _serialize_tenant(self.config.tenants_file.parent.parent, tenant)
                for tenant in self.config.tenants
            ]
        }
        self.config.tenants_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _replace_tenant(self, tenant: TenantConfig) -> None:
        self.config = replace(
            self.config,
            tenants=tuple(tenant if item.id == tenant.id else item for item in self.config.tenants),
        )
        self._refresh_tenant_runtime()
        self._save_tenants()

    def _tenant_with_webuntis_login(self, tenant: TenantConfig, username: str, password: str) -> TenantConfig:
        return replace(
            tenant,
            webuntis=replace(
                tenant.webuntis,
                username=str(username or "").strip(),
                password=str(password or "").strip() or tenant.webuntis.password,
            ),
            iserv=replace(
                tenant.iserv,
                username=str(username or "").strip() or tenant.iserv.username,
                password=str(password or "").strip() or tenant.iserv.password,
            ),
        )

    def _update_tenant_webuntis_login(self, tenant_id: str, username: str, password: str) -> None:
        self._replace_tenant(self._tenant_with_webuntis_login(self.tenant(tenant_id), username, password))


class PollingWorker:
    FULL_DAY_INTERVAL_SECONDS = 30 * 60
    WINDOW_RECOMMENDATION_INTERVAL_SECONDS = 30 * 60
    WINDOW_FULL_DAY_INTERVAL_SECONDS = 6 * 60 * 60

    def __init__(self, service: MonitorService) -> None:
        self.service = service
        self._stop = threading.Event()
        self._transit_wakeup = threading.Event()
        self._preload_wakeup = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        if any(thread.is_alive() for thread in self._threads):
            return
        self._stop.clear()
        self._threads = [
            threading.Thread(
                target=self._timetable_loop,
                name="schulplaner-timetable-poller",
                daemon=True,
            ),
            threading.Thread(
                target=self._transit_loop,
                name="schulplaner-transit-poller",
                daemon=True,
            ),
            threading.Thread(
                target=self._preload_loop,
                name="schulplaner-transit-preloader",
                daemon=True,
            ),
        ]
        for thread in self._threads:
            thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._transit_wakeup.set()
        self._preload_wakeup.set()
        for thread in self._threads:
            thread.join(timeout=5)

    def _timetable_loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.service.run_once()
            except Exception as exc:
                self._record_error("error", str(exc))
            finally:
                self._transit_wakeup.set()
                self._preload_wakeup.set()
            self._stop.wait(self.service.config.poll_interval_minutes * 60)

    def _transit_loop(self) -> None:
        last_full_refresh = 0.0
        while not self._stop.is_set():
            self._transit_wakeup.clear()
            try:
                self.service.warm_transit_cache(
                    notify_changes=True,
                    include_full_day=False,
                    force_refresh=True,
                )
                now_monotonic = time.monotonic()
                if now_monotonic - last_full_refresh >= self.FULL_DAY_INTERVAL_SECONDS:
                    self.service.warm_transit_cache(
                        notify_changes=False,
                        include_full_day=True,
                        force_refresh=True,
                    )
                    last_full_refresh = time.monotonic()
            except Exception as exc:
                self._record_error("transit_error", f"Busdaten konnten nicht aktualisiert werden: {exc}")
            self._transit_wakeup.wait(
                self.service.config.transit_poll_interval_minutes * 60
            )

    def _preload_loop(self) -> None:
        last_recommendation_refresh = 0.0
        last_full_refresh = 0.0
        while not self._stop.is_set():
            self._preload_wakeup.clear()
            now = _now(self.service.config.timezone)
            dates = [
                item for item in selectable_transit_dates(now.date())
                if item != now.date()
            ]
            current_monotonic = time.monotonic()
            try:
                if (
                    current_monotonic - last_recommendation_refresh
                    >= self.WINDOW_RECOMMENDATION_INTERVAL_SECONDS
                ):
                    self.service.warm_transit_cache(
                        notify_changes=False,
                        include_full_day=False,
                        force_refresh=True,
                        target_dates=dates,
                    )
                    last_recommendation_refresh = time.monotonic()
                if (
                    current_monotonic - last_full_refresh
                    >= self.WINDOW_FULL_DAY_INTERVAL_SECONDS
                ):
                    self.service.warm_transit_cache(
                        notify_changes=False,
                        include_full_day=True,
                        force_refresh=True,
                        target_dates=dates,
                    )
                    last_full_refresh = time.monotonic()
            except Exception as exc:
                self._record_error(
                    "transit_error",
                    f"Busdaten für auswählbare Tage konnten nicht vorgeladen werden: {exc}",
                )
            wait_seconds = min(
                self.WINDOW_RECOMMENDATION_INTERVAL_SECONDS,
                self.WINDOW_FULL_DAY_INTERVAL_SECONDS,
            )
            if self._preload_wakeup.wait(wait_seconds):
                last_recommendation_refresh = 0.0

    def _record_error(self, status: str, message: str) -> None:
        now = _now(self.service.config.timezone)
        self.service.store.append_run(
            {
                "timestamp": now.isoformat(),
                "status": status,
                "changes_count": 0,
                "notified_channels": [],
                "message": message,
            }
        )


def _transit_plan_successful(plan: dict[str, Any]) -> bool:
    feed = plan.get("feed") if isinstance(plan.get("feed"), dict) else {}
    return str(feed.get("status") or "") not in {
        "error",
        "missing",
        "downloading",
        "preparing",
    }


def _transit_recommendation_snapshot(plan: dict[str, Any]) -> dict[str, Any]:
    recommendation = plan.get("recommendation") if isinstance(plan.get("recommendation"), dict) else {}
    return {
        "schema": 2,
        "date": str(plan.get("date") or ""),
        "recommendation": {
            "outbound": _canonical_transit_connection(recommendation.get("outbound")),
            "return": _canonical_transit_connection(recommendation.get("return")),
        },
    }


def _canonical_transit_connection(connection: Any) -> dict[str, Any] | None:
    if not isinstance(connection, dict):
        return None
    return {
        "line": str(connection.get("line") or ""),
        "departure": str(connection.get("departure") or ""),
        "arrival": str(connection.get("arrival") or ""),
        "planned_departure": str(connection.get("planned_departure") or ""),
        "planned_arrival": str(connection.get("planned_arrival") or ""),
        "duration_minutes": _optional_int(connection.get("duration_minutes"), 0) or 0,
        "from": _canonical_transit_stop(connection.get("from")),
        "to": _canonical_transit_stop(connection.get("to")),
        "headsign": str(connection.get("headsign") or ""),
        "cancelled": bool(connection.get("cancelled")),
        "delay_seconds": _canonical_delay_seconds(connection.get("delay_seconds")),
        "platform": str(connection.get("platform") or ""),
        "realtime_platform": str(connection.get("realtime_platform") or ""),
        "legs": [
            _canonical_transit_leg(leg)
            for leg in connection.get("legs") or []
            if isinstance(leg, dict)
        ],
        "announcements": _canonical_transit_announcements(connection.get("announcements")),
    }


def _freeze_departed_recommendations(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
    now: datetime,
) -> dict[str, Any]:
    recommendation = dict(current.get("recommendation") or {})
    old_recommendation = (
        previous.get("recommendation")
        if isinstance(previous, dict) and previous.get("date") == current.get("date")
        and isinstance(previous.get("recommendation"), dict)
        else {}
    )
    for key in ("outbound", "return"):
        current_connection = recommendation.get(key)
        old_connection = old_recommendation.get(key)
        candidate = current_connection if isinstance(current_connection, dict) else old_connection
        if _transit_connection_departed(candidate, str(current.get("date") or ""), now):
            recommendation[key] = old_connection if old_recommendation else None
    return {**current, "recommendation": recommendation}


def _transit_connection_departed(connection: Any, service_date: str, now: datetime) -> bool:
    if not isinstance(connection, dict):
        return False
    departure = str(connection.get("departure") or "")
    try:
        departure_time = datetime.strptime(
            f"{service_date} {departure}",
            "%Y-%m-%d %H:%M",
        ).replace(tzinfo=now.tzinfo)
    except ValueError:
        return False
    return departure_time <= now


def _canonical_transit_stop(stop: Any) -> dict[str, str]:
    if not isinstance(stop, dict):
        return {"name": ""}
    return {
        "name": str(stop.get("name") or ""),
    }


def _canonical_transit_leg(leg: dict[str, Any]) -> dict[str, Any]:
    return {
        "line": str(leg.get("line") or ""),
        "from": _canonical_transit_stop(leg.get("from")),
        "to": _canonical_transit_stop(leg.get("to")),
        "departure": str(leg.get("departure") or ""),
        "arrival": str(leg.get("arrival") or ""),
        "departure_delay_seconds": _canonical_delay_seconds(leg.get("departure_delay_seconds")),
        "arrival_delay_seconds": _canonical_delay_seconds(leg.get("arrival_delay_seconds")),
        "cancelled": bool(leg.get("cancelled")),
        "platform": str(leg.get("platform") or ""),
        "realtime_platform": str(leg.get("realtime_platform") or ""),
        "announcements": _canonical_transit_announcements(leg.get("announcements")),
    }


def _canonical_transit_announcements(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result = [
        {
            "id": str(item.get("id") or ""),
            "summary": str(item.get("summary") or ""),
            "description": str(item.get("description") or ""),
            "planned": item.get("planned"),
            "reason": str(item.get("reason") or ""),
        }
        for item in value
        if isinstance(item, dict)
    ]
    return sorted(result, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, default=str))


def _canonical_delay_seconds(value: Any) -> int:
    seconds = _optional_int(value, 0) or 0
    return round(seconds / 60) * 60


def _transit_notification_fingerprint(subject: str, body: str) -> str:
    payload = f"{subject}\n{body}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_transit_notification(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> tuple[str, str]:
    service_date = str(current.get("date") or "")
    try:
        day_label = date.fromisoformat(service_date).strftime("%d.%m.%Y")
    except ValueError:
        day_label = service_date or "heute"
    subject = f"Dein Bus fährt anders: {day_label}"
    old_recommendation = previous.get("recommendation") if isinstance(previous.get("recommendation"), dict) else {}
    new_recommendation = current.get("recommendation") if isinstance(current.get("recommendation"), dict) else {}
    lines = ["Hallo,", "", f"Bus geändert – {day_label}"]
    for key, label in (("outbound", "Fahrt zur Schule"), ("return", "Fahrt nach Hause")):
        before = old_recommendation.get(key)
        after = new_recommendation.get(key)
        if before == after:
            continue
        lines.extend(["", f"{label}:"])
        for field, old, new in _transit_change_fields(before, after):
            if old and new:
                lines.append(f"- {field}: {old} → {new}")
            elif new:
                lines.append(f"- {field}: jetzt {new}")
            else:
                lines.append(f"- {field}: {old} gilt nicht mehr")
    lines.extend(["", "Bitte nutze die Angaben unter „Jetzt“."])
    return subject, "\n".join(lines)


def build_transit_notification_html(
    previous: dict[str, Any],
    current: dict[str, Any],
    transit_url: str = "",
) -> str:
    service_date = str(current.get("date") or "")
    try:
        day_label = date.fromisoformat(service_date).strftime("%d.%m.%Y")
    except ValueError:
        day_label = service_date or "heute"
    old_recommendation = previous.get("recommendation") if isinstance(previous.get("recommendation"), dict) else {}
    new_recommendation = current.get("recommendation") if isinstance(current.get("recommendation"), dict) else {}
    sections: list[str] = []
    for key, label in (("outbound", "Fahrt zur Schule"), ("return", "Fahrt nach Hause")):
        before = old_recommendation.get(key)
        after = new_recommendation.get(key)
        if before == after:
            continue
        rows = _transit_change_fields(before, after)
        cancelled = isinstance(after, dict) and bool(after.get("cancelled"))
        accent = "#ef4444" if cancelled else "#fbbf24"
        background = "#3b1118" if cancelled else "#3a2a0a"
        row_html = "".join(
            f'<div style="padding:9px 0;border-top:1px solid #475569">'
            f'<div style="color:#cbd5e1;font-size:13px;font-weight:700">{html.escape(field)}</div>'
            f'{f"<div style=\"margin-top:3px;color:#94a3b8;text-decoration:line-through\">{html.escape(old)}</div>" if old else ""}'
            f'<div style="margin-top:3px;color:{accent};font-size:17px;font-weight:800">Jetzt: {html.escape(new or "gilt nicht mehr")}</div>'
            f'</div>'
            for field, old, new in rows
        )
        sections.append(
            f"""
            <section style="margin:20px 0 0">
              <h2 style="margin:0 0 10px;font-size:18px;color:#f8fafc">{html.escape(label)}</h2>
              <div style="padding:5px 14px 8px;border:1px solid {accent};border-left:5px solid {accent};border-radius:6px;background:{background};color:#f8fafc">
                <strong style="display:block;padding:10px 0;color:{accent}">Das ist neu</strong>
                {row_html}
              </div>
            </section>
            """
        )
    link = (
        f'<p style="margin:24px 0 0"><a href="{html.escape(transit_url, quote=True)}" '
        'style="color:#2dd4bf;font-weight:700">Busfahrplan öffnen</a></p>'
        if transit_url
        else ""
    )
    return f"""<!doctype html>
<html lang="de">
  <body style="margin:0;padding:24px;background:#0b1220;color:#f8fafc;font-family:Arial,sans-serif">
    <main style="max-width:640px;margin:0 auto;padding:24px;border:1px solid #273449;border-radius:8px;background:#111827">
      <p style="margin:0 0 10px;color:#2dd4bf;font-size:13px;font-weight:700;text-transform:uppercase">Busänderung</p>
      <h1 style="margin:0 0 12px;font-size:24px">Dein Bus fährt anders</h1>
      <p style="margin:0;color:#cbd5e1;line-height:1.55">{html.escape(day_label)} · Nur die Änderungen:</p>
      {''.join(sections)}
      {link}
      <p style="margin:24px 0 0;color:#cbd5e1;line-height:1.55">Viele Grüße<br>Schulplaner</p>
    </main>
  </body>
</html>"""


def _transit_change_fields(
    before: Any,
    after: Any,
) -> list[tuple[str, str, str]]:
    if not isinstance(before, dict) and not isinstance(after, dict):
        return []
    if not isinstance(before, dict):
        return [("Neue Fahrt", "", _transit_connection_summary(after))]
    if not isinstance(after, dict):
        return [("Fahrt", _transit_connection_summary(before), "Keine passende Fahrt")]

    pairs = [
        ("Bus", str(before.get("line") or "Bus"), str(after.get("line") or "Bus")),
        ("Abfahrt", _clock_value(before.get("departure")), _clock_value(after.get("departure"))),
        ("Ankunft", _clock_value(before.get("arrival")), _clock_value(after.get("arrival"))),
        ("Strecke", _transit_route(before), _transit_route(after)),
        ("Fahrtrichtung", str(before.get("headsign") or ""), str(after.get("headsign") or "")),
        ("Verspätung", _transit_delay_label(before), _transit_delay_label(after)),
        ("Steig", _transit_platform(before), _transit_platform(after)),
        ("Status", "Fällt aus" if before.get("cancelled") else "Fährt", "Fällt aus" if after.get("cancelled") else "Fährt"),
        ("Hinweis", _transit_announcement_label(before), _transit_announcement_label(after)),
    ]
    changed = [(label, old, new) for label, old, new in pairs if old != new]
    if changed:
        return changed
    return [("Verbindung", _transit_connection_summary(before), _transit_connection_summary(after))]


def _clock_value(value: Any) -> str:
    text = str(value or "").strip()
    return f"{text} Uhr" if text else ""


def _transit_route(connection: dict[str, Any]) -> str:
    origin = str((connection.get("from") or {}).get("name") or "")
    destination = str((connection.get("to") or {}).get("name") or "")
    return " → ".join(value for value in (origin, destination) if value)


def _transit_delay_label(connection: dict[str, Any]) -> str:
    minutes = round((_optional_int(connection.get("delay_seconds"), 0) or 0) / 60)
    if minutes > 0:
        return f"+{minutes} Min"
    if minutes < 0:
        return f"{abs(minutes)} Min früher"
    return "Pünktlich"


def _transit_platform(connection: dict[str, Any]) -> str:
    return str(connection.get("realtime_platform") or connection.get("platform") or "")


def _transit_announcement_label(connection: dict[str, Any]) -> str:
    return " · ".join(
        str(item.get("summary") or item.get("description") or "").strip()
        for item in connection.get("announcements") or []
        if isinstance(item, dict) and str(item.get("summary") or item.get("description") or "").strip()
    )


def _transit_connection_summary(connection: dict[str, Any]) -> str:
    line = str(connection.get("line") or "Bus")
    departure = _clock_value(connection.get("departure"))
    route = _transit_route(connection)
    return " · ".join(value for value in (line, departure, route) if value)


def _format_transit_connection(connection: Any) -> str:
    if not isinstance(connection, dict):
        return "Es wurde keine passende Busfahrt gefunden."
    origin = str((connection.get("from") or {}).get("name") or "")
    destination = str((connection.get("to") or {}).get("name") or "")
    delay_minutes = round((_optional_int(connection.get("delay_seconds"), 0) or 0) / 60)
    platform = str(connection.get("realtime_platform") or connection.get("platform") or "")
    announcements = [
        str(item.get("summary") or item.get("description") or "").strip()
        for item in connection.get("announcements") or []
        if isinstance(item, dict)
    ]
    line = str(connection.get("line") or "Bus").replace(" → ", ", dann Bus ")
    lines = [
        f"- Bus {line}" if line != "Bus" else "- Bus",
        f"- Abfahrt: {connection.get('departure') or '--:--'} Uhr",
        f"- Ankunft: {connection.get('arrival') or '--:--'} Uhr",
    ]
    if origin and destination:
        lines.append(f"- Von {origin} nach {destination}")
    if connection.get("headsign"):
        lines.append(f"- Fahrtrichtung: {connection.get('headsign')}")
    duration = _optional_int(connection.get("duration_minutes"), 0) or 0
    if duration:
        lines.append(f"- Die Fahrt dauert ungefähr {duration} Minuten.")
    planned_departure = str(connection.get("planned_departure") or "")
    planned_arrival = str(connection.get("planned_arrival") or "")
    if planned_departure and planned_departure != str(connection.get("departure") or ""):
        lines.append(f"- Im Fahrplan stand zuerst {planned_departure} Uhr als Abfahrt.")
    if planned_arrival and planned_arrival != str(connection.get("arrival") or ""):
        lines.append(f"- Im Fahrplan stand zuerst {planned_arrival} Uhr als Ankunft.")
    if connection.get("cancelled"):
        lines.append("- Diese Fahrt fällt aus.")
    elif delay_minutes > 0:
        lines.append(f"- Der Bus ist voraussichtlich {delay_minutes} Minuten später da.")
    elif delay_minutes < 0:
        lines.append(f"- Der Bus ist voraussichtlich {abs(delay_minutes)} Minuten früher da.")
    if platform:
        lines.append(f"- Einsteigen an Steig {platform}")
    legs = [item for item in connection.get("legs") or [] if isinstance(item, dict)]
    if len(legs) > 1:
        lines.append("- So fährst du:")
        for index, leg in enumerate(legs, start=1):
            leg_line = str(leg.get("line") or "Bus")
            leg_from = str((leg.get("from") or {}).get("name") or "")
            leg_to = str((leg.get("to") or {}).get("name") or "")
            leg_departure = str(leg.get("departure") or "")
            leg_arrival = str(leg.get("arrival") or "")
            leg_route = f" von {leg_from} nach {leg_to}" if leg_from and leg_to else ""
            leg_times = f", {leg_departure}-{leg_arrival} Uhr" if leg_departure and leg_arrival else ""
            lines.append(f"  {index}. Bus {leg_line}{leg_route}{leg_times}")
            leg_platform = str(leg.get("realtime_platform") or leg.get("platform") or "")
            if leg_platform:
                lines.append(f"     Einsteigen an Steig {leg_platform}")
            if leg.get("cancelled"):
                lines.append("     Dieser Teil der Fahrt fällt aus.")
            leg_delays = [
                _optional_int(leg.get("departure_delay_seconds"), 0) or 0,
                _optional_int(leg.get("arrival_delay_seconds"), 0) or 0,
            ]
            leg_delay = round(max(leg_delays, key=abs) / 60)
            if leg_delay > 0:
                lines.append(f"     Dieser Bus ist ungefähr {leg_delay} Minuten später da.")
            elif leg_delay < 0:
                lines.append(f"     Dieser Bus ist ungefähr {abs(leg_delay)} Minuten früher da.")
            for item in leg.get("announcements") or []:
                if isinstance(item, dict):
                    note = str(item.get("summary") or item.get("description") or "").strip()
                    if note:
                        lines.append(f"     Wichtig: {note}")
    for announcement in announcements:
        if announcement:
            lines.append(f"- Wichtig: {announcement}")
    return "\n".join(lines)


def _now(timezone_name: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError:
        return datetime.now().astimezone()


def monitor_window(today: date) -> tuple[date, date]:
    current_monday = today - timedelta(days=today.weekday())
    next_friday = current_monday + timedelta(days=11)
    return current_monday, next_friday


def selectable_transit_dates(today: date) -> list[date]:
    current_monday = today - timedelta(days=today.weekday())
    weekdays = [
        current_monday + timedelta(days=offset)
        for offset in (*range(5), *range(7, 12))
    ]
    return sorted(
        weekdays,
        key=lambda item: (
            item != today,
            item < today,
            abs((item - today).days),
        ),
    )


def _comparison_dates(previous_payload: dict[str, Any] | None, current_today: date) -> set[str] | None:
    previous_today = _snapshot_date(previous_payload)
    if previous_today is None:
        return None

    previous_start, previous_end = monitor_window(previous_today)
    current_start, current_end = monitor_window(current_today)
    overlap_start = max(previous_start, current_start)
    overlap_end = min(previous_end, current_end)
    if overlap_start > overlap_end:
        return set()

    return {
        (overlap_start + timedelta(days=offset)).isoformat()
        for offset in range((overlap_end - overlap_start).days + 1)
    }


def _snapshot_date(previous_payload: dict[str, Any] | None) -> date | None:
    if not previous_payload:
        return None
    timestamp = str(previous_payload.get("timestamp") or "")
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _update_env_value(key: str, value: str) -> None:
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return

    lines = env_path.read_text(encoding="utf-8").splitlines()
    replaced = False
    updated = []
    for line in lines:
        if line.startswith(f"{key}="):
            updated.append(f"{key}={value}")
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.append(f"{key}={value}")
    env_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def _parse_list(value: str) -> list[str]:
    normalized = value.replace(";", ",").replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _week_for_changes(changes: list[Any], today: date) -> str:
    current_monday = today - timedelta(days=today.weekday())
    next_monday = current_monday + timedelta(days=7)
    for change in changes:
        try:
            changed_day = date.fromisoformat(change.date)
        except (TypeError, ValueError):
            continue
        if changed_day >= next_monday:
            return "next"
    return "current"


def _timetable_url(base_url: str, week: str) -> str:
    if not base_url:
        return ""
    if not week:
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}week={week}"


def _setup_url(base_url: str, token: str) -> str:
    app_url = _app_url(base_url)
    separator = "&" if "?" in app_url else "?"
    return f"{app_url.replace('/app', '/setup')}{separator}token={quote(token, safe='')}"


def _resolve_homework_due_date(
    item: dict[str, Any],
    lessons: list[dict[str, Any]],
    today: date,
) -> dict[str, Any]:
    due_date = _normalize_date_input(item.get("due_date"))
    subjects = item.get("subject") if isinstance(item.get("subject"), list) else []
    if not due_date and subjects:
        due_date = _next_subject_due_date(str(subjects[0]), lessons, today)
    return {**item, "due_date": due_date}


def _with_homework_status(
    item: dict[str, Any],
    completed_state: dict[str, Any],
    today: date,
) -> dict[str, Any]:
    state = completed_state.get(str(item.get("id")))
    if isinstance(state, dict):
        updated = {
            **item,
            "completed": bool(state.get("completed")),
            "completed_at": str(state.get("completed_at") or ""),
        }
    else:
        updated = {**item, "completed": bool(item.get("completed")), "completed_at": ""}
    return {**updated, "is_expired": _homework_expired(updated, today)}


def _with_local_completion(
    item: dict[str, Any],
    completed_state: dict[str, Any],
) -> dict[str, Any]:
    return _with_homework_status(item, completed_state, date.today())


def _homework_expired(item: dict[str, Any], today: date) -> bool:
    due_date = _normalize_date_input(item.get("due_date"))
    if not due_date:
        return False
    return date.fromisoformat(due_date) < today


def _homework_completed_retention_expired(item: dict[str, Any], today: date) -> bool:
    if not item.get("completed"):
        return False
    due_date = _normalize_date_input(item.get("due_date"))
    if not due_date:
        return False
    remove_on = date.fromisoformat(due_date) + timedelta(days=HOMEWORK_COMPLETED_RETENTION_DAYS)
    return remove_on <= today


def _cleanup_completed_homework_state(
    state: dict[str, Any],
    items: list[dict[str, Any]],
    today: date,
) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    expired_ids = {
        str(item.get("id"))
        for item in items
        if item.get("id") and _homework_completed_retention_expired(item, today)
    }
    if not expired_ids:
        return state, items, False

    manual = state.get("manual", []) if isinstance(state.get("manual"), list) else []
    completed_state = state.get("completed", {}) if isinstance(state.get("completed"), dict) else {}
    cleaned_manual = [
        item for item in manual
        if not (isinstance(item, dict) and str(item.get("id")) in expired_ids)
    ]
    cleaned_completed = {
        key: value
        for key, value in completed_state.items()
        if str(key) not in expired_ids
    }
    cleaned_state = {
        **state,
        "manual": cleaned_manual,
        "completed": cleaned_completed,
    }
    visible_items = [
        item for item in items
        if str(item.get("id")) not in expired_ids
    ]
    changed = cleaned_manual != manual or cleaned_completed != completed_state
    return cleaned_state, visible_items, changed


def _homework_sort_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return (
        item.get("due_date") or "9999-12-31",
        ", ".join(item.get("subject") if isinstance(item.get("subject"), list) else []),
        item.get("text") or "",
    )


def _manual_lesson_occurrences(
    items: list[dict[str, Any]],
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    lessons = []
    for item in items:
        if not isinstance(item, dict):
            continue
        for lesson_day in _manual_lesson_dates(item, start, end):
            lessons.append(_manual_lesson_occurrence(item, lesson_day))
    return sorted(lessons, key=lambda item: (item["date"], item["start"], item["end"], item["uid"]))


def _manual_lesson_dates(item: dict[str, Any], start: date, end: date) -> list[date]:
    if bool(item.get("recurring", True)):
        weekday = _optional_int(item.get("weekday"), None)
        if weekday is None or weekday < 0 or weekday > 4:
            return []
        cursor = start
        while cursor.weekday() != weekday:
            cursor += timedelta(days=1)
        days = []
        while cursor <= end:
            days.append(cursor)
            cursor += timedelta(days=7)
        return days

    lesson_date = _normalize_date_input(item.get("date"))
    if not lesson_date:
        return []
    day = date.fromisoformat(lesson_date)
    return [day] if start <= day <= end else []


def _manual_lesson_occurrence(item: dict[str, Any], lesson_day: date) -> dict[str, Any]:
    lesson_id = str(item.get("id") or "lesson:manual")
    title = str(item.get("title") or "Eigener Termin").strip() or "Eigener Termin"
    room = str(item.get("room") or "").strip()
    note = str(item.get("note") or "").strip()
    return {
        "uid": f"{lesson_id}:{lesson_day.isoformat()}",
        "source": "manual",
        "date": lesson_day.isoformat(),
        "start": _normalize_time_input(item.get("start")),
        "end": _normalize_time_input(item.get("end")),
        "subject": [title],
        "teacher": [],
        "room": [room] if room else [],
        "lesson_text": "",
        "substitution_text": "",
        "info": note,
        "status": "regular",
        "code": "manual",
        "removed": {},
    }


def _public_manual_lesson(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id") or ""),
        "source": "manual",
        "title": str(item.get("title") or ""),
        "recurring": bool(item.get("recurring", True)),
        "weekday": _optional_int(item.get("weekday"), None),
        "date": str(item.get("date") or ""),
        "start": str(item.get("start") or ""),
        "end": str(item.get("end") or ""),
        "room": str(item.get("room") or ""),
        "note": str(item.get("note") or ""),
        "created_at": str(item.get("created_at") or ""),
    }


def _manual_lesson_sort_key(item: dict[str, Any]) -> tuple[int, str, str, str]:
    recurring = bool(item.get("recurring", True))
    weekday_value = _optional_int(item.get("weekday"), 9)
    weekday = 9 if weekday_value is None else weekday_value
    return (
        0 if recurring else 1,
        str(weekday) if recurring else str(item.get("date") or "9999-12-31"),
        str(item.get("start") or ""),
        str(item.get("title") or ""),
    )


def _normalize_date_input(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ValueError("Datum muss im Format JJJJ-MM-TT angegeben werden.") from exc


def _normalize_time_input(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Uhrzeit ist erforderlich.")
    if ":" not in text and len(text) in {3, 4} and text.isdigit():
        text = f"{text[:-2]}:{text[-2:]}"
    parts = text.split(":", 1)
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError("Uhrzeit muss im Format HH:MM angegeben werden.")
    hours = int(parts[0])
    mins = int(parts[1])
    if hours < 0 or hours > 23 or mins < 0 or mins > 59:
        raise ValueError("Uhrzeit ist ungültig.")
    return f"{hours:02d}:{mins:02d}"


def minutes_of_day(value: str) -> int:
    hours, mins = _normalize_time_input(value).split(":", 1)
    return int(hours) * 60 + int(mins)


def _next_subject_due_date(subject: str, lessons: list[dict[str, Any]], today: date) -> str:
    matches = []
    for lesson in lessons:
        lesson_day = _normalize_date_input(lesson.get("date"))
        if not lesson_day or date.fromisoformat(lesson_day) < today:
            continue
        if _subjects_match(subject, lesson.get("subject")):
            matches.append(lesson_day)
    return min(matches) if matches else ""


def _subjects_match(subject: str, lesson_subjects: Any) -> bool:
    needle = _homework_search_value(subject)
    if not needle:
        return False
    if not isinstance(lesson_subjects, list):
        return False
    return any(needle in _homework_search_value(value) for value in lesson_subjects)


def _homework_search_value(value: Any) -> str:
    return str(value or "").replace("(", " ").replace(")", " ").casefold().strip()


def _public_profile(tenant: TenantConfig) -> dict[str, str]:
    first_name = tenant.student_first_name.strip()
    last_name = tenant.student_last_initial.strip()
    display_name = " ".join(item for item in [first_name, last_name] if item)
    return {
        "student_name": display_name,
        "school": tenant.school_label,
        "class": tenant.class_label,
    }


def _app_url(base_url: str) -> str:
    if not base_url:
        return "/app"
    cleaned = base_url.split("#", 1)[0].split("?", 1)[0].rstrip("/")
    if "/t/" in cleaned:
        cleaned = cleaned.split("/t/", 1)[0].rstrip("/")
    if cleaned.endswith("/app"):
        return cleaned
    return f"{cleaned}/app"


def _serialize_tenant(root: Path, tenant: TenantConfig) -> dict[str, Any]:
    try:
        data_dir = str(tenant.data_dir.relative_to(root))
    except ValueError:
        data_dir = str(tenant.data_dir)
    return {
        "id": tenant.id,
        "name": tenant.name,
        "public_id": tenant.public_id,
        "active": tenant.active,
        "data_dir": data_dir,
        "parent_email": tenant.parent_email,
        "public_timetable_url": _app_url(""),
        "display": {
            "student_first_name": tenant.student_first_name,
            "student_last_name": tenant.student_last_initial,
            "student_last_initial": tenant.student_last_initial,
            "school": tenant.school_label,
            "class": tenant.class_label,
        },
        "webuntis": {
            "server": tenant.webuntis.server,
            "school": tenant.webuntis.school,
            "username": tenant.webuntis.username,
            "password": tenant.webuntis.password,
            "app_secret": tenant.webuntis.app_secret,
            "school_number": tenant.webuntis.school_number,
            "element_type": tenant.webuntis.element_type,
            "element_id": tenant.webuntis.element_id,
            "class_name": tenant.webuntis.class_name,
        },
        "iserv": {
            "base_url": tenant.iserv.base_url,
            "username": tenant.iserv.username,
            "password": tenant.iserv.password,
            "enabled": tenant.iserv.enabled,
        },
        "email": {
            "recipients": ", ".join(tenant.email.recipients),
        },
        "transit": _public_transit_settings(tenant.transit),
    }


def _transit_from_payload(payload: dict[str, Any], source: TransitSettings) -> TransitSettings:
    def stop_list(key: str, current: tuple[str, ...]) -> tuple[str, ...]:
        if key not in payload:
            return current
        return tuple(_parse_transit_stops(payload.get(key)))

    return TransitSettings(
        outbound_origins=stop_list("outbound_origins", source.outbound_origins),
        outbound_destinations=stop_list("outbound_destinations", source.outbound_destinations),
        return_origins=stop_list("return_origins", source.return_origins),
        return_destinations=stop_list("return_destinations", source.return_destinations),
        arrive_min_before=max(0, _optional_int(payload.get("arrive_min_before"), source.arrive_min_before) or 0),
        arrive_window_minutes=max(1, _optional_int(payload.get("arrive_window_minutes"), source.arrive_window_minutes) or 60),
        depart_min_after=max(0, _optional_int(payload.get("depart_min_after"), source.depart_min_after) or 0),
        depart_window_minutes=max(1, _optional_int(payload.get("depart_window_minutes"), source.depart_window_minutes) or 90),
        day_start=_normalize_time_input(payload.get("day_start") or source.day_start),
        day_end=_normalize_time_input(payload.get("day_end") or source.day_end),
        direct_connections_only=(
            bool(payload.get("direct_connections_only"))
            if "direct_connections_only" in payload
            else source.direct_connections_only
        ),
    )


def _public_transit_settings(settings: TransitSettings) -> dict[str, Any]:
    return {
        "outbound_origins": list(settings.outbound_origins),
        "outbound_destinations": list(settings.outbound_destinations),
        "return_origins": list(settings.return_origins),
        "return_destinations": list(settings.return_destinations),
        "outbound_origin_names": [_transit_stop_label(value) for value in settings.outbound_origins],
        "outbound_destination_names": [_transit_stop_label(value) for value in settings.outbound_destinations],
        "return_origin_names": [_transit_stop_label(value) for value in settings.return_origins],
        "return_destination_names": [_transit_stop_label(value) for value in settings.return_destinations],
        "arrive_min_before": settings.arrive_min_before,
        "arrive_window_minutes": settings.arrive_window_minutes,
        "depart_min_after": settings.depart_min_after,
        "depart_window_minutes": settings.depart_window_minutes,
        "day_start": settings.day_start,
        "day_end": settings.day_end,
        "direct_connections_only": settings.direct_connections_only,
        "enabled": settings.enabled,
    }


def _exam_label(item: dict[str, Any]) -> str:
    start = _format_exam_datetime(str(item.get("start") or ""))
    title = str(item.get("title") or "Klassenarbeit").strip()
    group = str(item.get("group") or "").strip()
    if group:
        return f"{start}: {title} ({group})"
    return f"{start}: {title}"


def _format_exam_datetime(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    return parsed.strftime("%d.%m.%Y, %H:%M")


def _exam_not_past(item: dict[str, Any], now: datetime) -> bool:
    value = str(item.get("end") or item.get("start") or "")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return True
    if parsed.tzinfo is None and now.tzinfo is not None:
        parsed = parsed.replace(tzinfo=now.tzinfo)
    return parsed.date() >= now.date()


def _parse_transit_stops(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value:
        return []
    normalized = str(value).replace(";", "\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def _transit_stop_label(value: str) -> str:
    return str(value or "").split("|", 1)[0].strip()


def _new_identifier(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(9).replace('-', '').replace('_', '')}"


def _optional_int(value: Any, default: int | None) -> int | None:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _initial(value: Any) -> str:
    text = str(value or "").strip().replace(".", "")
    return text[:1].upper()

from __future__ import annotations

import csv
import hashlib
import io
import json
import threading
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from .config import GeofoxConfig, GtfsConfig, TransitSettings
from .geofox import GeofoxClient, GeofoxError


REQUIRED_FILES = {
    "agency.txt",
    "feed_info.txt",
    "stops.txt",
    "routes.txt",
    "calendar.txt",
    "calendar_dates.txt",
    "trips.txt",
    "stop_times.txt",
}


@dataclass(frozen=True)
class StopMatch:
    id: str
    name: str


class TransitDataPreparing(Exception):
    pass


class TransitPlanner:
    def __init__(
        self,
        config: GtfsConfig,
        geofox_config: GeofoxConfig | None = None,
        geofox_client: GeofoxClient | None = None,
    ) -> None:
        self.config = config
        self.geofox_config = geofox_config
        self.geofox = geofox_client or (
            GeofoxClient(geofox_config) if geofox_config and geofox_config.enabled else None
        )
        self.feed_path = config.cache_dir / "latest.zip"
        self.meta_path = config.cache_dir / "meta.json"
        self._download_lock = threading.Lock()
        self._download_thread: threading.Thread | None = None
        self._stops_lock = threading.Lock()
        self._stops_cache_mtime: float | None = None
        self._stops_cache: list[dict[str, Any]] | None = None
        self._stops_by_id_cache: dict[str, dict[str, Any]] | None = None

    def day_plan(
        self,
        settings: TransitSettings,
        lessons: list[dict[str, Any]],
        target_date: date,
        force_refresh: bool = False,
        include_full_day: bool = False,
    ) -> dict[str, Any]:
        if self.geofox and self.geofox_config and self.geofox_config.mode in {"auto", "geofox"}:
            try:
                return self.geofox.day_plan(
                    settings,
                    lessons,
                    target_date,
                    include_full_day=include_full_day,
                )
            except GeofoxError as exc:
                if self.geofox_config.mode == "geofox":
                    return _empty_plan(
                        target_date,
                        _public_settings(settings),
                        {
                            "status": "error",
                            "provider": "geofox",
                            "mode": "geofox",
                            "error": str(exc),
                        },
                        "Geofox-Live-Daten konnten nicht geladen werden.",
                        full_day=include_full_day,
                    )
                fallback = self._gtfs_day_plan(settings, lessons, target_date, force_refresh)
                fallback["feed"] = {
                    **fallback.get("feed", {}),
                    "provider": "gtfs",
                    "mode": "auto",
                    "fallback": True,
                    "geofox_error": str(exc),
                }
                fallback["warnings"] = [
                    "Live-Daten sind momentan nicht erreichbar. Es wird der Soll-Fahrplan angezeigt.",
                    *fallback.get("warnings", []),
                ]
                return fallback
        return self._gtfs_day_plan(settings, lessons, target_date, force_refresh)

    def _gtfs_day_plan(
        self,
        settings: TransitSettings,
        lessons: list[dict[str, Any]],
        target_date: date,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        public_settings = _public_settings(settings)
        if not settings.enabled:
            return _empty_plan(
                target_date,
                public_settings,
                {"status": "not_configured", "feed_url": self.config.feed_url},
                "Bus-Haltestellen sind noch nicht vollständig konfiguriert.",
                full_day=True,
            )

        feed = self.ensure_feed(force_refresh=force_refresh)

        if feed.get("status") in {"missing", "downloading"}:
            return _empty_plan(
                target_date,
                public_settings,
                feed,
                "GTFS-Fahrplandaten werden vorbereitet. Bitte gleich erneut aktualisieren.",
                full_day=True,
            )

        try:
            dataset = _GtfsDataset(
                self.feed_path,
                build_indexes_synchronously=not bool(self.config.feed_url),
            )
            outbound, inbound = dataset.connections_for_settings(settings, target_date)
        except TransitDataPreparing as exc:
            return _empty_plan(target_date, public_settings, {**feed, "status": "preparing"}, str(exc), full_day=True)
        except Exception as exc:
            return _empty_plan(target_date, public_settings, {**feed, "error": str(exc)}, "GTFS-Fahrplandaten konnten nicht ausgewertet werden.", full_day=True)

        day_lessons = [
            lesson for lesson in lessons
            if str(lesson.get("date") or "") == target_date.isoformat()
            and str(lesson.get("status") or "") != "cancelled"
        ]
        first_start = min((str(lesson.get("start") or "") for lesson in day_lessons if lesson.get("start")), default="")
        last_end = max((str(lesson.get("end") or "") for lesson in day_lessons if lesson.get("end")), default="")
        recommendation = {
            "outbound": _pick_outbound(outbound, first_start, settings),
            "return": _pick_return(inbound, last_end, settings),
        }
        warnings = []
        if not outbound:
            warnings.append("Keine Hinfahrt im konfigurierten Tagesfenster gefunden.")
        if not inbound:
            warnings.append("Keine Rückfahrt im konfigurierten Tagesfenster gefunden.")
        if first_start and not recommendation["outbound"]:
            warnings.append("Keine Hinfahrt passt zum Unterrichtsbeginn.")
        if last_end and not recommendation["return"]:
            warnings.append("Keine Rückfahrt passt zum Unterrichtsende.")

        return {
            "date": target_date.isoformat(),
            "settings": public_settings,
            "feed": feed,
            "day": {
                "first_lesson_start": first_start,
                "last_lesson_end": last_end,
                "has_lessons": bool(day_lessons),
            },
            "recommendation": recommendation,
            "outbound": outbound,
            "return": inbound,
            "full_day": True,
            "warnings": warnings,
        }

    def ensure_feed(self, force_refresh: bool = False) -> dict[str, Any]:
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        meta = _read_json(self.meta_path)
        should_download = force_refresh or not self.feed_path.exists() or _cache_stale(
            meta.get("downloaded_at"),
            self.config.cache_minutes,
        )
        if should_download and self.config.feed_url:
            self._start_download()

        if not self.feed_path.exists():
            return {
                "status": "downloading" if self._download_running() else "missing",
                "feed_url": self.config.feed_url,
                "downloaded_at": meta.get("downloaded_at", ""),
                "error": meta.get("error", ""),
            }

        return {
            "status": "ready" if not meta.get("error") else "stale",
            "feed_url": self.config.feed_url,
            "downloaded_at": meta.get("downloaded_at", ""),
            "last_attempt_at": meta.get("last_attempt_at", ""),
            "error": meta.get("error", ""),
            "info": meta.get("feed", {}),
        }

    def feed_cache_key(self) -> str:
        feed = self.ensure_feed()
        mtime = self.feed_path.stat().st_mtime if self.feed_path.exists() else 0
        return json.dumps(
            {
                "status": feed.get("status", ""),
                "downloaded_at": feed.get("downloaded_at", ""),
                "error": feed.get("error", ""),
                "mtime": mtime,
            },
            sort_keys=True,
        )

    def cache_key(self) -> str:
        if self.geofox and self.geofox_config and self.geofox_config.mode in {"auto", "geofox"}:
            bucket = int(datetime.now().timestamp()) // self.geofox_config.cache_seconds
            return json.dumps(
                {"provider": "geofox", "mode": self.geofox_config.mode, "bucket": bucket},
                sort_keys=True,
            )
        return self.feed_cache_key()

    def stop_suggestions(self, query: str, limit: int = 8) -> dict[str, Any]:
        if self.geofox and self.geofox_config and self.geofox_config.mode in {"auto", "geofox"}:
            try:
                return self.geofox.stop_suggestions(query, limit=limit)
            except GeofoxError:
                if self.geofox_config.mode == "geofox":
                    return {"feed": {"status": "error", "provider": "geofox"}, "items": []}
        feed = self.ensure_feed()
        if feed.get("status") in {"missing", "downloading"}:
            return {"feed": feed, "items": []}
        stops, _stops_by_id = self._stops()
        return {"feed": feed, "items": _stop_suggestions(stops, query, limit)}

    def validate_stops(self, settings: TransitSettings) -> dict[str, Any]:
        if self.geofox and self.geofox_config and self.geofox_config.mode in {"auto", "geofox"}:
            try:
                return self.geofox.validate_stops(settings)
            except GeofoxError:
                if self.geofox_config.mode == "geofox":
                    return {
                        "feed": {"status": "error", "provider": "geofox"},
                        "groups": {},
                        "ready": False,
                    }
        feed = self.ensure_feed()
        if feed.get("status") in {"missing", "downloading"}:
            return {"feed": feed, "groups": {}, "ready": False}
        _stops, stops = self._stops()
        groups = {
            "outbound_origins": _validate_stop_values(stops, settings.outbound_origins),
            "outbound_destinations": _validate_stop_values(stops, settings.outbound_destinations),
            "return_origins": _validate_stop_values(stops, settings.return_origins),
            "return_destinations": _validate_stop_values(stops, settings.return_destinations),
        }
        ready = all(bool(items) and all(item["status"] == "valid" for item in items) for items in groups.values())
        return {"feed": feed, "groups": groups, "ready": ready}

    def _stops(self) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        mtime = self.feed_path.stat().st_mtime
        with self._stops_lock:
            if (
                self._stops_cache is not None
                and self._stops_by_id_cache is not None
                and self._stops_cache_mtime == mtime
            ):
                return self._stops_cache, self._stops_by_id_cache

            with zipfile.ZipFile(self.feed_path) as archive:
                stops = [row for row in _read_csv(archive, "stops.txt")]
            stops_by_id = {str(row.get("stop_id") or ""): row for row in stops if row.get("stop_id")}
            self._stops_cache = stops
            self._stops_by_id_cache = stops_by_id
            self._stops_cache_mtime = mtime
            return stops, stops_by_id

    def _start_download(self) -> None:
        with self._download_lock:
            if self._download_thread and self._download_thread.is_alive():
                return
            self._download_thread = threading.Thread(
                target=self._download_feed_safely,
                name="stundenplaninfo-gtfs-download",
                daemon=True,
            )
            self._download_thread.start()

    def _download_running(self) -> bool:
        return bool(self._download_thread and self._download_thread.is_alive())

    def _download_feed_safely(self) -> None:
        meta = _read_json(self.meta_path)
        try:
            self._download_feed()
            meta = {
                "downloaded_at": datetime.now().astimezone().isoformat(),
                "feed_url": self.config.feed_url,
                "feed": self._feed_info(),
                "error": "",
            }
        except Exception as exc:
            meta = {
                **meta,
                "error": str(exc),
                "last_attempt_at": datetime.now().astimezone().isoformat(),
            }
        self.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def _download_feed(self) -> None:
        temp_path = self.feed_path.with_suffix(".download")
        with requests.get(self.config.feed_url, stream=True, timeout=(10, self.config.timeout_seconds)) as response:
            response.raise_for_status()
            with temp_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        with zipfile.ZipFile(temp_path) as archive:
            names = set(archive.namelist())
            missing = sorted(REQUIRED_FILES - names)
            if missing:
                raise ValueError(f"GTFS-Feed unvollständig: {', '.join(missing)}")
        temp_path.replace(self.feed_path)

    def _feed_info(self) -> dict[str, Any]:
        try:
            with zipfile.ZipFile(self.feed_path) as archive:
                rows = list(_read_csv(archive, "feed_info.txt"))
                return rows[0] if rows else {}
        except Exception:
            return {}


class _GtfsDataset:
    def __init__(self, feed_path: Path, build_indexes_synchronously: bool = False) -> None:
        self.feed_path = feed_path
        self._index_dir = feed_path.parent / "indexes"
        self.build_indexes_synchronously = build_indexes_synchronously

    def connections_for_settings(
        self,
        settings: TransitSettings,
        target_date: date,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        with zipfile.ZipFile(self.feed_path) as archive:
            stops = {row["stop_id"]: row for row in _read_csv(archive, "stops.txt")}
            outbound_origin_ids = _match_stop_ids(stops, settings.outbound_origins)
            outbound_destination_ids = _match_stop_ids(stops, settings.outbound_destinations)
            return_origin_ids = _match_stop_ids(stops, settings.return_origins)
            return_destination_ids = _match_stop_ids(stops, settings.return_destinations)
            if not (
                outbound_origin_ids
                and outbound_destination_ids
                and return_origin_ids
                and return_destination_ids
            ):
                return [], []

            active_services = _active_service_ids(archive, target_date)
            trips = {
                row["trip_id"]: row
                for row in _read_csv(archive, "trips.txt")
                if str(row.get("service_id") or "") in active_services
            }
            route_ids = {str(row.get("route_id") or "") for row in trips.values()}
            routes = {
                row["route_id"]: row
                for row in _read_csv(archive, "routes.txt")
                if row.get("route_id") in route_ids
            }
            interesting_stop_ids = (
                set(outbound_origin_ids)
                | set(outbound_destination_ids)
                | set(return_origin_ids)
                | set(return_destination_ids)
            )
            rows = self._indexed_stop_times(archive, interesting_stop_ids)
            times_by_trip: dict[str, list[dict[str, Any]]] = {}
            for row in rows:
                trip_id = row.get("trip_id") or ""
                if trip_id in trips:
                    times_by_trip.setdefault(trip_id, []).append(row)

        outbound = _connections_from_times(
            times_by_trip,
            trips,
            routes,
            stops,
            outbound_origin_ids,
            outbound_destination_ids,
            settings.day_start,
            settings.day_end,
        )
        inbound = _connections_from_times(
            times_by_trip,
            trips,
            routes,
            stops,
            return_origin_ids,
            return_destination_ids,
            settings.day_start,
            settings.day_end,
        )
        return outbound, inbound

    def _indexed_stop_times(
        self,
        archive: zipfile.ZipFile,
        stop_ids: set[str],
    ) -> list[dict[str, Any]]:
        index_path = self._stop_index_path(stop_ids)
        payload = _read_json(index_path)
        if isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]

        if self.build_indexes_synchronously:
            return self._build_stop_index(archive, stop_ids, index_path)

        lock_path = index_path.with_suffix(".lock")
        if _try_create_lock(lock_path):
            thread = threading.Thread(
                target=self._build_stop_index_safely,
                args=(stop_ids, index_path, lock_path),
                name="stundenplaninfo-gtfs-index",
                daemon=True,
            )
            thread.start()
        raise TransitDataPreparing("Fahrplan-Index wird vorbereitet. Bitte gleich erneut aktualisieren.")

    def _build_stop_index_safely(self, stop_ids: set[str], index_path: Path, lock_path: Path) -> None:
        try:
            with zipfile.ZipFile(self.feed_path) as archive:
                self._build_stop_index(archive, stop_ids, index_path)
        finally:
            try:
                lock_path.unlink()
            except OSError:
                pass

    def _build_stop_index(
        self,
        archive: zipfile.ZipFile,
        stop_ids: set[str],
        index_path: Path,
    ) -> list[dict[str, Any]]:
        items = [
            row for row in _read_csv(archive, "stop_times.txt")
            if row.get("stop_id") in stop_ids
        ]
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            json.dumps({"items": items}, ensure_ascii=False),
            encoding="utf-8",
        )
        return items

    def _stop_index_path(self, stop_ids: set[str]) -> Path:
        try:
            stat = self.feed_path.stat()
            feed_signature = f"{stat.st_size}:{stat.st_mtime_ns}"
        except OSError:
            feed_signature = "missing"
        digest = hashlib.sha256(
            f"{feed_signature}:{'|'.join(sorted(stop_ids))}".encode("utf-8")
        ).hexdigest()[:18]
        return self._index_dir / f"stop_times_{digest}.json"


def _connections_from_times(
    times_by_trip: dict[str, list[dict[str, Any]]],
    trips: dict[str, dict[str, Any]],
    routes: dict[str, dict[str, Any]],
    stops: dict[str, dict[str, Any]],
    origin_ids: set[str],
    destination_ids: set[str],
    start: str,
    end: str,
) -> list[dict[str, Any]]:
    start_minutes = _minutes(start)
    end_minutes = _minutes(end)
    items: list[dict[str, Any]] = []
    for trip_id, times in times_by_trip.items():
        origins = [row for row in times if row.get("stop_id") in origin_ids]
        destinations = [row for row in times if row.get("stop_id") in destination_ids]
        for origin in origins:
            for destination in destinations:
                if _int(destination.get("stop_sequence"), -1) <= _int(origin.get("stop_sequence"), -1):
                    continue
                depart = str(origin.get("departure_time") or origin.get("arrival_time") or "")
                arrive = str(destination.get("arrival_time") or destination.get("departure_time") or "")
                depart_minutes = _minutes(depart)
                arrive_minutes = _minutes(arrive)
                if depart_minutes < start_minutes or depart_minutes > end_minutes:
                    continue
                trip = trips[trip_id]
                route = routes.get(str(trip.get("route_id") or ""), {})
                items.append(
                    {
                        "trip_id": trip_id,
                        "route_id": trip.get("route_id", ""),
                        "line": route.get("route_short_name") or route.get("route_long_name") or "",
                        "headsign": trip.get("trip_headsign") or destination.get("stop_headsign") or "",
                        "departure": _clock(depart),
                        "arrival": _clock(arrive),
                        "departure_minutes": depart_minutes,
                        "arrival_minutes": arrive_minutes,
                        "duration_minutes": max(0, arrive_minutes - depart_minutes),
                        "from": _public_stop(stops.get(str(origin.get("stop_id") or ""), {})),
                        "to": _public_stop(stops.get(str(destination.get("stop_id") or ""), {})),
                        "realtime": False,
                    }
                )
    return sorted(
        _dedupe_connections(items),
        key=lambda item: (
            item["departure_minutes"],
            item["arrival_minutes"],
            item["line"],
            item["from"]["name"],
            item["to"]["name"],
        ),
    )


def _read_csv(archive: zipfile.ZipFile, name: str):
    with archive.open(name) as handle:
        yield from csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig", errors="replace", newline=""))


def _match_stop_ids(stops: dict[str, dict[str, Any]], names: tuple[str, ...]) -> set[str]:
    direct_ids = {
        stop_id for value in names
        for stop_id in [_stop_value_id(value)]
        if stop_id and stop_id in stops
    }
    wanted = {_stop_value_name(name).casefold().strip() for name in names if _stop_value_name(name).strip()}
    ids = {
        stop_id for stop_id, stop in stops.items()
        if str(stop.get("stop_name") or "").casefold().strip() in wanted
    }
    ids.update(direct_ids)
    parent_ids = {str(stop.get("parent_station") or "") for stop in stops.values() if stop.get("stop_id") in ids}
    ids.update(parent_id for parent_id in parent_ids if parent_id)
    ids.update(
        stop_id for stop_id, stop in stops.items()
        if str(stop.get("parent_station") or "") in ids
    )
    return ids


def _stop_value_name(value: str) -> str:
    return str(value or "").split("|", 1)[0].strip()


def _stop_value_id(value: str) -> str:
    parts = str(value or "").split("|", 1)
    return parts[1].strip() if len(parts) == 2 else ""


def _stop_value(name: str, stop_id: str) -> str:
    return f"{name.strip()}|{stop_id.strip()}"


def _validate_stop_values(stops: dict[str, dict[str, Any]], values: tuple[str, ...]) -> list[dict[str, str]]:
    name_index: dict[str, list[dict[str, Any]]] = {}
    for stop in stops.values():
        name = str(stop.get("stop_name") or "").strip()
        if name:
            name_index.setdefault(name.casefold(), []).append(stop)

    items = []
    for value in values:
        raw = str(value or "").strip()
        name = _stop_value_name(raw)
        stop_id = _stop_value_id(raw)
        if stop_id and stop_id in stops:
            stop = stops[stop_id]
            found_name = str(stop.get("stop_name") or name)
            items.append({
                "input": raw,
                "name": found_name,
                "id": stop_id,
                "value": _stop_value(found_name, stop_id),
                "status": "valid",
            })
            continue
        matches = name_index.get(name.casefold(), []) if name else []
        if len(matches) == 1:
            stop = matches[0]
            found_id = str(stop.get("stop_id") or "")
            found_name = str(stop.get("stop_name") or name)
            items.append({
                "input": raw,
                "name": found_name,
                "id": found_id,
                "value": _stop_value(found_name, found_id),
                "status": "valid",
            })
        elif len(matches) > 1 and (parent := _preferred_parent_stop(matches)):
            found_id = str(parent.get("stop_id") or "")
            found_name = str(parent.get("stop_name") or name)
            items.append({
                "input": raw,
                "name": found_name,
                "id": found_id,
                "value": _stop_value(found_name, found_id),
                "status": "valid",
            })
        elif len(matches) > 1:
            items.append({"input": raw, "name": name, "id": "", "value": raw, "status": "ambiguous"})
        else:
            items.append({"input": raw, "name": name, "id": "", "value": raw, "status": "missing"})
    return items


def _stop_suggestions(stops: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, str]]:
    normalized_query = " ".join(str(query or "").casefold().split())
    if len(normalized_query) < 2:
        return []
    scored = []
    for stop in _suggestion_stops(stops):
        stop_id = str(stop.get("stop_id") or "").strip()
        name = str(stop.get("stop_name") or "").strip()
        if not stop_id or not name:
            continue
        haystack = " ".join(name.casefold().split())
        if haystack == normalized_query:
            score = 0
        elif haystack.startswith(normalized_query):
            score = 1
        elif normalized_query in haystack:
            score = 2
        elif all(token in haystack for token in normalized_query.split()):
            score = 3
        else:
            continue
        scored.append((score, name, stop_id))
    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    return [
        {"id": stop_id, "name": name, "value": _stop_value(name, stop_id), "detail": f"Stop-ID {stop_id}"}
        for _, name, stop_id in scored[:max(1, min(limit, 20))]
    ]


def _suggestion_stops(stops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for stop in stops:
        name = str(stop.get("stop_name") or "").strip()
        if name:
            groups.setdefault(name.casefold(), []).append(stop)

    suggestions = []
    for matches in groups.values():
        parent = _preferred_parent_stop(matches)
        if parent:
            suggestions.append(parent)
        else:
            suggestions.extend(matches)
    return suggestions


def _preferred_parent_stop(stops: list[dict[str, Any]]) -> dict[str, Any] | None:
    parent_stops = [
        stop for stop in stops
        if str(stop.get("location_type") or "").strip() == "1"
    ]
    if len(parent_stops) == 1:
        return parent_stops[0]
    return None


def _active_service_ids(archive: zipfile.ZipFile, target_date: date) -> set[str]:
    active = set()
    weekday_key = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][target_date.weekday()]
    ymd = target_date.strftime("%Y%m%d")
    for row in _read_csv(archive, "calendar.txt"):
        if str(row.get("start_date") or "") <= ymd <= str(row.get("end_date") or ""):
            service_id = str(row.get("service_id") or "")
            if service_id and str(row.get(weekday_key) or "") == "1":
                active.add(service_id)
    for row in _read_csv(archive, "calendar_dates.txt"):
        if str(row.get("date") or "") != ymd:
            continue
        service_id = str(row.get("service_id") or "")
        exception_type = str(row.get("exception_type") or "")
        if service_id and exception_type == "1":
            active.add(service_id)
        elif service_id and exception_type == "2":
            active.discard(service_id)
    return active


def _pick_outbound(items: list[dict[str, Any]], first_start: str, settings: TransitSettings) -> dict[str, Any] | None:
    if not first_start:
        return None
    target = _minutes(first_start)
    earliest = target - settings.arrive_window_minutes
    latest = target - settings.arrive_min_before
    candidates = [
        item for item in items
        if earliest <= item["arrival_minutes"] <= latest
    ]
    return max(candidates, key=lambda item: (item["arrival_minutes"], -item["departure_minutes"])) if candidates else None


def _pick_return(items: list[dict[str, Any]], last_end: str, settings: TransitSettings) -> dict[str, Any] | None:
    if not last_end:
        return None
    target = _minutes(last_end)
    earliest = target + settings.depart_min_after
    latest = target + settings.depart_window_minutes
    candidates = [
        item for item in items
        if earliest <= item["departure_minutes"] <= latest
    ]
    return min(candidates, key=lambda item: (item["departure_minutes"], item["arrival_minutes"])) if candidates else None


def _dedupe_connections(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for item in items:
        key = (
            item["trip_id"],
            item["from"]["id"],
            item["to"]["id"],
            item["departure"],
            item["arrival"],
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _empty_plan(
    date_value: date,
    settings: dict[str, Any],
    feed: dict[str, Any],
    warning: str,
    *,
    full_day: bool = False,
) -> dict[str, Any]:
    return {
        "date": date_value.isoformat(),
        "settings": settings,
        "feed": feed,
        "day": {"first_lesson_start": "", "last_lesson_end": "", "has_lessons": False},
        "recommendation": {"outbound": None, "return": None},
        "outbound": [],
        "return": [],
        "full_day": full_day,
        "warnings": [warning],
    }


def _public_settings(settings: TransitSettings) -> dict[str, Any]:
    def names(values: tuple[str, ...]) -> list[str]:
        return [_stop_value_name(value) for value in values]

    return {
        "outbound_origins": names(settings.outbound_origins),
        "outbound_destinations": names(settings.outbound_destinations),
        "return_origins": names(settings.return_origins),
        "return_destinations": names(settings.return_destinations),
        "arrive_min_before": settings.arrive_min_before,
        "arrive_window_minutes": settings.arrive_window_minutes,
        "depart_min_after": settings.depart_min_after,
        "depart_window_minutes": settings.depart_window_minutes,
        "day_start": settings.day_start,
        "day_end": settings.day_end,
        "direct_connections_only": settings.direct_connections_only,
        "enabled": settings.enabled,
    }


def _public_stop(stop: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(stop.get("stop_id") or ""),
        "name": str(stop.get("stop_name") or ""),
    }


def _cache_stale(downloaded_at: Any, cache_minutes: int) -> bool:
    try:
        downloaded = datetime.fromisoformat(str(downloaded_at).replace("Z", "+00:00"))
    except ValueError:
        return True
    return datetime.now(downloaded.tzinfo) - downloaded > timedelta(minutes=cache_minutes)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _try_create_lock(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(datetime.now().astimezone().isoformat())
        return True
    except FileExistsError:
        return False


def _minutes(value: str) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    parts = text.split(":")
    if len(parts) < 2:
        return 0
    return int(parts[0]) * 60 + int(parts[1])


def _clock(value: str) -> str:
    minutes = _minutes(value)
    hours = (minutes // 60) % 24
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

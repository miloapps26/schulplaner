from __future__ import annotations

import base64
import hashlib
import hmac
import json
import threading
import time
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Callable

import requests

from .config import GeofoxConfig, TransitSettings


class GeofoxError(RuntimeError):
    pass


class GeofoxClient:
    def __init__(
        self,
        config: GeofoxConfig,
        *,
        session: requests.Session | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        self._monotonic = monotonic
        self._sleep = sleep
        self._request_lock = threading.Lock()
        self._last_request_at = 0.0
        self._stop_cache: dict[str, dict[str, Any]] = {}
        self._suggestion_cache: dict[tuple[str, int], dict[str, Any]] = {}
        self._announcements_cache: dict[tuple[str, ...], tuple[float, list[dict[str, Any]]]] = {}

    def request(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.config.enabled:
            raise GeofoxError("Geofox ist nicht konfiguriert.")
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        signature = base64.b64encode(
            hmac.new(
                self.config.password.encode("utf-8"),
                body,
                hashlib.sha1,
            ).digest()
        ).decode("ascii")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
            "geofox-auth-type": "HmacSHA1",
            "geofox-auth-user": self.config.username,
            "geofox-auth-signature": signature,
            "X-Platform": "web",
            "X-TraceId": str(uuid.uuid4()),
        }
        with self._request_lock:
            remaining = self.config.min_interval_seconds - (
                self._monotonic() - self._last_request_at
            )
            if remaining > 0:
                self._sleep(remaining)
            self._last_request_at = self._monotonic()
            try:
                response = self.session.post(
                    f"{self.config.base_url.rstrip('/')}/gti/public/{method}",
                    data=body,
                    headers=headers,
                    timeout=self.config.timeout_seconds,
                )
            except requests.RequestException as exc:
                raise GeofoxError(f"Geofox ist nicht erreichbar: {exc}") from exc
        try:
            data = response.json()
        except ValueError as exc:
            raise GeofoxError(
                f"Geofox lieferte keine JSON-Antwort (HTTP {response.status_code})."
            ) from exc
        if response.status_code >= 400:
            raise GeofoxError(f"Geofox HTTP-Fehler {response.status_code}.")
        if data.get("returnCode") != "OK":
            detail = str(data.get("errorText") or data.get("errorDevInfo") or "Unbekannter Fehler")
            raise GeofoxError(f"Geofox {data.get('returnCode') or 'Fehler'}: {detail}")
        return data

    def stop_suggestions(self, query: str, limit: int = 8) -> dict[str, Any]:
        text = " ".join(str(query or "").split())
        if len(text) < 2:
            return {"feed": self._feed(), "items": []}
        cache_key = (text.casefold(), max(1, min(limit, 20)))
        if cache_key in self._suggestion_cache:
            return self._suggestion_cache[cache_key]
        data = self.request(
            "checkName",
            {
                "version": self.config.api_version,
                "language": "de",
                "theName": {"name": text, "type": "STATION"},
                "maxList": max(1, min(limit, 20)),
                "coordinateType": "EPSG_4326",
            },
        )
        items = []
        for result in data.get("results") or []:
            item = _public_stop(result)
            if not item["id"] or not item["name"]:
                continue
            self._stop_cache[item["name"].casefold()] = dict(result)
            items.append(
                {
                    **item,
                    "value": f"{item['name']}|{item['id']}",
                    "detail": f"Geofox-ID {item['id']}",
                }
            )
        result = {"feed": self._feed(), "items": items}
        self._suggestion_cache[cache_key] = result
        return result

    def validate_stops(self, settings: TransitSettings) -> dict[str, Any]:
        groups = {
            key: [self._validated_stop(value) for value in values]
            for key, values in {
                "outbound_origins": settings.outbound_origins,
                "outbound_destinations": settings.outbound_destinations,
                "return_origins": settings.return_origins,
                "return_destinations": settings.return_destinations,
            }.items()
        }
        ready = all(
            bool(items) and all(item["status"] == "valid" for item in items)
            for items in groups.values()
        )
        return {"feed": self._feed(), "groups": groups, "ready": ready}

    def day_plan(
        self,
        settings: TransitSettings,
        lessons: list[dict[str, Any]],
        target_date: date,
        *,
        include_full_day: bool = True,
    ) -> dict[str, Any]:
        day_lessons = [
            lesson
            for lesson in lessons
            if str(lesson.get("date") or "") == target_date.isoformat()
            and str(lesson.get("status") or "") != "cancelled"
        ]
        first_start = min(
            (str(lesson.get("start") or "") for lesson in day_lessons if lesson.get("start")),
            default="",
        )
        last_end = max(
            (str(lesson.get("end") or "") for lesson in day_lessons if lesson.get("end")),
            default="",
        )
        if include_full_day:
            outbound = self._routes(
                settings.outbound_origins,
                settings.outbound_destinations,
                target_date,
                settings.day_start,
                window_start=settings.day_start,
                window_end=settings.day_end,
                time_is_departure=True,
            ) if first_start else []
            inbound = self._routes(
                settings.return_origins,
                settings.return_destinations,
                target_date,
                settings.day_start,
                window_start=settings.day_start,
                window_end=settings.day_end,
                time_is_departure=True,
            ) if last_end else []
        else:
            earliest_arrival = _shift_clock(first_start, -settings.arrive_window_minutes)
            latest_arrival = _shift_clock(first_start, -settings.arrive_min_before)
            outbound = self._routes(
                settings.outbound_origins,
                settings.outbound_destinations,
                target_date,
                latest_arrival,
                window_start=earliest_arrival,
                window_end=latest_arrival,
                time_is_departure=False,
                max_pages=1,
            ) if first_start else []
            earliest_return = _shift_clock(last_end, settings.depart_min_after)
            latest_return = _shift_clock(last_end, settings.depart_window_minutes)
            return_query_start = _shift_clock(earliest_return, -1)
            inbound = self._routes(
                settings.return_origins,
                settings.return_destinations,
                target_date,
                return_query_start,
                window_start=earliest_return,
                window_end=latest_return,
                time_is_departure=True,
                max_pages=1,
            ) if last_end else []
            outbound = _routes_allowed_by_settings(outbound, settings)
            inbound = _routes_allowed_by_settings(inbound, settings)
            if first_start and not _pick_outbound(outbound, first_start, settings):
                outbound = _routes_allowed_by_settings(_dedupe_routes([
                    *outbound,
                    *self._routes(
                        settings.outbound_origins,
                        settings.outbound_destinations,
                        target_date,
                        latest_arrival,
                        window_start=earliest_arrival,
                        window_end=latest_arrival,
                        time_is_departure=False,
                    ),
                ]), settings)
            if last_end and not _pick_return(inbound, last_end, settings):
                inbound = _routes_allowed_by_settings(_dedupe_routes([
                    *inbound,
                    *self._routes(
                        settings.return_origins,
                        settings.return_destinations,
                        target_date,
                        return_query_start,
                        window_start=earliest_return,
                        window_end=latest_return,
                        time_is_departure=True,
                    ),
                ]), settings)
        outbound = _routes_allowed_by_settings(outbound, settings)
        inbound = _routes_allowed_by_settings(inbound, settings)
        line_names = sorted(
            {
                leg["line"]
                for connection in [*outbound, *inbound]
                for leg in connection.get("legs") or []
                if leg.get("line") and leg.get("mode") not in {"CHANGE", "FOOTPATH"}
            }
        )
        if line_names:
            try:
                announcements = self._announcements(line_names)
            except GeofoxError:
                announcements = []
            for connection in [*outbound, *inbound]:
                connection_lines = {
                    leg["line"] for leg in connection.get("legs") or [] if leg.get("line")
                }
                matching = [
                    item
                    for item in announcements
                    if not item["affected_lines"]
                    or connection_lines.intersection(item["affected_lines"])
                ]
                connection["announcements"] = _dedupe_announcements(
                    [*connection.get("announcements", []), *matching]
                )
        outbound_recommendation = _pick_outbound(outbound, first_start, settings)
        return_recommendation = _pick_return(inbound, last_end, settings)
        if include_full_day and last_end and not return_recommendation:
            earliest_return = _shift_clock(last_end, settings.depart_min_after)
            latest_return = _shift_clock(last_end, settings.depart_window_minutes)
            targeted_return = self._routes(
                settings.return_origins,
                settings.return_destinations,
                target_date,
                earliest_return,
                window_start=earliest_return,
                window_end=latest_return,
                time_is_departure=True,
            )
            inbound = _routes_allowed_by_settings(
                _dedupe_routes([*inbound, *targeted_return]),
                settings,
            )
            return_recommendation = _pick_return(inbound, last_end, settings)
        recommendation = {
            "outbound": outbound_recommendation,
            "return": return_recommendation,
        }
        for connection in recommendation.values():
            if connection:
                try:
                    connection["vehicle"] = self.vehicle_status(connection, target_date)
                except GeofoxError:
                    connection["vehicle"] = {
                        "status": "error",
                        "message": "Fahrzeugposition momentan nicht erreichbar.",
                    }
        warnings: list[str] = []
        if first_start and not recommendation["outbound"]:
            warnings.append("Keine Live-Verbindung passt zum Unterrichtsbeginn.")
        if last_end and not recommendation["return"]:
            warnings.append("Keine Live-Verbindung passt zum Unterrichtsende.")
        if not day_lessons:
            warnings.append("Für diesen Tag liegt kein Unterricht vor.")
        live = any(item.get("realtime") for item in [*outbound, *inbound])
        return {
            "date": target_date.isoformat(),
            "settings": _public_settings(settings),
            "feed": self._feed(live=live),
            "day": {
                "first_lesson_start": first_start,
                "last_lesson_end": last_end,
                "has_lessons": bool(day_lessons),
            },
            "recommendation": recommendation,
            "outbound": outbound if include_full_day else [],
            "return": inbound if include_full_day else [],
            "full_day": include_full_day,
            "warnings": warnings,
        }

    def vehicle_status(
        self,
        connection: dict[str, Any],
        target_date: date,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now().astimezone()
        departure = _local_datetime(target_date, str(connection.get("departure") or ""))
        arrival = _local_datetime(target_date, str(connection.get("arrival") or ""))
        if not departure or not arrival:
            return {"status": "unavailable", "message": "Keine Fahrzeugzeit verfügbar."}
        if current < departure - timedelta(minutes=30):
            return {
                "status": "scheduled",
                "message": "Echte Fahrzeugposition wird kurz vor der Abfahrt geprüft.",
            }
        if current > arrival + timedelta(minutes=30):
            return {"status": "finished", "message": "Fahrt ist bereits beendet."}

        points = [
            stop.get("coordinate")
            for leg in connection.get("legs") or []
            for stop in (leg.get("from") or {}, leg.get("to") or {})
            if isinstance(stop.get("coordinate"), dict)
        ]
        coordinates = [
            (float(point["x"]), float(point["y"]))
            for point in points
            if point.get("x") is not None and point.get("y") is not None
        ]
        if not coordinates:
            return {
                "status": "unavailable",
                "message": "Für diese Fahrt fehlen Kartenkoordinaten.",
            }
        longitudes = [point[0] for point in coordinates]
        latitudes = [point[1] for point in coordinates]
        margin = 0.035
        line_names = {
            str(leg.get("line") or "")
            for leg in connection.get("legs") or []
            if leg.get("line") and leg.get("mode") not in {"CHANGE", "FOOTPATH"}
        }
        data = self.request(
            "getVehicleMap",
            {
                "version": self.config.api_version,
                "boundingBox": {
                    "lowerLeft": {
                        "x": min(longitudes) - margin,
                        "y": min(latitudes) - margin,
                        "type": "EPSG_4326",
                    },
                    "upperRight": {
                        "x": max(longitudes) + margin,
                        "y": max(latitudes) + margin,
                        "type": "EPSG_4326",
                    },
                },
                "periodBegin": int(departure.timestamp()) - 1800,
                "periodEnd": int(arrival.timestamp()) + 1800,
                "withoutCoords": True,
                "coordinateType": "EPSG_4326",
                "vehicleTypes": [
                    "REGIONALBUS",
                    "METROBUS",
                    "NACHTBUS",
                    "SCHNELLBUS",
                    "XPRESSBUS",
                ],
                "realtime": True,
            },
        )
        journeys = [
            journey
            for journey in data.get("journeys") or []
            if str((journey.get("line") or {}).get("name") or "") in line_names
        ]
        realtime_journeys = [journey for journey in journeys if journey.get("realtime") is True]
        if not realtime_journeys:
            return {
                "status": "unavailable",
                "message": "Geofox liefert für diese Fahrt keine echte Fahrzeugposition.",
            }

        now_epoch = int(current.timestamp())
        active: tuple[dict[str, Any], dict[str, Any], int, int] | None = None
        for journey in realtime_journeys:
            for segment in journey.get("segments") or []:
                delay_seconds = int(segment.get("realtimeDelay") or 0) * 60
                start_epoch = int(segment.get("startDateTime") or 0) + delay_seconds
                end_epoch = int(segment.get("endDateTime") or 0) + delay_seconds
                if start_epoch <= now_epoch <= end_epoch:
                    active = (journey, segment, start_epoch, end_epoch)
                    break
            if active:
                break
        if not active:
            return {
                "status": "unavailable",
                "message": "Noch keine aktuelle Position für diese Fahrt vorhanden.",
            }

        journey, segment, start_epoch, end_epoch = active
        track_data = self.request(
            "getTrackCoordinates",
            {
                "version": self.config.api_version,
                "coordinateType": "EPSG_4326",
                "stopPointKeys": [
                    str(segment.get("startStopPointKey") or ""),
                    str(segment.get("endStopPointKey") or ""),
                ],
            },
        )
        raw_track = ((track_data.get("tracks") or [{}])[0]).get("track") or []
        track = [
            [float(raw_track[index]), float(raw_track[index + 1])]
            for index in range(0, len(raw_track) - 1, 2)
        ]
        if len(track) < 2:
            return {
                "status": "unavailable",
                "message": "Für den aktuellen Abschnitt fehlen Kartenkoordinaten.",
            }
        progress = min(1.0, max(0.0, (now_epoch - start_epoch) / max(1, end_epoch - start_epoch)))
        position = _interpolate_track(track, progress)
        display_track = track[:: max(1, len(track) // 80)]
        if display_track[-1] != track[-1]:
            display_track.append(track[-1])
        return {
            "status": "available",
            "line": str((journey.get("line") or {}).get("name") or ""),
            "realtime": True,
            "from": str(segment.get("startStationName") or ""),
            "to": str(segment.get("endStationName") or ""),
            "delay_minutes": int(segment.get("realtimeDelay") or 0),
            "progress": round(progress, 4),
            "position": {"longitude": position[0], "latitude": position[1]},
            "track": display_track,
            "updated_at": current.isoformat(),
        }

    def _routes(
        self,
        origin_values: tuple[str, ...],
        destination_values: tuple[str, ...],
        target_date: date,
        clock: str,
        *,
        window_start: str,
        window_end: str,
        time_is_departure: bool,
        max_pages: int = 4,
    ) -> list[dict[str, Any]]:
        if not clock:
            return []
        window_start_minutes = _minutes(window_start)
        window_end_minutes = _minutes(window_end)
        current = datetime.now().astimezone()
        search_is_finished = (
            target_date < current.date()
            or (
                target_date == current.date()
                and window_end_minutes < current.hour * 60 + current.minute
            )
        )
        origins = [self._resolve_stop(value) for value in origin_values]
        destinations = [self._resolve_stop(value) for value in destination_values]
        routes: list[dict[str, Any]] = []
        errors: list[GeofoxError] = []
        for origin in origins:
            for destination in destinations:
                cursor = _minutes(clock)
                for _page in range(max(1, max_pages)):
                    payload = {
                        "version": self.config.api_version,
                        "language": "de",
                        "start": origin,
                        "dest": destination,
                        "time": {
                            "date": target_date.strftime("%d.%m.%Y"),
                            "time": _clock(cursor),
                        },
                        "timeIsDeparture": time_is_departure,
                        "tariffDetails": False,
                        "realtime": "PLANDATA" if search_is_finished else "AUTO",
                        "intermediateStops": True,
                        "useStationPosition": False,
                        "withPaths": False,
                        "coordinateType": "EPSG_4326",
                    }
                    payload[
                        "schedulesAfter" if time_is_departure else "schedulesBefore"
                    ] = 30
                    try:
                        data = self.request("getRoute", payload)
                    except GeofoxError as exc:
                        errors.append(exc)
                        break
                    selected = [
                        *(data.get("schedules") or []),
                        *(data.get("realtimeSchedules") or []),
                    ]
                    page_routes = _dedupe_routes([_connection(schedule) for schedule in selected])
                    if not page_routes:
                        break
                    routes.extend(page_routes)
                    time_key = "departure_minutes" if time_is_departure else "arrival_minutes"
                    date_key = "departure_date" if time_is_departure else "arrival_date"
                    page_minutes = [
                        item[time_key]
                        for item in page_routes
                        if item[time_key] > 0
                        and item[date_key] in {"", target_date.isoformat()}
                    ]
                    if not page_minutes:
                        break
                    edge_minute = max(page_minutes) if time_is_departure else min(page_minutes)
                    if (
                        time_is_departure and edge_minute >= window_end_minutes
                    ) or (
                        not time_is_departure and edge_minute <= window_start_minutes
                    ):
                        break
                    next_cursor = (
                        max(cursor + 1, edge_minute + 1)
                        if time_is_departure
                        else min(cursor - 1, edge_minute - 1)
                    )
                    if next_cursor == cursor:
                        break
                    cursor = next_cursor
        if not routes and errors:
            raise errors[0]
        time_key = "departure_minutes" if time_is_departure else "arrival_minutes"
        return _dedupe_routes(
            [
                item
                for item in routes
                if window_start_minutes <= item[time_key] <= window_end_minutes
                and item[
                    "departure_date" if time_is_departure else "arrival_date"
                ] in {"", target_date.isoformat()}
            ]
        )

    def _announcements(self, line_names: list[str]) -> list[dict[str, Any]]:
        cache_key = tuple(sorted(set(line_names)))
        cached = self._announcements_cache.get(cache_key)
        if cached and self._monotonic() - cached[0] < 300:
            return cached[1]
        data = self.request(
            "getAnnouncements",
            {
                "version": self.config.api_version,
                "language": "de",
                "names": line_names,
                "full": True,
                "filterPlanned": "NO_FILTER",
            },
        )
        items = []
        for raw in data.get("announcements") or []:
            item = _announcement(raw)
            item["affected_lines"] = sorted(
                {
                    str((location.get("line") or {}).get("name") or "")
                    for location in raw.get("locations") or []
                    if (location.get("line") or {}).get("name")
                }
            )
            items.append(item)
        self._announcements_cache[cache_key] = (self._monotonic(), items)
        return items

    def _validated_stop(self, value: str) -> dict[str, str]:
        try:
            stop = self._resolve_stop(value)
        except GeofoxError:
            name, _stop_id = _split_stop(value)
            return {"input": value, "name": name, "id": "", "value": value, "status": "missing"}
        item = _public_stop(stop)
        return {
            "input": value,
            "name": item["name"],
            "id": item["id"],
            "value": f"{item['name']}|{item['id']}",
            "status": "valid",
        }

    def _resolve_stop(self, value: str) -> dict[str, Any]:
        name, stop_id = _split_stop(value)
        if stop_id.startswith("Master:"):
            return {
                "id": stop_id,
                "name": name.split(",", 1)[-1].strip() or name,
                "city": name.split(",", 1)[0].strip() if "," in name else "",
                "combinedName": name,
                "type": "STATION",
            }
        cached = self._stop_cache.get(name.casefold())
        if cached:
            return cached
        result = self.stop_suggestions(name, limit=5).get("items") or []
        exact = next(
            (item for item in result if item.get("name", "").casefold() == name.casefold()),
            result[0] if len(result) == 1 else None,
        )
        if not exact:
            raise GeofoxError(f"Haltestelle nicht eindeutig gefunden: {name}")
        return self._resolve_stop(str(exact["value"]))

    def _feed(self, *, live: bool = False) -> dict[str, Any]:
        return {
            "status": "ready",
            "provider": "geofox",
            "mode": self.config.mode,
            "live": live,
            "requested_at": datetime.now().astimezone().isoformat(),
            "source_url": "https://www.hvv.de/",
        }


def _connection(schedule: dict[str, Any]) -> dict[str, Any]:
    legs = []
    for element in schedule.get("scheduleElements") or []:
        line = element.get("line") or {}
        start = element.get("from") or {}
        dest = element.get("to") or {}
        legs.append(
            {
                "line": str(line.get("name") or ""),
                "line_id": str(line.get("id") or ""),
                "mode": str((line.get("type") or {}).get("simpleType") or ""),
                "from": _public_stop(start),
                "to": _public_stop(dest),
                "departure": _gti_clock(start.get("depTime")),
                "arrival": _gti_clock(dest.get("arrTime")),
                "departure_delay_seconds": _optional_int(start.get("depDelay")),
                "arrival_delay_seconds": _optional_int(dest.get("arrDelay")),
                "cancelled": bool(element.get("cancelled") or start.get("cancelled") or dest.get("cancelled")),
                "extra": bool(element.get("extra")),
                "platform": str(start.get("platform") or ""),
                "realtime_platform": str(start.get("realtimePlatform") or ""),
                "announcements": [
                    _announcement(item) for item in (element.get("announcements") or [])
                ],
            }
        )
    transit_legs = [leg for leg in legs if leg["mode"] not in {"CHANGE", "FOOTPATH"}]
    display_legs = transit_legs or legs
    planned_departure = _datetime_clock(schedule.get("plannedDepartureTime"))
    planned_arrival = _datetime_clock(schedule.get("plannedArrivalTime"))
    real_departure = _datetime_clock(schedule.get("realDepartureTime"))
    real_arrival = _datetime_clock(schedule.get("realArrivalTime"))
    departure = real_departure or planned_departure
    arrival = real_arrival or planned_arrival
    delays = [
        value
        for leg in legs
        for value in (leg["departure_delay_seconds"], leg["arrival_delay_seconds"])
        if value is not None
    ]
    announcements = [item for leg in legs for item in leg["announcements"]]
    return {
        "trip_id": str(schedule.get("routeId") or ""),
        "route_id": str(schedule.get("routeId") or ""),
        "line": " → ".join(leg["line"] for leg in display_legs if leg["line"]),
        "headsign": " → ".join(
            leg["to"]["name"] for leg in display_legs if leg["to"]["name"]
        ),
        "departure": departure,
        "arrival": arrival,
        "departure_date": _datetime_date(
            schedule.get("realDepartureTime") or schedule.get("plannedDepartureTime")
        ),
        "arrival_date": _datetime_date(
            schedule.get("realArrivalTime") or schedule.get("plannedArrivalTime")
        ),
        "planned_departure": planned_departure,
        "planned_arrival": planned_arrival,
        "departure_minutes": _minutes(departure),
        "arrival_minutes": _minutes(arrival),
        "duration_minutes": int(schedule.get("time") or 0),
        "from": display_legs[0]["from"] if display_legs else _public_stop(schedule.get("start") or {}),
        "to": display_legs[-1]["to"] if display_legs else _public_stop(schedule.get("dest") or {}),
        "realtime": bool(real_departure or real_arrival or delays),
        "delay_seconds": max(delays, default=0),
        "cancelled": any(leg["cancelled"] for leg in legs),
        "platform": display_legs[0]["platform"] if display_legs else "",
        "realtime_platform": display_legs[0]["realtime_platform"] if display_legs else "",
        "legs": legs,
        "announcements": _dedupe_announcements(announcements),
        "provider": "geofox",
    }


def _pick_outbound(
    items: list[dict[str, Any]], first_start: str, settings: TransitSettings
) -> dict[str, Any] | None:
    target = _minutes(first_start)
    earliest = target - settings.arrive_window_minutes
    latest = target - settings.arrive_min_before
    candidates = [
        item for item in items
        if earliest <= item["arrival_minutes"] <= latest and not item.get("cancelled")
    ]
    return min(
        candidates,
        key=lambda item: (
            _transfer_count(item),
            int(item.get("duration_minutes") or 0),
            -item["arrival_minutes"],
            -item["departure_minutes"],
        ),
    ) if candidates else None


def _pick_return(
    items: list[dict[str, Any]], last_end: str, settings: TransitSettings
) -> dict[str, Any] | None:
    target = _minutes(last_end)
    earliest = target + settings.depart_min_after
    latest = target + settings.depart_window_minutes
    candidates = [
        item for item in items
        if earliest <= item["departure_minutes"] <= latest and not item.get("cancelled")
    ]
    return min(
        candidates,
        key=lambda item: (
            _transfer_count(item),
            item["departure_minutes"],
            int(item.get("duration_minutes") or 0),
            item["arrival_minutes"],
        ),
    ) if candidates else None


def _transfer_count(item: dict[str, Any]) -> int:
    vehicle_legs = [
        leg
        for leg in item.get("legs") or []
        if str(leg.get("mode") or "").upper() not in {"CHANGE", "FOOTPATH"}
        and "fußweg" not in str(leg.get("line") or "").casefold()
        and "fussweg" not in str(leg.get("line") or "").casefold()
    ]
    return max(0, len(vehicle_legs) - 1)


def _routes_allowed_by_settings(
    items: list[dict[str, Any]],
    settings: TransitSettings,
) -> list[dict[str, Any]]:
    if not settings.direct_connections_only:
        return items
    return [item for item in items if _transfer_count(item) == 0]


def _public_settings(settings: TransitSettings) -> dict[str, Any]:
    return {
        "outbound_origins": [_split_stop(value)[0] for value in settings.outbound_origins],
        "outbound_destinations": [_split_stop(value)[0] for value in settings.outbound_destinations],
        "return_origins": [_split_stop(value)[0] for value in settings.return_origins],
        "return_destinations": [_split_stop(value)[0] for value in settings.return_destinations],
        "arrive_min_before": settings.arrive_min_before,
        "arrive_window_minutes": settings.arrive_window_minutes,
        "depart_min_after": settings.depart_min_after,
        "depart_window_minutes": settings.depart_window_minutes,
        "day_start": settings.day_start,
        "day_end": settings.day_end,
        "direct_connections_only": settings.direct_connections_only,
        "enabled": settings.enabled,
    }


def _public_stop(stop: dict[str, Any]) -> dict[str, Any]:
    combined = str(stop.get("combinedName") or "").strip()
    city = str(stop.get("city") or "").strip()
    name = str(stop.get("name") or "").strip()
    label = combined or ", ".join(part for part in (city, name) if part)
    result: dict[str, Any] = {"id": str(stop.get("id") or ""), "name": label or name}
    coordinate = stop.get("coordinate") or {}
    if coordinate.get("x") is not None and coordinate.get("y") is not None:
        result["coordinate"] = {
            "x": float(coordinate["x"]),
            "y": float(coordinate["y"]),
        }
    return result


def _announcement(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id") or ""),
        "summary": str(item.get("summary") or "").strip(),
        "description": str(item.get("description") or "").strip(),
        "planned": item.get("planned"),
        "reason": str(item.get("reason") or ""),
    }


def _dedupe_announcements(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for item in items:
        key = item["id"] or f"{item['summary']}|{item['description']}"
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _dedupe_routes(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in items:
        key = (
            item.get("planned_departure") or item["departure"],
            item.get("planned_arrival") or item["arrival"],
            item["line"],
            item["from"]["id"],
            item["to"]["id"],
        )
        current = unique.get(key)
        if current is None or (item.get("realtime") and not current.get("realtime")):
            unique[key] = item
    return sorted(unique.values(), key=lambda item: (item["departure_minutes"], item["arrival_minutes"], item["line"]))


def _split_stop(value: str) -> tuple[str, str]:
    parts = str(value or "").split("|", 1)
    return parts[0].strip(), parts[1].strip() if len(parts) == 2 else ""


def _gti_clock(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("time") or "")[:5]
    return _datetime_clock(value)


def _datetime_clock(value: Any) -> str:
    text = str(value or "")
    return text[11:16] if len(text) >= 16 else ""


def _datetime_date(value: Any) -> str:
    text = str(value or "")
    return text[:10] if len(text) >= 10 else ""


def _optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _minutes(value: str) -> int:
    try:
        hour, minute = str(value).split(":", 1)
        return int(hour) * 60 + int(minute[:2])
    except (TypeError, ValueError):
        return 0


def _clock(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def _local_datetime(target_date: date, clock: str) -> datetime | None:
    try:
        parsed = datetime.strptime(f"{target_date.isoformat()} {clock}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None
    return parsed.astimezone()


def _interpolate_track(track: list[list[float]], progress: float) -> list[float]:
    scaled = min(1.0, max(0.0, progress)) * (len(track) - 1)
    index = min(len(track) - 2, int(scaled))
    fraction = scaled - index
    start = track[index]
    end = track[index + 1]
    return [
        round(start[0] + (end[0] - start[0]) * fraction, 7),
        round(start[1] + (end[1] - start[1]) * fraction, 7),
    ]


def _shift_clock(value: str, delta_minutes: int) -> str:
    if not value:
        return ""
    shifted = datetime.combine(date.today(), datetime.strptime(value, "%H:%M").time()) + timedelta(minutes=delta_minutes)
    return shifted.strftime("%H:%M")

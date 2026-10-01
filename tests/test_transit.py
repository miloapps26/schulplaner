import csv
import os
import sys
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milo_webuntis.config import GeofoxConfig, GtfsConfig, TransitSettings, load_config
from milo_webuntis.geofox import GeofoxError
from milo_webuntis.service import MonitorService
from milo_webuntis.transit import TransitPlanner


class TransitPlannerTests(unittest.TestCase):
    def test_service_returns_last_background_result_without_duplicate_query(self):
        class CountingPlanner:
            def __init__(self):
                self.calls = 0

            def cache_key(self):
                return "test"

            def day_plan(self, _settings, _lessons, target_date, **_kwargs):
                self.calls += 1
                return {
                    "date": target_date.isoformat(),
                    "feed": {"status": "ready", "provider": "geofox"},
                    "day": {},
                    "recommendation": {"outbound": None, "return": None},
                    "outbound": [],
                    "return": [],
                    "full_day": False,
                    "warnings": [],
                }

        with tempfile.TemporaryDirectory() as temp_dir:
            service = MonitorService(load_config(Path(temp_dir)))
            planner = CountingPlanner()
            service.transit_planner = planner

            first = service.transit(date(2026, 9, 17), force_refresh=True)
            second = service.transit(date(2026, 9, 17))

        self.assertEqual(planner.calls, 1)
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertEqual(second["cache_age_seconds"], 0)

    def test_failed_refresh_keeps_last_successful_bus_result(self):
        class FlakyPlanner:
            def __init__(self):
                self.calls = 0

            def cache_key(self):
                return "test"

            def day_plan(self, _settings, _lessons, target_date, **_kwargs):
                self.calls += 1
                if self.calls > 1:
                    return {
                        "date": target_date.isoformat(),
                        "feed": {"status": "error", "error": "offline"},
                    }
                return {
                    "date": target_date.isoformat(),
                    "feed": {"status": "ready", "provider": "geofox"},
                    "day": {},
                    "recommendation": {"outbound": None, "return": None},
                    "outbound": [],
                    "return": [],
                    "full_day": False,
                    "warnings": [],
                }

        with tempfile.TemporaryDirectory() as temp_dir:
            service = MonitorService(load_config(Path(temp_dir)))
            planner = FlakyPlanner()
            service.transit_planner = planner
            service.transit(date(2026, 9, 17), force_refresh=True)

            result = service.transit(date(2026, 9, 17), force_refresh=True)

        self.assertEqual(planner.calls, 2)
        self.assertTrue(result["cached"])
        self.assertTrue(result["stale"])
        self.assertEqual(result["refresh_error"], "offline")
        self.assertEqual(result["feed"]["status"], "ready")

    def test_auto_mode_falls_back_to_gtfs_when_geofox_fails(self):
        class FailingGeofox:
            def day_plan(self, *_args, **_kwargs):
                raise GeofoxError("test outage")

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            _write_gtfs(cache_dir / "latest.zip")
            planner = TransitPlanner(
                GtfsConfig("", cache_dir, 1440, 30),
                GeofoxConfig("auto", "https://example.test", "user", "secret", 63, 15, 60, 1.1),
                geofox_client=FailingGeofox(),
            )
            settings = TransitSettings(
                outbound_origins=("Wittorf, Birkenweg",),
                outbound_destinations=("Lüneburg, Herderschule",),
                return_origins=("Lüneburg, Herderschule",),
                return_destinations=("Wittorf, Birkenweg",),
                arrive_min_before=10,
                arrive_window_minutes=60,
                depart_min_after=5,
                depart_window_minutes=90,
                day_start="05:00",
                day_end="20:00",
            )
            lessons = [
                {"date": "2026-09-14", "start": "08:00", "end": "13:15", "status": "regular"},
            ]

            result = planner.day_plan(settings, lessons, date(2026, 9, 14))

        self.assertEqual(result["feed"]["provider"], "gtfs")
        self.assertTrue(result["feed"]["fallback"])
        self.assertIn("Soll-Fahrplan", result["warnings"][0])

    def test_direct_connections_and_recommendations_use_configured_buffers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            feed_path = cache_dir / "latest.zip"
            _write_gtfs(feed_path)
            planner = TransitPlanner(
                GtfsConfig(
                    feed_url="",
                    cache_dir=cache_dir,
                    cache_minutes=1440,
                    timeout_seconds=30,
                )
            )
            settings = TransitSettings(
                outbound_origins=("Wittorf, Birkenweg",),
                outbound_destinations=("Lüneburg, Herderschule", "Lüneburg, Witzendorffstraße"),
                return_origins=("Lüneburg, Herderschule", "Lüneburg, Witzendorffstraße"),
                return_destinations=("Wittorf, Birkenweg",),
                arrive_min_before=10,
                arrive_window_minutes=60,
                depart_min_after=5,
                depart_window_minutes=90,
                day_start="05:00",
                day_end="20:00",
            )
            lessons = [
                {"date": "2026-09-14", "start": "08:00", "end": "08:45", "status": "regular"},
                {"date": "2026-09-14", "start": "12:30", "end": "13:15", "status": "regular"},
            ]

            result = planner.day_plan(settings, lessons, date(2026, 9, 14))

        self.assertEqual(result["feed"]["status"], "ready")
        self.assertEqual(result["recommendation"]["outbound"]["line"], "5404")
        self.assertEqual(result["recommendation"]["outbound"]["arrival"], "07:42")
        self.assertEqual(result["recommendation"]["return"]["departure"], "13:25")
        self.assertEqual(len(result["outbound"]), 2)
        self.assertEqual(len(result["return"]), 1)

    def test_stop_ids_can_be_stored_with_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            feed_path = cache_dir / "latest.zip"
            _write_gtfs(feed_path)
            planner = TransitPlanner(
                GtfsConfig(
                    feed_url="",
                    cache_dir=cache_dir,
                    cache_minutes=1440,
                    timeout_seconds=30,
                )
            )
            settings = TransitSettings(
                outbound_origins=("Wittorf, Birkenweg|home",),
                outbound_destinations=("Lüneburg, Witzendorffstraße|witz",),
                return_origins=("Lüneburg, Herderschule|school",),
                return_destinations=("Wittorf, Birkenweg|home",),
                arrive_min_before=10,
                arrive_window_minutes=60,
                depart_min_after=5,
                depart_window_minutes=90,
                day_start="05:00",
                day_end="20:00",
            )
            lessons = [
                {"date": "2026-09-14", "start": "08:00", "end": "08:45", "status": "regular"},
                {"date": "2026-09-14", "start": "12:30", "end": "13:15", "status": "regular"},
            ]

            result = planner.day_plan(settings, lessons, date(2026, 9, 14))

        self.assertEqual(result["settings"]["outbound_origins"], ["Wittorf, Birkenweg"])
        self.assertEqual(result["recommendation"]["outbound"]["to"]["id"], "witz")
        self.assertEqual(result["recommendation"]["return"]["from"]["id"], "school")

    def test_stop_suggestions_return_stable_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            feed_path = cache_dir / "latest.zip"
            _write_gtfs(feed_path)
            planner = TransitPlanner(
                GtfsConfig(
                    feed_url="",
                    cache_dir=cache_dir,
                    cache_minutes=1440,
                    timeout_seconds=30,
                )
            )

            result = planner.stop_suggestions("witz", limit=3)

        self.assertEqual(result["items"][0]["id"], "witz")
        self.assertEqual(result["items"][0]["value"], "Lüneburg, Witzendorffstraße|witz")

    def test_stop_suggestions_prefer_parent_station_for_duplicate_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            feed_path = cache_dir / "latest.zip"
            _write_gtfs(feed_path)
            planner = TransitPlanner(
                GtfsConfig(
                    feed_url="",
                    cache_dir=cache_dir,
                    cache_minutes=1440,
                    timeout_seconds=30,
                )
            )
            settings = TransitSettings(
                outbound_origins=("Lüneburg, Herderschule",),
                outbound_destinations=("Lüneburg, Witzendorffstraße",),
                return_origins=("Lüneburg, Herderschule",),
                return_destinations=("Wittorf, Birkenweg",),
                arrive_min_before=10,
                arrive_window_minutes=60,
                depart_min_after=5,
                depart_window_minutes=90,
                day_start="05:00",
                day_end="20:00",
            )

            suggestions = planner.stop_suggestions("Herderschule", limit=3)
            validation = planner.validate_stops(settings)

        self.assertEqual(len(suggestions["items"]), 1)
        self.assertEqual(suggestions["items"][0]["id"], "school_station")
        self.assertEqual(validation["groups"]["outbound_origins"][0]["status"], "valid")
        self.assertEqual(validation["groups"]["outbound_origins"][0]["id"], "school_station")


def _write_gtfs(path: Path) -> None:
    rows = {
        "agency.txt": [
            ["agency_id", "agency_name", "agency_url", "agency_timezone"],
            ["220", "Hamburger Verkehrsverbund", "https://hvv.de", "Europe/Berlin"],
        ],
        "feed_info.txt": [
            ["feed_publisher_name", "feed_publisher_url", "feed_lang", "feed_version"],
            ["test", "https://example.test", "de", "test-feed"],
        ],
        "stops.txt": [
            ["stop_id", "stop_name", "parent_station", "stop_lat", "stop_lon", "location_type"],
            ["home", "Wittorf, Birkenweg", "", "53.0", "10.0", ""],
            ["school_station", "Lüneburg, Herderschule", "", "53.1", "10.1", "1"],
            ["school", "Lüneburg, Herderschule", "school_station", "53.1", "10.1", ""],
            ["witz", "Lüneburg, Witzendorffstraße", "", "53.1", "10.2", ""],
        ],
        "routes.txt": [
            ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"],
            ["r5404", "220", "5404", "", "3"],
        ],
        "calendar.txt": [
            ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"],
            ["schooldays", "1", "1", "1", "1", "1", "0", "0", "20260901", "20260930"],
        ],
        "calendar_dates.txt": [
            ["service_id", "date", "exception_type"],
        ],
        "trips.txt": [
            ["route_id", "service_id", "trip_id", "trip_headsign"],
            ["r5404", "schooldays", "morning_1", "Lüneburg, Herderschule"],
            ["r5404", "schooldays", "morning_2", "Lüneburg, Witzendorffstraße"],
            ["r5404", "schooldays", "return_1", "Wittorf, Birkenweg"],
        ],
        "stop_times.txt": [
            ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence", "stop_headsign"],
            ["morning_1", "07:05:00", "07:05:00", "home", "1", "Lüneburg, Herderschule"],
            ["morning_1", "07:33:00", "07:33:00", "school", "2", "Lüneburg, Herderschule"],
            ["morning_2", "07:14:00", "07:14:00", "home", "1", "Lüneburg, Witzendorffstraße"],
            ["morning_2", "07:42:00", "07:42:00", "witz", "2", "Lüneburg, Witzendorffstraße"],
            ["return_1", "13:25:00", "13:25:00", "school", "1", "Wittorf, Birkenweg"],
            ["return_1", "13:55:00", "13:55:00", "home", "2", "Wittorf, Birkenweg"],
        ],
        "attributions.txt": [
            ["attribution_id", "organization_name"],
        ],
    }
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in rows.items():
            with archive.open(name, "w") as handle:
                text = "\n".join(",".join(_csv_cell(cell) for cell in row) for row in content) + "\n"
                handle.write(text.encode("utf-8"))


def _csv_cell(value: str) -> str:
    output = []
    csv.writer(_ListWriter(output)).writerow([value])
    return output[0].strip()


class _ListWriter:
    def __init__(self, output):
        self.output = output

    def write(self, value):
        self.output.append(value)


if __name__ == "__main__":
    unittest.main()

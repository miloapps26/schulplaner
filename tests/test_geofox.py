import base64
import hashlib
import hmac
import json
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milo_webuntis.config import GeofoxConfig, TransitSettings
from milo_webuntis.geofox import GeofoxClient, _pick_outbound, _routes_allowed_by_settings


class _Response:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class _Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, *, data, headers, timeout):
        self.calls.append({"url": url, "data": data, "headers": headers, "timeout": timeout})
        return _Response(self.responses.pop(0))


def _config() -> GeofoxConfig:
    return GeofoxConfig(
        mode="auto",
        base_url="https://gti.example.test",
        username="test-user",
        password="test-password",
        api_version=63,
        timeout_seconds=15,
        cache_seconds=60,
        min_interval_seconds=1.1,
    )


class GeofoxClientTests(unittest.TestCase):
    def test_outbound_recommendation_prefers_short_direct_connection(self):
        settings = TransitSettings(
            outbound_origins=("Wittorf, Birkenweg",),
            outbound_destinations=("Lüneburg, Witzendorffstraße",),
            return_origins=("Lüneburg, Witzendorffstraße",),
            return_destinations=("Wittorf, Birkenweg",),
            arrive_min_before=5,
            arrive_window_minutes=60,
            depart_min_after=5,
            depart_window_minutes=90,
            day_start="05:00",
            day_end="20:00",
        )
        transfer = {
            "line": "5402 → 5201 → 5074",
            "departure_minutes": 398,
            "arrival_minutes": 462,
            "duration_minutes": 64,
            "cancelled": False,
            "legs": [{"line": line, "mode": "BUS"} for line in ("5402", "5201", "5074")],
        }
        direct = {
            "line": "5405",
            "departure_minutes": 432,
            "arrival_minutes": 458,
            "duration_minutes": 26,
            "cancelled": False,
            "legs": [{"line": "5405", "mode": "BUS"}],
        }

        result = _pick_outbound([transfer, direct], "08:00", settings)

        self.assertEqual(result["line"], "5405")

    def test_direct_only_setting_removes_transfer_connections(self):
        settings = TransitSettings(
            outbound_origins=("Start",),
            outbound_destinations=("Ziel",),
            return_origins=("Ziel",),
            return_destinations=("Start",),
            arrive_min_before=5,
            arrive_window_minutes=60,
            depart_min_after=5,
            depart_window_minutes=90,
            day_start="05:00",
            day_end="20:00",
            direct_connections_only=True,
        )
        transfer = {
            "line": "1 → 2",
            "legs": [{"line": "1", "mode": "BUS"}, {"line": "2", "mode": "BUS"}],
        }
        direct = {"line": "3", "legs": [{"line": "3", "mode": "BUS"}]}

        result = _routes_allowed_by_settings([transfer, direct], settings)

        self.assertEqual(result, [direct])

    def test_rate_limit_counts_time_since_request_started(self):
        clock = [10.0]
        sleeps = []

        class _DelayedSession(_Session):
            def post(self, url, *, data, headers, timeout):
                response = super().post(url, data=data, headers=headers, timeout=timeout)
                clock[0] += 2.0
                return response

        session = _DelayedSession([{"returnCode": "OK"}, {"returnCode": "OK"}])
        client = GeofoxClient(
            _config(),
            session=session,
            monotonic=lambda: clock[0],
            sleep=lambda seconds: (sleeps.append(seconds), clock.__setitem__(0, clock[0] + seconds)),
        )

        client.request("init", {})
        client.request("init", {})

        self.assertEqual(sleeps, [])

    def test_signature_uses_exact_utf8_request_body(self):
        session = _Session([{"returnCode": "OK"}])
        client = GeofoxClient(_config(), session=session, monotonic=lambda: 10.0, sleep=lambda _seconds: None)

        client.request("init", {"name": "Lüneburg"})

        call = session.calls[0]
        expected = base64.b64encode(
            hmac.new(b"test-password", call["data"], hashlib.sha1).digest()
        ).decode("ascii")
        self.assertEqual(json.loads(call["data"].decode("utf-8")), {"name": "Lüneburg"})
        self.assertEqual(call["headers"]["geofox-auth-signature"], expected)
        self.assertNotIn("test-password", str(call))

    def test_day_plan_normalizes_transfer_route_and_realtime_delay(self):
        session = _Session(
            [
                {
                    "returnCode": "OK",
                    "schedules": [],
                    "realtimeSchedules": [
                        {
                            "routeId": 7,
                            "time": 66,
                            "plannedDepartureTime": "2026-09-18T06:38:00.000+0200",
                            "plannedArrivalTime": "2026-09-18T07:44:00.000+0200",
                            "realDepartureTime": "2026-09-18T06:41:00.000+0200",
                            "realArrivalTime": "2026-09-18T07:47:00.000+0200",
                            "scheduleElements": [
                                {
                                    "from": {
                                        "id": "Master:53908",
                                        "combinedName": "Wittorf, Birkenweg",
                                        "depTime": {"time": "06:38"},
                                        "depDelay": 180,
                                    },
                                    "to": {
                                        "id": "Master:1",
                                        "combinedName": "Bardowick, Schulzentrum",
                                        "arrTime": {"time": "06:50"},
                                        "arrDelay": 180,
                                    },
                                    "line": {"name": "5402", "id": "line-5402", "type": {"simpleType": "BUS"}},
                                },
                                {
                                    "from": {"id": "Master:1", "combinedName": "Bardowick, Schulzentrum"},
                                    "to": {"id": "Master:15130", "combinedName": "Lüneburg, Herderschule"},
                                    "line": {"name": "5404", "id": "line-5404", "type": {"simpleType": "BUS"}},
                                },
                            ],
                        }
                    ],
                },
                {"returnCode": "OK", "schedules": []},
                {"returnCode": "OK", "announcements": []},
            ]
        )
        client = GeofoxClient(_config(), session=session, monotonic=lambda: 10.0, sleep=lambda _seconds: None)
        settings = TransitSettings(
            outbound_origins=("Wittorf, Birkenweg|Master:53908",),
            outbound_destinations=("Lüneburg, Herderschule|Master:15130",),
            return_origins=("Lüneburg, Herderschule|Master:15130",),
            return_destinations=("Wittorf, Birkenweg|Master:53908",),
            arrive_min_before=10,
            arrive_window_minutes=60,
            depart_min_after=5,
            depart_window_minutes=90,
            day_start="05:00",
            day_end="20:00",
        )

        result = client.day_plan(
            settings,
            [{"date": "2026-09-18", "start": "08:00", "status": "regular"}],
            date(2026, 9, 18),
        )

        connection = result["outbound"][0]
        self.assertEqual(connection["line"], "5402 → 5404")
        self.assertEqual(connection["departure"], "06:41")
        self.assertEqual(connection["arrival"], "07:47")
        self.assertEqual(connection["delay_seconds"], 180)
        self.assertTrue(connection["realtime"])
        self.assertEqual(result["feed"]["provider"], "geofox")

    def test_routes_request_and_filter_the_complete_departure_window(self):
        def schedule(route_id, departure, arrival):
            return {
                "routeId": route_id,
                "time": 20,
                "plannedDepartureTime": f"2026-09-18T{departure}:00.000+0200",
                "plannedArrivalTime": f"2026-09-18T{arrival}:00.000+0200",
                "scheduleElements": [
                    {
                        "from": {"id": "Master:15130", "combinedName": "Lüneburg, Herderschule"},
                        "to": {"id": "Master:53908", "combinedName": "Wittorf, Birkenweg"},
                        "line": {"name": "5402", "id": "line-5402", "type": {"simpleType": "BUS"}},
                    }
                ],
            }

        session = _Session([{"returnCode": "OK", "schedules": [
            schedule(1, "13:25", "13:45"),
            schedule(2, "14:05", "14:25"),
            schedule(3, "15:05", "15:25"),
        ]}])
        client = GeofoxClient(_config(), session=session, monotonic=lambda: 10.0, sleep=lambda _seconds: None)

        routes = client._routes(
            ("Lüneburg, Herderschule|Master:15130",),
            ("Wittorf, Birkenweg|Master:53908",),
            date(2026, 9, 18),
            "13:20",
            window_start="13:20",
            window_end="14:45",
            time_is_departure=True,
        )

        self.assertEqual([item["departure"] for item in routes], ["13:25", "14:05"])
        request = json.loads(session.calls[0]["data"])
        self.assertEqual(request["time"]["time"], "13:20")
        self.assertEqual(request["schedulesAfter"], 30)
        self.assertNotIn("numberOfSchedules", request)

    def test_vehicle_status_waits_until_shortly_before_departure(self):
        session = _Session([])
        client = GeofoxClient(_config(), session=session, monotonic=lambda: 10.0, sleep=lambda _seconds: None)
        current = datetime(2026, 9, 18, 10, 0, tzinfo=timezone(timedelta(hours=2)))

        result = client.vehicle_status(
            {"departure": "11:00", "arrival": "11:30", "legs": []},
            date(2026, 9, 18),
            now=current,
        )

        self.assertEqual(result["status"], "scheduled")
        self.assertEqual(session.calls, [])

    def test_vehicle_status_returns_only_explicit_realtime_position(self):
        local_timezone = timezone(timedelta(hours=2))
        current = datetime(2026, 9, 18, 13, 30, tzinfo=local_timezone)
        start = int(datetime(2026, 9, 18, 13, 20, tzinfo=local_timezone).timestamp())
        end = int(datetime(2026, 9, 18, 13, 40, tzinfo=local_timezone).timestamp())
        session = _Session(
            [
                {
                    "returnCode": "OK",
                    "journeys": [
                        {
                            "line": {"name": "5402"},
                            "realtime": True,
                            "segments": [
                                {
                                    "startDateTime": start,
                                    "endDateTime": end,
                                    "startStopPointKey": "A",
                                    "endStopPointKey": "B",
                                    "startStationName": "Herderschule",
                                    "endStationName": "Birkenweg",
                                    "realtimeDelay": 2,
                                }
                            ],
                        }
                    ],
                },
                {"returnCode": "OK", "tracks": [{"track": [10.0, 53.0, 10.2, 53.2]}]},
            ]
        )
        client = GeofoxClient(_config(), session=session, monotonic=lambda: 10.0, sleep=lambda _seconds: None)
        connection = {
            "departure": "13:20",
            "arrival": "13:40",
            "legs": [
                {
                    "line": "5402",
                    "mode": "BUS",
                    "from": {"coordinate": {"x": 10.0, "y": 53.0}},
                    "to": {"coordinate": {"x": 10.2, "y": 53.2}},
                }
            ],
        }

        result = client.vehicle_status(connection, date(2026, 9, 18), now=current)

        self.assertEqual(result["status"], "available")
        self.assertTrue(result["realtime"])
        self.assertAlmostEqual(result["position"]["longitude"], 10.08)
        self.assertAlmostEqual(result["position"]["latitude"], 53.08)
        self.assertEqual(len(session.calls), 2)
        vehicle_request = json.loads(session.calls[0]["data"])
        self.assertTrue(vehicle_request["realtime"])
        self.assertTrue(vehicle_request["withoutCoords"])

    def test_recommendation_only_plan_uses_one_route_page_per_direction(self):
        def schedule(route_id, departure, arrival, start_id, start_name, end_id, end_name, line):
            return {
                "routeId": route_id,
                "time": 25,
                "plannedDepartureTime": f"2026-09-18T{departure}:00.000+0200",
                "plannedArrivalTime": f"2026-09-18T{arrival}:00.000+0200",
                "scheduleElements": [
                    {
                        "from": {"id": start_id, "combinedName": start_name},
                        "to": {"id": end_id, "combinedName": end_name},
                        "line": {"name": line, "id": f"line-{line}", "type": {"simpleType": "BUS"}},
                    }
                ],
            }

        session = _Session(
            [
                {"returnCode": "OK", "schedules": [
                    schedule(1, "06:38", "07:44", "Master:53908", "Wittorf, Birkenweg", "Master:15130", "Lüneburg, Herderschule", "5402"),
                ]},
                {"returnCode": "OK", "schedules": [
                    schedule(2, "13:25", "14:10", "Master:15130", "Lüneburg, Herderschule", "Master:53908", "Wittorf, Birkenweg", "5402"),
                ]},
                {"returnCode": "OK", "announcements": []},
            ]
        )
        client = GeofoxClient(_config(), session=session, monotonic=lambda: 10.0, sleep=lambda _seconds: None)
        settings = TransitSettings(
            outbound_origins=("Wittorf, Birkenweg|Master:53908",),
            outbound_destinations=("Lüneburg, Herderschule|Master:15130",),
            return_origins=("Lüneburg, Herderschule|Master:15130",),
            return_destinations=("Wittorf, Birkenweg|Master:53908",),
            arrive_min_before=10,
            arrive_window_minutes=60,
            depart_min_after=5,
            depart_window_minutes=90,
            day_start="05:00",
            day_end="20:00",
        )

        result = client.day_plan(
            settings,
            [
                {"date": "2026-09-18", "start": "08:00", "end": "13:15", "status": "regular"},
            ],
            date(2026, 9, 18),
            include_full_day=False,
        )

        self.assertFalse(result["full_day"])
        self.assertEqual(result["recommendation"]["outbound"]["departure"], "06:38")
        self.assertEqual(result["recommendation"]["return"]["departure"], "13:25")
        self.assertEqual(result["outbound"], [])
        self.assertEqual(result["return"], [])
        route_requests = [json.loads(call["data"]) for call in session.calls if call["url"].endswith("/getRoute")]
        self.assertEqual(len(route_requests), 2)
        self.assertFalse(route_requests[0]["timeIsDeparture"])
        self.assertEqual(route_requests[0]["time"]["time"], "07:50")
        self.assertEqual(route_requests[0]["schedulesBefore"], 30)
        self.assertNotIn("schedulesAfter", route_requests[0])
        self.assertTrue(route_requests[1]["timeIsDeparture"])
        self.assertEqual(route_requests[1]["time"]["time"], "13:19")
        self.assertEqual(route_requests[1]["schedulesAfter"], 30)

    def test_recommendation_retries_an_incomplete_return_result(self):
        def schedule(route_id, departure, arrival, start_id, start_name, end_id, end_name):
            return {
                "routeId": route_id,
                "time": 22,
                "plannedDepartureTime": f"2026-09-18T{departure}:00.000+0200",
                "plannedArrivalTime": f"2026-09-18T{arrival}:00.000+0200",
                "scheduleElements": [{
                    "from": {"id": start_id, "combinedName": start_name},
                    "to": {"id": end_id, "combinedName": end_name},
                    "line": {"name": "5402", "id": "line-5402", "type": {"simpleType": "BUS"}},
                }],
            }

        outbound = schedule(
            1, "07:12", "07:38", "Master:53908", "Wittorf, Birkenweg",
            "Master:15130", "Lüneburg, Herderschule",
        )
        inbound = schedule(
            2, "13:20", "13:42", "Master:15130", "Lüneburg, Herderschule",
            "Master:53908", "Wittorf, Birkenweg",
        )
        session = _Session([
            {"returnCode": "OK", "schedules": [outbound]},
            {"returnCode": "OK", "schedules": []},
            {"returnCode": "OK", "schedules": [inbound]},
            {"returnCode": "OK", "schedules": []},
            {"returnCode": "OK", "announcements": []},
        ])
        client = GeofoxClient(_config(), session=session, monotonic=lambda: 10.0, sleep=lambda _seconds: None)
        settings = TransitSettings(
            outbound_origins=("Wittorf, Birkenweg|Master:53908",),
            outbound_destinations=("Lüneburg, Herderschule|Master:15130",),
            return_origins=("Lüneburg, Herderschule|Master:15130",),
            return_destinations=("Wittorf, Birkenweg|Master:53908",),
            arrive_min_before=5,
            arrive_window_minutes=60,
            depart_min_after=5,
            depart_window_minutes=90,
            day_start="05:00",
            day_end="20:00",
        )

        result = client.day_plan(
            settings,
            [{"date": "2026-09-18", "start": "08:00", "end": "13:15", "status": "regular"}],
            date(2026, 9, 18),
            include_full_day=False,
        )

        self.assertEqual(result["recommendation"]["return"]["departure"], "13:20")
        route_requests = [json.loads(call["data"]) for call in session.calls if call["url"].endswith("/getRoute")]
        self.assertEqual(len(route_requests), 4)


if __name__ == "__main__":
    unittest.main()

import os
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milo_webuntis.accounts import AccountStore
from milo_webuntis.app import TransitPayload, payload_dict
from milo_webuntis.auth import create_session_cookie, valid_session_user
from milo_webuntis.config import load_config
from milo_webuntis.service import (
    MonitorService,
    _app_url,
    _setup_url,
    _timetable_url,
    monitor_window,
    selectable_transit_dates,
)


class AuthConfigTests(unittest.TestCase):
    def test_transit_payload_keeps_direct_only_setting(self):
        payload = TransitPayload(direct_connections_only=True)

        self.assertTrue(payload_dict(payload)["direct_connections_only"])

    def test_selectable_transit_dates_cover_current_and_next_school_week(self):
        result = selectable_transit_dates(date(2026, 9, 17))

        self.assertEqual(len(result), 10)
        self.assertEqual(result[0], date(2026, 9, 17))
        self.assertEqual(set(result), {
            date(2026, 9, 14), date(2026, 9, 15), date(2026, 9, 16),
            date(2026, 9, 17), date(2026, 9, 18), date(2026, 9, 21),
            date(2026, 9, 22), date(2026, 9, 23), date(2026, 9, 24),
            date(2026, 9, 25),
        })

    def test_session_cookie_expires_after_idle_timeout(self):
        cookie = create_session_cookie("admin", "secret", now=1000)

        self.assertEqual(
            valid_session_user(cookie, "secret", {"admin": "pw"}, 30, now=1000 + 29 * 60),
            "admin",
        )
        self.assertIsNone(
            valid_session_user(cookie, "secret", {"admin": "pw"}, 30, now=1000 + 31 * 60)
        )

    def test_timetable_url_uses_login_protected_app_url(self):
        url = _timetable_url("https://webuntis.miloapps.net/app", "next")

        self.assertEqual(url, "https://webuntis.miloapps.net/app?week=next")

    def test_setup_url_uses_one_time_token_for_setup_only(self):
        url = _setup_url("https://webuntis.miloapps.net/app", "abc 123")

        self.assertEqual(url, "https://webuntis.miloapps.net/setup?token=abc%20123")

    def test_load_config_supports_tenants_file(self):
        old_env = os.environ.copy()
        try:
            os.environ.clear()
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                os.environ["USERPROFILE"] = str(root)
                config_dir = root / "config"
                config_dir.mkdir()
                (config_dir / "tenants.json").write_text(
                    """
                    {
                      "tenants": [
                        {
                          "id": "jonas",
                          "name": "Jonas",
                          "parent_email": "parent@example.com",
                          "display": {
                            "student_first_name": "Jonas",
                            "student_last_name": "Cichosz",
                            "school": "Herderschule Lueneburg",
                            "class": "5D"
                          },
                          "webuntis": {
                            "server": "school.webuntis.com",
                            "school": "school",
                            "username": "user",
                            "app_secret": "secret",
                            "element_type": 5,
                            "element_id": 6817
                          },
                          "email": {
                            "recipients": "one@example.com; two@example.com"
                          },
                          "transit": {
                            "outbound_origins": ["Wittorf, Birkenweg"],
                            "outbound_destinations": ["Lüneburg, Herderschule", "Lüneburg, Witzendorffstraße"],
                            "return_origins": "Lüneburg, Herderschule\\nLüneburg, Witzendorffstraße",
                            "return_destinations": "Wittorf, Birkenweg",
                            "direct_connections_only": true
                          }
                        }
                      ]
                    }
                    """,
                    encoding="utf-8",
                )

                config = load_config(root)

            self.assertEqual(len(config.tenants), 1)
            self.assertEqual(config.poll_interval_minutes, 15)
            self.assertEqual(config.transit_poll_interval_minutes, 2)
            self.assertEqual(config.tenants[0].id, "jonas")
            self.assertNotEqual(config.tenants[0].public_id, "jonas")
            self.assertTrue(config.tenants[0].public_id.startswith("view_"))
            self.assertEqual(config.tenants[0].parent_email, "parent@example.com")
            self.assertEqual(config.tenants[0].student_first_name, "Jonas")
            self.assertEqual(config.tenants[0].student_last_initial, "Cichosz")
            self.assertEqual(config.tenants[0].school_label, "Herderschule Lueneburg")
            self.assertEqual(config.tenants[0].class_label, "5D")
            self.assertEqual(config.tenants[0].webuntis.element_id, 6817)
            self.assertEqual(config.tenants[0].email.recipients, ["one@example.com", "two@example.com"])
            self.assertEqual(config.tenants[0].transit.outbound_origins, ("Wittorf, Birkenweg",))
            self.assertEqual(
                config.tenants[0].transit.outbound_destinations,
                ("Lüneburg, Herderschule", "Lüneburg, Witzendorffstraße"),
            )
            self.assertEqual(
                config.tenants[0].transit.return_origins,
                ("Lüneburg, Herderschule", "Lüneburg, Witzendorffstraße"),
            )
            self.assertTrue(config.tenants[0].transit.direct_connections_only)
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    def test_tenant_file_does_not_inherit_webuntis_secrets_from_env(self):
        old_env = os.environ.copy()
        try:
            os.environ.clear()
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                os.environ["USERPROFILE"] = str(root)
                os.environ["WEBUNTIS_USERNAME"] = "admin-should-not-be-parent"
                os.environ["WEBUNTIS_PASSWORD"] = "secret-should-not-leak"
                os.environ["WEBUNTIS_APP_SECRET"] = "app-secret-should-not-leak"
                config_dir = root / "config"
                config_dir.mkdir()
                (config_dir / "tenants.json").write_text(
                    """
                    {
                      "tenants": [
                        {
                          "id": "tenant_1",
                          "name": "Profil",
                          "webuntis": {
                            "server": "school.webuntis.com",
                            "school": "school",
                            "element_type": 5,
                            "element_id": 6817
                          }
                        }
                      ]
                    }
                    """,
                    encoding="utf-8",
                )

                config = load_config(root)

            self.assertEqual(config.tenants[0].webuntis.username, "")
            self.assertEqual(config.tenants[0].webuntis.password, "")
            self.assertEqual(config.tenants[0].webuntis.app_secret, "")
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    def test_app_url_removes_old_profile_path(self):
        url = _app_url("https://webuntis.miloapps.net/t/view_abcd#token=secret")

        self.assertEqual(url, "https://webuntis.miloapps.net/app")

    def test_create_tenant_keeps_parent_email_and_no_public_link(self):
        old_env = os.environ.copy()
        try:
            os.environ.clear()
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                os.environ["USERPROFILE"] = str(root)
                os.environ["PUBLIC_TIMETABLE_URL"] = "https://webuntis.miloapps.net"
                service = MonitorService(load_config(root))

                result = service.create_tenant(
                    {
                        "name": "Jonas intern",
                        "parent_email": "parent@example.com",
                        "active": True,
                        "display": {
                            "student_first_name": "Jonas",
                            "student_last_name": "Cichosz",
                            "school": "Herderschule Lueneburg",
                            "class_name": "5D",
                        },
                        "webuntis": {
                            "server": "school.webuntis.com",
                            "school": "school",
                            "element_type": 5,
                            "element_id": 6817,
                        },
                        "email": {"recipients": "one@example.com"},
                    }
                )

            created = result["tenants"][-1]
            self.assertEqual(created["parent_email"], "parent@example.com")
            self.assertEqual(created["app_url"], "https://webuntis.miloapps.net/app")
            self.assertNotIn("public_link", created)
            self.assertFalse(created["webuntis"]["has_app_secret"])
            self.assertEqual(created["display"]["student_name"], "Jonas Cichosz")
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    def test_parent_invitation_accepts_custom_username_and_password(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = AccountStore(Path(temp_dir))
            token, invite = store.create_invitation(
                "parent@example.com",
                "tenant_1",
                datetime(2026, 9, 9, 12, 0, 0),
            )

            parent = store.accept_invitation(
                token,
                "mein.webuntis.user",
                "ein-sicheres-passwort",
                datetime(2026, 9, 9, 12, 1, 0),
            )

            self.assertEqual(invite["email"], "parent@example.com")
            self.assertEqual(parent["username"], "mein.webuntis.user")
            self.assertEqual(parent["tenant_ids"], ["tenant_1"])
            self.assertIsNotNone(store.authenticate_parent("mein.webuntis.user", "ein-sicheres-passwort"))
            self.assertIsNotNone(store.authenticate_parent("parent@example.com", "ein-sicheres-passwort"))

    def test_parent_invitation_stores_webuntis_login_for_tenant(self):
        old_env = os.environ.copy()
        try:
            os.environ.clear()
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                os.environ["USERPROFILE"] = str(root)
                os.environ["PUBLIC_TIMETABLE_URL"] = "https://webuntis.miloapps.net"
                service = MonitorService(load_config(root))

                admin_state = service.create_tenant(
                    {
                        "name": "Jonas intern",
                        "parent_email": "parent@example.com",
                        "active": True,
                        "display": {
                            "student_first_name": "Jonas",
                            "student_last_name": "Cichosz",
                            "school": "Herderschule Lueneburg",
                            "class_name": "5D",
                        },
                        "webuntis": {
                            "server": "herderschule-lueneburg.webuntis.com",
                            "school": "herderschule-lueneburg",
                            "element_type": 5,
                            "element_id": 6817,
                        },
                    }
                )
                tenant_id = admin_state["tenants"][-1]["id"]
                invite_result = service.create_parent_invitation(tenant_id)
                token = parse_qs(urlparse(invite_result["invite"]["setup_url"]).query)["token"][0]

                profile = service.accept_parent_invitation(
                    token,
                    "Jonas.Cichosz",
                    "webuntis-pass",
                )
                tenant = service.tenant(tenant_id)
                parent_login = service.parent_by_login("jonas.cichosz", "webuntis-pass")

            self.assertEqual(profile["parent"]["username"], "Jonas.Cichosz")
            self.assertEqual(tenant.webuntis.username, "Jonas.Cichosz")
            self.assertEqual(tenant.webuntis.password, "webuntis-pass")
            self.assertTrue(profile["tenant"]["webuntis"]["has_password"])
            self.assertIsNotNone(parent_login)
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    def test_manual_lessons_are_merged_into_schedule_and_deletable(self):
        old_env = os.environ.copy()
        try:
            os.environ.clear()
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                os.environ["USERPROFILE"] = str(root)
                service = MonitorService(load_config(root))
                target_day = monitor_window(date.today())[0]

                created = service.add_manual_lesson(
                    {
                        "title": "Theater-AG",
                        "recurring": False,
                        "date": target_day.isoformat(),
                        "start": "14:15",
                        "end": "15:00",
                        "room": "Aula",
                        "note": "Probe",
                    },
                    service.default_tenant.id,
                )
                schedule = service.schedule(service.default_tenant.id)
                lesson = next(
                    item
                    for item in schedule["days"][target_day.isoformat()]
                    if item.get("source") == "manual"
                )

                after_delete = service.delete_manual_lesson(
                    created["items"][0]["id"],
                    service.default_tenant.id,
                )
                schedule_after_delete = service.schedule(service.default_tenant.id)

            self.assertEqual(lesson["subject"], ["Theater-AG"])
            self.assertEqual(lesson["room"], ["Aula"])
            self.assertEqual(lesson["info"], "Probe")
            self.assertEqual(after_delete["items"], [])
            self.assertNotIn(target_day.isoformat(), schedule_after_delete["days"])
        finally:
            os.environ.clear()
            os.environ.update(old_env)


if __name__ == "__main__":
    unittest.main()

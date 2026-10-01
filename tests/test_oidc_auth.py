import os
import sys
import tempfile
import unittest
import asyncio
import json
from http.cookies import SimpleCookie
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milo_webuntis.app import create_app
from milo_webuntis.oidc import OidcIdentity


class FakeOidcClient:
    def __init__(self, identity: OidcIdentity) -> None:
        self.identity = identity

    def authorization_url(self, state: str, code_challenge: str, next_url: str = "") -> str:
        return f"https://auth.example.invalid/authorize?state={state}&code_challenge={code_challenge}"

    def exchange_code(self, code: str, code_verifier: str) -> OidcIdentity:
        if code != "ok" or not code_verifier:
            raise ValueError("invalid code")
        return self.identity


class MiniResponse:
    def __init__(self, status_code: int, headers: dict[str, str], body: bytes) -> None:
        self.status_code = status_code
        self.headers = headers
        self._body = body

    def json(self) -> dict:
        return json.loads(self._body.decode("utf-8") or "{}")


class MiniClient:
    def __init__(self, app) -> None:
        self.app = app
        self.cookies: dict[str, str] = {}

    def get(self, url: str, follow_redirects: bool = True) -> MiniResponse:
        return self.request("GET", url)

    def post(self, url: str, json: dict | None = None) -> MiniResponse:
        body = b""
        headers = []
        if json is not None:
            body = __import__("json").dumps(json).encode("utf-8")
            headers.append((b"content-type", b"application/json"))
        return self.request("POST", url, body=body, extra_headers=headers)

    def request(self, method: str, url: str, body: bytes = b"", extra_headers=None) -> MiniResponse:
        return asyncio.run(self._request(method, url, body, extra_headers or []))

    async def _request(self, method: str, url: str, body: bytes, extra_headers) -> MiniResponse:
        parsed = urlparse(url)
        raw_headers = [(b"host", b"127.0.0.1")]
        raw_headers.extend(extra_headers)
        if self.cookies:
            cookie_header = "; ".join(f"{key}={value}" for key, value in self.cookies.items())
            raw_headers.append((b"cookie", cookie_header.encode("utf-8")))
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": parsed.path or "/",
            "raw_path": (parsed.path or "/").encode("ascii"),
            "query_string": parsed.query.encode("ascii"),
            "headers": raw_headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
        sent_request = False
        response_status = 500
        response_headers: list[tuple[bytes, bytes]] = []
        response_body = bytearray()

        async def receive():
            nonlocal sent_request
            if sent_request:
                return {"type": "http.disconnect"}
            sent_request = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            nonlocal response_status, response_headers
            if message["type"] == "http.response.start":
                response_status = int(message["status"])
                response_headers = list(message.get("headers", []))
            elif message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))

        await self.app(scope, receive, send)
        headers: dict[str, str] = {}
        for key, value in response_headers:
            text_key = key.decode("latin1").lower()
            text_value = value.decode("latin1")
            if text_key == "set-cookie":
                self._store_cookie(text_value)
            headers[text_key] = text_value
        return MiniResponse(response_status, headers, bytes(response_body))

    def _store_cookie(self, header: str) -> None:
        cookie = SimpleCookie()
        cookie.load(header)
        for key, morsel in cookie.items():
            if morsel.value:
                self.cookies[key] = morsel.value
            else:
                self.cookies.pop(key, None)


class OidcAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_env = os.environ.copy()
        os.environ.clear()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "config").mkdir()
        (self.root / "config" / "tenants.json").write_text(
            """
            {
              "tenants": [
                {
                  "id": "tenant_1",
                  "name": "Testprofil",
                  "parent_email": "parent@example.com",
                  "display": {
                    "student_first_name": "Max",
                    "student_last_name": "Mustermann",
                    "school": "Testschule",
                    "class": "5D"
                  },
                  "webuntis": {
                    "server": "school.webuntis.com",
                    "school": "school",
                    "username": "user",
                    "app_secret": "secret",
                    "element_type": 5,
                    "element_id": 1234
                  }
                }
              ]
            }
            """,
            encoding="utf-8",
        )
        os.environ.update(
            {
                "USERPROFILE": str(self.root),
                "DATA_DIR": str(self.root / "data"),
                "TENANTS_FILE": str(self.root / "config" / "tenants.json"),
                "MILO_AUTH_REQUIRED": "1",
                "MILO_SESSION_SECRET": "test-session-secret",
                "MILO_OIDC_ISSUER": "https://auth.example.invalid/application/o/schulplaner/",
                "MILO_OIDC_CLIENT_ID": "schulplaner",
                "MILO_OIDC_CLIENT_SECRET": "secret",
                "MILO_OIDC_REDIRECT_URI": "http://127.0.0.1:8000/auth/callback",
                "MILO_OIDC_ADMIN_GROUP": "milo-admins",
                "MILO_OIDC_USER_GROUP": "milo-webuntis-users",
            }
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.clear()
        os.environ.update(self.old_env)

    def test_version_endpoint_is_public_and_minimal(self):
        client = MiniClient(create_app())

        response = client.get("/api/version")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json().keys()), {"version"})

    def test_authorized_group_member_can_sign_in(self):
        app = create_app()
        app.state.oidc_client = FakeOidcClient(
            OidcIdentity(
                subject="sub-1",
                username="parent",
                email="parent@example.com",
                groups=("milo-webuntis-users",),
                claims={},
            )
        )
        client = MiniClient(app)

        callback = self._start_oidc(client)
        response = client.get(callback, follow_redirects=False)
        me = client.get("/api/me")

        self.assertEqual(response.status_code, 303)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["role"], "parent")

    def test_unauthorized_group_member_is_rejected(self):
        app = create_app()
        app.state.oidc_client = FakeOidcClient(
            OidcIdentity(
                subject="sub-2",
                username="stranger",
                email="stranger@example.com",
                groups=("some-other-group",),
                claims={},
            )
        )
        client = MiniClient(app)

        callback = self._start_oidc(client)
        response = client.get(callback, follow_redirects=False)

        self.assertEqual(response.status_code, 403)

    def test_sensitive_api_routes_are_protected_server_side(self):
        client = MiniClient(create_app())

        self.assertEqual(client.get("/api/schedule").status_code, 401)
        self.assertEqual(client.get("/api/status").status_code, 401)
        self.assertEqual(client.post("/api/check").status_code, 401)

    def test_logout_invalidates_session(self):
        app = create_app()
        app.state.oidc_client = FakeOidcClient(
            OidcIdentity(
                subject="sub-3",
                username="parent",
                email="parent@example.com",
                groups=("milo-webuntis-users",),
                claims={},
            )
        )
        client = MiniClient(app)
        client.get(self._start_oidc(client), follow_redirects=False)

        self.assertEqual(client.get("/api/me").status_code, 200)
        self.assertEqual(client.post("/api/logout").status_code, 200)
        self.assertEqual(client.get("/api/me").status_code, 401)

    def test_parent_password_login_stays_enabled_when_auth_is_required(self):
        app = create_app()
        service = app.state.service
        token, _invite = service.accounts.create_invitation(
            "parent@example.com",
            "tenant_1",
            datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc),
        )
        service.accept_parent_invitation(token, "mein.webuntis.user", "webuntis-pass")
        client = MiniClient(app)

        response = client.post(
            "/api/login",
            json={"username": "mein.webuntis.user", "password": "webuntis-pass"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "parent")

    def test_admin_password_fallback_is_disabled_when_auth_is_required(self):
        os.environ["MILO_AUTH_USERS"] = "admin=secret"
        client = MiniClient(create_app())

        response = client.post("/api/login", json={"username": "admin", "password": "secret"})

        self.assertEqual(response.status_code, 401)

    def _start_oidc(self, client: MiniClient) -> str:
        login = client.get("/auth/login?next=/app", follow_redirects=False)
        self.assertEqual(login.status_code, 303)
        state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
        return f"/auth/callback?code=ok&state={state}"


if __name__ == "__main__":
    unittest.main()

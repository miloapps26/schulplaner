from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


COOKIE_NAME = "milo_session"


def create_session_cookie(
    username: str,
    secret: str,
    now: int | None = None,
    role: str = "admin",
    account_id: str = "",
    groups: list[str] | None = None,
    email: str = "",
    auth_provider: str = "legacy",
    oidc_sub: str = "",
) -> str:
    issued_at = now or int(time.time())
    payload = {
        "u": username,
        "role": role,
        "sub": account_id,
        "iat": issued_at,
        "last": issued_at,
        "auth": auth_provider,
    }
    if groups:
        payload["groups"] = sorted({str(group) for group in groups if str(group)})
    if email:
        payload["email"] = email
    if oidc_sub:
        payload["oidc_sub"] = oidc_sub
    return create_signed_token(payload, secret)


def refresh_session_cookie(cookie_value: str, secret: str, now: int | None = None) -> str:
    payload = read_session_cookie(cookie_value, secret)
    if not payload:
        return ""
    payload["last"] = now or int(time.time())
    return create_signed_token(payload, secret)


def create_signed_token(payload: dict[str, Any], secret: str) -> str:
    payload_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_token = _b64(payload_text.encode("utf-8"))
    signature = _sign(payload_token, secret)
    return f"{payload_token}.{signature}"


def read_signed_token(cookie_value: str, secret: str) -> dict[str, Any] | None:
    return read_session_cookie(cookie_value, secret)


def read_session_cookie(cookie_value: str, secret: str) -> dict[str, Any] | None:
    if not cookie_value or "." not in cookie_value or not secret:
        return None
    payload_token, signature = cookie_value.rsplit(".", 1)
    expected = _sign(payload_token, secret)
    if not hmac.compare_digest(signature.encode("utf-8"), expected.encode("utf-8")):
        return None
    try:
        payload = json.loads(_unb64(payload_token).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def valid_session_user(
    cookie_value: str,
    secret: str,
    users: dict[str, str],
    idle_timeout_minutes: int,
    now: int | None = None,
) -> str | None:
    payload = valid_session_payload(cookie_value, secret, idle_timeout_minutes, now=now)
    if not payload:
        return None
    username = str(payload.get("u") or "")
    if username not in users:
        return None
    return username


def valid_session_payload(
    cookie_value: str,
    secret: str,
    idle_timeout_minutes: int,
    now: int | None = None,
) -> dict[str, Any] | None:
    payload = read_session_cookie(cookie_value, secret)
    if not payload:
        return None
    last_seen = _int(payload.get("last"))
    timestamp = now or int(time.time())
    if not last_seen or timestamp - last_seen > idle_timeout_minutes * 60:
        return None
    return payload


def credentials_valid(username: str, password: str, users: dict[str, str]) -> bool:
    expected = users.get(username)
    if expected is None:
        return False
    return hmac.compare_digest(password.encode("utf-8"), expected.encode("utf-8"))


def _sign(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64(digest)


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

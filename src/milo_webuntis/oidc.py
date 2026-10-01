from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests

from .config import OidcConfig


@dataclass(frozen=True)
class PkceChallenge:
    verifier: str
    challenge: str


@dataclass(frozen=True)
class OidcIdentity:
    subject: str
    username: str
    email: str
    groups: tuple[str, ...]
    claims: dict[str, Any]


class OidcClient:
    def __init__(self, config: OidcConfig, timeout_seconds: int = 10) -> None:
        self.config = config
        self.timeout_seconds = timeout_seconds
        self._metadata: dict[str, Any] | None = None

    def authorization_url(self, state: str, code_challenge: str, next_url: str = "") -> str:
        metadata = self.metadata()
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if next_url:
            params["next"] = next_url
        return f"{metadata['authorization_endpoint']}?{urlencode(params)}"

    def exchange_code(self, code: str, code_verifier: str) -> OidcIdentity:
        metadata = self.metadata()
        token_response = requests.post(
            str(metadata["token_endpoint"]),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.config.redirect_uri,
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "code_verifier": code_verifier,
            },
            headers={"Accept": "application/json"},
            timeout=self.timeout_seconds,
        )
        token_response.raise_for_status()
        token_payload = token_response.json()
        claims: dict[str, Any] = {}
        access_token = str(token_payload.get("access_token") or "")
        if access_token and metadata.get("userinfo_endpoint"):
            userinfo_response = requests.get(
                str(metadata["userinfo_endpoint"]),
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                timeout=self.timeout_seconds,
            )
            userinfo_response.raise_for_status()
            claims.update(userinfo_response.json())
        id_token = str(token_payload.get("id_token") or "")
        if id_token:
            claims = {**_decode_jwt_payload(id_token), **claims}
        return identity_from_claims(claims)

    def metadata(self) -> dict[str, Any]:
        if self._metadata is not None:
            return self._metadata
        response = requests.get(
            f"{self.config.issuer}/.well-known/openid-configuration",
            headers={"Accept": "application/json"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        metadata = response.json()
        if metadata.get("issuer", self.config.issuer).rstrip("/") != self.config.issuer.rstrip("/"):
            raise ValueError("OIDC issuer stimmt nicht mit der Konfiguration überein.")
        for key in ("authorization_endpoint", "token_endpoint"):
            if not metadata.get(key):
                raise ValueError(f"OIDC Metadata enthält keinen Wert für {key}.")
        self._metadata = metadata
        return metadata


def create_pkce_challenge() -> PkceChallenge:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return PkceChallenge(verifier=verifier, challenge=challenge)


def new_state() -> str:
    return secrets.token_urlsafe(32)


def identity_from_claims(claims: dict[str, Any]) -> OidcIdentity:
    subject = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip().lower()
    username = (
        str(claims.get("preferred_username") or "").strip()
        or str(claims.get("username") or "").strip()
        or email
        or subject
    )
    groups = _groups_from_claims(claims)
    if not subject:
        raise ValueError("OIDC Antwort enthält kein Subject.")
    return OidcIdentity(subject=subject, username=username, email=email, groups=groups, claims=claims)


def _groups_from_claims(claims: dict[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for key in ("groups", "ak_groups", "group", "https://schemas.goauthentik.io/groups"):
        raw = claims.get(key)
        if isinstance(raw, list):
            values.extend(str(item).strip() for item in raw if str(item).strip())
        elif isinstance(raw, str):
            values.extend(item.strip() for item in raw.replace(";", ",").split(",") if item.strip())
    return tuple(sorted(set(values)))


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    padding = "=" * ((4 - len(parts[1]) % 4) % 4)
    try:
        payload = base64.urlsafe_b64decode(parts[1] + padding)
        decoded = json.loads(payload.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}

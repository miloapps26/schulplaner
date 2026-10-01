from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 200_000


class AccountStore:
    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "accounts.json"

    def authenticate_parent(self, username: str, password: str) -> dict[str, Any] | None:
        parent = self.parent_by_login(username)
        if not parent or not parent.get("active", True):
            return None
        if not parent.get("password_hash"):
            return None
        if verify_password(password, str(parent.get("password_hash") or "")):
            return parent
        return None

    def parent_by_id(self, parent_id: str) -> dict[str, Any] | None:
        for parent in self._load().get("parents", []):
            if parent.get("id") == parent_id:
                return parent
        return None

    def parent_by_email(self, email: str) -> dict[str, Any] | None:
        normalized = normalize_email(email)
        for parent in self._load().get("parents", []):
            if normalize_email(parent.get("email")) == normalized:
                return parent
        return None

    def parent_by_login(self, username: str) -> dict[str, Any] | None:
        normalized_username = normalize_username(username)
        normalized_email = normalize_email(username)
        for parent in self._load().get("parents", []):
            if normalize_username(parent.get("username")) == normalized_username:
                return parent
            if normalize_email(parent.get("email")) == normalized_email:
                return parent
        return None

    def parent_by_oidc_identity(
        self,
        email: str = "",
        username: str = "",
        subject: str = "",
    ) -> dict[str, Any] | None:
        normalized_email = normalize_email(email)
        normalized_username = normalize_username(username)
        normalized_subject = str(subject or "").strip()
        for parent in self._load().get("parents", []):
            if normalized_subject and str(parent.get("oidc_sub") or "") == normalized_subject:
                return parent
            if normalized_email and normalize_email(parent.get("email")) == normalized_email:
                return parent
            if normalized_username and normalize_username(parent.get("username")) == normalized_username:
                return parent
        return None

    def ensure_oidc_parent(
        self,
        email: str,
        username: str,
        subject: str,
        tenant_ids: list[str],
        now: datetime,
    ) -> dict[str, Any]:
        payload = self._load()
        parents = payload.get("parents", [])
        normalized_email = normalize_email(email)
        clean_username = str(username or normalized_email).strip()
        parent = None
        for item in parents:
            if str(item.get("oidc_sub") or "") == str(subject or "").strip():
                parent = item
                break
            if normalized_email and normalize_email(item.get("email")) == normalized_email:
                parent = item
                break
        if parent is None:
            parent = {
                "id": _new_identifier("parent"),
                "email": normalized_email,
                "created_at": now.isoformat(),
            }
            parents.append(parent)
        existing_tenant_ids = [str(item) for item in parent.get("tenant_ids", []) if item]
        for tenant_id in tenant_ids:
            if tenant_id and tenant_id not in existing_tenant_ids:
                existing_tenant_ids.append(tenant_id)
        parent.update(
            {
                "email": normalized_email or normalize_email(parent.get("email")),
                "username": clean_username or str(parent.get("username") or ""),
                "oidc_sub": str(subject or "").strip(),
                "tenant_ids": existing_tenant_ids,
                "active": True,
                "updated_at": now.isoformat(),
            }
        )
        payload["parents"] = parents
        self._save(payload)
        return parent

    def parents(self) -> list[dict[str, Any]]:
        return self._load().get("parents", [])

    def invitations(self) -> list[dict[str, Any]]:
        return self._load().get("invitations", [])

    def create_invitation(
        self,
        email: str,
        tenant_id: str,
        now: datetime,
        valid_hours: int = 72,
    ) -> tuple[str, dict[str, Any]]:
        payload = self._load()
        normalized = normalize_email(email)
        token = secrets.token_urlsafe(32)
        invitation = {
            "id": _new_identifier("invite"),
            "email": normalized,
            "tenant_id": tenant_id,
            "token_hash": token_digest(token),
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=valid_hours)).isoformat(),
            "accepted_at": "",
            "sent_at": "",
        }
        payload["invitations"] = [
            item
            for item in payload.get("invitations", [])
            if not _same_pending_invite(item, normalized, tenant_id, now)
        ]
        payload["invitations"].append(invitation)
        self._save(payload)
        return token, invitation

    def mark_invitation_sent(self, invite_id: str, now: datetime) -> None:
        payload = self._load()
        for invitation in payload.get("invitations", []):
            if invitation.get("id") == invite_id:
                invitation["sent_at"] = now.isoformat()
                break
        self._save(payload)

    def invitation_for_token(self, token: str, now: datetime) -> dict[str, Any] | None:
        digest = token_digest(token)
        for invitation in self._load().get("invitations", []):
            if not hmac.compare_digest(str(invitation.get("token_hash") or ""), digest):
                continue
            if invitation.get("accepted_at"):
                return None
            expires_at = parse_datetime(invitation.get("expires_at"))
            if not expires_at or expires_at < now:
                return None
            return invitation
        return None

    def accept_invitation(
        self,
        token: str,
        username: str,
        password: str,
        now: datetime,
        store_password: bool = True,
    ) -> dict[str, Any]:
        payload = self._load()
        digest = token_digest(token)
        invitation = None
        for item in payload.get("invitations", []):
            if hmac.compare_digest(str(item.get("token_hash") or ""), digest):
                invitation = item
                break
        if not invitation:
            raise ValueError("Einladung nicht gefunden.")
        if invitation.get("accepted_at"):
            raise ValueError("Einladung wurde bereits verwendet.")
        expires_at = parse_datetime(invitation.get("expires_at"))
        if not expires_at or expires_at < now:
            raise ValueError("Einladung ist abgelaufen.")

        email = normalize_email(invitation.get("email"))
        clean_username = str(username or "").strip()
        if not clean_username:
            raise ValueError("Benutzername ist erforderlich.")
        if any(
            normalize_username(item.get("username")) == normalize_username(clean_username)
            and normalize_email(item.get("email")) != email
            for item in payload.get("parents", [])
        ):
            raise ValueError("Benutzername ist bereits vergeben.")
        tenant_id = str(invitation.get("tenant_id") or "")
        parents = payload.get("parents", [])
        parent = next((item for item in parents if normalize_email(item.get("email")) == email), None)
        if parent is None:
            parent = {
                "id": _new_identifier("parent"),
                "email": email,
                "tenant_ids": [],
                "active": True,
                "created_at": now.isoformat(),
            }
            parents.append(parent)
        tenant_ids = [str(item) for item in parent.get("tenant_ids", []) if item]
        if tenant_id and tenant_id not in tenant_ids:
            tenant_ids.append(tenant_id)
        parent.update(
            {
                "email": email,
                "username": clean_username,
                "tenant_ids": tenant_ids,
                "active": True,
                "updated_at": now.isoformat(),
            }
        )
        if store_password:
            parent["password_hash"] = hash_password(password)
        invitation["accepted_at"] = now.isoformat()
        payload["parents"] = parents
        self._save(payload)
        return parent

    def update_parent_login(
        self,
        parent_id: str,
        username: str | None = None,
        password: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        payload = self._load()
        parents = payload.get("parents", [])
        parent = next((item for item in parents if item.get("id") == parent_id), None)
        if parent is None:
            raise ValueError("Elternzugang nicht gefunden.")

        clean_username = str(username or parent.get("username") or "").strip()
        if not clean_username:
            raise ValueError("Benutzername ist erforderlich.")
        if any(
            item.get("id") != parent_id
            and normalize_username(item.get("username")) == normalize_username(clean_username)
            for item in parents
        ):
            raise ValueError("Benutzername ist bereits vergeben.")

        parent["username"] = clean_username
        if password:
            parent["password_hash"] = hash_password(password)
        parent["updated_at"] = (now or datetime.now()).isoformat()
        payload["parents"] = parents
        self._save(payload)
        return parent

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"parents": [], "invitations": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"parents": [], "invitations": []}
        return {
            "parents": payload.get("parents") if isinstance(payload.get("parents"), list) else [],
            "invitations": payload.get("invitations") if isinstance(payload.get("invitations"), list) else [],
        }

    def _save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "parents": payload.get("parents") if isinstance(payload.get("parents"), list) else [],
                    "invitations": payload.get("invitations") if isinstance(payload.get("invitations"), list) else [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return "$".join(
        [
            PASSWORD_SCHEME,
            str(PASSWORD_ITERATIONS),
            _b64(salt),
            _b64(digest),
        ]
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations_text, salt_text, digest_text = stored_hash.split("$", 3)
        iterations = int(iterations_text)
    except ValueError:
        return False
    if scheme != PASSWORD_SCHEME:
        return False
    salt = _unb64(salt_text)
    expected = _unb64(digest_text)
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalize_email(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_username(value: Any) -> str:
    return str(value or "").strip().lower()


def parse_datetime(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def _same_pending_invite(
    invitation: dict[str, Any],
    email: str,
    tenant_id: str,
    now: datetime,
) -> bool:
    if normalize_email(invitation.get("email")) != email:
        return False
    if str(invitation.get("tenant_id") or "") != tenant_id:
        return False
    if invitation.get("accepted_at"):
        return False
    expires_at = parse_datetime(invitation.get("expires_at"))
    return bool(expires_at and expires_at >= now)


def _new_identifier(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(9).replace('-', '').replace('_', '')}"


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)

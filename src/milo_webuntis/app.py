from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status as http_status
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles

from .auth import (
    COOKIE_NAME,
    create_session_cookie,
    create_signed_token,
    credentials_valid,
    refresh_session_cookie,
    read_signed_token,
    valid_session_payload,
)
from .config import load_config
from . import __version__
from .oidc import OidcClient, OidcIdentity, create_pkce_challenge, new_state
from .service import MonitorService, PollingWorker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
security = HTTPBasic(auto_error=False)
OIDC_STATE_COOKIE = "milo_oidc_state"


class SettingsPayload(BaseModel):
    poll_interval_minutes: int | None = Field(default=None, ge=1, le=1440)
    transit_poll_interval_minutes: int | None = Field(default=None, ge=1, le=1440)
    email_recipients: str | None = None


class ManualHomeworkPayload(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    subject: str | None = Field(default=None, max_length=120)
    due_date: str | None = None


class HomeworkCompletionPayload(BaseModel):
    completed: bool = True


class ManualLessonPayload(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    recurring: bool = True
    weekday: int | None = Field(default=None, ge=0, le=4)
    date: str | None = None
    start: str = Field(min_length=4, max_length=5)
    end: str = Field(min_length=4, max_length=5)
    room: str | None = Field(default=None, max_length=120)
    note: str | None = Field(default=None, max_length=500)


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=500)


class SetupAcceptPayload(BaseModel):
    token: str = Field(min_length=20, max_length=500)
    username: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=1, max_length=500)


class TenantDisplayPayload(BaseModel):
    student_first_name: str | None = Field(default=None, max_length=120)
    student_last_name: str | None = Field(default=None, max_length=120)
    student_last_initial: str | None = Field(default=None, max_length=120)
    school: str | None = Field(default=None, max_length=200)
    class_name: str | None = Field(default=None, max_length=80)


class TenantWebUntisPayload(BaseModel):
    server: str | None = Field(default=None, max_length=300)
    school: str | None = Field(default=None, max_length=200)
    username: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, max_length=500)
    app_secret: str | None = Field(default=None, max_length=500)
    school_number: str | None = Field(default=None, max_length=80)
    element_type: int | None = Field(default=None, ge=1, le=5)
    element_id: int | None = Field(default=None)
    class_name: str | None = Field(default=None, max_length=120)


class TenantEmailPayload(BaseModel):
    recipients: str | None = None


class TransitPayload(BaseModel):
    outbound_origins: str | None = Field(default=None, max_length=2000)
    outbound_destinations: str | None = Field(default=None, max_length=2000)
    return_origins: str | None = Field(default=None, max_length=2000)
    return_destinations: str | None = Field(default=None, max_length=2000)
    arrive_min_before: int | None = Field(default=None, ge=0, le=180)
    arrive_window_minutes: int | None = Field(default=None, ge=1, le=360)
    depart_min_after: int | None = Field(default=None, ge=0, le=180)
    depart_window_minutes: int | None = Field(default=None, ge=1, le=360)
    day_start: str | None = Field(default=None, max_length=5)
    day_end: str | None = Field(default=None, max_length=5)
    direct_connections_only: bool | None = None


class TenantPayload(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    parent_email: str | None = Field(default=None, max_length=200)
    active: bool = True
    display: TenantDisplayPayload = Field(default_factory=TenantDisplayPayload)
    webuntis: TenantWebUntisPayload = Field(default_factory=TenantWebUntisPayload)
    email: TenantEmailPayload = Field(default_factory=TenantEmailPayload)


class ParentProfilePayload(BaseModel):
    webuntis: TenantWebUntisPayload = Field(default_factory=TenantWebUntisPayload)
    transit: TransitPayload = Field(default_factory=TransitPayload)


def payload_dict(payload: BaseModel) -> dict:
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return payload.dict()


def create_app() -> FastAPI:
    config = load_config(PROJECT_ROOT)
    service = MonitorService(config)
    worker = PollingWorker(service)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        worker.start()
        try:
            yield
        finally:
            worker.stop()

    app = FastAPI(title="Schulplaner", lifespan=lifespan)
    app.state.service = service
    app.state.worker = worker
    app.state.oidc_client = OidcClient(config.auth.oidc) if config.auth.oidc.enabled else None
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.allowed_hosts)

    @app.middleware("http")
    async def security_headers(request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    def set_auth_cookie(
        response: Response,
        username: str,
        role: str = "admin",
        account_id: str = "",
        groups: list[str] | None = None,
        email: str = "",
        auth_provider: str = "legacy",
        oidc_sub: str = "",
    ) -> None:
        response.set_cookie(
            COOKIE_NAME,
            create_session_cookie(
                username,
                service.config.auth.secret,
                role=role,
                account_id=account_id,
                groups=groups,
                email=email,
                auth_provider=auth_provider,
                oidc_sub=oidc_sub,
            ),
            max_age=service.config.auth.idle_timeout_minutes * 60,
            httponly=True,
            secure=service.config.auth.cookie_secure,
            samesite="strict",
        )

    def clear_auth_cookie(response: Response) -> None:
        response.delete_cookie(COOKIE_NAME)
        response.delete_cookie(OIDC_STATE_COOKIE)

    def set_oidc_state_cookie(response: Response, state: str, verifier: str, next_url: str) -> None:
        response.set_cookie(
            OIDC_STATE_COOKIE,
            create_signed_token(
                {
                    "state": state,
                    "verifier": verifier,
                    "next": next_url if next_url.startswith("/") else "/app",
                },
                service.config.auth.secret,
            ),
            max_age=10 * 60,
            httponly=True,
            secure=service.config.auth.cookie_secure,
            samesite="lax",
        )

    def role_for_oidc_groups(groups: tuple[str, ...]) -> str:
        group_set = set(groups)
        if service.config.auth.oidc.admin_group in group_set:
            return "admin"
        if service.config.auth.oidc.user_group in group_set:
            return "parent"
        return ""

    def principal_from_oidc_identity(identity: OidcIdentity) -> dict:
        role = role_for_oidc_groups(identity.groups)
        if not role:
            raise PermissionError("Dieser Benutzer ist nicht für Schulplaner freigegeben.")
        if role == "admin":
            return {
                "role": "admin",
                "username": identity.username,
                "account_id": "",
                "tenant_ids": [tenant.id for tenant in service.config.tenants],
                "groups": list(identity.groups),
                "email": identity.email,
                "oidc_sub": identity.subject,
            }
        parent = service.parent_by_oidc_identity(identity.email, identity.username, identity.subject)
        if not parent:
            raise PermissionError("Für diesen Milo-Zugang ist noch kein Schulplaner-Profil hinterlegt.")
        return {
            "role": "parent",
            "username": str(parent.get("username") or identity.username),
            "account_id": str(parent.get("id") or ""),
            "tenant_ids": [str(item) for item in parent.get("tenant_ids", []) if item],
            "groups": list(identity.groups),
            "email": identity.email,
            "oidc_sub": identity.subject,
        }

    def session_principal(
        request: Request,
        response: Response | None = None,
        credentials: HTTPBasicCredentials | None = None,
    ) -> dict | None:
        cookie_value = request.cookies.get(COOKIE_NAME, "")
        payload = valid_session_payload(
            cookie_value,
            service.config.auth.secret,
            service.config.auth.idle_timeout_minutes,
        )
        if payload:
            role = str(payload.get("role") or "admin")
            username = str(payload.get("u") or "")
            account_id = str(payload.get("sub") or "")
            auth_provider = str(payload.get("auth") or "legacy")
            groups = [str(item) for item in payload.get("groups", []) if item] if isinstance(payload.get("groups"), list) else []
            principal = None
            if (
                role == "admin"
                and auth_provider == "oidc"
                and service.config.auth.oidc.admin_group in groups
            ):
                principal = {
                    "role": "admin",
                    "username": username,
                    "account_id": "",
                    "tenant_ids": [tenant.id for tenant in service.config.tenants],
                    "groups": groups,
                    "email": str(payload.get("email") or ""),
                }
            elif (
                role == "admin"
                and auth_provider == "legacy"
                and not service.config.auth.required
                and username in service.config.auth.users
            ):
                principal = {
                    "role": "admin",
                    "username": username,
                    "account_id": "",
                    "tenant_ids": [tenant.id for tenant in service.config.tenants],
                }
            elif role == "parent":
                parent = service.parent_by_id(account_id)
                if parent and parent.get("active", True):
                    principal = {
                        "role": "parent",
                        "username": username,
                        "account_id": account_id,
                        "tenant_ids": [str(item) for item in parent.get("tenant_ids", []) if item],
                        "groups": groups,
                        "email": str(payload.get("email") or parent.get("email") or ""),
                    }
            if not principal:
                return None
            if response:
                refreshed = refresh_session_cookie(cookie_value, service.config.auth.secret)
                if refreshed:
                    response.set_cookie(
                        COOKIE_NAME,
                        refreshed,
                        max_age=service.config.auth.idle_timeout_minutes * 60,
                        httponly=True,
                        secure=service.config.auth.cookie_secure,
                        samesite="strict",
                    )
            return principal

        if (
            credentials
            and not service.config.auth.required
            and credentials_valid(
            credentials.username,
            credentials.password,
            service.config.auth.users,
            )
        ):
            return {
                "role": "admin",
                "username": credentials.username,
                "account_id": "",
                "tenant_ids": [tenant.id for tenant in service.config.tenants],
            }

        return None

    def has_valid_admin(
        request: Request,
        response: Response | None = None,
        credentials: HTTPBasicCredentials | None = None,
    ) -> bool:
        principal = session_principal(request, response, credentials)
        return bool(principal and principal.get("role") == "admin")

    def require_admin(
        request: Request,
        response: Response,
        credentials: HTTPBasicCredentials | None = Depends(security),
    ) -> None:
        if not service.config.auth.users and not service.config.auth.oidc.enabled:
            raise HTTPException(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin-Login ist noch nicht konfiguriert.",
            )
        if not has_valid_admin(request, response, credentials):
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Benutzername oder Passwort falsch.",
                headers={"WWW-Authenticate": "Basic"},
            )

    def require_schedule_access(
        request: Request,
        response: Response,
        tenant_id: str | None = None,
        credentials: HTTPBasicCredentials | None = Depends(security),
    ) -> dict:
        principal = session_principal(request, response, credentials)
        if principal:
            try:
                tenant = tenant_for_principal(principal, tenant_id)
            except PermissionError as exc:
                raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
            except ValueError as exc:
                raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
            if principal.get("role") != "parent":
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Bitte als Elternteil anmelden.",
                )
            if not tenant.active:
                raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Profil nicht aktiv.")
            return principal
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Bitte anmelden.",
            headers={"WWW-Authenticate": "Basic"},
        )

    def tenant_for_principal(principal: dict, tenant_id: str | None = None):
        if principal.get("role") == "admin":
            return service.tenant(tenant_id)
        parent = service.parent_by_id(str(principal.get("account_id") or ""))
        if not parent:
            raise ValueError("Elternzugang nicht gefunden.")
        return service.tenant_for_parent(parent, tenant_id)

    static_dir = PROJECT_ROOT / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    if config.milo_ci_dir.exists():
        app.mount("/ci", StaticFiles(directory=str(config.milo_ci_dir)), name="ci")

    @app.get("/")
    def root() -> RedirectResponse:
        return RedirectResponse("/app", status_code=http_status.HTTP_303_SEE_OTHER)

    @app.get("/api/version")
    def version() -> dict:
        return {"version": __version__}

    @app.get("/app")
    def index(
        request: Request,
        response: Response,
        credentials: HTTPBasicCredentials | None = Depends(security),
    ):
        principal = session_principal(request, response, credentials)
        if not principal:
            return RedirectResponse("/login?next=/app", status_code=http_status.HTTP_303_SEE_OTHER)
        if principal.get("role") == "admin":
            return RedirectResponse("/admin", status_code=http_status.HTTP_303_SEE_OTHER)
        return FileResponse(PROJECT_ROOT / "static" / "index.html")

    @app.get("/t/{tenant_id}")
    def tenant_index(tenant_id: str) -> RedirectResponse:
        return RedirectResponse("/app", status_code=http_status.HTTP_303_SEE_OTHER)

    @app.get("/login")
    def login_page() -> FileResponse:
        return FileResponse(PROJECT_ROOT / "static" / "login.html")

    @app.get("/api/auth/mode")
    def auth_mode() -> dict:
        return {
            "oidc_enabled": service.config.auth.oidc.enabled,
            "legacy_enabled": service.config.auth.legacy_enabled,
            "parent_login_enabled": service.config.auth.parent_password_login_enabled,
            "auth_required": service.config.auth.required,
        }

    @app.get("/auth/login")
    def oidc_login(response: Response, next: str = "/app") -> RedirectResponse:
        client = app.state.oidc_client
        if not client:
            return RedirectResponse(f"/login?next={next}", status_code=http_status.HTTP_303_SEE_OTHER)
        state = new_state()
        pkce = create_pkce_challenge()
        redirect = RedirectResponse(
            client.authorization_url(state, pkce.challenge, next),
            status_code=http_status.HTTP_303_SEE_OTHER,
        )
        set_oidc_state_cookie(redirect, state, pkce.verifier, next)
        return redirect

    @app.get("/auth/callback")
    def oidc_callback(request: Request, code: str = "", state: str = "") -> RedirectResponse:
        client = app.state.oidc_client
        state_payload = read_signed_token(
            request.cookies.get(OIDC_STATE_COOKIE, ""),
            service.config.auth.secret,
        )
        if not client or not code or not state_payload or state_payload.get("state") != state:
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="OIDC Anmeldung ungültig.")
        try:
            identity = client.exchange_code(code, str(state_payload.get("verifier") or ""))
            principal = principal_from_oidc_identity(identity)
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        next_url = str(state_payload.get("next") or "/app")
        if principal["role"] == "admin" and next_url == "/app":
            next_url = "/admin"
        redirect = RedirectResponse(next_url if next_url.startswith("/") else "/app", status_code=http_status.HTTP_303_SEE_OTHER)
        set_auth_cookie(
            redirect,
            str(principal.get("username") or identity.username),
            role=str(principal.get("role") or "parent"),
            account_id=str(principal.get("account_id") or ""),
            groups=list(identity.groups),
            email=identity.email,
            auth_provider="oidc",
            oidc_sub=identity.subject,
        )
        redirect.delete_cookie(OIDC_STATE_COOKIE)
        return redirect

    @app.get("/setup")
    def setup_page() -> FileResponse:
        return FileResponse(PROJECT_ROOT / "static" / "setup.html")

    @app.post("/api/login")
    def login(payload: LoginPayload, response: Response) -> dict:
        if (
            not service.config.auth.required
            and credentials_valid(payload.username, payload.password, service.config.auth.users)
        ):
            set_auth_cookie(response, payload.username, role="admin")
            return {"status": "ok", "role": "admin", "next": "/admin"}
        parent = service.parent_by_login(payload.username, payload.password)
        if parent:
            set_auth_cookie(
                response,
                str(parent.get("username") or parent.get("email") or payload.username),
                role="parent",
                account_id=str(parent.get("id") or ""),
            )
            return {"status": "ok", "role": "parent", "next": "/app"}
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Benutzername oder Passwort falsch.",
        )

    @app.post("/api/logout")
    def logout(response: Response) -> dict:
        clear_auth_cookie(response)
        return {"status": "ok"}

    @app.get("/admin")
    def admin(
        request: Request,
        response: Response,
        credentials: HTTPBasicCredentials | None = Depends(security),
    ):
        if not service.config.auth.users and not service.config.auth.oidc.enabled:
            raise HTTPException(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin-Login ist noch nicht konfiguriert.",
            )
        if not has_valid_admin(request, response, credentials):
            return RedirectResponse("/login?next=/admin", status_code=http_status.HTTP_303_SEE_OTHER)
        return FileResponse(PROJECT_ROOT / "static" / "admin.html")

    @app.get("/api/me")
    def me(
        request: Request,
        response: Response,
        credentials: HTTPBasicCredentials | None = Depends(security),
    ) -> dict:
        principal = session_principal(request, response, credentials)
        if not principal:
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Bitte anmelden.")
        return {
            "role": principal.get("role"),
            "username": principal.get("username"),
            "tenant_ids": principal.get("tenant_ids", []),
        }

    @app.get("/api/setup/context")
    def setup_context(token: str) -> dict:
        try:
            return service.setup_context(token)
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.post("/api/setup/accept")
    def setup_accept(payload: SetupAcceptPayload, response: Response) -> dict:
        try:
            profile = service.accept_parent_invitation(payload.token, payload.username, payload.password)
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        parent = profile.get("parent", {})
        set_auth_cookie(
            response,
            str(parent.get("username") or payload.username),
            role="parent",
            account_id=str(parent.get("id") or ""),
        )
        return {"status": "ok", "next": "/app"}

    @app.get("/api/parent/profile")
    def parent_profile(
        request: Request,
        response: Response,
        tenant_id: str | None = None,
        credentials: HTTPBasicCredentials | None = Depends(security),
    ) -> dict:
        principal = session_principal(request, response, credentials)
        if not principal or principal.get("role") != "parent":
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Bitte als Elternteil anmelden.")
        try:
            return service.parent_profile(str(principal.get("account_id") or ""), tenant_id)
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.put("/api/parent/profile")
    def update_parent_profile(
        payload: ParentProfilePayload,
        request: Request,
        response: Response,
        tenant_id: str | None = None,
        credentials: HTTPBasicCredentials | None = Depends(security),
    ) -> dict:
        principal = session_principal(request, response, credentials)
        if not principal or principal.get("role") != "parent":
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Bitte als Elternteil anmelden.")
        try:
            return service.update_parent_profile(
                str(principal.get("account_id") or ""),
                payload_dict(payload),
                tenant_id,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/api/transit/stops")
    def transit_stops(
        q: str = "",
        limit: int = 8,
        principal: dict = Depends(require_schedule_access),
    ) -> dict:
        _tenant = tenant_for_principal(principal)
        try:
            return service.transit_stop_suggestions(q, limit=max(1, min(limit, 20)))
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/api/status", dependencies=[Depends(require_admin)])
    def status(tenant_id: str | None = None) -> dict:
        try:
            return service.status(tenant_id)
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/api/tenants", dependencies=[Depends(require_admin)])
    def tenants() -> dict:
        return service.tenant_admin()

    @app.post("/api/tenants", dependencies=[Depends(require_admin)])
    def create_tenant(payload: TenantPayload) -> dict:
        return service.create_tenant(payload_dict(payload))

    @app.put("/api/tenants/{tenant_id}", dependencies=[Depends(require_admin)])
    def update_tenant(tenant_id: str, payload: TenantPayload) -> dict:
        try:
            return service.update_tenant(tenant_id, payload_dict(payload))
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post("/api/tenants/{tenant_id}/invite", dependencies=[Depends(require_admin)])
    def invite_parent(tenant_id: str) -> dict:
        try:
            return service.create_parent_invitation(tenant_id)
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/api/schedule")
    def schedule(principal: dict = Depends(require_schedule_access)) -> dict:
        tenant = tenant_for_principal(principal)
        return service.schedule(tenant.id)

    @app.get("/api/t/{tenant_id}/schedule")
    def tenant_schedule(tenant_id: str, principal: dict = Depends(require_schedule_access)) -> dict:
        try:
            tenant = tenant_for_principal(principal, tenant_id)
            return service.schedule(tenant.id)
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/api/transit")
    def transit(
        date: str | None = None,
        refresh: bool = False,
        full: bool = False,
        principal: dict = Depends(require_schedule_access),
    ) -> dict:
        tenant = tenant_for_principal(principal)
        try:
            target_date = _date_from_query(date)
            return service.transit(
                target_date,
                tenant.id,
                force_refresh=refresh,
                include_full_day=full,
            )
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/api/t/{tenant_id}/transit")
    def tenant_transit(
        tenant_id: str,
        date: str | None = None,
        refresh: bool = False,
        full: bool = False,
        principal: dict = Depends(require_schedule_access),
    ) -> dict:
        try:
            tenant = tenant_for_principal(principal, tenant_id)
            target_date = _date_from_query(date)
            return service.transit(
                target_date,
                tenant.id,
                force_refresh=refresh,
                include_full_day=full,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/api/homework")
    def homework(principal: dict = Depends(require_schedule_access)) -> dict:
        tenant = tenant_for_principal(principal)
        return service.homework(tenant.id)

    @app.get("/api/exams")
    def exams(refresh: bool = False, principal: dict = Depends(require_schedule_access)) -> dict:
        tenant = tenant_for_principal(principal)
        return service.exams(tenant.id, force_refresh=refresh)

    @app.get("/api/t/{tenant_id}/exams")
    def tenant_exams(
        tenant_id: str,
        refresh: bool = False,
        principal: dict = Depends(require_schedule_access),
    ) -> dict:
        try:
            tenant = tenant_for_principal(principal, tenant_id)
            return service.exams(tenant.id, force_refresh=refresh)
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/api/t/{tenant_id}/homework")
    def tenant_homework(tenant_id: str, principal: dict = Depends(require_schedule_access)) -> dict:
        try:
            tenant = tenant_for_principal(principal, tenant_id)
            return service.homework(tenant.id)
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/api/manual-lessons")
    def manual_lessons(principal: dict = Depends(require_schedule_access)) -> dict:
        tenant = tenant_for_principal(principal)
        return service.manual_lessons(tenant.id)

    @app.get("/api/t/{tenant_id}/manual-lessons")
    def tenant_manual_lessons(tenant_id: str, principal: dict = Depends(require_schedule_access)) -> dict:
        try:
            tenant = tenant_for_principal(principal, tenant_id)
            return service.manual_lessons(tenant.id)
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post("/api/manual-lessons")
    def add_manual_lesson(payload: ManualLessonPayload, principal: dict = Depends(require_schedule_access)) -> dict:
        tenant = tenant_for_principal(principal)
        try:
            return service.add_manual_lesson(payload_dict(payload), tenant.id)
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.post("/api/t/{tenant_id}/manual-lessons")
    def add_tenant_manual_lesson(
        tenant_id: str,
        payload: ManualLessonPayload,
        principal: dict = Depends(require_schedule_access),
    ) -> dict:
        try:
            tenant = tenant_for_principal(principal, tenant_id)
            return service.add_manual_lesson(payload_dict(payload), tenant.id)
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    @app.delete("/api/manual-lessons/{manual_lesson_id}")
    def delete_manual_lesson(manual_lesson_id: str, principal: dict = Depends(require_schedule_access)) -> dict:
        tenant = tenant_for_principal(principal)
        try:
            return service.delete_manual_lesson(manual_lesson_id, tenant.id)
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.delete("/api/t/{tenant_id}/manual-lessons/{manual_lesson_id}")
    def delete_tenant_manual_lesson(
        tenant_id: str,
        manual_lesson_id: str,
        principal: dict = Depends(require_schedule_access),
    ) -> dict:
        try:
            tenant = tenant_for_principal(principal, tenant_id)
            return service.delete_manual_lesson(manual_lesson_id, tenant.id)
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    @app.post("/api/homework/manual")
    def add_manual_homework(payload: ManualHomeworkPayload, principal: dict = Depends(require_schedule_access)) -> dict:
        tenant = tenant_for_principal(principal)
        try:
            return service.add_manual_homework(
                text=payload.text,
                subject=payload.subject,
                due_date=payload.due_date,
                tenant_id=tenant.id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.post("/api/t/{tenant_id}/homework/manual")
    def add_tenant_manual_homework(
        tenant_id: str,
        payload: ManualHomeworkPayload,
        principal: dict = Depends(require_schedule_access),
    ) -> dict:
        try:
            tenant = tenant_for_principal(principal, tenant_id)
            return service.add_manual_homework(
                text=payload.text,
                subject=payload.subject,
                due_date=payload.due_date,
                tenant_id=tenant.id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    @app.post("/api/homework/{homework_id}/complete")
    def complete_homework(
        homework_id: str,
        payload: HomeworkCompletionPayload,
        principal: dict = Depends(require_schedule_access),
    ) -> dict:
        tenant = tenant_for_principal(principal)
        return service.set_homework_completed(homework_id, completed=payload.completed, tenant_id=tenant.id)

    @app.post("/api/t/{tenant_id}/homework/{homework_id}/complete")
    def complete_tenant_homework(
        tenant_id: str,
        homework_id: str,
        payload: HomeworkCompletionPayload,
        principal: dict = Depends(require_schedule_access),
    ) -> dict:
        try:
            tenant = tenant_for_principal(principal, tenant_id)
            return service.set_homework_completed(homework_id, completed=payload.completed, tenant_id=tenant.id)
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.delete("/api/homework/{homework_id}")
    def delete_homework(homework_id: str, principal: dict = Depends(require_schedule_access)) -> dict:
        tenant = tenant_for_principal(principal)
        try:
            return service.delete_manual_homework(homework_id, tenant_id=tenant.id)
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.delete("/api/t/{tenant_id}/homework/{homework_id}")
    def delete_tenant_homework(
        tenant_id: str,
        homework_id: str,
        principal: dict = Depends(require_schedule_access),
    ) -> dict:
        try:
            tenant = tenant_for_principal(principal, tenant_id)
            return service.delete_manual_homework(homework_id, tenant_id=tenant.id)
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    @app.get("/api/runs", dependencies=[Depends(require_admin)])
    def runs(
        limit: int = Query(default=25, ge=1, le=100),
        tenant_id: str | None = None,
    ) -> dict:
        try:
            return {"runs": service.store_for(tenant_id).runs(limit=limit)}
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post("/api/check", dependencies=[Depends(require_admin)])
    def check(force_notify: bool = False, tenant_id: str | None = None) -> dict:
        try:
            return service.run_once(force_notify=force_notify, tenant_id=tenant_id).__dict__
        except ValueError as exc:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post("/api/settings", dependencies=[Depends(require_admin)])
    def settings(payload: SettingsPayload, tenant_id: str | None = None) -> dict:
        return service.update_settings(
            poll_interval_minutes=payload.poll_interval_minutes,
            transit_poll_interval_minutes=payload.transit_poll_interval_minutes,
            email_recipients=payload.email_recipients,
            tenant_id=tenant_id,
        )

    return app


def _date_from_query(value: str | None):
    if not value:
        return None
    from datetime import date as date_class

    try:
        return date_class.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Datum muss im Format JJJJ-MM-TT angegeben werden.") from exc


app = create_app()


if __name__ == "__main__":
    runtime_config = load_config(PROJECT_ROOT)
    uvicorn.run(
        "milo_webuntis.app:app",
        host=runtime_config.app_host,
        port=runtime_config.app_port,
        reload=False,
    )

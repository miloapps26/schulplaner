from __future__ import annotations

import json
import os
import hashlib
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int(value: str | None, default: int) -> int:
    try:
        return int(value or default)
    except ValueError:
        return default


def _float(value: str | None, default: float) -> float:
    try:
        return float(value or default)
    except ValueError:
        return default


def _list(value: str | None) -> list[str]:
    if not value:
        return []
    normalized = value.replace(";", ",").replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _transit_stop_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value:
        return []
    normalized = str(value).replace(";", "\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def _allowed_hosts(value: str | None) -> list[str]:
    hosts = _list(value)
    if not hosts or "*" in hosts:
        return hosts or ["*"]

    for local_host in ("127.0.0.1", "localhost"):
        if local_host not in hosts:
            hosts.append(local_host)
    return hosts


def _auth_users(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    users: dict[str, str] = {}
    for raw_item in value.replace("\n", ";").split(";"):
        item = raw_item.strip()
        if not item or "=" not in item:
            continue
        username, password = item.split("=", 1)
        username = username.strip()
        password = password.strip()
        if username and password:
            users[username] = password
    return users


def _resolve_path(root: Path, value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path


def _opaque_public_id(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:18]
    return f"view_{digest}"


@dataclass(frozen=True)
class WebUntisConfig:
    server: str
    school: str
    username: str
    password: str
    app_secret: str
    school_number: str
    element_type: int
    element_id: int | None
    class_name: str

    @property
    def missing_fields(self) -> list[str]:
        missing = []
        for key, value in {
            "WEBUNTIS_SERVER": self.server,
            "WEBUNTIS_SCHOOL": self.school,
            "WEBUNTIS_USERNAME": self.username,
        }.items():
            if not value:
                missing.append(key)
        if not self.password and not self.app_secret:
            missing.append("WEBUNTIS_PASSWORD oder WEBUNTIS_APP_SECRET")
        if not self.class_name and self.element_id is None:
            missing.append("WEBUNTIS_CLASS_NAME oder WEBUNTIS_ELEMENT_ID")
        return missing

    @property
    def is_complete(self) -> bool:
        return not self.missing_fields


@dataclass(frozen=True)
class EmailConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str
    reply_to: str
    recipients: list[str]
    use_tls: bool

    @property
    def enabled(self) -> bool:
        has_auth = not self.username or bool(self.password)
        return bool(self.host and self.sender and self.recipients and has_auth)


@dataclass(frozen=True)
class TwilioConfig:
    account_sid: str
    auth_token: str
    whatsapp_from: str
    recipients: list[str]

    @property
    def enabled(self) -> bool:
        return bool(
            self.account_sid
            and self.auth_token
            and self.whatsapp_from
            and self.recipients
        )


@dataclass(frozen=True)
class OidcConfig:
    issuer: str
    client_id: str
    client_secret: str
    redirect_uri: str
    admin_group: str
    user_group: str
    scopes: tuple[str, ...]

    @property
    def enabled(self) -> bool:
        return bool(self.issuer and self.client_id and self.client_secret and self.redirect_uri)


@dataclass(frozen=True)
class AuthConfig:
    required: bool
    users: dict[str, str]
    secret: str
    cookie_secure: bool
    idle_timeout_minutes: int
    oidc: OidcConfig

    @property
    def enabled(self) -> bool:
        return self.required or self.oidc.enabled or bool(self.users)

    @property
    def legacy_enabled(self) -> bool:
        return bool(self.users) and not self.required

    @property
    def parent_password_login_enabled(self) -> bool:
        return True


@dataclass(frozen=True)
class TransitSettings:
    outbound_origins: tuple[str, ...]
    outbound_destinations: tuple[str, ...]
    return_origins: tuple[str, ...]
    return_destinations: tuple[str, ...]
    arrive_min_before: int
    arrive_window_minutes: int
    depart_min_after: int
    depart_window_minutes: int
    day_start: str
    day_end: str
    direct_connections_only: bool = False

    @property
    def enabled(self) -> bool:
        return bool(
            self.outbound_origins
            and self.outbound_destinations
            and self.return_origins
            and self.return_destinations
        )


@dataclass(frozen=True)
class IServConfig:
    base_url: str
    username: str
    password: str
    enabled: bool

    @property
    def is_complete(self) -> bool:
        return bool(self.enabled and self.base_url and self.username and self.password)


@dataclass(frozen=True)
class TenantConfig:
    id: str
    name: str
    public_id: str
    parent_email: str
    student_first_name: str
    student_last_initial: str
    school_label: str
    class_label: str
    active: bool
    webuntis: WebUntisConfig
    iserv: IServConfig
    email: EmailConfig
    transit: TransitSettings
    public_timetable_url: str
    data_dir: Path


@dataclass(frozen=True)
class GtfsConfig:
    feed_url: str
    cache_dir: Path
    cache_minutes: int
    timeout_seconds: int


@dataclass(frozen=True)
class GeofoxConfig:
    mode: str
    base_url: str
    username: str
    password: str
    api_version: int
    timeout_seconds: int
    cache_seconds: int
    min_interval_seconds: float

    @property
    def enabled(self) -> bool:
        return self.mode in {"auto", "geofox"} and bool(self.username and self.password)


@dataclass(frozen=True)
class AppConfig:
    app_host: str
    app_port: int
    webuntis: WebUntisConfig
    email: EmailConfig
    twilio: TwilioConfig
    webhook_url: str
    poll_interval_minutes: int
    transit_poll_interval_minutes: int
    days_back: int
    days_ahead: int
    notify_on_first_run: bool
    timezone: str
    data_dir: Path
    milo_ci_dir: Path
    admin_username: str
    admin_password: str
    public_timetable_url: str
    allowed_hosts: list[str]
    auth: AuthConfig
    gtfs: GtfsConfig
    geofox: GeofoxConfig
    tenants_file: Path
    tenants: tuple[TenantConfig, ...]

    @property
    def notification_channels(self) -> list[str]:
        channels = []
        if self.email.enabled:
            channels.append("email")
        if self.twilio.enabled:
            channels.append("whatsapp")
        if self.webhook_url:
            channels.append("webhook")
        return channels


def load_config(project_root: Path | None = None) -> AppConfig:
    root = project_root or Path.cwd()
    _load_env_file(root / ".env")

    element_id_raw = (
        os.environ.get("WEBUNTIS_ELEMENT_ID", "").strip()
        or os.environ.get("WEBUNTIS_CLASS_ID", "").strip()
    )
    element_id = int(element_id_raw) if element_id_raw.isdigit() else None
    element_type = _int(
        os.environ.get("WEBUNTIS_ELEMENT_TYPE")
        or os.environ.get("WEBUNTIS_CLASS_TYPE"),
        1,
    )

    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    if not data_dir.is_absolute():
        data_dir = root / data_dir

    default_ci_dir = Path.home() / "Documents" / "ChatGPT" / "Milo CI"
    milo_ci_dir = Path(os.environ.get("MILO_CI_DIR", str(default_ci_dir)))

    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
    if smtp_host.lower() == "smtp.gmail.com":
        smtp_password = "".join(smtp_password.split())

    webuntis = WebUntisConfig(
        server=os.environ.get("WEBUNTIS_SERVER", "").strip(),
        school=os.environ.get("WEBUNTIS_SCHOOL", "").strip(),
        username=os.environ.get("WEBUNTIS_USERNAME", "").strip(),
        password=os.environ.get("WEBUNTIS_PASSWORD", "").strip(),
        app_secret=os.environ.get("WEBUNTIS_APP_SECRET", "").strip(),
        school_number=os.environ.get("WEBUNTIS_SCHOOL_NUMBER", "").strip(),
        element_type=element_type,
        element_id=element_id,
        class_name=os.environ.get("WEBUNTIS_CLASS_NAME", "").strip(),
    )
    email = EmailConfig(
        host=smtp_host,
        port=_int(os.environ.get("SMTP_PORT"), 587),
        username=os.environ.get("SMTP_USERNAME", "").strip(),
        password=smtp_password,
        sender=os.environ.get("SMTP_FROM", "").strip(),
        reply_to=os.environ.get("SMTP_REPLY_TO", "").strip(),
        recipients=_list(os.environ.get("EMAIL_TO")),
        use_tls=_bool(os.environ.get("SMTP_USE_TLS"), True),
    )
    public_timetable_url = os.environ.get("PUBLIC_TIMETABLE_URL", "").strip()
    tenants_file = _resolve_path(
        root,
        os.environ.get("TENANTS_FILE", "").strip(),
        root / "config" / "tenants.json",
    )
    admin_username = os.environ.get("ADMIN_USERNAME", "admin").strip() or "admin"
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
    auth_users = _auth_users(os.environ.get("MILO_AUTH_USERS"))
    if not auth_users and admin_password:
        auth_users = {admin_username: admin_password}
    oidc = OidcConfig(
        issuer=os.environ.get("MILO_OIDC_ISSUER", "").strip().rstrip("/"),
        client_id=os.environ.get("MILO_OIDC_CLIENT_ID", "").strip(),
        client_secret=os.environ.get("MILO_OIDC_CLIENT_SECRET", "").strip(),
        redirect_uri=os.environ.get("MILO_OIDC_REDIRECT_URI", "").strip(),
        admin_group=os.environ.get("MILO_OIDC_ADMIN_GROUP", "milo-admins").strip() or "milo-admins",
        user_group=os.environ.get("MILO_OIDC_USER_GROUP", "milo-webuntis-users").strip()
        or "milo-webuntis-users",
        scopes=tuple(_list(os.environ.get("MILO_OIDC_SCOPES")) or ["openid", "profile", "email", "groups"]),
    )

    app_config = AppConfig(
        app_host=os.environ.get("APP_HOST", "127.0.0.1").strip() or "127.0.0.1",
        app_port=_int(os.environ.get("APP_PORT"), 8000),
        webuntis=webuntis,
        email=email,
        twilio=TwilioConfig(
            account_sid=os.environ.get("TWILIO_ACCOUNT_SID", "").strip(),
            auth_token=os.environ.get("TWILIO_AUTH_TOKEN", "").strip(),
            whatsapp_from=os.environ.get("TWILIO_WHATSAPP_FROM", "").strip(),
            recipients=_list(os.environ.get("WHATSAPP_TO")),
        ),
        webhook_url=os.environ.get("NOTIFICATION_WEBHOOK_URL", "").strip(),
        poll_interval_minutes=max(1, _int(os.environ.get("POLL_INTERVAL_MINUTES"), 15)),
        transit_poll_interval_minutes=max(
            1,
            _int(os.environ.get("TRANSIT_POLL_INTERVAL_MINUTES"), 2),
        ),
        days_back=max(0, _int(os.environ.get("DAYS_BACK"), 0)),
        days_ahead=max(0, _int(os.environ.get("DAYS_AHEAD"), 7)),
        notify_on_first_run=_bool(os.environ.get("NOTIFY_ON_FIRST_RUN"), False),
        timezone=os.environ.get("TIMEZONE", "Europe/Berlin").strip() or "Europe/Berlin",
        data_dir=data_dir,
        milo_ci_dir=milo_ci_dir,
        admin_username=admin_username,
        admin_password=admin_password,
        public_timetable_url=public_timetable_url,
        allowed_hosts=_allowed_hosts(os.environ.get("ALLOWED_HOSTS")),
        auth=AuthConfig(
            required=_bool(os.environ.get("MILO_AUTH_REQUIRED"), False),
            users=auth_users,
            secret=(
                os.environ.get("MILO_SESSION_SECRET", "").strip()
                or os.environ.get("MILO_AUTH_SECRET", "").strip()
                or admin_password
            ),
            cookie_secure=_bool(os.environ.get("MILO_COOKIE_SECURE"), False),
            idle_timeout_minutes=max(1, _int(os.environ.get("MILO_IDLE_TIMEOUT_MINUTES"), 30)),
            oidc=oidc,
        ),
        gtfs=GtfsConfig(
            feed_url=os.environ.get(
                "GTFS_FEED_URL",
                "https://download.gtfs.de/germany/nv_free/latest.zip",
            ).strip(),
            cache_dir=_resolve_path(
                root,
                os.environ.get("GTFS_CACHE_DIR", "").strip(),
                data_dir / "gtfs",
            ),
            cache_minutes=max(60, _int(os.environ.get("GTFS_CACHE_MINUTES"), 1440)),
            timeout_seconds=max(30, _int(os.environ.get("GTFS_DOWNLOAD_TIMEOUT_SECONDS"), 300)),
        ),
        geofox=GeofoxConfig(
            mode=(os.environ.get("TRANSIT_PROVIDER_MODE", "auto").strip().lower() or "auto")
            if (os.environ.get("TRANSIT_PROVIDER_MODE", "auto").strip().lower() or "auto")
            in {"auto", "geofox", "gtfs"}
            else "auto",
            base_url=os.environ.get("GEOFOX_BASE_URL", "https://gti.geofox.de").strip()
            or "https://gti.geofox.de",
            username=os.environ.get("GEOFOX_USERNAME", "").strip(),
            password=os.environ.get("GEOFOX_PASSWORD", "").strip(),
            api_version=max(1, _int(os.environ.get("GEOFOX_API_VERSION"), 63)),
            timeout_seconds=max(3, _int(os.environ.get("GEOFOX_TIMEOUT_SECONDS"), 15)),
            cache_seconds=max(15, _int(os.environ.get("GEOFOX_CACHE_SECONDS"), 60)),
            min_interval_seconds=max(
                1.0,
                _float(os.environ.get("GEOFOX_MIN_INTERVAL_SECONDS"), 1.1),
            ),
        ),
        tenants_file=tenants_file,
        tenants=(),
    )
    tenants = _load_tenants(root, app_config)
    return replace(app_config, tenants=tenants)


def _load_tenants(root: Path, config: AppConfig) -> tuple[TenantConfig, ...]:
    path = config.tenants_file
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_tenants = payload.get("tenants") if isinstance(payload, dict) else payload
        if isinstance(raw_tenants, list) and raw_tenants:
            return tuple(
                _tenant_from_mapping(root, item, config)
                for item in raw_tenants
                if isinstance(item, dict)
            )

    tenant_id = os.environ.get("TENANT_ID", "default").strip() or "default"
    public_seed = public_id_seed(config, tenant_id)
    return (
        TenantConfig(
            id=tenant_id,
            name=os.environ.get("TENANT_NAME", "Stundenplan").strip() or "Stundenplan",
            public_id=os.environ.get("TENANT_PUBLIC_ID", "").strip() or _opaque_public_id(public_seed),
            parent_email=os.environ.get("PARENT_EMAIL", "").strip(),
            student_first_name=os.environ.get("STUDENT_FIRST_NAME", "").strip(),
            student_last_initial=(
                os.environ.get("STUDENT_LAST_NAME", "").strip()
                or os.environ.get("STUDENT_LAST_INITIAL", "").strip()
            ),
            school_label=os.environ.get("SCHOOL_LABEL", "").strip(),
            class_label=os.environ.get("CLASS_LABEL", "").strip(),
            active=True,
            webuntis=config.webuntis,
            iserv=_iserv_from_mapping({}, config.webuntis),
            email=config.email,
            transit=_transit_from_mapping({}),
            public_timetable_url=config.public_timetable_url,
            data_dir=config.data_dir,
        ),
    )


def public_id_seed(config: AppConfig, tenant_id: str) -> str:
    return "|".join(
        [
            tenant_id,
            config.webuntis.server,
            config.webuntis.school,
            config.webuntis.username,
            str(config.webuntis.element_id or ""),
            "",
        ]
    )


def _tenant_from_mapping(root: Path, item: dict[str, Any], config: AppConfig) -> TenantConfig:
    tenant_id = str(item.get("id") or "default").strip() or "default"
    public_id = str(item.get("public_id") or _opaque_public_id(tenant_id)).strip()
    webuntis = item.get("webuntis") if isinstance(item.get("webuntis"), dict) else {}
    iserv = item.get("iserv") if isinstance(item.get("iserv"), dict) else {}
    email = item.get("email") if isinstance(item.get("email"), dict) else {}
    display = item.get("display") if isinstance(item.get("display"), dict) else {}
    transit = item.get("transit") if isinstance(item.get("transit"), dict) else {}
    parent_email = (
        str(item.get("parent_email") or "").strip()
        or str(display.get("parent_email") or "").strip()
    )
    element_id_raw = str(webuntis.get("element_id") or "").strip()
    element_id = int(element_id_raw) if element_id_raw.isdigit() else config.webuntis.element_id
    tenant_webuntis = WebUntisConfig(
        server=str(webuntis.get("server") or config.webuntis.server).strip(),
        school=str(webuntis.get("school") or config.webuntis.school).strip(),
        username=str(webuntis.get("username") or "").strip(),
        password=str(webuntis.get("password") or "").strip(),
        app_secret=str(webuntis.get("app_secret") or "").strip(),
        school_number=str(webuntis.get("school_number") or config.webuntis.school_number).strip(),
        element_type=_int(str(webuntis.get("element_type") or ""), config.webuntis.element_type),
        element_id=element_id,
        class_name=str(webuntis.get("class_name") or config.webuntis.class_name).strip(),
    )
    return TenantConfig(
        id=tenant_id,
        name=str(item.get("name") or tenant_id).strip(),
        public_id=public_id,
        parent_email=parent_email,
        student_first_name=str(display.get("student_first_name") or item.get("student_first_name") or "").strip(),
        student_last_initial=str(
            display.get("student_last_name")
            or display.get("student_last_initial")
            or item.get("student_last_name")
            or item.get("student_last_initial")
            or ""
        ).strip(),
        school_label=str(display.get("school") or item.get("school_label") or "").strip(),
        class_label=str(display.get("class") or item.get("class_label") or webuntis.get("class_name") or "").strip(),
        active=_bool(str(item.get("active") if item.get("active") is not None else "true"), True),
        webuntis=tenant_webuntis,
        iserv=_iserv_from_mapping(iserv, tenant_webuntis),
        email=replace(
            config.email,
            recipients=_list(str(email.get("recipients") or "")) or config.email.recipients,
        ),
        transit=_transit_from_mapping(transit),
        public_timetable_url=str(item.get("public_timetable_url") or config.public_timetable_url).strip(),
        data_dir=_resolve_path(root, str(item.get("data_dir") or ""), root / "data" / "tenants" / tenant_id),
    )


def _transit_from_mapping(item: dict[str, Any]) -> TransitSettings:
    return TransitSettings(
        outbound_origins=tuple(_transit_stop_list(item.get("outbound_origins"))),
        outbound_destinations=tuple(_transit_stop_list(item.get("outbound_destinations"))),
        return_origins=tuple(_transit_stop_list(item.get("return_origins"))),
        return_destinations=tuple(_transit_stop_list(item.get("return_destinations"))),
        arrive_min_before=max(0, _int(str(item.get("arrive_min_before") or ""), 10)),
        arrive_window_minutes=max(1, _int(str(item.get("arrive_window_minutes") or ""), 60)),
        depart_min_after=max(0, _int(str(item.get("depart_min_after") or ""), 5)),
        depart_window_minutes=max(1, _int(str(item.get("depart_window_minutes") or ""), 90)),
        day_start=str(item.get("day_start") or "05:00").strip() or "05:00",
        day_end=str(item.get("day_end") or "20:00").strip() or "20:00",
        direct_connections_only=_bool(
            str(item.get("direct_connections_only") or ""),
            False,
        ),
    )


def _iserv_from_mapping(item: dict[str, Any], webuntis: WebUntisConfig) -> IServConfig:
    base_url = str(
        item.get("base_url")
        or os.environ.get("ISERV_BASE_URL", "")
        or _default_iserv_base_url(webuntis)
    ).strip().rstrip("/")
    username = str(item.get("username") or os.environ.get("ISERV_USERNAME", "") or webuntis.username).strip()
    password = str(item.get("password") or os.environ.get("ISERV_PASSWORD", "") or webuntis.password).strip()
    enabled = _bool(
        str(item.get("enabled") if item.get("enabled") is not None else os.environ.get("ISERV_EXAMS_ENABLED", "")),
        bool(base_url),
    )
    return IServConfig(
        base_url=base_url,
        username=username,
        password=password,
        enabled=enabled,
    )


def _default_iserv_base_url(webuntis: WebUntisConfig) -> str:
    combined = " ".join([webuntis.server, webuntis.school, webuntis.school_number]).lower()
    if "herderschule" in combined or webuntis.school_number == "2340000":
        return "https://gymherderschule.de"
    return ""

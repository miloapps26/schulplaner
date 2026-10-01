#!/usr/bin/env bash
set -euo pipefail

APP_DOMAIN="${1:?Domain or Azure FQDN is required}"
APP_NAME="${2:-stundenplaninfo}"
APP_PORT="${3:-8000}"
APP_USER="${4:-stundenplan}"
APP_ROOT="/srv/apps/${APP_NAME}/app"
UPLOAD_ROOT="/tmp/stundenplaninfo-app"

apt-get update
apt-get install -y python3 python3-venv python3-pip rsync caddy

if ! id "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --create-home --shell /usr/sbin/nologin "${APP_USER}"
fi

mkdir -p "${APP_ROOT}" /etc/caddy/apps
rsync -a --delete \
  --exclude ".env" \
  --exclude ".venv" \
  --exclude "config/tenants.json" \
  --exclude "data" \
  "${UPLOAD_ROOT}/" "${APP_ROOT}/"

mkdir -p "${APP_ROOT}/data"
chown -R "${APP_USER}:${APP_USER}" "/srv/apps/${APP_NAME}"

cd "${APP_ROOT}"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
chown -R "${APP_USER}:${APP_USER}" "${APP_ROOT}/.venv"

cat >/etc/systemd/system/${APP_NAME}.service <<SERVICE
[Unit]
Description=Schulplaner WebUntis Monitor (${APP_NAME})
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_ROOT}
Environment=PYTHONPATH=${APP_ROOT}/src
Environment=APP_HOST=127.0.0.1
Environment=APP_PORT=${APP_PORT}
ExecStart=${APP_ROOT}/.venv/bin/python -m milo_webuntis.app
Restart=always
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=${APP_ROOT}/data ${APP_ROOT}/.env

[Install]
WantedBy=multi-user.target
SERVICE
systemctl daemon-reload

if [ ! -f /etc/caddy/Caddyfile ]; then
  cat >/etc/caddy/Caddyfile <<'CADDY'
import /etc/caddy/apps/*.caddy
CADDY
elif ! grep -q 'import /etc/caddy/apps/\*.caddy' /etc/caddy/Caddyfile; then
  printf '\nimport /etc/caddy/apps/*.caddy\n' >>/etc/caddy/Caddyfile
fi

cat >/etc/caddy/apps/${APP_NAME}.caddy <<CADDY
${APP_DOMAIN} {
	encode zstd gzip
	reverse_proxy 127.0.0.1:${APP_PORT}

	header {
		X-Robots-Tag "noindex, nofollow, noarchive"
		X-Content-Type-Options "nosniff"
		Referrer-Policy "no-referrer"
		Cache-Control "no-store"
		-Server
	}
}
CADDY

caddy validate --config /etc/caddy/Caddyfile
systemctl enable caddy
systemctl reload caddy || systemctl restart caddy

if [ -f "${APP_ROOT}/.env" ]; then
  chmod 600 "${APP_ROOT}/.env"
  chown "${APP_USER}:${APP_USER}" "${APP_ROOT}/.env"
  systemctl enable --now "${APP_NAME}"
  systemctl restart "${APP_NAME}"
else
  echo "App installiert. .env fehlt noch; Dienst wird nach upload-env.ps1 gestartet."
fi

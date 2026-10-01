# Deployment auf einem VPS

Diese Anleitung beschreibt den empfohlenen Dauerbetrieb auf einem kleinen Ubuntu-Server.

Wenn Azure genutzt werden soll, ist die konkretere Anleitung hier:

```text
deployment/azure/README.md
```

## Zielbild

- Die App läuft dauerhaft als `systemd`-Dienst.
- Caddy übernimmt HTTPS und leitet an `127.0.0.1:8000` weiter.
- `/admin` und `/app` sind per Milo-Auth-Login, Logout und Idle-Timeout geschützt.
- Eltern werden per einmaligem Setup-Link eingeladen und melden sich danach mit Benutzername und Passwort an.
- Zugangsdaten bleiben nur in `.env` auf dem Server.

## Umgebungsmodell

| Umgebung | Zweck | Muster |
| --- | --- | --- |
| Lokal | Entwicklung | `http://127.0.0.1:8000` |
| Staging | Test auf Azure vor Production | `https://<app-slug>-dev.miloapps.net` |
| Production | Live-Version | `https://<app-slug>.miloapps.net` |

Fuer diese App ist Staging konkret als `webuntis-dev.miloapps.net` in `deployment/environments/staging.yaml` dokumentiert. Staging und Production muessen eigene `.env`-Dateien, eigene Zugaenge und eigene interne Ports nutzen.

## Production-Release-Kommunikation

Nach jedem Production-Deployment muss eine Release-Mail an alle in Production konfigurierten
Empfaenger gesendet werden. Die Mail fasst neue Funktionen und behobene Fehler aus `CHANGELOG.md`
kurz zusammen, nennt die Version und verwendet denselben HTML-Stil wie die bestehenden
Schulplaner-Benachrichtigungen. Staging-Deployments loesen keine Release-Mail aus.

## 1. Server anlegen

Empfehlung: kleiner VPS mit Ubuntu 24.04 LTS, Region Deutschland oder EU.

Mindestgröße:

- 1 vCPU
- 1 GB RAM
- 10 GB Speicher

## 2. DNS setzen

Eine Subdomain wie `stundenplan.deinedomain.de` auf die Server-IP zeigen lassen.

## 3. Per SSH anmelden

```bash
ssh root@SERVER_IP
```

## 4. Basispakete installieren

```bash
apt update
apt upgrade -y
apt install -y python3 python3-venv python3-pip git rsync ufw caddy
```

## 5. Firewall aktivieren

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## 6. App-Benutzer anlegen

```bash
useradd --system --create-home --shell /usr/sbin/nologin stundenplan
mkdir -p /srv/apps/stundenplaninfo/app
chown -R stundenplan:stundenplan /srv/apps/stundenplaninfo
```

## 7. App-Dateien hochladen

Vom lokalen Rechner aus:

```powershell
scp -r src static tests deployment requirements.txt pyproject.toml README.md root@SERVER_IP:/srv/apps/stundenplaninfo/app/
```

Alternativ per Git-Repository klonen, wenn das Projekt später in Git liegt.

## 8. Python-Umgebung einrichten

Auf dem Server:

```bash
cd /srv/apps/stundenplaninfo/app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
chown -R stundenplan:stundenplan /srv/apps/stundenplaninfo
```

## 9. `.env` auf dem Server anlegen

```bash
nano /srv/apps/stundenplaninfo/app/.env
chmod 600 /srv/apps/stundenplaninfo/app/.env
chown stundenplan:stundenplan /srv/apps/stundenplaninfo/app/.env
```

Wichtig:

- WebUntis-Key eintragen
- GMX-SMTP-Daten eintragen
- `MILO_AUTH_REQUIRED=1` setzen
- `MILO_OIDC_ISSUER`, `MILO_OIDC_CLIENT_ID`, `MILO_OIDC_CLIENT_SECRET` und `MILO_OIDC_REDIRECT_URI` setzen
- `MILO_OIDC_ADMIN_GROUP=milo-admins` und `MILO_OIDC_USER_GROUP=milo-webuntis-users` setzen
- `MILO_SESSION_SECRET` lang und einzigartig setzen
- `MILO_COOKIE_SECURE=1` setzen
- `PUBLIC_TIMETABLE_URL=https://stundenplan.deinedomain.de/app`
- `ALLOWED_HOSTS=stundenplan.deinedomain.de` setzen

Stage und Production brauchen getrennte Authentik-Anwendungen, Client-Secrets,
Callback-URLs, `.env`-Dateien, Dienste, Ports und Domains. Die app-spezifischen
Rahmendaten liegen in `deployment/environments/staging.yaml` und
`deployment/environments/production.yaml`.

Bei mehreren Profilen zusätzlich `TENANTS_FILE=config/tenants.json` setzen und die Datei mit eigenen `data_dir`, `parent_email`, `webuntis`- und `email`-Werten pro Profil anlegen. Diese Datei enthält Secrets und wird nicht committed.

## 10. systemd-Dienst installieren

```bash
cp /srv/apps/stundenplaninfo/app/deployment/stundenplaninfo.service /etc/systemd/system/stundenplaninfo.service
systemctl daemon-reload
systemctl enable --now stundenplaninfo
systemctl status stundenplaninfo
```

Logs:

```bash
journalctl -u stundenplaninfo -f
```

## 11. Caddy konfigurieren

In `/srv/apps/stundenplaninfo/app/deployment/Caddyfile` die Domain ersetzen:

```text
stundenplan.example.de
```

durch deine echte Subdomain.

Dann:

```bash
mkdir -p /etc/caddy/apps
cp /srv/apps/stundenplaninfo/app/deployment/Caddyfile /etc/caddy/apps/stundenplaninfo.caddy
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
```

Caddy erstellt automatisch HTTPS-Zertifikate.

## 12. Test

Elternansicht:

```text
https://stundenplan.deinedomain.de/app
```

Admin:

```text
https://stundenplan.deinedomain.de/admin
```

## Sicherheitsregeln

- `.env` niemals veröffentlichen oder committen.
- `config/tenants.json` niemals veröffentlichen oder committen.
- Admin-Anmeldung läuft über Authentik; Eltern melden sich mit ihren hinterlegten WebUntis-Zugangsdaten an.
- `MILO_AUTH_USERS`, `ADMIN_USERNAME` und `ADMIN_PASSWORD` nur lokal für Admin-Entwicklung verwenden; bei `MILO_AUTH_REQUIRED=1` ist dieser Admin-Fallback deaktiviert.
- `MILO_SESSION_SECRET` lang und einzigartig wählen.
- Einladungslinks sind einmalig und nur zur Kontoerstellung gedacht.
- Öffentliche URLs dürfen keine Namen, Klassen oder Schulen enthalten.
- Server regelmäßig aktualisieren: `apt update && apt upgrade -y`.
- Nur Ports 22, 80 und 443 offen lassen.

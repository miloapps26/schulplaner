# Schulplaner - WebUntis Automatisation

Automatischer Monitor für den WebUntis-Stundenplan einer Klasse. Der Dienst prüft regelmäßig den aktuellen Plan, vergleicht ihn mit dem letzten Snapshot und verschickt bei Änderungen eine kurze Zusammenfassung mit Link zur aktuellen Stundenplanansicht.

## Was schon vorbereitet ist

- WebUntis-Abfrage per JSON-RPC
- Snapshot-Vergleich für neue, entfernte und geänderte Stunden
- Benachrichtigung per E-Mail, WhatsApp via Twilio oder Webhook
- Mandanten/Profile mit getrennten Datenordnern, Authentik-Anmeldung und WebUntis-Zugängen
- Busfahrplan-Tab mit GTFS-Sollzeiten, Tagesempfehlung und konfigurierbaren Schulweg-Haltestellen
- Kleine Admin-UI unter `http://127.0.0.1:8000/admin`
- Lokale Speicherung unter `data/`

## Einrichtung

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Danach `.env` ausfüllen. Aus deinem Link
`https://herderschule-lueneburg.webuntis.com/WebUntis?school=herderschule-lueneburg#/basic/timetablePublic/my-student?date=2026-08-24&entityId=6817`
kommen diese Werte:

- `WEBUNTIS_SERVER=herderschule-lueneburg.webuntis.com`
- `WEBUNTIS_SCHOOL=herderschule-lueneburg`
- `WEBUNTIS_ELEMENT_TYPE=5`, weil WebUntis Student als Elementtyp 5 führt
- `WEBUNTIS_ELEMENT_ID=6817`
- `WEBUNTIS_SCHOOL_NUMBER=2340000`, falls aus dem App-/QR-Zugang genutzt

Zusätzlich brauchst du:

- `WEBUNTIS_USERNAME`
- `WEBUNTIS_PASSWORD` oder bei IServ/SSO besser `WEBUNTIS_APP_SECRET`
- optional `EMAIL_TO` und SMTP-Daten
- optional `WHATSAPP_TO` und Twilio-Daten

Der URL-Parameter `date=2026-08-24` ist nur der im Browser gewählte Starttag und wird nicht fest in der `.env` gebraucht.

### Mehrere Profile / Mandanten

Ohne weitere Konfiguration läuft die App mit einem Default-Profil aus der `.env`.
Für mehrere Kinder, Klassen oder Nutzer kann stattdessen eine lokale Datei angelegt werden:

```powershell
New-Item -ItemType Directory -Force config
Copy-Item config\tenants.example.json config\tenants.json
```

`config/tenants.json` wird nicht committed. Jedes Profil bekommt eigene Werte:

- `id`: interne technische ID ohne Namen, zum Beispiel `tenant_q7k4m2x9`
- `name`: interne Anzeige im Adminbereich
- `public_id`: interne, zufällige technische ID ohne Namen
- `data_dir`: eigener Datenordner, zum Beispiel `data/tenants/tenant_q7k4m2x9`
- `parent_email`: E-Mail-Adresse fuer die einmalige Einladung
- `public_timetable_url`: App-Basis, zum Beispiel `https://webuntis.miloapps.net/app`
- `display`: Profilanzeige, also Vorname, vollständiger Nachname, Schule und Klasse
- `webuntis`: eigener WebUntis-Zugang bzw. eigenes Element; Benutzer und App-Schluessel koennen Eltern spaeter selbst setzen
- `email.recipients`: Empfänger für dieses Profil

Eltern erhalten keinen dauerhaften Token-Link. Der Admin sendet eine einmalige Einladung an `parent_email`. Darueber hinterlegen Eltern ihren bestehenden WebUntis-Benutzernamen und ihr WebUntis-Passwort. Diese Zugangsdaten werden danach zugleich fuer den Eltern-Login und fuer die WebUntis-Abfrage dieses Profils genutzt. Danach melden sie sich regulär an:

```text
https://webuntis.miloapps.net/app
```

Der Einladungslink enthaelt technisch einen einmaligen Setup-Token. Dieser dient nur zur Kontoerstellung und ersetzt keinen Login.

Eine bebilderte Anleitung zum Finden von WebUntis-Server, Schulname, Element-ID und App-Schlüssel liegt unter [docs/webuntis-setup-anleitung.md](docs/webuntis-setup-anleitung.md). Die dort verwendeten Screenshots sind anonymisierte Musterbilder.

Die Busfunktion bevorzugt im HVV-Gebiet Geofox fuer aktuelle Routen, Echtzeitinformationen und Stoerungsmeldungen. Wenn Geofox nicht konfiguriert oder voruebergehend nicht erreichbar ist, verwendet die App automatisch den deutschlandweiten GTFS-Sollfahrplan als gekennzeichneten Rueckfall.

Empfohlene Fahrten zeigen einen laufenden Abfahrts-Countdown. Der regulaere Monitor vergleicht zudem die empfohlene Hin- und Rueckfahrt des aktuellen Tages mit dem zuletzt erfolgreich verarbeiteten Stand und sendet bei jeder inhaltlichen Aenderung eine E-Mail an die fuer das Profil konfigurierten Empfaenger. Eine schematische Fahrzeugposition erscheint ausschliesslich dann, wenn Geofox die Fahrt ausdruecklich als Echtzeitfahrt mit verwertbarer Position meldet. Die App leitet keine vermeintliche Live-Position aus reinen Sollzeiten ab; laufende Positionsaenderungen loesen deshalb auch keine E-Mail aus.

Fuer eine kurze Ladezeit aktualisiert ein eigener Hintergrundlauf die Zeitfenster rund um Unterrichtsbeginn und Unterrichtsende des aktuellen Tages standardmaessig alle zwei Minuten. Zusaetzlich werden die Empfehlungen fuer alle zehn auswaehlbaren Schultage der aktuellen und naechsten Woche vorgeladen und alle 30 Minuten erneuert. Die umfangreicheren Tagesfahrplaene werden danach schrittweise fuer dieselben Tage vorbereitet; der heutige Tagesfahrplan wird alle 30 Minuten und die weiteren Tage alle sechs Stunden aktualisiert. Die Busansicht liefert sofort den letzten erfolgreichen Stand aus, waehrend neue Daten im Hintergrund geholt werden. Wenn sich der Stundenplan aktualisiert, werden die Empfehlungen erneut priorisiert vorgeladen.

### Schnellster Mailversand mit GMX

Gmail-App-Passwörter sind nicht für jedes Konto verfügbar. Für diese App ist deshalb eine eigene GMX-Versandadresse der einfachste Weg, zum Beispiel `stundenplaninfo@gmx.de`. Das Postfach muss nicht gelesen werden; es dient nur als authentifizierter technischer Absender.

```env
SMTP_HOST=mail.gmx.net
SMTP_PORT=587
SMTP_USERNAME=stundenplaninfo@gmx.de
SMTP_FROM=Schulplaner <stundenplaninfo@gmx.de>
SMTP_REPLY_TO=
EMAIL_TO=eltern@example.com
```

In GMX muss `POP3/IMAP Zugriff erlauben` aktiviert werden. Danach die Zugangsdaten lokal setzen:

```powershell
.\scripts\set-gmx.ps1
```

Wenn niemand antworten soll, bleibt `SMTP_REPLY_TO` leer. Technisch kann trotzdem jemand auf die GMX-Adresse antworten; das Postfach wird dann einfach nicht aktiv genutzt.

### Zugänge prüfen

```powershell
.\scripts\check.ps1 --webuntis --email-to "eltern@example.com"
```

Wenn WebUntis über IServ angemeldet wird, funktionieren die normalen IServ-Zugangsdaten nicht zwingend am WebUntis-JSON-RPC-Endpunkt. IServ bindet WebUntis per OpenID Connect an; der direkte JSON-RPC-Passwortlogin kann deshalb `bad credentials` liefern, obwohl der Browser-Login über IServ funktioniert.

Alternative für IServ/SSO-Schulen: Nach dem Login im Browser zu WebUntis im Profil unter `Freigaben` den Zugriff über App aktivieren bzw. den QR-Code anzeigen. Der QR-Code enthält typischerweise `url`, `school`, `user`, `key` und `schoolNumber`. Trage den Wert aus `key` als `WEBUNTIS_APP_SECRET` ein. `WEBUNTIS_PASSWORD` kann dann leer bleiben.

Für die Herderschule ist die lokale `.env` auf diese nicht geheimen Werte vorbereitet:

```env
WEBUNTIS_SERVER=herderschule-lueneburg.webuntis.com
WEBUNTIS_SCHOOL=herderschule-lueneburg
WEBUNTIS_USERNAME=Max.Mustermann
WEBUNTIS_SCHOOL_NUMBER=2340000
WEBUNTIS_ELEMENT_TYPE=5
WEBUNTIS_ELEMENT_ID=6817
```

Bei Gmail bedeutet `5.7.8 Username and Password not accepted` in der Regel: `SMTP_PASSWORD` ist kein gültiges Gmail-App-Passwort oder SMTP ist für dieses Konto nicht freigegeben.

WhatsApp braucht einen Versanddienst. Im Code ist Twilio vorbereitet, weil WhatsApp selbst keine freie direkte Gruppenversand-Schnittstelle für solche Automationen anbietet. Alternativ kann `NOTIFICATION_WEBHOOK_URL` auf Make, n8n, Zapier oder einen eigenen WhatsApp-Cloud-API-Adapter zeigen.

### Gmail ohne App-Passwort über Make

Wenn nur Gmail-Adressen vorhanden sind, ist Make + Gmail der schnellste Weg:

1. In Make ein neues Scenario erstellen.
2. Als erstes Modul `Webhooks > Custom webhook` hinzufügen.
3. Einen neuen Webhook anlegen und die Webhook-URL kopieren.
4. Danach `Gmail > Send an email` hinzufügen und per Google anmelden.
5. In Gmail die Felder aus dem Webhook mappen:
   - `To`: Empfänger, zum Beispiel `eltern@example.com`
   - `Subject`: `subject`
   - `Content`: `body`
6. Webhook lokal speichern:

```powershell
.\scripts\set-webhook.ps1
```

7. Test senden:

```powershell
.\scripts\check.ps1 --webhook
```

## Start

```powershell
.\scripts\run.ps1
```

Die Elternansicht ist dann lokal erreichbar:

```text
http://127.0.0.1:8000/app
```

Diese Ansicht ist für eingeloggte Eltern gedacht: Stundenplan, Hausaufgaben, Profil, Zeitstempel und Umschalter zwischen `Aktuell` und `Änderungen`. Admin-Funktionen stehen getrennt hier:

```text
http://127.0.0.1:8000/admin
```

Der Adminbereich unterscheidet zwei Bereiche:

- `Einstellungen`: getrennte Prüfintervalle für Stundenplan und Bus, E-Mail-Empfänger und Kanalstatus
- `Log`: Protokoll der letzten Prüfungen inklusive E-Mail-Versandstatus

Vor einer öffentlichen Veröffentlichung muss `/admin` per Milo/Authentik geschützt sein.
Eltern melden sich weiterhin mit den pro Profil hinterlegten WebUntis-Zugangsdaten an.
Die App unterstützt für den Adminbereich den Milo-Auth-Standard per OpenID Connect Authorization Code Flow mit PKCE:

```env
MILO_AUTH_REQUIRED=1
MILO_OIDC_ISSUER=https://auth.example.com/application/o/schulplaner/
MILO_OIDC_CLIENT_ID=...
MILO_OIDC_CLIENT_SECRET=...
MILO_OIDC_REDIRECT_URI=https://webuntis.miloapps.net/auth/callback
MILO_OIDC_ADMIN_GROUP=milo-admins
MILO_OIDC_USER_GROUP=milo-webuntis-users
MILO_SESSION_SECRET=langer-zufallswert
MILO_COOKIE_SECURE=1
MILO_IDLE_TIMEOUT_MINUTES=30
```

`MILO_AUTH_USERS`, `ADMIN_USERNAME` und `ADMIN_PASSWORD` sind nur noch lokale Admin-Entwicklungsfallbacks. Sobald `MILO_AUTH_REQUIRED=1` gesetzt ist, ist dieser Admin-Passwortfallback technisch deaktiviert. Der Eltern-Login per WebUntis-Zugang bleibt aktiv. Der Adminbereich hat einen echten Logout und die Server-Session läuft nach Inaktivität ab.

Der öffentliche, nicht sensible Versionsendpunkt lautet:

```text
/api/version
```

Er liefert nur die App-Version, zum Beispiel `{"version":"0.9.1"}`.

## Umgebungen

Fuer Weiterentwicklungen gilt ab jetzt diese feste Trennung:

| Umgebung | Zweck | URL-Muster |
| --- | --- | --- |
| Lokal | Entwicklung auf diesem Rechner | `http://127.0.0.1:8000` |
| Staging | Azure-Testumgebung vor Production | `https://webuntis-dev.miloapps.net` |
| Production | Live-Version fuer Eltern | `https://webuntis.miloapps.net` |

Die konkrete Staging-Konfiguration liegt in:

```text
deployment/environments/staging.yaml
```

Staging und Production laufen auf Azure als getrennte App-Instanzen mit eigenen Ports, eigenen `.env`-Secrets, eigenen Authentik-Anwendungen, eigenen Client-Secrets, eigenen Callback-URLs und eigenen Gruppen-/Zugriffsbindungen.

Geplante Authentik-Callbacks:

```text
Lokal:      http://127.0.0.1:8000/auth/callback
Staging:    https://webuntis-dev.miloapps.net/auth/callback
Production: https://webuntis.miloapps.net/auth/callback
```

## Veröffentlichen

Vor dem Veröffentlichen zuerst den Admin-Login setzen:

```powershell
.\scripts\set-admin-login.ps1
```

Der Adminbereich `/admin`, die Elternansicht `/app` und die Daten-APIs sind dann per Browser-Login geschützt.

Für einen schnellen Test kann die lokal laufende App per Cloudflare Quick Tunnel veröffentlicht werden:

```powershell
cloudflared tunnel --url http://localhost:8000
```

Für dauerhaften Betrieb sollte ein fester Cloudflare Tunnel mit eigener Domain oder ein kleiner Server/VPS genutzt werden. Wichtig ist: keine WebUntis- oder GMX-Zugangsdaten ins Repository committen, `.env` bleibt lokal bzw. wird nur als Server-Secret hinterlegt.

Die empfohlene Anleitung fuer den dauerhaften Betrieb liegt unter:

```text
deployment/README.md
```

Fuer Azure liegt eine konkrete Variante mit Skripten hier:

```text
deployment/azure/README.md
```

Der erste erfolgreiche Lauf speichert nur den Basis-Snapshot. Ab dem zweiten Lauf werden Änderungen gemeldet. Wer schon beim ersten Lauf testweise senden will, kann `NOTIFY_ON_FIRST_RUN=true` setzen; echte Änderungen entstehen aber erst gegen einen vorhandenen Vergleichsstand.

## Stundenplananzeige

Die App ruft immer die aktuelle und die nächste Schulwoche ab. Angezeigt werden nur Montag bis Freitag. In der Stundenplanansicht kann zwischen `Diese Woche` und `Nächste Woche` gewechselt werden.

Standardauswahl:

- Montag bis Freitag: `Diese Woche`
- Samstag und Sonntag: `Nächste Woche`; die vorherige Schulwoche heißt dann `Letzte Woche`

Zusätzlich kann zwischen `Woche` und `Tag` gewechselt werden. Die Wochenansicht ist Standard. Die Tagesansicht zeigt einen auswählbaren Montag-bis-Freitag-Tag aus der gewählten Woche.

Die E-Mail-Benachrichtigung ist bewusst knapp: betroffene Änderung(en) plus Link zur Elternansicht `/app`.

## Eigene Termine

Eltern koennen im Reiter `Termine` eigene Unterrichtsstunden oder AGs anlegen. Unterstuetzt werden woechentliche Termine von Montag bis Freitag und einmalige Termine mit Datum. Diese Eintraege werden nur lokal im jeweiligen Profil gespeichert und erscheinen im Stundenplan. WebUntis wird dabei nicht beschrieben.

## Busfahrplan

Eltern koennen im Profil die relevanten Haltestellen fuer den Schulweg konfigurieren. Pro Richtung sind mehrere Haltestellen moeglich, zum Beispiel:

```text
Hin Start:
Wittorf, Birkenweg

Hin Ziel:
Lueneburg, Herderschule
Lueneburg, Witzendorffstrasse

Zurueck Start:
Lueneburg, Herderschule
Lueneburg, Witzendorffstrasse

Zurueck Ziel:
Wittorf, Birkenweg
```

Der Reiter `Bus` zeigt fuer den gewaehlten Tag zwei Ebenen:

- eine Empfehlung passend zum ersten Unterrichtsbeginn und letzten Unterrichtsende
- den gesamten relevanten Soll-Fahrplan des Tages fuer Hin- und Rueckfahrt

Die Puffer sind je Profil einstellbar:

- `Ankunft min. vorher`: Bus muss mindestens so viele Minuten vor Unterrichtsbeginn ankommen
- `Hin Suchfenster`: wie weit vor Unterrichtsbeginn die App noch Vorschlaege anzeigen darf
- `Abfahrt min. nachher`: Bus darf fruehestens so viele Minuten nach Unterrichtsende starten
- `Zurueck Suchfenster`: wie lange nach Unterrichtsende Rueckfahrten angezeigt werden
- `Nur Direktverbindungen`: zeigt in Empfehlung und Tagesfahrplan ausschliesslich Fahrten ohne Umstieg; deaktiviert bleiben auch Umsteigeverbindungen sichtbar

Im Standardmodus `TRANSIT_PROVIDER_MODE=auto` wird Geofox bevorzugt. Die Zugangsdaten liegen ausschliesslich in der lokalen beziehungsweise serverseitigen `.env`:

```env
TRANSIT_PROVIDER_MODE=auto
GEOFOX_BASE_URL=https://gti.geofox.de
GEOFOX_USERNAME=
GEOFOX_PASSWORD=
GEOFOX_API_VERSION=63
GEOFOX_TIMEOUT_SECONDS=15
GEOFOX_CACHE_SECONDS=60
GEOFOX_MIN_INTERVAL_SECONDS=1.1
```

`geofox` erzwingt Geofox fuer Diagnosezwecke, `gtfs` den bisherigen Sollfahrplan. Diese technische Auswahl wird nicht Eltern aufgebuerdet. In `auto` faellt die App bei Geofox-Fehlern auf GTFS zurueck und kennzeichnet die Quelle in der Busansicht. Das Intervall des Bus-Hintergrundlaufs kann im Adminbereich oder ueber `TRANSIT_POLL_INTERVAL_MINUTES` eingestellt werden; Standard sind zwei Minuten.

Die GTFS-Daten kommen aus dem kostenlosen Feed `OePNV Deutschland`, aktuell `download.gtfs.de/germany/nv_free/latest.zip`. Die App speichert den Feed lokal unter `GTFS_CACHE_DIR` und laedt ihn nach Ablauf von `GTFS_CACHE_MINUTES` automatisch neu. Wenn der Download fehlschlaegt, wird der letzte funktionierende Stand weiter verwendet und als alter Stand erkennbar.

Geofox-Inhalte duerfen nach den vereinbarten Nutzungsbedingungen nur fuer eine unentgeltliche Fahrplanauskunft eingesetzt werden. Die Busansicht verlinkt deshalb sichtbar auf die HVV-Auskunft, nennt die Datenherkunft und weist auf Angaben ohne Gewaehr hin. Eine kostenpflichtige oder ueber Drittanbieter weitergegebene Nutzung muss vorab schriftlich geklaert werden.

## Datenschutz und Zugriff

- WebUntis-Zugangsdaten, SMTP-Passwörter, Auth-User und Elternkonten gehören nur in `.env`, `config/tenants.json` oder `data/accounts.json`, nie ins Repository.
- Jedes Profil nutzt einen eigenen Datenordner. Snapshots, Logs, lokale Hausaufgaben und Erledigt-Markierungen werden dadurch voneinander getrennt.
- Die Elternoberfläche liefert ohne gültige Login-Session keine Stundenplan- oder Hausaufgabendaten aus.
- Öffentliche URLs enthalten keine Namen, Klassen oder Schulen. Diese Informationen erscheinen nur reduziert in der Eltern-UI.
- Admin- und Elternbereich sind per Server-Session geschützt, haben Logout und 30 Minuten Idle-Timeout.
- Eltern-/WebUntis-Passwörter werden fuer den App-Login gehasht gespeichert; fuer die automatische WebUntis-Abfrage liegt das WebUntis-Passwort zusaetzlich serverseitig im Profil-Secret. Einladungslinks sind einmalig.

## Betriebsidee

Für einen dauerhaften Betrieb eignet sich ein kleiner Server, ein NAS, ein Raspberry Pi oder ein Windows-Rechner mit Autostart/Task Scheduler. Das Stundenplanintervall wird über `POLL_INTERVAL_MINUTES`, das Busintervall über `TRANSIT_POLL_INTERVAL_MINUTES` gesteuert. Beide Werte sind auch im Adminbereich einstellbar.

## Tests

```powershell
.\scripts\test.ps1
```

# Azure Deployment

Diese Variante ist fuer den dauerhaften Betrieb gedacht, wenn der lokale Rechner nicht durchgehend laufen soll.

## Zielarchitektur

- Azure VM mit Ubuntu
- Caddy fuer HTTPS
- Schulplaner als systemd-Dienst
- `.env` nur auf dem Server
- Elternbereich mit Login
- Adminbereich mit Login

## Umgebungen

| Umgebung | Zweck | URL |
| --- | --- | --- |
| Lokal | Entwicklung auf diesem Rechner | `http://127.0.0.1:8000` |
| Staging | Testversion auf Azure | `https://webuntis-dev.miloapps.net` |
| Production | Live-Version | `https://webuntis.miloapps.net` |

AzureHosting haelt nur die allgemeine Regel fest: Staging heisst immer `<app-slug>-dev.miloapps.net`, Production heisst `<app-slug>.miloapps.net`. Die konkrete WebUntis-Staging-Konfiguration liegt in `deployment/environments/staging.yaml`.

## Empfohlene Startgroesse

Fuer die Stundenplan-App reicht klein:

- Region: `germanywestcentral`
- VM: `Standard_B1s`
- Image: `Ubuntu2204`

Spaeter fuer Audio-/Video-Jobs nicht diese VM gross machen, sondern separate Job-Worker nutzen, zum Beispiel Azure Batch oder groessere temporäre VMs.

## Lokale Voraussetzungen

- Azure Konto
- Azure CLI
- OpenSSH `ssh` und `scp`
- Ein vorbereiteter AzureHosting-Server mit Caddy-Import unter `/etc/caddy/apps/*.caddy`

OpenSSH ist auf diesem Rechner bereits vorhanden. Azure CLI fehlt aktuell noch.

## Ablauf

### 1. AzureHosting-Server auswählen

Wenn der gemeinsame AzureHosting-Server bereits eingerichtet ist, brauchst du fuer diese App keine zweite VM. Verwende dann den vorhandenen FQDN oder spaeter deine eigene Domain.

Beispiel aus AzureHosting:

```text
azurehosting-web01.swedencentral.cloudapp.azure.com
```

### 2. Azure CLI installieren

Microsoft-Anleitung: https://learn.microsoft.com/cli/azure/install-azure-cli-windows

Danach PowerShell neu starten.

### 3. Bei Azure anmelden

```powershell
az login
```

### 4. Nur falls noch kein AzureHosting-Server existiert: VM erstellen

```powershell
.\deployment\azure\create-vm.ps1
```

Das Skript erzeugt:

- Resource Group `rg-stundenplaninfo`
- VM `vm-stundenplaninfo`
- DNS-Namen wie `stundenplaninfo-abc123.germanywestcentral.cloudapp.azure.com`
- offene Ports 80 und 443

### 5. App hochladen und Server einrichten

Den vorhandenen AzureHosting-FQDN oder den FQDN aus Schritt 4 verwenden:

```powershell
.\deployment\azure\upload-app.ps1 -ServerHost "stundenplaninfo-abc123.germanywestcentral.cloudapp.azure.com"
```

Wenn SSH ueber den Azure-FQDN laeuft, die App aber unter einer eigenen Domain erscheinen soll:

```powershell
.\deployment\azure\upload-app.ps1 -ServerHost "azurehosting-web01.swedencentral.cloudapp.azure.com" -AppDomain "stundenplan.deinedomain.de"
```

Das Skript installiert die App unter `/srv/apps/stundenplaninfo/app` und legt die Caddy-Konfiguration als `/etc/caddy/apps/stundenplaninfo.caddy` ab.

Staging fuer diese App:

```powershell
.\deployment\azure\upload-app.ps1 -ServerHost "azurehosting-web01.swedencentral.cloudapp.azure.com" -AppDomain "webuntis-dev.miloapps.net" -AppName "webuntis-dev" -AppPort 8010
```

Production spaeter:

```powershell
.\deployment\azure\upload-app.ps1 -ServerHost "azurehosting-web01.swedencentral.cloudapp.azure.com" -AppDomain "webuntis.miloapps.net" -AppName "webuntis" -AppPort 8000
```

Nach einem erfolgreichen Production-Deployment wird eine Release-Mail an alle Production-Empfaenger
versendet. Inhalt: Version, neue Funktionen, behobene Fehler und Link zur Elternansicht. Grundlage
sind `CHANGELOG.md` und der Unterschied seit dem vorherigen Git-Tag. Die Mail nutzt den bestehenden
Schulplaner-HTML-Stil; Staging-Deployments versenden diese Mail nicht.

### 6. Lokale Secrets finalisieren

Admin-Login setzen:

```powershell
.\scripts\set-admin-login.ps1
```

Als URL den Azure-FQDN mit HTTPS eingeben:

```text
https://webuntis-dev.miloapps.net
```

Setze zusaetzlich `PUBLIC_TIMETABLE_URL=https://webuntis-dev.miloapps.net` und `ALLOWED_HOSTS=webuntis-dev.miloapps.net`.

### 7. `.env` auf Server hochladen und Dienst starten

```powershell
.\deployment\azure\upload-env.ps1 -ServerHost "azurehosting-web01.swedencentral.cloudapp.azure.com" -AppName "webuntis-dev"
```

### 8. Testen

Elternansicht:

```text
https://webuntis-dev.miloapps.net/app
```

Admin:

```text
https://webuntis-dev.miloapps.net/admin
```

## Betrieb

Status:

```bash
sudo systemctl status stundenplaninfo
```

Logs:

```bash
sudo journalctl -u stundenplaninfo -f
```

Update:

```powershell
.\deployment\azure\upload-app.ps1 -ServerHost "DEIN_FQDN"
.\deployment\azure\upload-env.ps1 -ServerHost "DEIN_FQDN"
```

## Sicherheit

- `.env` nie committen.
- Admin-Anmeldung in Stage und Production über Authentik betreiben; Eltern melden sich per WebUntis-Zugang an.
- `MILO_SESSION_SECRET` lang und einzigartig wählen.
- Keine Milo-/Authentik-Passwörter in Schulplaner speichern.
- Einladungslinks sind nur einmalig zur Einrichtung gedacht.
- `ALLOWED_HOSTS` im Hostingbetrieb auf die echte Domain oder den Azure-FQDN beschränken.
- Azure-VM regelmäßig aktualisieren.
- Nur Ports 22, 80 und 443 öffnen.

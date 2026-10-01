# Milo CI Adoption

Milo CI ist erst dann uebernommen, wenn die betroffenen echten App-Seiten und Assets gegen die zentralen Regeln geprueft wurden. Das Kopieren oder Vendorn von `tokens.css`, `ci.css` und `assets/` reicht allein nicht aus.

## Pflichtablauf

Wenn ein Projekt `Milo CI aktualisieren`, `Milo CI pruefen` oder einen Release/Deployment-Schritt ausfuehrt:

1. `VERSION`, `ci-manifest.json`, `CHANGELOG.md` und die referenzierten Regeldateien im zentralen Milo-CI-Projekt lesen.
2. Benoetigte Dateien und Assets ins Zielprojekt kopieren oder vendorn.
3. Alle betroffenen echten UI-Seiten auf die neuen Komponenten und Regeln migrieren.
4. Den Adoption-Checker gegen das Zielprojekt laufen lassen.
5. Alle Fehler beheben. Warnungen bewusst pruefen und entweder beheben oder im Projekt dokumentieren.
6. Erst danach duerfen Commit, Tag, Stage, Prod oder Redeployment vorbereitet werden.

## Checker

Aus einem beliebigen Projekt heraus:

```powershell
node "C:\Users\admin\Documents\ChatGPT\Milo CI\tools\check-adoption.mjs" .
```

Oder mit explizitem Ziel:

```powershell
node "C:\Users\admin\Documents\ChatGPT\Milo CI\tools\check-adoption.mjs" "C:\Users\admin\Documents\ChatGPT\WebUntis"
```

Der Checker gibt JSON aus und beendet sich mit Exitcode 1, wenn verbindliche Regeln verletzt sind.

## Was Geprueft Wird

- Vendored Milo-CI-Version und Manifest muessen zur zentralen Version passen.
- Pflichtdateien wie `tokens.css`, `ci.css`, `LOGIN.md`, Mark, Favicons und Apple-Touch-Icon muessen vorhanden sein.
- `ci.css` muss die native `[hidden]`-Regel enthalten.
- HTML-Shells muessen aktuelle versionierte Milo-Favicons verwenden.
- `.ci-mark` muss das offizielle `assets/milo-mark.svg` verwenden.
- App-Topbars brauchen `.ci-topbar-meta` und `.ci-version`.
- Login-Seiten duerfen keine normale Topbar verwenden und muessen `.ci-login-page`, `.ci-login-card`, `.ci-login-title`, `.ci-login-form`, `.ci-login-actions`, `input.ci-input` und `.ci-button-primary.ci-button-block` nutzen.

Der Checker ersetzt keine fachliche UI-Pruefung, schliesst aber die Luecke zwischen "CI-Dateien vorhanden" und "CI wirklich angewendet".
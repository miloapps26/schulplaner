# Milo CI Integration

## PDF- und Export-Integration

Die Corporate Identity gilt auch fuer PDF-Berichte und andere Exporte.
`PDF.md` beschreibt die verbindlichen Layout-, Metadaten- und Dateinamenregeln.
Fuer PDF-Renderer `pdf-tokens.json` ins Projekt uebernehmen und mitliefern.
Die Datei verwendet dieselben Farben wie `tokens.css`; keine eigene Palette
im Berichtscode pflegen. PDF-Seiten nach Aenderungen rendern und pruefen.

Alle Downloads, CLI-Ausgaben und Archivmitglieder muessen ihrer Quelle
zuordenbar sein und zusammengehoerige Dateien einen gemeinsamen Basisnamen
tragen. Download-Header und tatsaechliche Exportdateien automatisiert testen.

## 1. Dateien einbinden

HTML:

```html
<link rel="stylesheet" href="../Milo CI/tokens.css">
<link rel="stylesheet" href="../Milo CI/ci.css">
```

React/Vite/Next:

```ts
import "../../Milo CI/tokens.css";
import "../../Milo CI/ci.css";
```

Pfad je Projekt anpassen. Reihenfolge bleibt immer: erst `tokens.css`, dann `ci.css`.

Wichtig fuer Deployments:

- Andere Projekte duerfen Milo CI als Quelle fuer Vorgaben, Tokens, Klassen und Assets nutzen.
- Beim Deployment darf keine Laufzeit- oder Build-Abhaengigkeit auf diesen lokalen Milo-CI-Projektordner bestehen.
- Projekte kopieren oder vendorn die benoetigten CI-Dateien/Assets in ihr eigenes Repository oder in ihren eigenen Build-Artefakt-Pfad.
- Relative Links auf `../Milo CI/...` sind nur fuer lokale Entwicklung, Beispiele und manuelle Referenzpruefung gedacht.
- Vor Release oder Deployment pruefen Projekte die aktuelle CI-Version, uebernehmen noetige Aenderungen lokal und deployen danach aus dem eigenen Projekt heraus.

## 2. App-Shell verwenden

UI-Titel schreiben Milo nicht aus. Das Zeichen traegt den Milo-Schriftzug; der sichtbare Titel nennt nur das Tool, zum Beispiel `LEQ`, `Upmix` oder `SSP Request`.

```html
<div class="ci-app">
  <header class="ci-topbar">
    <div class="ci-brand">
      <div class="ci-mark" aria-hidden="true">
        <img class="ci-mark-img" src="../Milo CI/assets/milo-mark.svg" alt="">
      </div>
      <div>
        <h1 class="ci-brand-title">LEQ</h1>
        <p class="ci-brand-subtitle">Audio Tools</p>
      </div>
    </div>
    <div class="ci-topbar-meta">
      <div class="ci-status">Ready</div>
      <div class="ci-version">v1.0.1</div>
      <button class="ci-logout-button" type="button">Logout</button>
    </div>
  </header>

  <nav class="ci-tabs" aria-label="Werkzeuge">
    <button class="ci-tab" type="button" aria-selected="true">Measure</button>
    <button class="ci-tab" type="button">Reports</button>
  </nav>

  <main class="ci-main">
    <section class="ci-workspace">
      ...
    </section>
  </main>
</div>
```

## 3. Versionsnummer

Die Versionsnummer steht in jeder Milo-App immer rechts oben in der Topbar, direkt neben dem Status.

```html
<div class="ci-topbar-meta">
  <div class="ci-status">Ready</div>
  <div class="ci-version">v1.0.1</div>
</div>
```

Regel:

- Format: `vMAJOR.MINOR.PATCH`, zum Beispiel `v1.0.1`.
- Die Version ist die Version der jeweiligen App, nicht die CI-Version.
- Die CI-Version wird separat ueber `VERSION` und `ci-manifest.json` im CI-Ordner geprueft.

## 4. Auth und Logout

Sobald eine Milo-App Authentifizierung hat, gelten diese Regeln:

- Es gibt immer einen sichtbaren Logout-Button in der Topbar, rechts neben Status und Version.
- Standard-Idle-Logout: nach 30 Minuten ohne Bedienung.
- Aktivitaet sind mindestens Klick, Tastatur, Touch, Scroll, Datei-Auswahl und relevante Formularaenderungen.
- Der Logout muss serverseitig oder token-seitig wirksam sein, nicht nur eine UI-Weiterleitung.
- Projekte mit sensibleren Daten duerfen kuerzere Zeiten verwenden, aber nicht laenger als 30 Minuten ohne bewusste Entscheidung.

Topbar-Beispiel:

```html
<div class="ci-topbar-meta">
  <div class="ci-status">Ready</div>
  <div class="ci-version">v1.0.1</div>
  <button class="ci-logout-button" type="button">Logout</button>
</div>
```

## 5. Login-Seiten

Login-Seiten verwenden nicht die normale App-Shell, sondern das Milo-Login-Layout aus `LOGIN.md`: dunkler Hintergrund, zentrierte `.ci-login-card`, offizielles Milo-Zeichen, kurzer Kontext, klare Labels und eine einzelne Primaeraktion.

```html
<main class="ci-login-page">
  <section class="ci-login-card">
    <div class="ci-mark" aria-hidden="true">
      <img class="ci-mark-img" src="../Milo CI/assets/milo-mark.svg" alt="">
    </div>
    <p class="ci-section-kicker">ZUGANG</p>
    <h1 class="ci-login-title">Anmelden</h1>
    <p class="ci-login-copy">Sitzung wegen Inaktivitaet beendet.</p>
    <form class="ci-login-form">
      <label class="ci-field"><span class="ci-label">Benutzername</span><input class="ci-input" autocomplete="username"></label>
      <label class="ci-field"><span class="ci-label">Passwort</span><input class="ci-input" type="password" autocomplete="current-password"></label>
      <button class="ci-button ci-button-primary ci-button-block" type="submit">Anmelden</button>
    </form>
  </section>
</main>
```

Fuer Browser-Tabs, iPhone-Homescreen und installierbare Web-App-Icons immer die aktuellen Milo-Icons einbinden. Der Query-String an Favicons ist bewusst erlaubt, damit Browser nicht alte Favicons aus dem Cache zeigen:

```html
<link rel="icon" href="/assets/favicon.svg?v=1.4.0" type="image/svg+xml">
<link rel="icon" href="/assets/favicon-32.png?v=1.4.0" sizes="32x32" type="image/png">
<link rel="shortcut icon" href="/assets/favicon.ico?v=1.4.0">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#0f141a">
```

## 6. Activity-/Kommandozeilenbereich

Logs und laufende Kommandoausgaben sollen nicht dominant sein. Standard:

- kompakter Status in der Topbar,
- Details nur einklappbar,
- alternativ eigener Tab `Activity`, `Runs` oder `Logs`.

Einklappbare Variante:

```html
<details class="ci-activity">
  <summary>
    <span>Activity</span>
    <span class="ci-badge">3 steps</span>
  </summary>
  <pre class="ci-console">Analyzing source...
Creating output...
Done.</pre>
</details>
```

Eigener Tab:

```html
<button class="ci-tab" type="button" aria-selected="false">Activity</button>
<section class="ci-activity-tab" aria-hidden="true">
  <pre class="ci-console">...</pre>
</section>
```

## 7. Native hidden

Wenn ein Element das native HTML-Attribut `hidden` hat, muss es unsichtbar bleiben. Das gilt auch fuer Milo-Komponenten wie `.ci-workspace`, `.ci-tabs`, `.ci-button`, `.ci-activity` oder andere Klassen mit eigenem `display`.

Regel:

```html
<section class="ci-workspace" hidden>...</section>
<nav class="ci-tabs" hidden>...</nav>
```

Projekt-CSS darf `[hidden]` nicht ueberschreiben. Zum Pruefen liegt `hidden-regression.html` bereit; der statische Test ist `tests/hidden-attribute-regression.ps1`.

## 8. Stabile Prozess-UX

Grundsatz: Die Oberflaeche darf bei Auswahl, Zustandswechseln und Prozessschritten nicht springen. Verwende die Regeln aus `PROCESS-UX.md` und die zentralen Komponenten aus `ci.css`.

Empfohlenes Grundmuster:

```html
<section class="ci-workspace ci-process">
  <div class="ci-process-bar">
    <div class="ci-process-steps">...</div>
    <div class="ci-process-nav">...</div>
  </div>
  <div class="ci-process-stage">
    <div class="ci-media-workbench">
      <section class="ci-preview-pane"><div class="ci-preview-frame">...</div></section>
      <section class="ci-settings-pane">...</section>
    </div>
  </div>
</section>
```

Desktop nutzt bei motivbezogenen Tools Vorschau links und Einstellungen rechts. Mobil werden die Bereiche untereinander angeordnet. Dynamische Inhalte kommen in `.ci-status-panel`, `.ci-reserved-region`, `.ci-suggestion` oder `.ci-step-body`, damit kurze und lange Zustaende dieselbe Struktur behalten.

Bestehende Milo-Apps uebernehmen die Aenderung so:

1. Prozessnavigation nach oben in `.ci-process-bar` verschieben.
2. Gemeinsame Arbeitsflaeche mit `.ci-process-stage` reservieren.
3. Motiv- oder Dokumentvorschau in `.ci-preview-frame` stabil halten; Ergebnis ersetzt die Referenz im selben Platz.
4. Lade-, Fehler-, Vorschlags- und Ergebniszustaende im bestehenden Layout anzeigen, nicht als komplette Ersatzseite.
5. KI-Aktionen mit `.ci-ai-action` und Sparkles-/Zauberstab-Icon neben dem Eingabefeld platzieren; Vorschlaege erst nach bewusster Uebernahme anwenden.
6. Mit `process-stability-demo.html` und `tests/process-stability-playwright.js` gegen Desktop, kleinen Laptop und Mobilgeraet pruefen.
## 9. Robuste Workflows

Fuer laengere, kostenrelevante, asynchrone oder redaktionell freizugebende Ablaeufe gilt `WORKFLOW-UX.md`.

Kernregeln:

- Vor dem Absenden eine dauerhafte Job-ID erzeugen und mit Quelle, Eingaben, Anbieter/Modell, App-Version, Milo-CI-Version und Regelversion speichern.
- Reload, erneuter Login und verlorene Serverantwort fragen zuerst den bestehenden Jobstatus ab.
- Eine neue kostenpflichtige Variante entsteht nur durch eine eigene, klar benannte Aktion.
- Autosave zeigt einen kleinen Speicherstatus; alte Eingaben, Quellen, Warenkoerbe und Ergebnisse bleiben bei Fehlern sichtbar.
- Vorschlaege erscheinen als Kandidaten mit Uebernehmen/Verwerfen/Vergleichen und ueberschreiben Nutzereingaben nicht automatisch.
- Ergebnisansichten zeigen sichtbare Download-/Exportaktionen und unterscheiden Entwurf, Testpreview, Freigabe, ausstehenden Export, Fehler und manuellen Eingriff.
- Fehler benennen die passende Ursache und bieten den naechsten sinnvollen Schritt an.

Empfohlene Klassen: `.ci-job-card`, `.ci-job-meta`, `.ci-save-state`, `.ci-candidate`, `.ci-result-toolbar`, `.ci-action-bar`, `.ci-error-note`, `.ci-state-list`. Pruefung: `workflow-resilience-demo.html` und `tests/workflow-resilience-playwright.js`.


## 10. Dark Mode

Dark Mode ist Standard. Apps verwenden Milo Night Workbench ohne zusaetzliches Theme-Attribut. Light Mode ist optional per `data-ci-theme="light"` verfuegbar.

```html
<html lang="de" data-ci-theme="light">
  ...
</html>
```

Regeln und Pruefkriterien stehen in `DARK-MODE.md`. Die visuelle Referenz ist `dark-mode-demo.html`; der Smoke-Test ist `tests/dark-mode-playwright.js`. Dark und Light verwenden dieselben `ci-*` Komponenten und duerfen keine konkurrierenden Paletten in App-CSS aufbauen.


## 11. Einheitliche Controls

Buttons, Inputs, Segmente, Icon-Buttons, Prozessschritte und KI-Aktionen verwenden die zentralen Control-Tokens aus `tokens.css` und die Komponenten aus `ci.css`.

Grundmuster:

```html
<input class="ci-input" aria-label="Name">
<button class="ci-button ci-button-primary" type="button">Start</button>
<button class="ci-icon-button" type="button" aria-label="Aktualisieren">...</button>
<div class="ci-segmented" role="group">
  <button type="button" aria-pressed="true">Woche</button>
  <button type="button" aria-pressed="false">Tag</button>
</div>
```

Regel: Standardcontrols haben 44px Mindesthoehe und 6px Radius. Container und Panele haben 8px Radius. Pills/Badges bleiben pill-foermig. `.ci-button` ist bewusst ruhig; Teal ist `.ci-button-primary` und echten Hauptaktionen vorbehalten. Messwertfelder nutzen `.ci-input-group ci-metric-input`. Viele Tabs duerfen `.ci-tabs-compact` verwenden. Lokale Apps duerfen diese Werte nicht je Control neu definieren. Vollbreite Hauptaktionen nutzen `.ci-button ci-button-primary ci-button-block`.

Bestehende Apps pruefen lokale Button-, Input-, Select-, Segment- und Icon-Button-CSS gegen `CONTROLS.md` und `controls-consistency-demo.html`.
## 12. Icons

Bevorzugt `lucide` verwenden. Falls ein Projekt kein Icon-Paket nutzt, sind inline SVGs ok. Icons sollen Funktionen markieren, nicht dekorieren.

Empfohlene Icons:

- Upload/Import: `upload`, `file-plus`
- Analyse: `scan`, `activity`, `search`
- Parameter: `sliders-horizontal`, `settings`
- Ausgabe: `package`, `download`, `send`
- Activity/Logs: `terminal`, `list-checks`
- Logout: `log-out`
- Zuruecksetzen: `rotate-ccw`
## 13. Adoption-Check

Eine Milo-CI-Aktualisierung ist erst vollstaendig, wenn nicht nur die CI-Dateien kopiert, sondern die echten App-Seiten migriert und geprueft wurden. Fuehre nach jeder Milo-CI-Uebernahme und vor jedem UI-Release/Deployment den Checker aus:

```powershell
node "C:\Users\admin\Documents\ChatGPT\Milo CI\tools\check-adoption.mjs" .
```

Der Checker muss ohne Fehler durchlaufen. Warnungen werden bewusst geprueft und entweder behoben oder projektbezogen dokumentiert. Siehe `ADOPTION.md`.

## 14. Milo-Markenzeichen

Das offizielle Milo-Zeichen liegt hier:

```text
C:\Users\admin\Documents\ChatGPT\Milo CI\assets\milo-mark.svg
```

Regel: Jede sichtbare Milo-Marke verwendet `assets/milo-mark.svg` in einem `.ci-mark` Container mit `.ci-mark-img`. Keine Fallback-Balken, keine umgefaerbten Roboter, keine dunkle Logo-Kachel im Dark Mode. Das Standardzeichen bleibt: weisser Hintergrund, dunkle Milo-Figur, sichtbarer Milo-Schriftzug.

Fuer Dokumente, Praesentationen, Favicons ausserhalb von SVG-Kontexten oder externe Verwendung liegen exportierte Varianten unter `assets/milo/`. PNG gibt es mit weissem und transparentem Hintergrund; JPG gibt es technisch nur mit weissem Hintergrund. Neue Apps sollen fuer UI-Shells weiter `assets/milo-mark.svg` verwenden und nur fuer Export-/Dokumentkontexte auf `assets/milo/` zurueckgreifen.

Als Favicon:

```html
<link rel="icon" href="../Milo CI/assets/favicon.svg?v=1.4.0" type="image/svg+xml">
<link rel="icon" href="../Milo CI/assets/favicon-32.png?v=1.4.0" sizes="32x32" type="image/png">
<link rel="shortcut icon" href="../Milo CI/assets/favicon.ico?v=1.4.0">
```

## 15. CI-Aenderungen erkennen

Andere Projekte sollen bei CI-Checks immer diese Dateien lesen:

```text
C:\Users\admin\Documents\ChatGPT\Milo CI\VERSION
C:\Users\admin\Documents\ChatGPT\Milo CI\ci-manifest.json
C:\Users\admin\Documents\ChatGPT\Milo CI\CHANGELOG.md
```

`VERSION` enthaelt nur die aktuelle CI-Version. `ci-manifest.json` ist maschinenlesbar und nennt geaenderte Dateien, Regeln und empfohlene Anpassungen. `CHANGELOG.md` ist die lesbare Historie.

## 16. Lokale Anpassungen

Projekt-CSS soll nur Fachlayout und Sonderzustaende ergaenzen. Farben, Abstaende, Radien, Buttons, Tabs, Inputs und Panels kommen aus dem Milo-CI.

Ausgewaehlte Button- oder Segment-Zustaende verwenden die CI-Tokens:

```css
background: var(--milo-selected-bg);
color: var(--milo-selected-text);
```

Der dunkle Milo-Ink-Ton bleibt fuer Topbar, Konsolen und starke Rahmen reserviert, nicht fuer ausgewaehlte Toggle-Buttons.

## 17. Datenvisualisierung

Diagramme, Spektren, Balken, Linien und Report-Grafiken verwenden die Milo-Chart-Palette aus `tokens.css` oder `pdf-tokens.json`.

Web-CSS:

```css
color: var(--milo-chart-1);
background: var(--milo-chart-muted);
```

Empfohlene Reihenfolge fuer Datenreihen:

```text
--milo-chart-1, --milo-chart-2, --milo-chart-3, --milo-chart-4,
--milo-chart-5, --milo-chart-6, --milo-chart-7, --milo-chart-8
```

Chart-Library-Defaultpaletten muessen ueberschrieben werden. Braun, generisches Gruen und zufaellige warme Farben sind nicht als Standard-Datenfarben erlaubt. Warnung und Fehler nur semantisch verwenden: `--milo-chart-warning` und `--milo-chart-danger`.

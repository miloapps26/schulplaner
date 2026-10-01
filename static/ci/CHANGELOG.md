# Milo CI Changelog

## Unreleased

## 1.5.0 - 2026-09-12
- Milo-CI-Adoption technisch abgesichert: `ADOPTION.md`, `tools/check-adoption.mjs` und `tests/adoption-checker-regression.js` ergaenzt, damit Zielprojekte nicht nur CI-Dateien kopieren, sondern echte App-Seiten gegen verbindliche Regeln pruefen.
- Globale Codex-Anweisung geschaerft: Milo-CI-Aktualisierung und UI-Deployment sind erst abgeschlossen, wenn der Adoption-Checker ohne Fehler laeuft.

## 1.4.0 - 2026-09-12
- Robuste Workflow-UX aus Motion Still Frame, Reframing, Qrder und Film Data Agent als globalen Milo-Standard ergaenzt: dauerhafte Job-IDs, Autosave/Resume, Idempotenz, Vorschlagsuebernahme, Versionen, Freigaben, klare Fehlerursachen und explizite Exportaktionen.
- `WORKFLOW-UX.md`, `workflow-resilience-demo.html`, neue Workflow-Komponenten und `tests/workflow-resilience-playwright.js` ergaenzt.

- Browser-Tab-Favicons auf das aktuelle Milo-Zeichen abgesichert: SVG, PNG und ICO-Fallbacks mit Versions-Query sowie Regressionstest ergaenzt.

- Login-Layout nach Animation-Referenz als verbindlichen Milo-Standard ergaenzt; iPhone-Homescreen-Icon und Web-App-Manifest-Assets bereitgestellt.

- Milo-Grafikassets als wiederverwendbare SVG-, PNG- und JPG-Varianten mit weissem Hintergrund sowie SVG/PNG mit Alpha-Hintergrund unter `assets/milo/` bereitgestellt.

- Stabile Prozess-UX aus Motion Still Frame als verbindliche Milo-Regel uebernommen: Prozessnavigation, Arbeitsflaechen, Vorschau, Status, Vorschlaege und KI-Aktionen duerfen bei Zustandswechseln nicht springen.
- Neue wiederverwendbare Komponenten fuer Prozessleisten, stabile Prozessbuehnen, motivbezogene Preview/Settings-Layouts, Statuspanels, reservierte Inhaltsbereiche und KI-Aktionen ergaenzt.
- `PROCESS-UX.md`, `process-stability-demo.html` und `tests/process-stability-playwright.js` ergaenzt; bestehende Milo-Apps erhalten konkrete Uebernahmeschritte.
- `Milo Night Workbench` als neuen Standardmodus festgelegt; Light Mode bleibt als opt-in Variante verfuegbar. Standardlogo fuer den Dark-Standard finalisiert: urspruengliche dunkle Milo-Figur auf weissem Hintergrund; helle Variante `assets/milo-mark-light.svg` bleibt gesichert.

## 1.3.2 - 2026-09-03

- Milo-Markenzeichen erweitert: Der kleine Roboter traegt den sichtbaren Milo-Schriftzug direkt im Icon.
- UI-Namensregel angepasst: App-Titel verwenden keinen Milo-Textpraefix mehr, sondern nur den aussagekraeftigen Werkzeugnamen.
- Referenzscreen, Integrationsbeispiel, Codex-Anweisung, Manifest und Favicon synchronisiert.

## 1.3.1 - 2026-09-01

- Native HTML-Ausblendung robust gemacht: `[hidden]` setzt zentral `display: none !important;` und gewinnt gegen Milo-Komponenten mit explizitem `display`.
- Regression-Demo und Test fuer versteckte `.ci-workspace`, `.ci-tabs`, `.ci-button` und `.ci-activity` ergaenzt.
- CI-Version und Manifest auf `1.3.1` synchronisiert.

## 1.2.2 - 2026-08-31

- PDF-Gestaltung verbindlich in die Corporate Identity aufgenommen; portable PDF-Tokens bereitgestellt.
- Quellenbezogene, zusammenpassende Exportnamen fuer alle Dateitypen, CLI/API und Archivmitglieder vorgeschrieben.
- Renderpruefungen und Tests tatsaechlicher Downloadnamen als Integrationsanforderung dokumentiert.

## 1.2.1 - 2026-08-31

- Lokale Pfadbeispiele und Codex-Integrationshinweise auf den neuen Projektordner Milo CI aktualisiert.
- Deployment-Isolation dokumentiert: Projekte nutzen Milo CI als Vorgabe, muessen benoetigte Dateien aber lokal kopieren oder vendorn und duerfen keine produktive Abhaengigkeit auf den Milo-CI-Ordner behalten.

## 1.2.0 - 2026-08-30

- Auth-Regel fuer Milo-Apps ergaenzt: Sobald eine App Authentifizierung hat, braucht sie einen sichtbaren Logout-Button in der Topbar.
- Standard fuer automatischen Logout definiert: 30 Minuten Inaktivitaet.
- Neue CSS-Klasse `.ci-logout-button` ergaenzt.
- Integration und Codex-Anweisung aktualisiert, damit neue und bestehende Auth-Apps die Regel uebernehmen.

## 1.1.1 - 2026-08-30

- Ausgewaehlte Button-/Segment-Zustaende von dunkler Flaeche auf Milo-Teal umgestellt.
- Neue Tokens `--milo-selected-bg` und `--milo-selected-text` ergaenzt.
- Dokumentiert, dass schwarzer Ink-Ton fuer Topbar/Konsole reserviert bleibt und nicht fuer ausgewaehlte Toggle-Buttons verwendet wird.

## 1.1.0 - 2026-08-29

- Standardplatz fuer App-Versionen definiert: rechts oben in der Topbar neben dem Status.
- Neue CSS-Klassen `.ci-topbar-meta` und `.ci-version` ergaenzt.
- CI-Update-Erkennung eingefuehrt: `VERSION`, `ci-manifest.json` und `CHANGELOG.md`.
- Integration und Codex-Anweisung aktualisiert, damit andere Projekte CI-Aenderungen klar erkennen und umsetzen koennen.

## 1.0.0 - 2026-08-28

- Milo CI Kit erstellt.
- Finale Richtung festgelegt: Milo Workbench + Command Colors.
- Milo-Markenzeichen und Favicon hinzugefuegt.
- Basis-Tokens, Komponenten-CSS, Referenzscreen und Integrationsdokumentation erstellt.

# Milo CI Kit

PDF-Berichte gehoeren ebenfalls zum Milo-CI. `PDF.md` definiert verbindliche
Regeln fuer PDF-Layout und quellenbezogene Exportnamen in allen Milo-Tools.
`pdf-tokens.json` liefert die passenden Farben fuer PDF-Renderer.

Zentrale Quelle fuer das gemeinsame Look & Feel deiner kleinen Tools.

**Milo** steht intern fuer **My Idea Lab Online**. Diese Langform muss nicht in jeder App sichtbar sein. In den Tools selbst steht der klare Werkzeugname ohne Milo-Textpraefix, zum Beispiel `LEQ`, `Upmix` oder `SSP Request`. Milo ist im Zeichen sichtbar.

## Finales CI

**Milo Night Workbench + Command Colors**

- Struktur: LEQ-nahe Workbench mit dunkler Topbar, Tabs und dunklem Arbeitsbereich.
- Marke im Zeichen: Das Logo zeigt den kleinen Roboter mit sichtbarem Milo-Schriftzug; UI-Titel nutzen nur den Werkzeugnamen.
- Farben: modernes Command-Dunkel, ruhiges dunkles App-Umfeld, Teal als Hauptakzent, Blau fuer sekundare Daten.
- Stil: ruhig, technisch, aufgeraeumt, modern, icon-basiert.
- Activity-/Kommandozeilenlogs: nicht dominant, sondern einklappbar oder in einem eigenen Tab.
- App-Version: immer rechts oben in der Topbar neben dem Status.
- Ausgewaehlte Button-/Segment-Zustaende: Milo-Teal statt schwarzer Flaeche.
- Auth-Apps: Login nach Milo-Login-Layout, Logout-Button rechts oben und Auto-Logout nach 30 Minuten Inaktivitaet.
- Datenvisualisierung: Diagramme nutzen die Milo-Chart-Palette, keine Library-Defaultfarben.
- Native `hidden`-Elemente bleiben immer unsichtbar, auch wenn eine `ci-*` Komponente ein eigenes `display` setzt.
- Prozesslayout, Motivbezug, Statuswechsel und KI-Aktionen bleiben stabil: keine Layout- oder Scrollspruenge bei normalen Zustandswechseln.
- Robuste Workflows: Laengere, teure oder redaktionelle Jobs haben dauerhafte Job-IDs, Autosave, Resume, Versionen, klare Fehlerursachen, bewusste Vorschlagsuebernahme und explizite Exportaktionen.
- Adoption ist pruefpflichtig: CI-Dateien kopieren reicht nicht; Zielprojekte muessen echte Seiten und Assets mit `tools/check-adoption.mjs` gegen Milo CI pruefen.
- Dark Mode ist Standard: Milo Night Workbench. Light Mode ist optional per `data-ci-theme="light"` verfuegbar.
- Einheitliche Controls: Buttons, Inputs, Segmente, Icon-Aktionen und Prozessschritte nutzen dieselben Hoehen, Radien, Abstaende und Zustandsfarben.
- Milo-Mark-Konsistenz: Jede `.ci-mark` Darstellung verwendet das offizielle `assets/milo-mark.svg` mit weissem Hintergrund, dunkler Figur und Milo-Schriftzug.

## Dateien

- `tokens.css`: zentrale Design-Tokens.
- `ci.css`: wiederverwendbare Komponentenklassen.
- `example.html`: Referenzscreen fuer die finale Milo-Workbench.
- `hidden-regression.html`: kleine Regression-Demo fuer das native `hidden`-Attribut.
- `process-stability-demo.html`: Demo fuer stabile Prozess-, Vorschau-, Status- und KI-Aktionsmuster.
- `workflow-resilience-demo.html`: visuelle Demo fuer langlebige Jobs, Vorschlaege, Fehler und Ergebnisaktionen.
- `PROCESS-UX.md`: verbindliche Regeln fuer stabile Prozess-UX und Motivbezug.
- `WORKFLOW-UX.md`: verbindliche Regeln fuer robuste Auftraege, Autosave, Resume, Versionen, Freigaben, Fehler und Exporte.
- `DARK-MODE.md`: Regeln und Zielbild fuer Milo Night Workbench.
- `LOGIN.md`: verbindliche Login- und iPhone-Home-Screen-Icon-Regeln.
- `CONTROLS.md`: verbindliche Regeln fuer einheitliche Buttons, Inputs, Segmente und Control-Zustaende.
- `dark-mode-demo.html`: visuelle Dark-Mode-Referenz.
- `login-demo.html`: visuelle Referenz fuer Milo-Loginseiten.
- `controls-consistency-demo.html`: Mockup und Regression-Demo fuer einheitliche Controls.
- `BRAND.md`: Marken- und Namensregeln.
- `INTEGRATION.md`: konkrete Einbauanleitung fuer andere Projekte.
- `ADOPTION.md`: verbindlicher Ablauf und Checker fuer vollstaendige Milo-CI-Uebernahme in Zielprojekten.
- `codex-ui-instructions.md`: Vorgabe fuer Codex, wenn neue Milo-UIs gebaut oder bestehende angepasst werden.
- `VERSION`: aktuelle Version dieses globalen CI-Kits.
- `ci-manifest.json`: maschinenlesbare CI-Aenderungen fuer andere Projekte.
- `CHANGELOG.md`: lesbare Aenderungshistorie.
- `tests/hidden-attribute-regression.ps1`: statischer Regression-Test fuer `[hidden]` gegen Komponenten-`display`.
- `tests/process-stability-playwright.js`: Playwright-Regressionspruefung fuer Layoutstabilitaet.
- `tests/workflow-resilience-playwright.js`: Playwright-Test fuer robuste Workflow-Zustaende und Ergebnisaktionen.
- `tests/dark-mode-playwright.js`: Playwright-Smoke-Test fuer die Dark-Mode-Referenz.
- `tests/controls-consistency-playwright.js`: Playwright-Test fuer Control-Radien, Hoehen und Ueberlauf.
- `tests/milo-mark-consistency.ps1`: statischer Test fuer die offizielle Milo-Mark-Verwendung.
- `DATA-VIS.md`: Regeln und Palette fuer Diagramme und Datenvisualisierung.
- `PDF.md`: Regeln fuer PDF-Berichte und Exportnamen.
- `pdf-tokens.json`: portable Farb-Tokens fuer PDF-Renderer.
- `assets/milo-mark.svg`: dark-optimiertes Standard-Markenzeichen.
- `assets/milo-mark-light.svg`: helle Logo-Variante fuer Light-Kontexte.
- `assets/favicon.svg`: Favicon auf Basis des Milo-Zeichens.
- `assets/favicon-16.png`, `assets/favicon-32.png`, `assets/favicon-48.png` und `assets/favicon.ico`: Browser-Tab-Favicons aus dem aktuellen Milo-Zeichen.
- `assets/apple-touch-icon.png`: iPhone-Homescreen-Icon mit Milo-Zeichen.
- `assets/app-icon-192.png` und `assets/app-icon-512.png`: Web-App-Manifest-Icons.
- `assets/milo/`: exportierte Milo-Grafiken als SVG, PNG und JPG, jeweils mit weissem bzw. transparentem Hintergrund, soweit das Format Alpha unterstuetzt.
- `tests/milo-generated-assets.ps1`: statischer Test fuer die generierten Milo-Grafikassets.
- `tests/login-layout-playwright.js`: Playwright-Test fuer Milo-Loginlayout.
- `tests/app-icon-assets.ps1`: statischer Test fuer iPhone-/Web-App-Icon-Assets.
- `tests/favicon-consistency.ps1`: statischer Test fuer aktuelle Browser-Tab-Favicons und Favicon-Links.
- `tools/check-adoption.mjs`: projektuebergreifender Checker fuer vendored CI-Version, Assets, Loginlayout, Favicons, Mark und Topbar-Version.
- `tests/adoption-checker-regression.js`: Regressionstest fuer den Adoption-Checker.

## Minimaler Einbau

In HTML-Projekten:

```html
<link rel="stylesheet" href="../Milo CI/tokens.css">
<link rel="stylesheet" href="../Milo CI/ci.css">
```

In React/Vite/Next-Projekten einmal zentral importieren:

```ts
import "../../Milo CI/tokens.css";
import "../../Milo CI/ci.css";
```

Danach Komponenten bevorzugt mit den `ci-*` Klassen aufbauen und Farben aus `--milo-*` Tokens verwenden.

## Deployment-Regel

Andere Projekte duerfen dieses Kit als zentrale CI-Quelle verwenden, sollen aber beim Deployment keine Abhaengigkeit auf diesen lokalen Ordner behalten. Fuer produktive Builds werden die benoetigten CSS-Dateien und Assets in das jeweilige Projekt kopiert oder gevendort. Relative Pfade wie `../Milo CI/...` sind nur fuer lokale Entwicklung und Referenzbeispiele gedacht.

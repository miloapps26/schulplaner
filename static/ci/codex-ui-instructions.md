# Codex-Anweisung fuer Milo-UIs

Nutze diese Vorgabe, wenn Codex neue kleine Anwendungen, MVPs oder Proof-of-Concept-Tools mit UI baut oder bestehende Tools auf Milo umstellt.

## CI-Quelle

Verwende das zentrale CI-Kit aus `C:\Users\admin\Documents\ChatGPT\Milo CI`.

Bindend sind:

- `tokens.css`
- `ci.css`
- `BRAND.md`
- `INTEGRATION.md`
- `PDF.md`
- `pdf-tokens.json` fuer PDF-Ausgaben

## Zielbild

Die UI folgt **Milo Night Workbench + Command Colors**:

- dunkle Topbar,
- Milo-Markenzeichen links, mit sichtbarem Milo-Schriftzug im Zeichen,
- Toolname ohne Milo-Textpraefix, als `<aussagekraeftiger Name>`,
- Kategorie darunter,
- Versionsnummer rechts oben in der Topbar neben dem Status,
- bei Auth ein Logout-Button rechts oben in der Topbar,
- flache Tab-Navigation,
- dunkler, ruhiger Arbeitsbereich,
- moderne klare Icons,
- Teal als Hauptakzent,
- Teal als Flaeche fuer ausgewaehlte Button-/Segment-Zustaende,
- Blau fuer sekundare Daten oder Messlinien.

Die erste Ansicht ist immer das eigentliche Werkzeug, keine Landingpage.

## Namensregel

Toolnamen muessen direkt verstaendlich sein:

- gut: `LEQ`, `Upmix`, `SSP Request`, `DCP`
- vermeiden: abstrakte Fantasienamen ohne Funktionshinweis

`My Idea Lab Online` ist Hintergrundbedeutung und wird nicht dauerhaft in der UI ausgeschrieben. `Milo` steht sichtbar im Logo, nicht als Textpraefix im App-Titel.

## Milo-Mark-Konsistenz

Ueberall, wo das Milo-Zeichen in einer UI auftaucht, verwende den offiziellen Markup-Aufbau: `.ci-mark` mit `<img class="ci-mark-img" src=".../assets/milo-mark.svg" alt="">`. Das Standardzeichen bleibt die urspruengliche dunkle Milo-Figur auf weissem Hintergrund mit sichtbarem Milo-Schriftzug. Keine alte Balkenmarke, keine umgefaerbte weisse Roboter-Variante und keine dunkle Logo-Kachel im Standard-Dark-Mode. Fuer externe Grafiknutzung, Dokumente oder Uploads nutze die abgeleiteten Dateien in `assets/milo/`; UI-Shells verwenden weiterhin `assets/milo-mark.svg`.

## PDFs und Exportnamen

Auch PDFs muessen dem Milo-CI entsprechen. Verwende `PDF.md` und die lokal
vendorten `pdf-tokens.json`: korrekter Produktname, Milo-Farben, klare Typografie,
Quelle, App-Version und Seitenzahlen. Gerenderte Seiten visuell pruefen.

Alle Exporte muessen uebergreifend eindeutig ihrer Quelle zuzuordnen sein.
PDF, CSV, Audio und Dateien in Archiven teilen einen quellenbezogenen Basisnamen
mit relevantem Verarbeitungsschritt/Parameter. Generische Downloadnamen allein
sind nicht erlaubt. Das gilt auch fuer CLI/API und Hintergrundjobs. Regeln und
Pruefkriterien stehen verbindlich in `PDF.md`.

## Versionsregel

Jede Milo-App zeigt ihre eigene App-Version an derselben Stelle:

```html
<div class="ci-topbar-meta">
  <div class="ci-status">Ready</div>
  <div class="ci-version">v1.0.1</div>
</div>
```

Die Version steht immer rechts oben in der Topbar. Sie ist nicht im Footer, nicht in Settings versteckt und nicht je Tool unterschiedlich platziert.

## Login-Regel

Login-Seiten verwenden das Layout aus `LOGIN.md`: `.ci-login-page`, zentrierte `.ci-login-card`, offizielles Milo-Zeichen oben, kurzer Kontext, klare Labels, `input.ci-input` und eine einzelne `.ci-button ci-button-primary ci-button-block` Aktion. Keine normale Topbar auf Login-Seiten. Session-/Fehlermeldungen ruhig als `.ci-login-copy`, keine grosse Warnbox. Fuer Browser-Tabs und iPhone-Homescreen-URLs bindet jede deploybare Milo-Web-App `assets/favicon.svg?v=1.4.0`, `assets/favicon-32.png?v=1.4.0`, `assets/favicon.ico?v=1.4.0`, `assets/apple-touch-icon.png` und `site.webmanifest` ein. Favicons duerfen einen Versions-Query tragen, damit alte Browser-Caches nicht das fruehere Icon zeigen.

## Auth-Regel

Sobald eine Milo-App Authentifizierung hat:

- Fuege einen sichtbaren Logout-Button in der Topbar hinzu, rechts neben Status und Version.
- Verwende `.ci-logout-button` und bevorzugt ein `log-out` Icon.
- Implementiere automatischen Logout nach 30 Minuten Inaktivitaet.
- Der Logout muss technisch wirksam sein, also Session/Token invalidieren oder serverseitig beenden, wenn das Auth-System das vorsieht.
- Fuer sensible Apps darf der Timeout kuerzer sein; laenger als 30 Minuten nur bei expliziter Projektentscheidung.

## CI-Update-Regel

Wenn ein Projekt pruefen soll, ob sich das globale Milo-CI geaendert hat, lies zuerst:

- `C:\Users\admin\Documents\ChatGPT\Milo CI\VERSION`
- `C:\Users\admin\Documents\ChatGPT\Milo CI\ci-manifest.json`
- `C:\Users\admin\Documents\ChatGPT\Milo CI\CHANGELOG.md`

`ci-manifest.json` ist die maschinenlesbare Quelle fuer Version, geaenderte Dateien, betroffene Regeln und empfohlene Anpassungen.
## Milo-CI-Adoption Ist Pflicht

Wenn der Nutzer in einem Projekt Milo CI aktualisieren, Milo CI pruefen, releasen oder deployen laesst, reicht das Kopieren der CI-Dateien nie aus. Nach dem Lesen von `VERSION`, `ci-manifest.json`, `CHANGELOG.md` und den referenzierten Regeldateien muessen die echten App-Seiten auf die betroffenen Regeln migriert werden.

Fuehre anschliessend den Adoption-Checker aus:

```powershell
node "C:\Users\admin\Documents\ChatGPT\Milo CI\tools\check-adoption.mjs" "<Projektpfad>"
```

Fehler sind Blocker fuer Commit, Tag, Stage, Prod und Redeployment. Warnungen bewusst pruefen und im Projekt beheben oder dokumentieren. Besonders bei Auth/Login muss der Checker bestaetigen, dass die echte Login-Seite das aktuelle `LOGIN.md`-Pattern nutzt.

## Deployment-Isolation

Andere Projekte bedienen sich an den Milo-CI-Vorgaben, duerfen aber beim Deployment keine Abhaengigkeit auf `C:\Users\admin\Documents\ChatGPT\Milo CI` behalten.

- Nutze Milo CI als Source of Truth fuer Designregeln, Tokens, Komponentenklassen und Assets.
- Kopiere oder vendore die benoetigten CI-Dateien/Assets in das jeweilige Projekt, bevor es gebaut oder deployed wird.
- Lokale Importpfade wie `../Milo CI/tokens.css` sind nur fuer Entwicklung, Beispiele und Referenzchecks erlaubt.
- Produktionsbuilds muessen aus dem jeweiligen Projekt alleine funktionieren, ohne Zugriff auf den Milo-CI-Ordner.
- Vor Release oder Deployment zuerst `VERSION`, `ci-manifest.json` und `CHANGELOG.md` pruefen, dann die relevanten Aenderungen lokal uebernehmen.

## Datenvisualisierung

Diagramme, Spektren, Balken, Linien und Report-Grafiken verwenden die Milo-Chart-Tokens aus `tokens.css` oder `pdf-tokens.json`. Ueberschreibe Defaultpaletten von Chart-Libraries. Braun, generisches Gruen und zufaellige warme Farben sind nicht als Standard-Datenfarben erlaubt. Nutze `--milo-chart-warning` und `--milo-chart-danger` nur fuer echte Warn-/Fehlerbedeutung.

## Sichtbarkeit

Das native HTML-Attribut `hidden` hat Vorrang vor allen Milo-Komponentenklassen. Elemente wie `.ci-workspace`, `.ci-tabs`, `.ci-button`, `.ci-activity` und andere `ci-*` Klassen duerfen ein Element mit `hidden` nicht sichtbar machen. Projekt-CSS darf die zentrale Regel `[hidden] { display: none !important; }` nicht abschwaechen oder ueberschreiben.

## Stabile Prozess-UX

Grundsatz: Die Oberflaeche darf bei Auswahl, Zustandswechseln und Prozessschritten nicht springen.

- Zusammengehoerige Prozessschritte verwenden dieselbe `.ci-process-stage`; Zurueck-/Weiter-Navigation bleibt vorzugsweise oben in `.ci-process-bar`.
- Die Arbeitsflaeche beruecksichtigt den groessten regulaer benoetigten Zustand. Kurze Schritte duerfen freie Flaeche behalten.
- Dynamische Inhalte wie Vorschlaege, Hoerproben, Validierung, Fortschritt und Fehler verwenden reservierte oder begrenzte Bereiche wie `.ci-status-panel`, `.ci-reserved-region`, `.ci-suggestion` und `.ci-step-body`.
- Keine universellen starren Pixelhoehen. Nutze responsive Mindesthoehen, stabile Grid-Tracks und internes Scrollen, damit Inhalt nie abgeschnitten oder unzugaenglich wird.
- Normale Auswahlwechsel duerfen keinen automatischen Scrollsprung ausloesen; Fokus und Scrollposition bleiben erhalten.

## Motivbezogene Werkzeuge

Bild-, Video-, Audio- und Dokumentwerkzeuge verwenden `.ci-media-workbench`: Desktop mit Vorschau links und Einstellungen rechts, mobil untereinander. Die Referenz bleibt waehrend Texteingabe, Auswahl, Hoerprobe und Verarbeitung sichtbar. Das Ergebnis ersetzt die Referenz im selben `.ci-preview-frame`; unterschiedliche Medienformate werden ohne Layoutsprung eingepasst.

## Verarbeitungszustaende

Laden ersetzt nicht die gesamte Arbeitsflaeche. Fortschritt wird platzsparend in das bestehende Layout integriert. Zeige die tatsaechliche Phase (`analyzing`, `creating`, `checking`, `complete`, `error`). Prozentwerte nur bei messbarem Fortschritt, sonst unbestimmt mit `aria-busy="true"`. Eingaben und Ergebnisse bleiben bei Fehlern erhalten; Doppelauftraege werden verhindert. Statusaenderungen barrierefrei mit `role="status"` und `aria-live` ankuendigen, ohne den Fokus staendig zu verschieben.

## KI-Aktionen

KI-Aktionen verwenden `.ci-ai-action` mit Sparkles- oder Zauberstab-Icon aus der bestehenden Icon-Bibliothek, ausreichendem Kontrast, Tooltip und `aria-label`. Sie duerfen eingegebenen Text nicht ueberdecken. Vorschlaege erscheinen in `.ci-suggestion` und werden erst nach bewusster Uebernahme angewendet. Lade-, deaktivierter und Fehlerzustand behalten dieselben Abmessungen.
## Robuste Workflow-UX

Bei laengeren, kostenrelevanten, asynchronen oder redaktionell freizugebenden Workflows gilt zusaetzlich `WORKFLOW-UX.md`.

- Erzeuge eine dauerhafte Job-ID vor dem Start und speichere Quelle, Eingaben, Anbieter/Modell, App-Version, Milo-CI-Version und Regelversion dazu.
- Nach Reload, erneutem Login oder unklarer Serverantwort zuerst vorhandenen Jobstatus abfragen; keine automatische neue kostenpflichtige Variante.
- Zeige Autosave ruhig und sichtbar mit `.ci-save-state`.
- Zeige echte Phasen statt erfundener Prozentwerte und integriere sie in `.ci-status-panel`.
- Vorschlaege sind Kandidaten in `.ci-candidate` oder `.ci-suggestion`; sie brauchen Uebernehmen/Verwerfen und ueberschreiben Texte nicht ungefragt.
- Freigaben und Exporte beziehen sich auf den sichtbaren Stand samt Quellen, Regeln und Versionen.
- Alte Ergebnisse, Snapshots, Warenkoerbe, Quellen und Freigaben bleiben lesbar, wenn neue Regeln oder Stammdaten gelten.
- Fehler unterscheiden Zugangsdaten, Sitzung, Netzwerk/Server, Anbieter, Validierung, Berechtigung und unklaren Auftragsstatus.
- Fertige Ergebnisse haben eine sichtbare Download-/Exportaktion im App-UI.


## Dark Mode

Dark Mode ist Standard. Verwende Milo Night Workbench ohne zusaetzliches Theme-Attribut und dieselben `ci-*` Komponenten wie in der optionalen Light-Variante. Light Mode wird nur bewusst mit `data-ci-theme="light"` aktiviert. Farben kommen aus `tokens.css`, nicht aus projektspezifischen Kopien. Dark Mode muss auf Desktop, kleinem Laptop und Mobil ohne horizontalen Ueberlauf, mit lesbarem Kontrast und stabilen Prozess-/Preview-/Statusbereichen geprueft werden. Siehe `DARK-MODE.md`, `dark-mode-demo.html` und `tests/dark-mode-playwright.js`.

## Einheitliche Controls

Verwende `CONTROLS.md` als verbindliche Formsprache. Standardcontrols haben 44px Mindesthoehe, 6px Radius, 1px Border, zentrale Padding-/Gap-Tokens und behalten ihre Abmessungen in Hover-, Fokus-, Lade-, Fehler- und Disabled-Zustaenden. Container und Panele nutzen 8px, Pills/Badges 999px. Nutze `.ci-button`, `.ci-button-primary`, `.ci-button-secondary`, `.ci-button-block`, `.ci-icon-button`, `.ci-control`, `.ci-input`, `.ci-input-group`, `.ci-metric-input`, `.ci-segmented`, `.ci-tabs-compact`, `.ci-ai-action` und `.ci-process-step`, statt lokale Varianten zu bauen. Teal ist Primaeraktionen vorbehalten; Standardbuttons bleiben ruhig. Eingabefelder innerhalb von `.ci-input-group` haben innen keine eigenen Rundungen. Pruefe neue UIs gegen `controls-consistency-demo.html` und `tests/controls-consistency-playwright.js`.
## Activity und Kommandoausgaben

Viele Milo-Tools zeigen laufende Arbeit wie eine Kommandozeile. Das ist wichtig, darf aber nicht dominieren.

Standard:

- Topbar zeigt nur kompakten Status wie `Ready`, `Running`, `Done`, `Warning`.
- Ausfuehrliche Logs sind einklappbar mit `.ci-activity` und `.ci-console`.
- Bei groesseren Tools kann es einen eigenen Tab `Activity`, `Runs` oder `Logs` geben.
- Kein dauerhaft grosser Terminalblock auf der Hauptansicht, ausser der Nutzer hat ihn aktiv geoeffnet.

## UI-Regeln

- Verwende `ci-*` Klassen aus `ci.css`, bevor du lokale Stile ergaenzt.
- Verwende `--milo-*` Tokens fuer neue projektspezifische CSS-Regeln.
- Ecken maximal 8px; Standardcontrols 6px, Container/Panele 8px, Pills/Badges 999px.
- Keine Karten-in-Karten.
- Keine dekorativen Gradients, Orbs oder Hero-Layouts.
- Buttons, Inputs, Segmente, Icon-Buttons und KI-Aktionen nutzen die zentralen Control-Klassen und keine lokalen Hoehen/Radien.
- Teal-Buttons nur fuer echte Primaeraktionen verwenden; normale Aktionen bleiben .ci-button/.ci-button-secondary.
- Buttons nutzen Icons, wenn die Aktion dadurch schneller erkennbar wird.
- Ausgewaehlte Toggle-/Segment-Buttons verwenden `--milo-selected-bg` und `--milo-selected-text`, nicht den dunklen Topbar-Ton.
- Native `hidden`-Elemente bleiben unsichtbar, auch wenn `ci-*` Klassen ein eigenes `display` setzen.
- Text knapp halten; keine sichtbaren Bedienungsanleitungen, wenn Controls selbsterklaerend sind.
- Layouts muessen auf Desktop und Mobile ohne Textueberlauf funktionieren.
- Keine Layout- oder Scrollspruenge bei normalen Auswahl-, Status- oder Prozesswechseln.

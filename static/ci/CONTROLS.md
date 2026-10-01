# Milo Controls

Diese Regeln definieren die gemeinsame Formsprache fuer Eingabefelder, Buttons
und interaktive Zustandswaehler in Milo-Apps. Ziel: Alle Tools wirken gleich,
ohne dass jedes Projekt eigene Radien, Hoehen oder Buttonvarianten erfindet.

## Grundsatz

Bedienelemente sind stabil, gleich hoch und klar voneinander unterscheidbar.
Ein Zustandswechsel darf weder Hoehe, Breite noch Ausrichtung veraendern.

## Token

- Standard-Control: `--milo-control-height` = 44px.
- Kompakt-Control: `--milo-control-height-sm` = 34px.
- Grosse Messwert-/Parameter-Eingabegruppen: `--milo-control-height-lg` = 50px.
- Control-Radius: `--milo-control-radius` = 6px.
- Container-Radius: `--milo-container-radius` = 8px.
- Pill-Radius: `--milo-pill-radius` = 999px.
- Control-Rand: `--milo-control-border-width` = 1px.
- Horizontaler Control-Innenabstand: `--milo-control-padding-x`.
- Control-Abstand fuer Icon + Text: `--milo-control-gap`.

## Komponenten

- `.ci-button`: ruhiger Standard-/Sekundaerbutton, 44px Mindesthoehe, 6px Radius, automatische Breite.
- `.ci-button-primary`: Teal-Button nur fuer klare Primaeraktionen wie Start, Erstellen, Export oder Uebernehmen.
- `.ci-button-secondary`: explizite ruhige Variante, wenn semantisch hilfreich.
- `.ci-button-block`: Vollbreite Variante fuer primaere Formularaktionen.
- `.ci-icon-button`: quadratischer Icon-Button, 44px x 44px.
- `.ci-logout-button`: kompakte Topbar-Aktion, gleiche Radius- und Gap-Regel.
- `.ci-control`: generischer Text-/Select-Control fuer projektspezifische Elemente.
- `input.ci-input`, `select.ci-input`, `textarea.ci-input`: native Formularfelder mit Milo-Control-Stil.
- `.ci-input-group`: gerahmte Eingabegruppe mit 6px Aussenradius; innere Felder haben keinen eigenen Radius.
- `.ci-metric-input`: bewusst groessere Messwert-/Parameter-Eingabegruppe, 50px Mindesthoehe und staerkere Zahlendarstellung.
- `.ci-segmented`: segmentierte Auswahl mit 6px Aussenradius; ausgewaehlte Zustaende nutzen Milo-Teal.
- `.ci-tabs-compact`: kompakte Tab-Variante fuer Tools mit vielen Bereichen.
- `.ci-ai-action`: quadratische KI-Aktion mit Sparkles-/Zauberstab-Icon und stabiler Groesse.
- `.ci-process-step`: Prozessschritt als Control, nicht als freie Badge-Sonderform.
- `.ci-badge`: echte Status-/Meta-Pills bleiben pill-foermig.

## Verbindliche Regeln

- Keine lokalen `border-radius`, `height`, `min-height` oder Button-Paddings fuer Standardcontrols.
- Keine Mischung aus eckigen Segmenten, 8px Buttons und runden Inputs in derselben App.
- Ausgewaehlte Segmente, Toggle-Buttons und Prozessschritte verwenden `--milo-selected-bg` und `--milo-selected-text`.
- Deaktivierte, ladende und Fehlerzustaende behalten dieselbe Control-Groesse.
- Icon-Buttons bleiben quadratisch und bekommen immer ein `aria-label` oder einen klaren Tooltip.
- Eingabefelder in `.ci-input-group` uebernehmen die Gruppe als sichtbare Form; innen keine eigenen Rundungen.
- Grosse Hauptaktionen werden nicht ueber eigene Hoehen gebaut, sondern mit `.ci-button ci-button-primary ci-button-block`.
- Container, Vorschauen, Statuspanels und Karten verwenden 8px. Pills/Badges verwenden 999px.

## Uebernahme in bestehende Apps

1. `tokens.css` und `ci.css` aktualisieren oder lokal vendorn.
2. Eigene Button-/Input-Klassen durch `.ci-button`, `.ci-icon-button`, `.ci-control`, `.ci-input`, `.ci-input-group` und `.ci-segmented` ersetzen.
3. Lokale Radien und Hoehen entfernen, wenn sie Standardcontrols betreffen.
4. Vollbreite Hauptaktionen explizit mit `.ci-button ci-button-primary ci-button-block` markieren; normale Aktionen bleiben ruhig.
5. Segmentierte Auswahl und aktive Prozessschritte auf Milo-Teal pruefen.
6. `controls-consistency-demo.html` visuell vergleichen und `tests/controls-consistency-playwright.js` ausfuehren.

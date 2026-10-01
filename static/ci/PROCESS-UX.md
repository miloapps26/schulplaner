# Milo Prozess-UX

Grundsatz: Die Oberflaeche darf bei Auswahl, Zustandswechseln und Prozessschritten nicht springen. Milo-Apps behalten Navigation, Vorschau, Fokus und Scrollposition stabil, solange der Nutzer nicht bewusst navigiert oder scrollt.

## Stabiles Prozesslayout

- Zusammengehoerige Prozessschritte verwenden dieselbe Arbeitsflaeche, Ausrichtung und Navigationsposition.
- Zurueck-/Weiter-Buttons bleiben auf demselben Viewport an derselben Stelle; Navigation liegt vorzugsweise oben in einer gemeinsamen Prozessleiste mit `.ci-process-bar`.
- Die Arbeitsflaeche beruecksichtigt den groessten regulaer benoetigten Zustand. Kurze Schritte duerfen freie Flaeche behalten.
- Dynamische Bereiche wie Vorschlaege, Hoerproben, Validierung und Fortschritt verwenden reservierte Bereiche: `.ci-reserved-region`, `.ci-status-panel`, `.ci-suggestion` oder klar begrenztes Scrollen in `.ci-step-body`.
- Keine universellen starren Pixelhoehen. Nutze responsive Mindesthoehen, stabile Grid-Tracks und bedarfsgerechtes Scrollen. Inhalte duerfen nicht abgeschnitten oder unzugaenglich werden.
- Auswahlwechsel duerfen keinen automatischen Scrollsprung ausloesen. Fokus und Scrollposition bleiben erhalten, ausser der Nutzer wechselt bewusst die Ansicht.

## Bestaendiger Motivbezug

Bild-, Video-, Audio- und dokumentbezogene Werkzeuge verwenden `.ci-media-workbench`:

- Desktop: Vorschau links, Einstellungen rechts.
- Die Referenz bleibt waehrend Texteingabe, Auswahl, Hoerprobe, Validierung und Verarbeitung sichtbar.
- Nach Fertigstellung ersetzt das Ergebnis die Referenz im selben `.ci-preview-frame`.
- Vorschauabmessungen bleiben stabil. Unterschiedliche Medienformate werden mit `object-fit: contain` ohne Layoutsprung eingepasst.
- Mobil: Vorschau und Einstellungen werden untereinander angeordnet. Keine erzwungene Desktop-Aufteilung und keine dauerhaft uebergrosse fixierte Vorschau.

## Einheitliche Verarbeitungszustaende

- Laden ersetzt nicht die gesamte Arbeitsflaeche und nicht das vorhandene Motiv.
- Fortschritt wird platzsparend in das bestehende Layout integriert, zum Beispiel mit `.ci-status-panel` und `.ci-progress`.
- Nutze einheitliche Statusphasen: `idle`, `analyzing`, `creating`, `checking`, `complete`, `error`.
- Hintergrundarbeit wird als Status dargestellt, nicht als scheinbar notwendiger Button `Status pruefen`.
- Zeige die tatsaechliche Phase. Prozentwerte nur bei messbarem Fortschritt; sonst eine unbestimmte Fortschrittsanzeige mit `aria-busy="true"`.
- Eingaben und vorhandene Ergebnisse bleiben bei Fehlern erhalten. Doppelauftraege werden durch deaktivierte Startaktionen verhindert.
- Statusaenderungen werden mit `role="status"`, `aria-live="polite"` oder `aria-live="assertive"` fuer Fehler angekuendigt, ohne Fokus dauerhaft zu verschieben.

## Erkennbare KI-Aktionen

- KI-Aktionen verwenden `.ci-ai-action` mit Sparkles- oder Zauberstab-Icon aus der bestehenden Icon-Bibliothek.
- Die Aktion hat ausreichenden Kontrast, `title`, `aria-label` und eine zugaengliche Beschriftung.
- Aktionen an Textfeldern stehen neben dem Feld oder in einer stabilen Toolbar und ueberdecken den eingegebenen Text nicht.
- Bestehende Inhalte werden nicht ungefragt ueberschrieben. Vorschlaege erscheinen in `.ci-suggestion` und werden bewusst uebernommen.
- Lade-, deaktivierter und Fehlerzustand behalten dieselben Abmessungen.

## Uebernahmeschritte fuer bestehende Milo-Apps

1. Prozess- oder Wizard-Flows in `.ci-process`, `.ci-process-bar`, `.ci-process-stage` und `.ci-process-nav` einfassen.
2. Medien- oder Dokumentbezug in `.ci-media-workbench` mit `.ci-preview-pane`, `.ci-preview-frame` und `.ci-settings-pane` abbilden.
3. Dynamische Bereiche aus der Hauptflaeche herausloesen und in `.ci-status-panel`, `.ci-reserved-region`, `.ci-suggestion` oder `.ci-step-body` begrenzen.
4. Lade- und Fehlerzustaende so umbauen, dass sie Motiv, Eingaben und Ergebnisbereiche nicht ersetzen.
5. KI-Hilfen auf `.ci-ai-action` und `.ci-suggestion` umstellen; Vorschlaege nur nach bewusster Uebernahme anwenden.
6. Mit `process-stability-demo.html` und `tests/process-stability-playwright.js` gegen Desktop, kleinen Laptop und Mobilgeraet pruefen.

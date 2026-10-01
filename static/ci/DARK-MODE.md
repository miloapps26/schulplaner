# Milo Dark Mode

Milo Dark Mode ist der Standardmodus fuer Milo-UIs. Light bleibt als opt-in Variante fuer helle Kontexte, Dokumentnaehe oder ausdrueckliche Nutzerwahl verfuegbar.

```html
<html lang="de">
  ...
</html>
```

## Zielbild

Milo Night Workbench wirkt wie ein ruhiger Kontrollraum: dunkel, technisch, konzentriert und nicht verspielt. Es ist kein Gaming-Theme und keine komplett schwarze Flaeche.

- App-Hintergrund: tiefes Anthrazit statt Schwarz.
- Flaechen: abgestufte, klare dunkle Panels.
- Text: hellgrau statt reines Weiss.
- Teal bleibt Hauptakzent und Auswahlfarbe.
- Blau bleibt zweite Daten- und Messfarbe.
- Borders ersetzen schwere Schatten.
- Status, Fortschritt und KI-Aktionen bleiben sichtbar, aber nicht laut.

## Regeln

- Dark Mode ist der Default und nutzt dieselben `ci-*` Komponenten wie die Light-Variante.
- Neue Farben werden als Tokens in `tokens.css` gepflegt, nicht lokal in Apps dupliziert.
- Apps koennen Light Mode bei Bedarf mit `data-ci-theme="light"` aktivieren, muessen aber Dark und Light mit denselben Layoutregeln testen.
- Ausgewaehlte Buttons bleiben Teal; der dunkle Ink-Ton bleibt fuer Topbar, Konsole und starke Struktur reserviert.
- Datenvisualisierung verwendet auch in Dark Mode die Milo-Chart-Tokens; Achsen, Raster und flaechige Hilfsfarben muessen auf dunklem Hintergrund lesbar bleiben.
- Das Standardzeichen `assets/milo-mark.svg` behaelt die urspruengliche dunkle Milo-Figur auf weissem Hintergrund. Fuer explizite Light-Kontexte steht `assets/milo-mark-light.svg` bereit.

## Pruefung

Vor einer Uebernahme oder Aenderung des Standardmodus in einer App pruefen:

1. Kein horizontaler Ueberlauf auf Desktop, kleinem Laptop und Mobilgeraet.
2. Text, Labels, Buttons, Statusmeldungen und Fehlermeldungen sind kontrastreich lesbar.
3. Fokusrahmen, ausgewaehlte Zustaende und deaktivierte Aktionen sind unterscheidbar.
4. Preview-, Prozess- und KI-Aktionslayouts bleiben stabil wie in Light Mode.
5. PDF- oder Exportvorschauen behalten eigene Ausgabevorgaben und werden nicht blind aus dem Browser-Dark-Mode abgeleitet.

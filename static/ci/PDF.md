# Milo PDFs und Exportnamen

Diese Regeln gelten fuer alle Milo-Anwendungen, einschliesslich CLI, API,
Hintergrundjobs und herunterladbarer Berichte, nicht nur fuer Web-UIs.

## PDF-Gestaltung

- PDFs gehoeren zur gleichen Corporate Identity wie die Anwendung.
- Vollstaendiger, korrekter Produktname und Kategorie stehen im Berichtskopf.
  Der PDF-Titel in den Metadaten verwendet dieselbe Bezeichnung.
- Dunkler Milo-Ink-Kopf, helle Arbeitsflaechen, Teal als Hauptakzent und Blau
  fuer sekundaere Daten. Keine unabhaengige Berichtspalette erfinden.
- `pdf-tokens.json` stellt die Druckfarben aus `tokens.css` bereit. Bei
  Farbaenderungen beide Dateien synchron halten. Downstream-Projekte vendorn
  die JSON-Datei und benoetigte Assets; keine Laufzeitabhaengigkeit zum CI-Ordner.
- Inter bevorzugen, wenn als einbettbare Schrift vorhanden. Sonst ist Helvetica
  als portable PDF-Ersatzschrift erlaubt. Fuer weitere Zeichensaetze geeignete
  eingebettete Schriften verwenden; keine stillen Ersatzkaestchen akzeptieren.
- Ueberschriften, Messwerte, Tabellen und Diagramme folgen einer klaren Hierarchie.
  Tabellenkoepfe auf Folgeseiten wiederholen; Abschnitte nicht unlesbar verkleinern.
- Quelle, Erstellungszeit, App-Version und Seitenzahlen sichtbar machen.
  Lange Dateinamen umbrechen, nicht ohne erkennbaren Quellenbezug abschneiden.
- Jede repraesentative PDF-Seite rendern und auf Lesbarkeit, Seitenumbrueche,
  fehlende Zeichen, Beschnitt und Ueberlappungen pruefen, auch bei langen Namen.

## Exportnamen

- Jeder Export ist auch ausserhalb der App seiner Quelle oder seinem Projekt
  zuzuordnen. Das gilt fuer PDF, CSV, Audio, Archive und deren enthaltene Dateien.
- Zusammengehoerige Dateien teilen einen aussagekraeftigen Basisnamen.
  Ergaenze Artefakttyp und relevante Verarbeitungsschritte/Parameter.
- Beispiel: `Spot_leqm_82dB.wav`, `Spot_leqm_82dB_analysis.csv`,
  `Spot_leqm_82dB_analysis.pdf`; im Multi-Mono-Archiv
  `Spot_leqm_82dB_L.wav`, `Spot_leqm_82dB_R.wav` usw.
- Keine alleinstehenden generischen Namen wie `download`, `analysis` oder
  `normalized`. Interne Speicherbezeichnungen duerfen davon abweichen.
- Pfadtrenner, Steuerzeichen, reservierte Namen und Laengenlimits behandeln.
  Bei mehrdeutiger Bereinigung oder Kuerzung einen stabilen kurzen Hash nutzen.
  Aussagekraeftige Namen duerfen durch Bereinigung nicht unbemerkt kollidieren.
- Explizit vom Nutzer gesetzte Ausgabepfade respektieren. Zugehoerige Berichte
  daran ausrichten. Originale und vorhandene Ausgaben nie still ueberschreiben.
- Tatsachliche Downloadnamen (Content-Disposition), CLI-Ausgaben und
  Archivmitglieder testen, nicht nur interne Dateipfade.

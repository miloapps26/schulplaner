# Milo Datenvisualisierung

Diese Regeln gelten fuer Diagramme, Metriken, Skalen, Spektren, Balken, Linien, Donuts, Heatmaps und Report-Grafiken in Milo-Apps und Milo-PDFs.

## Grundregel

Diagrammfarben kommen aus den Milo-Chart-Tokens. Keine zufaelligen Browser-, Framework- oder Library-Defaultpaletten verwenden. Besonders Braun, generisches Gruen, grelle Regenbogenpaletten und unpassende Rot-Gelb-Gruen-Ampeln sind als Standardfarben zu vermeiden.

## Standardpalette

Verwende diese Reihenfolge fuer kategoriale Reihen:

1. `--milo-chart-1` Teal `#2dd4bf`
2. `--milo-chart-2` Blue `#3b82f6`
3. `--milo-chart-3` Cyan `#38bdf8`
4. `--milo-chart-4` Indigo `#6366f1`
5. `--milo-chart-5` Deep Teal `#14b8a6`
6. `--milo-chart-6` Soft Blue `#60a5fa`
7. `--milo-chart-7` Violet `#8b5cf6`
8. `--milo-chart-8` Slate `#64748b`

## Neutrale Elemente

- Hintergrund-/Restbalken: `--milo-chart-muted`
- Rasterlinien: `--milo-chart-grid`
- Achsen und Ticklabels: `--milo-chart-axis`

## Bedeutung statt Dekoration

- Warnungen, Grenzwerte oder moderate Abweichungen: `--milo-chart-warning`
- Fehler, Ueberschreitungen oder kritische Abweichungen: `--milo-chart-danger`
- Erfolg/OK nur verwenden, wenn die Bedeutung wirklich Erfolg ist, nicht als beliebige Datenreihe.

## Balkendiagramme

Bei Spektren, Energieverteilungen und aehnlichen Balkendiagrammen sollen neutrale oder nicht-dominante Balken hell bleiben. Hervorgehobene Balken verwenden die Chart-Palette, nicht Braun oder generisches Gruen. Wenn eine Farbe fachlich keine Bedeutung hat, lieber Teal/Blue/Cyan nutzen als warme Sonderfarben.

## Downstream-Anforderung

Projekte, die Chart-Libraries verwenden, muessen deren Default-Farbskalen ueberschreiben und die Milo-Chart-Tokens mappen. Bei Canvas/SVG/Chart.js/ECharts/Recharts/D3 sind die Farben explizit aus `tokens.css` oder aus `pdf-tokens.json` zu beziehen.

# Versionierung

Dieses Projekt nutzt Git fuer die technische Historie und ein Changelog fuer die lesbare Zusammenfassung.

## Arbeitsweise

1. Kleine, zusammenhaengende Aenderungen machen.
2. Tests ausfuehren.
3. Aenderungen ansehen:

```powershell
git status
git diff
```

4. Aenderungen vormerken:

```powershell
git add .
git diff --cached
```

5. Commit erstellen:

```powershell
git commit -m "Kurze Beschreibung der Aenderung"
```

## Versionen

Die technische Paketversion steht in `pyproject.toml`.

Fuer veroeffentlichte Staende wird zusaetzlich ein Git-Tag gesetzt:

```powershell
git tag -a v0.1.0 -m "Version 0.1.0"
```

So sieht man spaeter exakt, was sich zwischen zwei Versionen geaendert hat:

```powershell
git diff v0.1.0..v0.2.0
git log --oneline v0.1.0..v0.2.0
```

## Changelog

`CHANGELOG.md` ist fuer Menschen gedacht. Dort steht nicht jeder einzelne Dateidiff, sondern die Zusammenfassung:

- Was wurde hinzugefuegt?
- Was wurde geaendert?
- Was wurde behoben?
- Gibt es Sicherheits- oder Deployment-Hinweise?

Vor einem Deployment sollte die neue Version dort kurz eingetragen werden.

## Production-Release-Mail

Nach jedem Production-Release wird eine E-Mail an alle konfigurierten Production-Empfaenger versendet.

Die Mail enthaelt kurz und verstaendlich:

- neue Funktionen
- behobene Fehler
- relevante Hinweise zur Nutzung
- Link zur Elternansicht

Grundlage sind `CHANGELOG.md`, der Release-Commit und die Release-Notizen seit dem vorherigen Tag.
Die Mail nutzt denselben HTML-Stil wie die bestehenden Schulplaner-Benachrichtigungen. Der Betreff
soll klar die Version nennen, zum Beispiel `Schulplaner v0.8.0 ist live`.

Diese Release-Mail wird nur nach Production-Deployments verschickt, nicht nach lokalen Tests oder
Staging-Deployments.

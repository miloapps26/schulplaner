# Milo Login

Milo-Apps mit Authentifizierung verwenden ein einheitliches Login-Layout nach
dem ruhigen Animation-Muster: dunkler Hintergrund, zentrierte Card, Milo-Zeichen
oben, kurzer Kontext, klare Felder und eine einzelne Primaeraktion.

## Layout

- Kein App-Topbar-Layout auf der Login-Seite.
- Die Login-Seite nutzt `.ci-login-page` als vollhoehe Arbeitsflaeche.
- Das Formular sitzt in `.ci-login-card`, maximal 420px breit.
- Oben steht immer das offizielle Milo-Zeichen: `.ci-mark` mit `.ci-mark-img`.
- Kicker beschreibt den Zugriff, zum Beispiel `ZUGANG`, `GESCHUETZTER TESTZUGANG` oder den fachlichen Bereich.
- H1 ist `Anmelden` oder bei sehr produktnahen Apps der klare Toolname.
- Statusmeldungen wie abgelaufene Sitzung stehen ruhig unter dem Titel, nicht als grosse Warnbox.
- Labels stehen ueber den Feldern; Username und Passwort nutzen `input.ci-input`.
- Die Login-Aktion ist `.ci-button ci-button-primary ci-button-block`.
- Optionale Umgebungsauswahl oder Links stehen unterhalb der Card in `.ci-login-footer`.

## Verhalten

- Falsche Zugangsdaten zeigen eine neutrale Meldung wie `Benutzername oder Passwort falsch.`.
- Keine Information ausgeben, welches Feld falsch war.
- Nach erfolgreichem Login fuehrt die App in das eigentliche Werkzeug.
- Nach 30 Minuten Inaktivitaet erfolgt Auto-Logout; beim erneuten Login kann ein kurzer Hinweis wie `Sitzung wegen Inaktivitaet beendet.` angezeigt werden.

## iPhone Home Screen

Wenn eine Milo-App als URL auf dem iPhone-Homescreen abgelegt wird, muss das
Symbol das Milo-Zeichen sein. Jede deploybare Web-App bindet deshalb mindestens
ein Apple-Touch-Icon ein:

```html
<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png">
<link rel="icon" href="/assets/favicon.svg?v=1.4.0" type="image/svg+xml">
<link rel="icon" href="/assets/favicon-32.png?v=1.4.0" sizes="32x32" type="image/png">
<link rel="shortcut icon" href="/assets/favicon.ico?v=1.4.0">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#0f141a">
<meta name="apple-mobile-web-app-title" content="Toolname">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
```

Das Apple-Touch-Icon ist eine 180x180 PNG-Datei mit weissem Hintergrund, weil
iOS Homescreen-Icons verlaesslich als opake Kachel darstellen soll. Fuer andere
Kontexte liegen weitere Milo-Grafiken in `assets/milo/`.


## Browser Tab Icon

Browser-Tabs muessen ebenfalls das aktuelle Milo-Zeichen verwenden. Favicons werden mit Versions-Query eingebunden, damit alte Browser-Caches nicht das fruehere Icon zeigen.

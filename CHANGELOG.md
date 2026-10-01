# Changelog

Alle nennenswerten Aenderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format orientiert sich an Keep a Changelog. Versionsnummern folgen Semantic Versioning:

- `MAJOR`: inkompatible Aenderungen
- `MINOR`: neue Funktionen ohne Bruch bestehender Nutzung
- `PATCH`: Fehlerkorrekturen, Dokumentation, kleine interne Verbesserungen

## [Unreleased]

## [0.9.1] - 2026-09-24

### Fixed

- Eltern-Login bleibt auch bei aktivem `MILO_AUTH_REQUIRED=1` ueber die hinterlegten WebUntis-Zugangsdaten nutzbar.
- Die Milo/Authentik-Anmeldung ist auf den Adminzugang ausgerichtet; der lokale Admin-Passwortfallback wird bei verpflichtender Authentik-Anmeldung weiterhin deaktiviert.
- Loginseite und Dokumentation unterscheiden klar zwischen Eltern-Login per WebUntis und Admin-Login per Milo/Authentik.

## [0.9.0] - 2026-09-24

### Added

- Authentik/OpenID-Connect-Anmeldung mit Authorization Code Flow und PKCE vorbereitet.
- Milo-Gruppensteuerung ergaenzt: `milo-webuntis-users` fuer App-Zugriff und `milo-admins` fuer Adminzugriff.
- Oeffentlichen, nicht sensiblen Versionsendpunkt `/api/version` ergaenzt.
- Automatisierte Authentik-Tests fuer berechtigte und unberechtigte Gruppen, geschuetzte API-Routen, Logout, Sessionablauf und Versionsendpunkt ergaenzt.
- Getrennte Stage- und Production-Umgebungsdokumentation fuer Authentik, Ports, Domains und Callback-URLs ergaenzt.

### Changed

- App-Anmeldung von lokalen Schulplaner-Passwoertern auf Milo/Authentik als zentrale Identitaetsquelle umgestellt.
- Lokale Passwortanmeldung ist nur noch Entwicklungsfallback und bei `MILO_AUTH_REQUIRED=1` technisch deaktiviert.
- Eltern-Einladungen dienen nur noch zum Hinterlegen der WebUntis-Daten; Schulplaner speichert keine Milo-/Authentik-Passwoerter.
- Login-Seite zeigt primaer `Mit Milo anmelden` und blendet lokale Fallbackfelder nur ein, wenn diese in der Umgebung erlaubt sind.
- Dokumentation und `.env.example` auf die neuen Milo-OIDC-Variablen und getrennte Stage-/Prod-Secrets aktualisiert.

### Security

- Sensitive App-, Admin-, Schreib-, Job- und Daten-APIs bleiben serverseitig geschuetzt und pruefen die Authentik-Rolle/Gruppen statt nur UI-Zustand.
- Logout loescht die lokale Sitzung und die PKCE-State-Cookies; Sitzungen laufen weiter nach dem konfigurierten Idle-Timeout ab.

## [0.8.1] - 2026-09-21

### Changed

- Production-Release-Prozess dokumentiert: Nach jedem Production-Deployment wird eine HTML-Release-Mail im bestehenden Schulplaner-Stil an alle Production-Empfaenger verschickt.

## [0.8.0] - 2026-09-21

### Added

- Elternansicht um den Reiter `Klassenarbeiten` mit anstehenden IServ-Klausurplan-Eintraegen erweitert.
- IServ-Klausurplan-Abfrage ueber das Kalender-Plugin `exam-plan` ergaenzt; pro Profil wird eine Baseline gespeichert, damit E-Mails nur bei neu erkannten Klassenarbeiten versendet werden.
- E-Mail-Benachrichtigung fuer neue Klassenarbeiten ergaenzt und die Beispielkonfiguration um optionale IServ-Variablen erweitert.

## [0.7.3] - 2026-09-18

### Changed

- Bus- und Stundenplanaenderungsmails zeigen nur die tatsaechlich geaenderten Angaben in kurzen Vorher-/Jetzt-Zeilen; der neue Zustand ist farblich hervorgehoben und fuer Kinder ab zehn Jahren schnell erfassbar. Die aktuelle Bus-Empfehlung markiert dieselben Echtzeitabweichungen ebenfalls sichtbar.

### Fixed

- Identische Bus-Aenderungsmails werden auch dann nicht erneut versendet, wenn Geofox kurz zwischen bereits bekannten Zustaenden pendelt; minutengleiche Prognoseschwankungen und parallele Versandpruefungen sind zusaetzlich abgesichert.

## [0.7.2] - 2026-09-17

### Changed

- Die Eltern-Hilfe erklaert jetzt Geofox-Live-Daten, Tagesfahrplan, Direktverbindungen, Hintergrundaktualisierung und Bus-E-Mails mit kurzen, alltagstauglichen Hinweisen.
- Der Fahrdatenhinweis im Profil beschreibt die aktuelle Geofox-Nutzung und den gekennzeichneten GTFS-Rueckfall korrekt.

## [0.7.1] - 2026-09-17

### Fixed

- Die Option `Nur Direktverbindungen` wird auf Mobilgeraeten wieder vollstaendig dargestellt; nach dem Speichern werden alte Tagesfahrplaene verworfen und mit den neuen Profileinstellungen neu geladen.

## [0.7.0] - 2026-09-17

### Added

- Geofox-GTI als bevorzugte Quelle fuer Fahrplanauskunft, Echtzeitinformationen und linienbezogene Stoerungsmeldungen ergaenzt.
- Automatischer Rueckfall auf den bisherigen GTFS-Sollfahrplan, wenn Geofox nicht konfiguriert oder voruebergehend nicht erreichbar ist.
- Technischer Provider-Modus `auto`, `geofox` oder `gtfs` sowie Geofox-Konfiguration ausschliesslich ueber Umgebungsvariablen ergaenzt.
- Busansicht zeigt Datenquelle, Aktualitaet, Verspaetung, Ausfall, Planzeiten, Steig und relevante Fahrplanhinweise differenziert an.
- Sichtbarer Herkunfts-, HVV- und Ohne-Gewaehr-Hinweis in der Busansicht ergaenzt.
- Live-Countdown fuer empfohlene Abfahrten und eine schematische Fahrzeugposition bei tatsaechlich verfuegbaren Geofox-Echtzeitdaten ergaenzt.
- E-Mail-Benachrichtigung ergaenzt, sobald sich die empfohlene Busverbindung des aktuellen Tages gegenueber dem zuletzt erfolgreich verarbeiteten Stand veraendert.
- E-Mails zu Stundenplan- und Busaenderungen in kurze, kindgerechte Saetze mit klarer Vorher-/Jetzt-Erklaerung ueberarbeitet.
- Pro Profil kann mit `Nur Direktverbindungen` festgelegt werden, ob Empfehlungen und Tagesfahrplan Umsteigeverbindungen ausblenden.

### Changed

- Stundenplan und Busverbindungen verwenden getrennt einstellbare Hintergrundintervalle; die heutige Bus-Empfehlung wird standardmaessig alle zwei Minuten und der heutige vollstaendige Tagesfahrplan alle 30 Minuten aktualisiert.
- Die Busansicht liefert sofort den letzten erfolgreichen Hintergrundstand aus. Gleichzeitige Seiten- und Hintergrundabfragen werden zusammengefuehrt, damit keine doppelten Geofox-Abfrageketten entstehen.
- Der Hintergrundcache laedt Empfehlungen fuer alle zehn auswaehlbaren Wochentage vor; die vollstaendigen Tagesfahrplaene werden danach schrittweise fuer dieselben Tage vorbereitet.
- Haltestellensuche und -validierung verwenden bei aktivem Geofox stabile Geofox-IDs; vorhandene namensbasierte und GTFS-basierte Einstellungen bleiben kompatibel.
- Live-Routenergebnisse werden nur kurz gecacht und Geofox-Aufrufe pro Prozess auf hoechstens einen Aufruf je 1,1 Sekunden begrenzt.
- Der Geofox-Tagesfahrplan umfasst wie zuvor der GTFS-Fahrplan alle Verbindungen im konfigurierten Tagesfenster; Empfehlungen bleiben auf Unterrichtsbeginn und -ende zugeschnitten.
- Der Bus-Aktualisieren-Button umgeht den Kurzzeitcache; fehlt in der Tagesliste eine Rückfahrtempfehlung, wird das Zeitfenster nach Unterrichtsende gezielt nachgeladen.
- Die Busansicht und der E-Mail-Monitor laden zuerst nur die relevanten Zeitfenster. Der vollstaendige Tagesfahrplan wird erst beim Oeffnen dieser Ansicht geladen; Fahrplanhinweise werden kurzzeitig separat gecacht.

### Fixed

- Automatische Kurzabfragen brechen einen parallel ladenden Tagesfahrplan nicht mehr faelschlich mit `Tagesfahrplan nicht erreichbar` ab.
- Die Einstellung `Nur Direktverbindungen` bleibt nach dem Speichern des Elternprofils erhalten.
- Die Hinfahrt-Schnellabfrage sucht Ankunftsverbindungen jetzt korrekt rueckwaerts vom spaetesten erlaubten Ankunftszeitpunkt und verliert dadurch keine spaeteren Direktverbindungen mehr.
- Empfehlungen bevorzugen kurze Direktverbindungen vor laengeren Umsteigeverbindungen; passende Rueckfahrten werden im konfigurierten Zeitfenster wieder verlaesslich gefunden.
- Liefert Geofox fuer ein Empfehlungsfenster sporadisch keinen passenden Treffer, wiederholt die App nur die betroffene Richtung mit einer vollstaendigeren Seitensuche, bevor ein leerer Stand gecacht wird.
- Bereits beendete Suchfenster werden stabil aus den Geofox-Plandaten rekonstruiert, statt durch spaetere Echtzeitberechnungen eine zuvor gefundene Tagesempfehlung wieder zu verlieren.

## [0.6.1] - 2026-09-12

### Added

- Elternansicht um einen eigenen Reiter `Hilfe` mit kompakten Erklaerkarten fuer Stundenplan, Hausaufgaben, Bus, Termine und Profil ergaenzt.

## [0.6.0] - 2026-09-12

### Added

- Bebilderte WebUntis-Einrichtungsanleitung fuer Eltern ergaenzt, inklusive Freigaben-/App-Schluessel-Screenshot und Element-ID-Hinweis.
- Haltestellen-Konfiguration nutzt Autocomplete mit Validierungsstatus und gespeicherten Stop-IDs.
- Deploybare Milo-Web-App-Icons, Apple-Touch-Icon und app-spezifisches Webmanifest fuer `Schulplaner` ergaenzt.

### Changed

- Vendored Milo CI auf Version `1.5.0` aktualisiert und die neue Adoption-Pruefung ohne Fehler/Warnungen bestanden.
- Login-Seite auf das aktuelle Milo-Login-Layout ohne normale App-Topbar umgestellt.
- WebUntis-Hilfetexte in der Eltern-Profilmaske auf den grauen Freigaben-Kasten unter dem QR-Code ausgerichtet.
- Bus-Konfiguration beschreibt die verfuegbaren Fahrdaten nutzerverstaendlich als deutschlandweite Nahverkehrs-Sollfahrplaene statt als technische GTFS-ZIP-Quelle.
- Admin- und Elternoberflaeche verwenden aktuelle Milo-Favicon-Links mit Versions-Query.

### Fixed

- Admin-Profil-Dropdown aktualisiert seinen angezeigten Namen jetzt auch dann, wenn sich nur der interne Profilname aendert.
- Profil- und Einladungsformulare behalten Nutzereingaben waehrend automatischer Hintergrundaktualisierungen stabil.
- Busfahrplan nutzt gecachte Fahrplandaten und leert alte Ergebnisse beim Tageswechsel, bis die neuen Daten geladen sind.

## [0.5.0] - 2026-09-12

### Added

- Busansicht bietet einen Segment-Umschalter zwischen `Empfohlen` und `Vollstaendig`; der vollstaendige Tagesfahrplan erscheint nur im entsprechenden Modus.
- Erledigte Hausaufgaben werden sieben Tage nach Faelligkeitsdatum aus der sichtbaren Elternansicht entfernt; eigene erledigte Aufgaben werden dabei lokal bereinigt.

### Changed

- Anwendung, Login, Adminbereich, E-Mail-Betreffzeilen und Mailtexte verwenden den Namen `Schulplaner`.
- Topbar verwendet den Slogan `Organisiert durch die Schulwoche`.
- Busansicht zeigt beim Tageswechsel sofort Ladezustaende, damit keine alten Fahrten fuer den neuen Tag sichtbar bleiben.
- Lokale GMX-/SMTP-Beispiele verwenden `Schulplaner` als Absendernamen.

## [0.4.4] - 2026-09-11

### Fixed

- Mobile Stundenplan-Steuerung zeigt Segment-Buttons wieder in normaler Control-Hoehe statt als ueberhohe Flaechen.

## [0.4.3] - 2026-09-11

### Changed

- Stundenplanansicht startet jetzt in der Tagesansicht; der Umschalter zeigt `Tag` vor `Woche`.
- Mobile Elternoberflaeche gegen horizontalen Seitenueberlauf abgesichert, inklusive Topbar, Tab-Leiste und Terminformular.

## [0.4.2] - 2026-09-11

### Changed

- Vendored Milo CI auf den aktuellen Stand mit vereinheitlichten Controls, Mark-Konsistenztests und generierten Milo-Mark-Assets aktualisiert.
- Sichtbare App-Version auf `v0.4.2` synchronisiert.

## [0.4.1] - 2026-09-11

### Changed

- Vendored Milo CI auf den aktuellen Night-Workbench-Stand aktualisiert, inklusive Dark-Mode-Default, Prozess-UX-Regeln, Demos/Tests und neuer Logo-Variante.
- Stundenplanzellen nutzen CI-Surface-Tokens statt hartem Weiss, damit die App im neuen Dark-Default konsistent bleibt.

## [0.4.0] - 2026-09-11

### Changed

- Einladungs-Setup nutzt den bestehenden WebUntis-Benutzernamen und das WebUntis-Passwort zugleich als App-Login und WebUntis-Abfragezugang.
- Admin-Login ist strikt vom Elternzugang getrennt: Admins werden in den Adminbereich geleitet und erhalten keinen Eltern-Datenzugriff ueber `/app`.
- Eltern- und Setup-Anzeigen verwenden den vollstaendigen Nachnamen statt eines Nachnamen-Initials.
- Busansicht leert alte Fahrplanergebnisse sofort beim Tageswechsel und zeigt den gesamten Tagesfahrplan erst aufgeklappt an.
- Busansicht zeigt den Zeitpunkt der verwendeten GTFS-Fahrplandaten deutlicher.

### Added

- Eltern koennen eigene Termine oder Unterrichtsstunden als woechentliche oder einmalige Eintraege anlegen; diese werden lokal pro Profil gespeichert und in der Stundenplanansicht angezeigt.
- Eltern-Profilfelder enthalten kurze Hinweise dazu, was einzutragen ist und wo die jeweilige WebUntis-Information zu finden ist.
- Eltern koennen pro Profil Bus-Haltestellen und Zeitpuffer fuer Hin- und Rueckfahrt konfigurieren.
- Neuer Eltern-Tab `Bus` zeigt eine passende Tagesempfehlung zum Stundenplan sowie den gesamten relevanten Soll-Fahrplan des Tages auf Basis von GTFS.
- GTFS-Fahrplandaten werden gecacht und nach Ablauf des Aktualisierungsintervalls automatisch neu geladen; bei Fehlern nutzt die App den letzten funktionierenden Stand weiter.

### Fixed

- Admin- und Elternprofil-Formulare behalten ungespeicherte Eingaben waehrend automatischer Hintergrundaktualisierungen.
- Profile aus `tenants.json` erben keine WebUntis-Benutzer, Passwoerter oder App-Schluessel mehr aus der globalen `.env`.
- Tenant-spezifische Eltern-API-Routen pruefen den angefragten Tenant jetzt gegen den angemeldeten Elternzugang.
- Der vorbereitete Einladungslink im Adminbereich bleibt nach automatischen Hintergrundaktualisierungen sichtbar.
- Azure-Upload uebertraegt lokale `config/tenants.json` nicht mehr in den temporaeren Server-Upload.

## [0.3.0] - 2026-09-10

### Added

- Mandanten-/Profilkonfiguration ueber `config/tenants.json` mit getrennten Datenordnern, WebUntis-Zugaengen, Eltern-E-Mails und E-Mail-Empfaengern.
- Eltern-Accounts mit frei waehlbarem Benutzernamen, gehashten Passwoertern und serverseitiger Profilzuordnung.
- Einmalige Einladungslinks fuer die Einrichtung von Elternzugaengen.
- Admin-Oberfläche zum Anlegen und Bearbeiten von Profilen sowie zum Versenden von Eltern-Einladungen.
- Eltern-Profilbereich zum selbststaendigen Hinterlegen der WebUntis-Zugangsdaten und App-Schluessel.
- Milo-Auth-Login mit Session-Cookie, sichtbarem Admin-Logout und Idle-Timeout.
- Beispielkonfiguration fuer mehrere Profile unter `config/tenants.example.json`.
- Hausaufgabenansicht fuer die Elternoberflaeche ergaenzt.
- WebUntis-Hausaufgaben werden read-only aus dem separaten Hausaufgaben-Endpunkt gelesen.
- Eigene Hausaufgaben koennen lokal angelegt, als erledigt markiert und wieder geoeffnet werden.
- Eigene und WebUntis-Hausaufgaben bleiben bis zum Faelligkeitsdatum sichtbar.

### Changed

- Elternzugriff erfolgt ueber Login statt ueber dauerhafte Elternlink-Token; Benachrichtigungen verlinken auf die generische App-Ansicht `/app`.
- Elternansicht zeigt nur Vorname, Nachnamen-Initial, Schule und Klasse als reduzierte Profildaten.
- Neue Profile erben keine WebUntis-Secrets aus dem Default-Profil.
- Admin-Einstellungen und Statusansicht zeigen das aktuell ausgewaehlte Profil.
- Hausaufgaben aus dem Abfragezeitraum bleiben sichtbar; abgelaufene Aufgaben werden separat gekennzeichnet und gezaehlt.

## [0.2.1] - 2026-09-09

### Changed

- Mitgelieferte Milo-CI-Assets auf Version `1.3.2` aktualisiert.
- Sichtbare App-Titel an die aktuelle Milo-CI-Namensregel angepasst.

### Fixed

- Reiner Wochenwechsel im Monitoring-Fenster loest keine hinzugefuegten oder entfernten Stundenplanmeldungen mehr aus.

## [0.2.0] - 2026-08-30

### Added

- Elternansicht um Tages-/Wochenansicht mit Standard-Wochenansicht erweitert.
- Admin-Einstellungen fuer E-Mail-Empfaenger hinzugefuegt.
- Log-Protokoll zeigt jetzt erfolgreichen oder fehlgeschlagenen E-Mail-Versand.
- Fehlgeschlagene Benachrichtigungen werden fuer einen spaeteren erneuten Versand vorgemerkt.
- Staging-Profil fuer `webuntis-dev.miloapps.net` dokumentiert.

### Changed

- Aenderungsansicht zeigt pro Unterrichtsstunde eine fokussierte Bubble und nur die tatsaechlich geaenderten Informationen.
- Azure-Deployment an die gemeinsame AzureHosting-Konvention angepasst.
- App-Host und App-Port sind per `.env` konfigurierbar, damit lokale Entwicklung, Staging und Production getrennt laufen.
- Optional konfigurierbare Host-Pruefung ueber `ALLOWED_HOSTS` ergaenzt.
- Admin-Oberflaeche auf die Bereiche `Einstellungen` und `Log` reduziert.
- Admin-Konfigurationsdetails aus der Oberflaeche entfernt.
- Aenderungsmails auf kurze Zusammenfassung plus Elternlink gestrafft.
- Aenderungsansicht im Stundenplan visuell fokussierter dargestellt.
- Wochenwahl benennt die aktuelle Woche am Wochenende als `Letzte Woche`.
- Mitgelieferte Milo-CI-Assets auf Version `1.1.1` aktualisiert.

### Fixed

- Zufalls-Token-Erzeugung in PowerShell 5 kompatibel gemacht.
- Azure-Upload-Skripte finden OpenSSH auch ueber Windows- und Git-for-Windows-Standardpfade.
- Gehostete UI nutzt wieder die Milo-CI-Styles als mitgelieferte App-Assets.

## [0.1.0] - 2026-08-30

### Added

- Erste versionierte Basis der Stundenplaninfo-App.
- WebUntis-Abfrage, Snapshot-Vergleich und Benachrichtigungslogik.
- Lokale FastAPI-App mit Elternansicht und geschuetzter Admin-UI.
- Deployment-Unterlagen fuer einen kleinen Azure-/VPS-Betrieb.
- Tests fuer die Kernlogik.

# Milo Workflow UX

Diese Regeln gelten fuer Milo-Tools mit laengeren, teuren, asynchronen oder redaktionell freizugebenden Ablaeufen. Sie erweitern `PROCESS-UX.md`: Die Oberflaeche bleibt stabil, und der Arbeitsstand bleibt nachvollziehbar.

## Durable Jobs

- Jeder laengere oder kostenrelevante Auftrag bekommt vor dem Absenden eine dauerhafte Job-ID.
- Die Job-ID wird mit Quelle, Eingaben, Modell/Anbieter, App-Version, Milo-CI-Version und fachlicher Regel-/Konfigurationsversion gespeichert.
- Reload, erneuter Login oder kurz verlorene Serverantwort setzen zuerst den vorhandenen Job fort oder fragen dessen Status ab.
- Eine neue kostenpflichtige Variante entsteht nur durch eine eigene, klar benannte Aktion.
- Primaeraktionen werden waehrend laufender Jobs deaktiviert oder auf den bestehenden Job gelenkt; Doppelauftraege werden serverseitig durch Idempotenzschluessel verhindert.

## Autosave Und Resume

- Eingaben, ausgewaehlte Quellen, Warenkoerbe, redaktionelle Entscheidungen und Zwischenergebnisse werden leise gespeichert.
- Die UI zeigt einen kleinen Speicherstatus, zum Beispiel `Saved`, `Saving` oder `Offline`.
- Vorhandene Eingaben und Ergebnisse bleiben bei Fehlern sichtbar.
- Alte Jobs bleiben mindestens lesbar, wenn sich Regeln, Kataloge oder Konfigurationen geaendert haben.
- Resume ist nur automatisch, wenn Quelle, Datei-/Datenstand, Zielformat, Modell und relevante Regeln uebereinstimmen. Sonst bleibt der alte Stand erhalten und die UI bietet bewusst Migration, neue Variante oder erneute Freigabe an.

## Status Und Fehler

- Laufende Hintergrundarbeit wird als Jobstatus dargestellt, nicht als Button `Status pruefen`.
- Zeige die echte Phase: angenommen, Quellenanalyse, Erstellung, Pruefung, Export, abgeschlossen, fehlgeschlagen oder manueller Eingriff erforderlich.
- Prozentwerte nur verwenden, wenn der Fortschritt wirklich messbar ist. Sonst eine unbestimmte Fortschrittsanzeige verwenden.
- Fehler nennen die passende Ursache: falsche Zugangsdaten, Sitzung abgelaufen, Netzwerk/Server nicht erreichbar, Anbieterfehler, unklarer Auftragsstatus, Validierung oder Berechtigung.
- Pro Fehler gibt es einen passenden naechsten Schritt. Auth-Fehler vermeiden weiterhin Account Enumeration.

## Vorschlaege, Varianten Und Freigaben

- KI- oder Systemvorschlaege ueberschreiben Nutzereingaben nicht automatisch.
- Vorschlaege erscheinen als Kandidat mit `Uebernehmen`, `Verwerfen` und bei relevanten Tools sichtbarem Vergleich zur aktuellen Version.
- Unterscheide `Aenderung anwenden`, `Neue Variante erstellen`, `Pruefung wiederholen` und `Freigeben`.
- Freigaben gelten fuer den angezeigten Stand samt Quellen, Regeln und Versionen.
- Manuelle Endzustaende sind erlaubt und sichtbar, wenn Automatik eine sichere Entscheidung nicht treffen kann.

## Ergebnisse Und Exporte

- Ein abgeschlossenes Ergebnis zeigt eine klare Abschlussaktion wie `Herunterladen`, `Exportieren` oder `Freigabeexport`.
- Browser-native Player- oder Kontextmenues ersetzen keine sichtbare App-Aktion.
- Entwurf, Testpreview, nicht freigegebener Stand, freigegebener Stand, ausstehender Export und Fehlerzustand sind unterscheidbar.
- Historische Snapshots, Preise, Quellen, Umsatzanteile, Freigaben und Exporte bleiben unveraendert, wenn spaetere Stammdaten oder Regeln geaendert werden.

## Globale Herkunft

Diese Regeln wurden aus juengsten Milo-Projekten verdichtet:

- Motion Still Frame: persistenter Produktionsauftrag, Autosave, Versionen, Vorschlagsuebernahme, Download und Fehlerursachen.
- Reframing: Checkpoint-Resume mit exakter Quellen-/Regelidentitaet, Kandidatenvergleich und manueller Endzustand.
- Qrder: idempotente Auftraege, Warenkorb-/Bestellstatus, unveraenderliche Snapshots, klare Konflikte und Polling-Fehler.
- Film Data Agent: belegte Kandidaten, Freigaben, sichtbare Quellen, getrennte Fehlerursachen und kein stilles Ueberschreiben.

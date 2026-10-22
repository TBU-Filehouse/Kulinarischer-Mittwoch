# Journal — Der kulinarische Mittwoch
Stand: 22.10.2026. Dieses Journal protokolliert echte Schritte; Szenariozeiten aus dem Plan sind keine Ist-Zeiten. Keine früheren halbstündlichen Arbeitseinträge rekonstruieren, wenn sie nicht belegt sind.

## Fortsetzung der unterbrochenen Planung — 22.10.2026
- Ist-Stand geprüft: im Zielordner lag nur .gitignore. Fotos als Aufgabenquelle ausgewertet; M1–M8, S1–S5, optionale Funktionen und Abgabeformat übernommen. Drei Nutzer-Skills sowie Origo-/Sourcerer-Struktur gelesen.
- Lastenheft, Pflichtenheft und Projektplan mit MoSCoW erstellt; Fachentscheidungen in ADRs. Fünf Diagramme durch ausdrücklich beauftragtes günstigeres Modell erstellt und anschließend vom Hauptlauf geprüft. Claude-Modellnamen Sonnet/Haiku stehen im hiesigen Agent-Werkzeug nicht zur Verfügung; verwendet: gpt-6-luna.
- Aktueller Umfang ist Dokumentation. Software, Softwaretests und Produktabnahme bleiben offen. Claude-Plugins laut Manifest vorhanden; Hookfunktion nicht geprüft, keine Settings verändert.

## Entscheidungen mit Begründung
1. Flask/Jinja/SQLite statt getrennter SPA/API: weniger Aufbau- und Integrationsarbeit im lokalen Einzelprojekt (ADR-001).
2. Köche nur bei separater Essen-Anmeldung mitzählen: Ernährung und Portionenzahl eindeutig (ADR-002).
3. Absage erhält Daten, aktive Einkaufssumme 0: kein stiller Datenverlust (ADR-003).
4. Namensvetter mit Zusatz: ohne Login mit M5 vereinbar (ADR-004).
5. Koch-Ein-/Austragen ebenfalls ab Dienstag 12 Uhr sperren: Planungssicherheit (ADR-005).

## Prompt-Highlights aus dem vorliegenden Auftrag
- „Ich will das du ein lastenheft und dann ein pflichtenheft aufstellst. Dann Projekt Dokumentation“.
- „am wichtigsten Projektplanung“ und „mach auch moscow prio“.
- Fortsetzungsauftrag nach abgebrochener Sitzung; daraus folgt: vorhandenen Stand prüfen und Dateien konkret schreiben.
- Delegation: nur fünf Diagrammdateien, festgelegte Architektur/Fachregeln, konkrete Gegenproben, keine Commits/Pushes/Versand, keine erfundenen Erfolge.

## Vorlage für tatsächliche Bauintervalle
| Tatsächliche Zeit | Arbeit / KI-Einsatz | Ergebnis, Problem, Entscheidung / nächster Schritt |
|---|---|---|
| beim Bau eintragen | 2–3 Zeilen etwa alle 30 Minuten | nur tatsächlich ausgeführte Arbeit |

## Abweichungen und Abschluss
Keine App gebaut. Kein Softwaretest bestanden. Kein Commit, Push, Versand oder Deployment. Freeze-Zeit aus dem Aufgabenblatt bekannt, Veranstaltungsdatum unbekannt; eine eventuelle Überschreitung ist erst bei tatsächlicher Bau-/Abgabephase einzutragen.

## AP1-Bau und anschließende QS — 22.10.2026
Nutzerauftrag: „a1? und nach a1 qs absichern“, als AP1 verstanden und umgesetzt. Ausführender Agent mit ausdrücklichem Modell gpt-6-luna baute ausschließlich Grundgerüst/Abhängigkeiten; Hauptlauf schrieb unabhängige Tests und nahm selbst ab.
- Lokaler Start und SQLite-Persistenz stehen. Pip-Abhängigkeiten konsistent. Echter HTTP-Server wurde gestartet, mit isoliertem SQL-Testbestand befüllt, beendet und neu gestartet; Zustand blieb erhalten.
- Zusätzliche QS fand eine SQLite-Eigenheit: TEXT PRIMARY KEY ließ NULL zu. Rote Gegenprobe zuerst dokumentiert, explizites NOT NULL ergänzt; danach 14 Tests grün.
- QS-Harness eingerichtet und mit absichtlich fehlgeschlagenem temporärem Test auf Exit 1/technisch_erfolgreich=false geprüft; Probe anschließend entfernt. Keine fachliche Produktabnahme und keine Hookdiagnose. AP2 bleibt nächster Bauabschnitt.

## AP2-Bau und QS — 22.10.2026
Nach Nutzerfreigabe „ok go“ AP2 begonnen. Implementierung an gpt-6-luna mit ausdrücklich begrenzten Dateien rules.py/clock.py delegiert; unabhängige Tests und Review durch Hauptlauf.
- 51 neue Prüfungen: feste Kalender-/UTC-Sollwerte, Mikrosekunden-Fristgrenzen, ungültige Daten/Zeit, Namen/Duplikate und Kochgrenze. Regelkern ohne tatsächliche Uhrabfrage; SystemClock austauschbar.
- Zusätzlicher Reviewfall mit 80-mal ß zuerst rot: Längenprüfung erfolgte nach casefold. Korrigiert auf getrimmten Anzeigenamen vor casefold; Regressionstest bleibt erhalten.
- 65 Tests insgesamt bestanden. MS1 erreicht, nächster Bauabschnitt AP3. Keine Fachformulare/HTTP-Schreibendpunkte, keine Produktabnahme, kein Commit/Push und keine Änderung an Hooks/Settings.

## AP3 und echte Browser-E2E — 22.10.2026
Nutzer beauftragte Monatskalender mit E2E und ergänzte während des Baus die Nutzung von Superpowers/ECC. ECC e2e-testing gelesen; Superpowers-Einstieg, TDD, Debugging, Abschlussverifikation und Code-Review verwendet. Implementierung gpt-6-luna, unabhängige HTTP-/Browserprüfungen und Gegenabnahme Hauptlauf; separates read-only Review ohne offene AP3-Befunde.
- Erster HTTP-Lauf fand falschen Aufruf von calendar.monthdayscalendar auf Modulebene; auf Calendar(MONDAY).monthdayscalendar korrigiert. Die frühe Probe traf außerdem den noch unvollständigen Import-Zwischenstand; das war kein fachlicher TDD-Nachweis.
- Chromium-E2E eingerichtet. Screenshotprüfung zeigte gekürzte Mittwochangaben bei375px: zuerst roten Clipping-Test ergänzt, dann CSS-Wrapping korrigiert. Zusätzlicher frischer Subprozess fand ZoneInfo-Import vor Startguard: erst rot, dann Blueprint-Import hinter Guard verschoben.
- 98 Tests insgesamt:90Logik/HTTP +8Browser. Eigene temporäre DB und feste Testzeit; normaler Datenbestand unverändert. AP3-Leseumfang geprüft, Schreiben und Buchbarkeit erst AP4/AP5. Kein Commit/Push/Deployment oder Änderung laufender Hooks/Settings.

## AP4 — 22.10.2026
Mit echtem roten Formulartest begonnen (CSRF-Form fehlte), Baseline 90 Logik-/HTTP-Fälle grün. Günstiger Implementierer baute App-Dateien; Hauptlauf schrieb unabhängige Tests und nahm ab. Superpowers Test-zuerst/Debugging/Verifikation/Review sowie ECC E2E/Security angewendet.
Korrigiert nach Gegenproben: Unicode-CSRF-TypeError, Detailroute verschluckte GET auf Schreibpfaden, ungespeicherter Gerichtentwurf im Summary, übergroße Requests mit Echo, unbeschränkte Hostnamen. Ein alter Browserselektor wurde durch das neue Textarea mehrdeutig und auf das Beschreibungselement präzisiert. Windows-Unicodeausgabe im Harness mit rotem/grünem Regressionstest abgesichert.
139 Tests grün. Unabhängiger Reviewer bestätigte die Korrektur seines Bodylimit-Befunds. Gesamtproduktabnahme offen; nächster Bauabschnitt AP5. Nutzer stellte Repository tib019/Kulinarischer-Mittwoch für die Fortschrittssicherung bereit; Repository-Verbindung und erster geprüfter Stand folgen.

## Repository-Sicherung — 22.10.2026
Nutzer stellte https://github.com/tib019/Kulinarischer-Mittwoch bereit. Repository war leer und öffentlich. Lokale Git-Sicherung wird vorbereitet; CLI-Identität TBU-Filehouse hat aktuell nur READ. Push ist deshalb offen, bis Schreibzugriff bereitsteht. Lokale Daten, Sitzungskontext, virtuelle Umgebung und Testartefakte bleiben ausgeschlossen. Rechnerbezogene absolute Quellenpfade sind für die öffentliche Dokumentation neutralisiert; lokale Originalnotiz liegt nur im ignorierten Kontextordner.

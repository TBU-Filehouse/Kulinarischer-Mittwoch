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

## Repository-Ziel gewechselt — 22.10.2026
Nutzer bat wegen fehlender Schreibrechte bei tib019 um TBU-Filehouse. Privates Repository TBU-Filehouse/Kulinarischer-Mittwoch erstellt und lokale Origin-URL umgestellt. Erster gesicherter Code-Stand bleibt AP4 mit 139 Tests; vor dem Push wird der QS-Bericht nach diesen Dokumentänderungen erneuert.

## AP5 — 22.10.2026
Neue Sitzung (Claude Code) auf Nutzerauftrag „weitermachen am besten bei ap5“. Superpowers TDD und Verifikation angewendet; 25 HTTP-/Service-Tests (später 30) zuerst geschrieben und rot gesehen, dann Service, Routen und Formular gebaut. Sechs Chromium-Fälle nach der Implementierung ergänzt (kein Test-zuerst-Nachweis).
Gesamtharness fand eine alte AP3-Erwartung „kein Anmeldeformular“; als überholte Bereichsgrenze erkannt und durch Listenprüfung ersetzt. Playwright-Chromium fehlte im Benutzerprofil und wurde per dokumentiertem Befehl nachinstalliert. 175 Tests grün (154+21). Unabhängiges Review durch günstigeres Modell beauftragt. Kein Commit/Push, keine Hooks/Settings verändert. Nächster Bauabschnitt AP6.
Review (Sonnet, read-only): keine kritischen/hohen Befunde. Zwei LOW-Befunde mit rotem Test zuerst korrigiert (Doppelnamenmeldung, CRLF im Hinweis), drei Lückentests ergänzt; zwei LOW-Punkte begründet offen (siehe docs/11-ap5-qs-e2e.md).

## Änderung 1: Ausgaben & Buchhaltung — 22.10.2026
Neues Aufgabenblatt per Foto. Nutzer warnte vor Fallen für Sprachmodelle und bat um Schutz gegen Endlosschleifen. Vorgehen: erst Blatt als Quelle analysieren und rechnerisch gegenprüfen (in sich konsistent), Fallen und Entscheidungen festhalten (docs/12-change-ausgaben.md, ADR-007), dann 42 Abnahmetests aus den Blattzahlen schreiben und rot sehen, dann Umsetzung an Sonnet mit begrenzten Dateien delegieren, dann Abnahme im Hauptlauf.
**Wie viel musste umgebaut werden?** Wenig. Die Struktur aus Service mit Transaktionen, Routen mit CSRF und Jinja-Templates trug die Erweiterung ohne Umbau. Neu: zwei Tabellen (per CREATE IF NOT EXISTS, bestehende Daten bleiben), ein Geldmodul, ein Report-Template; insgesamt rund 560 Zeilen App-Code und 550 Zeilen Tests. Geändert am Bestehenden: Koch-Austragen ist jetzt gesperrt, wenn der Koch Ausgaben hat; die Detailseite bekam eine Budgetkarte. Zwei alte Tests mussten nachgeschärft werden, weil sie die frühere Bereichsgrenze prüften (nach Frist „gar kein Formular“; Kochname nur einmal auf der Seite). Die Dienstagsfrist wurde bewusst nicht wiederverwendet: Belege entstehen nach dem Einkauf.
Gefundene Fallen: Semikolon und Anführungszeichen in Beschreibungen, Umlaute bei Excel-Doppelklick (BOM), Float-Rundung, Frist, Division durch 0, „4 Zeilen“ plus Kopfzeile, CSV-Formelinjektion, selbst abgehakte Checkliste. Abnahme-Haken bleiben offen.
Hängerschutz: Loop-Guard-Skript für Agenten (Wiederholung, Pingpong, nie endende Vordergrundbefehle, Notschalter) mit 22 Tests gebaut, Windows-Kodierungsbefund behoben. Als Hook noch nicht aktiviert (G9), Freigabe beim Nutzer angefragt. 242 Tests grün. Kein Commit/Push.
Loop-Guard auf ausdrückliche Nutzerfreigabe (G9-Ausnahme) als PreToolUse-Hook in .claude/settings.json aktiviert; .claude/kontext/ und settings.local.json in .gitignore. Live-Probe fand Fehlalarm bei `timeout N`-begrenzten Befehlen, mit rotem Test zuerst korrigiert; beide Richtungen live belegt.

## AP6 Einkaufsübersicht — 22.10.2026
Direkt im Hauptlauf gebaut (Auftrag an Sub-Agent wäre länger als die Arbeit). 13 HTTP-Fälle und ein Chromium-Fall zuerst geschrieben und rot gesehen, dann Repository-Lesefunktion, Route, Template und Link. Teststrategie-Bestand ergibt 4 = 2+1+1, Koch ohne Anmeldung zählt nicht. 258 Tests grün. Kein Commit auf Nutzerwunsch.

## AP7 Gesamtprobe — 22.10.2026
Gesamtprobe im Browser gegen den echten Einstieg `python -m app` mit Systemuhr und isolierter DB: kompletter MUSS- und Änderung-1-Ablauf, harter Prozessneustart auf gleichem Port, frischer Browserkontext liest alle Werte und CSV-Bytes identisch; altes Formular wird abgelehnt. Erster Lauf grün; Gegenprobe mit gelöschter DB beim Neustart wurde rot. Eigener Entwurfsfehler vor dem ersten Lauf bemerkt: Neustart auf neuem Port hätte den Alt-Formular-Fall still übersprungen, korrigiert. Anforderungs-/Abnahmematrix docs/15-ap7-gesamtprobe.md. Loop-Guard blockierte einen Doku-Heredoc (Fehlalarm), mit rotem Test zuerst korrigiert. 263 Tests grün. MS3 technisch erreicht; Fachabnahme offen. Nicht committet.

## AP8 Abgabe — 22.10.2026
README-Start in leerem Ordner mit genau den drei Befehlen geprüft (Kopie aller Repository-Dateien, Port 5000, alle Seiten und CSV 200, data/app.db neu angelegt). Abnahme-Checkliste als ausfüllbares Protokoll mit konkreten Eingaben und Sollwerten umgebaut, alte Fassung eingeklappt erhalten; keine Haken gesetzt. README neu gegliedert, veraltete Zwischenstände entfernt. Nachweis docs/16-ap8-abgabe.md. MS4 technisch erreicht; offen bleiben Excel-Doppelklick und fachliche Abnahme durch eine Person.

## Nutzerprüfung und SOLL-Auftrag — 22.10.2026
Nutzer hat die App persönlich im Browser getestet und mündlich gemeldet: „es klappt alles“. Zwei Bedienbefunde aus dem Test: (1) Im Kalender waren offene und geschlossene Mittwoche nicht unterscheidbar — wird mit S4 erledigt (Status je Mittwoch). (2) Ohne rechtzeitig eingetragenen Koch können nach der Frist keine Ausgaben erfasst werden — fachliche Entscheidung beim Nutzer, nicht Teil von S1–S4. Checkliste wird vom Nutzer selbst ausgefüllt; das Modell setzt keine Haken.
Auftrag S1–S4: Entscheidungen in ADR-008 (Warteliste aus Reihenfolge abgeleitet, nur Limit und Absage gespeichert, Ausgaben bleiben bei Absage und Historie möglich). 21 HTTP- und 2 Browser-Abnahmefälle zuerst geschrieben und rot gesehen; Umsetzung an Sonnet mit begrenzten Dateien.

## SOLL S1–S4 und Entscheidung B — 22.10.2026
Sonnet setzte S1–S4 gegen 21 vorab rote Tests um; Abnahme im Hauptlauf mit Stichprobe. Sonnet meldete zwei rote Bestandstests, statt sie selbst zu ändern. Der Nutzer unterbrach, als ich einen Kalendertest anpasste, ohne die angekündigte Prüfung auf abgeschnittenen Text schon belegt zu haben; danach Browserlauf, Abschneide-Prüfung grün. Lehre: Testanpassungen vorher ankündigen, begründen und danach belegen.
Abrechnungslücke per Brainstorming gegen die Quellen geprüft: Die Aufgabenblätter sperren nur die Essen-An-/Abmeldung, die Kochfrist ist eigene ADR-005. Abwägung D (Hinweis) gegen B (Nachtragen nur für die Abrechnung); der Nutzer ließ entscheiden und bestätigte B. Eigener Weg /cooks/backfill, damit die normale Koch-Fristsperre unverändert bleibt. 11 Tests zuerst; einer war ohne Funktion grün und wurde verschärft. Zwei Browsertests „0 Formulare am vergangenen Mittwoch“ bewusst auf „genau das Nachtrage-Formular“ geändert. 298 Tests grün. Nicht committet.

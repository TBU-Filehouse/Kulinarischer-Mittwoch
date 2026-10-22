# Teststrategie und QS-Plan
Status: geplant; kein Anwendungstest wurde ausgeführt, da noch kein Anwendungscode vorhanden ist.

## Ebenen und Gegenproben
| Ebene | Beweist | Positiver Fall | Negativer / Grenzfall |
|---|---|---|---|
| Regeln | Kalender-/Zeitberechnung und Name | 1 s vor Frist, Name anderer Mittwoch | exakt/1 s nach Frist, Rand-Leerzeichen/casefold-Duplikat |
| DB | Integrität/Transaktion | zwei Köche, eine Anmeldung | zwei parallele dritte Köche; Duplicate-Rennen; Rollback ohne Teiländerung |
| HTTP | Server erzwingt Regeln | gültiger POST und 303 | direkter POST trotz ausgeblendeter UI abgewiesen; ungültige enums/IDs |
| Integration | Seiten und gespeicherter Stand stimmen überein | vier bestätigte Essende ergeben 4 im Kalender und Einkauf | Koch allein zählt nicht, stornierte/wartende Person nicht im Einkauf |
| Neustart | dauerhafte Persistenz | Datei bei zweitem Prozess erneut gelesen | Initialisierung überschreibt vorhandenes Gericht nicht |
| Browser | tatsächlich benutzbarer Ablauf | Monat wählen → Koch → Gericht → Anmeldung → Einkauf | verständlicher Duplikat-/Fristfehler, keine Erfolgsmeldung bei Fehler |
Die Zeitprobe verwendet die im Pflichtenheft notierten unabhängigen Winter-/Sommer-Sollwerte. Nicht bloß dieselbe Berechnungsfunktion als Test-Erwartung erneut aufrufen.

## Testdaten
Nur fiktive Namen: Anna Beispiel, Ben Muster, Cora Demo, Deniz Test. Isolierte SQLite-Datei im temporären Verzeichnis. Kein Test verändert data/app.db. Einkaufssoll: zwei „alles“, eine „vegetarisch“, eine „vegan“, ein Hinweis „keine Nüsse“ → Gesamt 4, Kategorien 2/1/1, ein Hinweis. Köche ohne separate Anmeldung ergeben 0 zusätzliche Portionen.

## Mechanische Prüfungen beim Bau
Geplant: scripts/check.py führt Tests aus und erzeugt einen JSON-Bericht mit geprüften Schritten/Exit-Codes, Zeitpunkt, Quellstand-Hash vorher/nachher, quellstand_unveraendert, technisch_erfolgreich und produkt_abgenommen. Bei Änderung während des Laufs kein aktueller technischer Nachweis. Produktabnahme bleibt eigenständig offen und macht technische Einzelergebnisse nicht unsichtbar.

Geplante Befehle nach AP7 (aktuell noch nicht ausführbar):
```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/check.py
```
CI/automatische Hooks sind keine Voraussetzung des Aufgabenblatts. Falls eingerichtet: nur denselben funktionierenden lokalen Check aufrufen, keine Änderung an der laufenden Sitzungs-Konfiguration im Rahmen dieses Auftrags. Das Vorhandensein eines Pluginmanifests beweist keine Hook-Ausführung.

## Abnahme und Fehlerverfahren
03-abnahme-checkliste.md enthält die manuell durchzugehenden Fälle. Für jeden: Ist-Ergebnis, Stand, Nachweis und prüfende Person ergänzen. Ein fehlgeschlagener Fall bleibt offen und erhält eine konkrete Fehlernotiz. „Technisch geprüft“ und „fachlich abgenommen“ getrennt berichten. Aus dem Doku-Linkcheck lässt sich keinerlei App-Funktion ableiten.

## Tatsächlich eingerichtet nach AP1 — 22.10.2026
14 Tests in tests/test_ap1.py; realer HTTP-Serverprozess vor/nach Neustart, Persistenzvergleich aller drei Entitäten, idempotenter Start, unabhängiger DB-Pfad, FK/UNIQUE/Enum/NOT-NULL-Negativfälle, Fehlerpfad für fehlende Zeitzone und ungültigen DB-Pfad. Daten liegen ausschließlich im pytest-Temporärordner.
Gemeinsamer Check: `.venv\Scripts\python.exe scripts/check.py`. Bericht .harness/result.json enthält die ausgeführten Schritte, Exit-Codes, Laufzeiten, Source-Hash vorher/nachher, technisch_erfolgreich und produkt_abgenommen=false. Exit 1 bei technischem Fehler oder verändertem Quellstand. Ein absichtlich fehlschlagender temporärer Test wurde erkannt; negativer Bericht in .harness/negative-probe.json lokal erhalten. Keine Hooks/CI eingerichtet; spätere Fachregeln und Produktabnahme bleiben offen.

## AP2-Regelprüfung — 22.10.2026
51 neue unabhängige Regel-/Clock-/Guardrail-Fälle; zusammen 65 Tests einschließlich AP1. Feste UTC-Sollwerte für Sommer/Winter und Wochen vor/nach Zeitumstellungen; 1 Mikrosekunde vor/exakt/nach Frist; Jahreswechsel; ungültiger Wochentag und naive Zeit. Normalisierung einschließlich Unicode-casefold, Namenszusatz, Längengrenze und Kochgrenze jeweils mit Gegenfällen.
Mechanische Guardrail prüft den AST von rules.py auf erlaubte Imports und verbotene Echtzeit-/Dateiaufrufe; dies ist eine gezielte Projektregel, keine vollständige Sicherheitsanalyse. Der Harness führt alle Tests aus. Transaktions-/HTTP-Integration von M2/M5/M6 bleibt AP4/AP5 vorbehalten, Gesamtproduktabnahme offen.

## Tatsächliche Browser-E2E ab AP3 — 22.10.2026
90 Logik-/HTTP-Fälle und8 Chromium-E2E-Fälle, insgesamt98. Playwright1.64.0 und das Pytest-Plugin pytest-playwright0.10.0 installiert; Browser über separat dokumentierten Installationsbefehl. Versionen in requirements-dev.txt fixiert, keine zusätzlichen Laufzeitabhängigkeiten für Nutzer.
Der Harness hat drei Stufen: dependencies, logic_http, browser_e2e. JUnit-Berichte unter test-results/logic-http.xml und test-results/e2e.xml; Browserfehler erzeugen Screenshot/Trace, jeder Test erhält eigenen Browsercontext. Testserver läuft in eigenem Prozess, eigene temporäre DB, feste UTC-Zeit. Acht Browserfälle: Jahreswechsel, Monatseingabe/Schaltjahr,24MonateNavigation,gespeicherte Details/Zählung,ungültigeURLs,XSS,375px und ungekürzte Mittwochangaben. Kein Retry zur Kaschierung eines Fehlers.
Superpowers-Verifikation: Frische Gesamtläufe vor Abschluss; unabhängiges read-only Review. Rote/grüne Regressionen für mobile Textkürzung und Startprüfung bei frischem Import. Kein voller Buchungs-E2E-Nachweis vor AP4/AP5.


## AP4-QS — 22.10.2026
139 Tests insgesamt: 124 Logik/HTTP und 15 Browser. Zwei Thread-Rennen prüfen maximal zwei Köche und eindeutige normalisierte Namen. Ein Schreiblock-Trace synchronisiert die Fristprobe: Die Uhr wird nach Erhalt der Sperre gelesen; eine inzwischen erreichte Frist verhindert die Buchung. Ein Trigger provoziert einen DB-Abbruch nach lazy Anlage: vollständiger Rollback.
CSRF auf allen Schreibrouten, fremde Sitzung/Origin/Host, Unicode-Token, Sommer-/Winterfrist, Datum/ID, Oversize-413 und größte gültige Unicode-Felder geprüft. Ungespeicherte Entwürfe erscheinen nicht als gespeicherte Gerichte.
Sieben neue Browserfälle prüfen Kochablauf, drei Gerichttypen/Bearbeitung/Monatsübersicht, geschlossene Formulare, Mobilansicht und XSS. Jeder Browserfall hat nun einen eigenen Server mit temporärer DB.
Der Harness erzwingt UTF-8 für Unterprozess und Ausgabe; ein Regressionstest belegt die korrekte Ausgabe von Unicode auf Windows. Reviewbefund zur Bodygrenze behoben und nachgeprüft.

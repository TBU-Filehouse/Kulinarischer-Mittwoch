# AP7 — Gesamtprobe und Anforderungs-/Abnahmematrix
Stand 22.10.2026. MS3 technisch geprüft für diesen Stand; fachliche Abnahme durch eine Person offen.

## Integrierte Gesamtprobe mit echtem Prozessneustart
tests/e2e/test_full_flow_restart.py startet den **echten Einstiegspunkt `python -m app`** mit echter Systemuhr, aber mit isolierter Datenbank (`KUMI_DATABASE` im Temp-Ordner; `data/app.db` bleibt unberührt). Zielmittwoch ist der erste Mittwoch mindestens 8 Tage nach dem Laufdatum, damit die Frist an jedem Tag offen ist.
Ablauf im Chromium-Browser: Kalender → Mittwoch → zwei Köche → Gericht → vier Anmeldungen (2 alles, 1 vegetarisch mit Hinweis, 1 vegan) → Einkaufsübersicht → drei Blattpositionen (Rest 255,95 €) → „Großeinkauf Fisch“ (24,05 € über) → Genehmigung → Monatsreport → CSV-Download.
Dann wird der Prozess hart beendet und auf derselben Datei und demselben Port neu gestartet. Ein frischer Browserkontext liest alle sichtbaren Werte erneut: Köche, Gericht, Anmeldezahl und -liste, Budgetsumme, Überschreitung, Status, Genehmigungsvermerk, Einkaufszahlen, Hinweise, Reportsumme, Erstattung pro Koch und die CSV-Bytes. **Alles ist identisch.** Ein vor dem Neustart geöffnetes Formular wird mit verständlicher Meldung abgelehnt und ändert nichts (neuer Sitzungsschlüssel ohne `KUMI_SECRET_KEY`).
**Gegenprobe:** Ein Prüfskript außerhalb des Repositorys löscht beim Neustart die Datenbank; derselbe Test wird dann rot. Er erkennt Datenverlust also tatsächlich. Kein Test-zuerst-Nachweis, da AP7 keine neue Funktion baut; der erste Lauf war grün.

## Matrix MUSS
| Anforderung | Automatisierter Nachweis | Manuell offen (Person) |
|---|---|---|
| M1 Monatskalender, beliebige Zukunft buchbar | test_calendar.py, e2e/test_calendar_browser.py (24 Monate, Jahreswechsel, Schaltjahr), Gesamtprobe (Buchung ohne vorbereiteten Datensatz) | A-M1 durchklicken |
| M2 max. zwei Köche, Austragen | test_writes.py (inkl. Thread-Rennen), e2e/test_write_browser.py | A-M2 |
| M3 Gericht mit Kennzeichnung | test_writes.py, e2e/test_write_browser.py, Gesamtprobe | A-M3 |
| M4 Essen an-/abmelden, Hinweis optional | test_registrations.py, e2e/test_registration_browser.py, Gesamtprobe | A-M4 |
| M5 Doppelname trim+casefold | test_rules.py, test_registrations.py (Rennen), e2e/test_registration_browser.py | A-M5 |
| M6 Dienstag 12:00 Berlin, direkter POST | test_rules.py (Sommer/Winter/Umstellung), test_writes.py, test_registrations.py | A-M6 |
| M7 Einkaufsübersicht | test_shopping.py, e2e/test_shopping_browser.py, Gesamtprobe | A-M7 |
| M8 Persistenz über Neustart | test_ap1.py (Prozessneustart, anderes Arbeitsverzeichnis), **Gesamtprobe mit Produktionsstart** | A-M8 mit echter data/app.db |

## Matrix Änderung 1
| Anforderung | Automatisierter Nachweis | Manuell offen |
|---|---|---|
| A1 Budget sichtbar | test_expenses.py, e2e/test_expenses_browser.py | A1 |
| A2 Positionen, ausgelegt von Koch | test_expenses.py (Fremd-Koch, Beträge, Float), Browser, Gesamtprobe | A2 |
| A3 Plan vs. Ist, Kosten pro Person | test_expenses.py (0 Anmeldungen, Rundung), Browser, Gesamtprobe | A3 |
| A3a Überschreitung, Genehmigung | test_expenses.py (genau 300 €, Wiederöffnung), Browser, Gesamtprobe | A3a |
| A4 Monatsreport, Erstattung | test_expenses.py, Browser (375 px Status sichtbar), Gesamtprobe | A4 |
| A5 CSV | test_expenses.py (Bytes, BOM, Quoting, Formelschutz), Browser-Download, Gesamtprobe (Bytes über Neustart) | **Doppelklick in Excel** |

## SOLL
Nicht gebaut und nicht als erfüllt markiert: S1 Kochstatus, S2 Warteliste, S3 Absage, S4 Historie-Sperre. S5 mobile Nutzung ist für Kalender, Formulare, Einkauf und Report bei 375 px automatisiert geprüft, wird aber erst nach manueller Prüfung abgehakt.

## Nebenbefund Loop-Guard
Beim Schreiben dieser Datei blockierte der Loop-Guard einen Heredoc, dessen Text `python -m app` erwähnt. Heredocs mit gequotetem Begrenzer werden nie ausgeführt; mit rotem Test zuerst korrigiert. Ungequotete Heredocs bleiben geprüft, weil die Shell dort Backticks ausführt.

## Wiederholen
    .\.venv\Scripts\python.exe scripts/check.py

237 Logik-/HTTP- und 26 Chromium-Fälle: insgesamt 263, grün auf diesem Stand.

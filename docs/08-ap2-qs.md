# AP2 — Fachregeln und QS-Nachweis
Stand 22.10.2026 · AP2 technisch geprüft, Gesamtproduktabnahme offen.

## Umsetzung und Verantwortung
app/rules.py enthält reine Regeln mit den Fehlerklassen RuleViolation, InvalidInputError, DuplicateNameError, CookLimitError und RegistrationClosedError. Keine Datenbank-/Datei-/HTTP-Aufrufe oder aktuelle Uhrabfrage im Regelkern. Aufrufende erhalten Fehler statt eines stillen positiven Ergebnisses.

| API | Vertrag |
|---|---|
| validate_wednesday(date) | Reines date, Wochentag Mittwoch; keine datetime-/String-Eingaben |
| registration_deadline(date) | Dienstag davor 12:00, zoniert Europe/Berlin |
| is_locked(now, date) | Zoniertes now, UTC-Instantvergleich, ab exakter Grenze true |
| ensure_open(now, date) | Bei Sperre RegistrationClosedError, sonst keine Änderung |
| normalize_name(name) | Eingabe trimmen, Länge 1–80 vor casefold prüfen; casefold für Vergleich, innere Leerzeichen erhalten |
| ensure_name_available(name, existing_names) | Vergleicht normalisierte Namen derselben Rolle/desselben Termins; Duplikat ablehnen |
| ensure_cook_slot(count) | 0/1 erlauben, ab 2 ablehnen; negative/bool/nicht ganzzahlige Werte ungültig |

app/clock.py definiert Clock als Protokoll und SystemClock.now() als aktuelle UTC-Zeit. Tests können einen FakeClock übergeben. Die fachliche Anbindung an einen Service folgt in AP4/AP5.

## Unabhängige Gegenproben
51 neue Fälle in tests/test_rules.py; 14 AP1-Fälle bleiben grün, insgesamt 65.
- Winter 28.10.2026: Frist 27.10.2026 11:00 UTC.
- Sommer 24.06.2026: Frist 23.06.2026 10:00 UTC.
- Wochen vor/nach März-Zeitumstellung, Woche vor Oktober-Zeitumstellung und Jahreswechsel 01.01.2025 mit festen unabhängigen UTC-Sollwerten.
- Jeweils 1 Mikrosekunde vor Frist erlaubt, exakt/1 Mikrosekunde danach und am Folgetag gesperrt. Derselbe Zeitpunkt mit unterschiedlichen UTC-Offsets gleich behandelt.
- Alle sechs anderen Wochentage, datetime statt date sowie naive/ungültige Zeitwerte zurückgewiesen. Gültiger Schaltjahr-Mittwoch und fernes zukünftiges Datum erlaubt.
- Anna/ANNA/Rand-Leerzeichen, ß/ss-casefold, sichtbarer Namenszusatz und erhaltene innere Leerzeichen. Leerwerte und zu lange Namen abgewiesen; bestehende Namensliste unverändert.
- Erster/zweiter Koch erlaubt, dritter/weitere abgewiesen; ungültige Zählwerte abgewiesen.
- SystemClock liefert UTC; FakeClock kann die Sperrgrenze reproduzierbar überschreiten. AST-Gegenprobe begrenzt Imports und verhindert bekannte Echtzeit-/Dateiaufrufe in rules.py.

## Beim Review gefundener Fehler
Längenprüfung nach casefold lehnte 80 gültige ß-Zeichen ab, weil deren Vergleichsschlüssel 160 Zeichen lang ist. Erst rote Gegenprobe, dann Prüfung vor casefold korrigiert und vollständiger Testlauf grün. Vergleichsschlüssel bleibt weiterhin eindeutig normalisiert.

## QS und Grenzen
```powershell
.\.venv\Scripts\python.exe scripts/check.py
```
Harness prüft Abhängigkeiten und gesamte Testsuite, bindet Ergebnis an Source-Hash vorher/nachher und führt produkt_abgenommen=false separat. Aktueller lokaler Bericht: .harness/result.json.

MS1 Fundament erreicht. Kalender/Details folgen AP3. Regeln noch nicht in fachliche HTTP-Schreibabläufe eingebunden; Transaktionen, Rennen und direkte POST-Sperre müssen AP4/AP5 nachweisen. Kein Produktfall wird allein aufgrund der Unit-Tests abgehakt. Keine Plugin-/Hookdiagnose und keine laufenden Settings verändert.

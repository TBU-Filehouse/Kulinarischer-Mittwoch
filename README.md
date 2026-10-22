# Der kulinarische Mittwoch
Lokale Hackathon-WebApp zur Organisation des gemeinsamen Mittwochsessens.

**Stand 22.10.2026: AP1 bis AP4 umgesetzt und technisch geprüft.** Flask-Grundgerüst und SQLite-Persistenz stehen. Monatskalender, Mittwoch-Details, Koch-Ein-/Austragen und Gerichtformulare stehen. Essen-Anmeldung und Einkaufsübersicht folgen ab AP5; die vollständige Produktabnahme ist offen.

## Start unter Windows
Voraussetzung: Python mit pip; geprüft mit Python 3.14.7. Internet wird für die erstmalige Installation benötigt. Aus diesem Projektordner:
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app
```
Danach http://127.0.0.1:5000 im Browser öffnen. Beenden mit Strg+C. Debugger und Reloader sind aus. Die Datenbank wird beim ersten Start unter data/app.db angelegt und bei weiteren Starts erhalten. Vor Anmeldeschluss können Köche ein-/ausgetragen und Gerichte gespeichert werden.

Für isolierte Tests/Betriebskopien kann KUMI_DATABASE einen **absoluten** anderen Dateipfad vorgeben; relative Pfade werden abgewiesen. KUMI_PORT kann einen anderen lokalen Port wählen. Start bindet ausschließlich an 127.0.0.1.

## QS ausführen
Nach einmaliger Installation der Entwicklungsabhängigkeiten und des Testbrowsers:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe scripts/check.py
```
Der Check prüft Abhängigkeiten, Logik/HTTP und Chromium-E2E als getrennte Stufen, liefert Exit 1 bei Fehlern und schreibt .harness/result.json mit Quellstand-Hash vorher/nachher. **Technischer Erfolg ist keine Produktabnahme.** 139 Tests prüfen AP1 bis AP4, darunter 15 echte Chromium-E2E-Fälle. Datenbanktests nutzen ausschließlich temporäre Datenbanken, darunter einen echten Serverneustart; die Fachregeln werden ohne Datenbank mit vorgegebenen Zeitpunkten geprüft. Die normale data/app.db wird dabei nicht beschrieben.
Details und Grenzen: [AP1-QS-Nachweis](docs/07-ap1-qs.md) und [AP2-QS-Nachweis](docs/08-ap2-qs.md) sowie [AP3 mit E2E](docs/09-ap3-qs-e2e.md). Die Claude-/Codex-Hookdiagnose bleibt wie besprochen zurückgestellt; der lokale Check ist jetzt tatsächlich eingerichtet.

## Planung und Dokumentation
1. [Lastenheft mit MoSCoW](docs/01-lastenheft.md)
2. [Pflichtenheft](docs/02-pflichtenheft.md)
3. [Projektplan mit Arbeitspaketen und Zeitbudgets](docs/03-projektplan.md)
4. [Teststrategie](docs/04-teststrategie.md) und [Abnahmecheckliste](03-abnahme-checkliste.md)
5. [Projektvertrag](CONTEXT.md), [Journal](02-journal.md), [Quellen/Skills](docs/05-quellen-und-skillinventar.md)

## Diagramme und Entscheidungen
[Architektur](docs/architecture.md) · [Datenmodell](docs/er-diagram.md) · [Klassen](docs/class-diagram.md) · [Sequenz](docs/sequence-anmeldung.md) · [Aktivität](docs/activity-anmeldung.md)

[ADR-001 Stack](docs/adr/ADR-001-lokaler-stack.md) · [ADR-002 Köche](docs/adr/ADR-002-koeche-als-esser.md) · [ADR-003 Absage](docs/adr/ADR-003-absage.md) · [ADR-004 Namen](docs/adr/ADR-004-namensvetter.md) · [ADR-005 Frist](docs/adr/ADR-005-frist.md)

Nächster Bauabschnitt: AP5, Essen-An-/Abmeldung mit Ernährungsform und optionalem Hinweis.


## E2E separat ausführen
```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/e2e --browser chromium --tracing retain-on-failure --screenshot only-on-failure --output test-results/e2e
```
Der Testserver verwendet eine eigene temporäre Datenbank und feste Testzeit. Keine Zeitsteuerung oder Seed-Endpunkte in der normalen App. Berichte, Screenshots und Fehlertraces liegen unter test-results/. Die Browserprüfung deckt Kalender/Details und echte Koch-/Gericht-Schreibabläufe ab; Essensanmeldungen folgen mit AP5.

## AP4 und Formularschutz
[AP4-QS-Nachweis](docs/10-ap4-qs-e2e.md): 124 Logik-/HTTP-Tests plus 15 Chromium-E2E-Fälle. Formularänderungen nutzen SQLite-Schreibtransaktionen, serverseitige Fristprüfung und Session-CSRF-Token. Nur Loopback-Hosts sind zugelassen; HTTP-Formulare sind auf 16 KiB begrenzt. Ohne KUMI_SECRET_KEY entsteht beim App-Neustart ein neuer zufälliger Sitzungsschlüssel: alte Formulare dann neu laden. Daten bleiben erhalten. Dies fügt keinen Login hinzu.

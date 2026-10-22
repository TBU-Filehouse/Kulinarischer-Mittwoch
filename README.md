# Der kulinarische Mittwoch
Lokale WebApp für das gemeinsame Mittwochsessen am Standort Hamburg: wer kocht, was es gibt, wer mitisst, was eingekauft werden muss und was es gekostet hat.

**Stand 22.10.2026: alle MUSS-Anforderungen M1–M8, Änderung 1 (Ausgaben & Buchhaltung) und SOLL S1–S4 gebaut und technisch geprüft. Abnahme-Checkliste am 22.10.2026 in der laufenden App durchgespielt: 24 von 25 Punkten mit Nachweis abgehakt (ADR-009), offen nur D4 (Sperrliste echter Namen fehlt)** ([Abnahme-Checkliste](03-abnahme-checkliste.md)). Kann-Anforderungen C1 (.ics-Export), C2 (Bewertung) und C3 (Rezept) gebaut und technisch geprüft, ohne Produktabnahme; C4 (Erinnerungsmail) und C5 (Firmennetz-Deployment) bewusst nicht gebaut ([ADR-010](docs/adr/ADR-010-kann-umfang.md), [QS](docs/18-kann-qs.md)).

## Start unter Windows
Voraussetzung: Python mit pip (geprüft mit Python 3.14.7); Internet nur für die erstmalige Installation. Aus diesem Projektordner:
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app
```
Danach http://127.0.0.1:5000 öffnen, beenden mit Strg+C. Diese drei Befehle wurden in einem leeren Ordner mit einer Kopie aller Repository-Dateien geprüft ([AP8-Nachweis](docs/16-ap8-abgabe.md)).
Die Datenbank entsteht beim ersten Start unter `data/app.db` und bleibt bei weiteren Starts erhalten. `KUMI_DATABASE` (absoluter Pfad) wählt eine andere Datei, `KUMI_PORT` einen anderen Port. Die App bindet nur an 127.0.0.1. Ohne `KUMI_SECRET_KEY` entsteht bei jedem Start ein neuer Sitzungsschlüssel: Vor dem Neustart geöffnete Formulare dann neu laden, die Daten bleiben erhalten.

## Was die App kann
- **Monatskalender** mit hervorgehobenen Mittwochen, beliebig weit blätterbar; Köche, Gericht und Anmeldezahl je Mittwoch.
- **Köche** (höchstens zwei) und **Gericht** mit Kennzeichnung vegan/vegetarisch/Fleisch oder Fisch.
- **Essen-An-/Abmeldung** mit Ernährungsform und optionalem Allergiehinweis; gleicher Name pro Mittwoch nur einmal (ohne Groß-/Kleinschreibung und Rand-Leerzeichen).
- **Anmeldeschluss** Dienstag 12:00 Uhr Europe/Berlin vor dem Mittwoch, serverseitig auch für direkte Anfragen.
- **Einkaufsübersicht**: Personen gesamt, nach Ernährungsform, Hinweise mit Namen.
- **SOLL S1–S4**: Kochstatus, Portionslimit mit Warteliste, Absage mit Grund, vergangene Mittwoche als Historie; der Kalender zeigt je Mittwoch offen/geschlossen/vergangen/abgesagt. Fehlt nach der Frist ein Koch, kann er nur für die Abrechnung nachgetragen werden.
- **Ausgaben & Buchhaltung** (Änderung 1): Budget 300 € je Mittwoch, Positionen mit „ausgelegt von“, Plan vs. Ist, Kosten pro Person, Genehmigung von Überschreitungen, Monatsreport mit Erstattung pro Koch, CSV für Excel (Semikolon, Dezimalkomma, UTF-8 mit BOM).
Kein Login: Jede Person am lokalen Rechner kann Einträge ändern. Das entspricht dem Hackathon-Umfang.

## Qualitätssicherung
Einmalig die Entwicklungsabhängigkeiten und den Testbrowser installieren, dann den Prüflauf starten:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe scripts/check.py
```
Vier getrennte Stufen (G5-Scan, Abhängigkeiten, Logik/HTTP, Chromium-E2E), Exit 1 bei Fehlern, Bericht `.harness/result.json` mit Quellstand-Hash. **327 Tests**, darunter 29 Browserfälle und 29 Scanner-Tests und eine Gesamtprobe mit echtem Neustart von `python -m app`. Tests verwenden ausschließlich temporäre Datenbanken; `data/app.db` wird nie beschrieben. **Technischer Erfolg ist keine Produktabnahme.**
Welche Anforderung wo geprüft ist: [Anforderungs-/Abnahmematrix](docs/15-ap7-gesamtprobe.md).

**Commit-Schutz (G5):** `scripts/scan_commit.py` sucht in allen Dateien, die git aufnehmen würde, nach Zugangsdaten, persönlichen Pfaden, E-Mail-Adressen, lokalen Datenbanken/Kontextdateien und echten Namen. Die Namensliste liegt bewusst außerhalb des Repositorys in `.Codex/kontext/scan-denylist.txt` (ein Name pro Zeile, wird ignoriert); ohne diese Datei wird die Namensprüfung übersprungen und das gemeldet. Als Git-Hook einmalig pro Klon einrichten (Git Bash):
```bash
printf '#!/bin/sh
root="$(git rev-parse --show-toplevel)"
exec "$root/.venv/Scripts/python.exe" "$root/scripts/scan_commit.py"
' > .git/hooks/pre-commit
```

## Loop-Guard für Agentensitzungen
`.claude/settings.json` aktiviert einen PreToolUse-Hook (`scripts/hooks/loop_guard.py`), der wiederholte Werkzeugaufrufe ohne Fortschritt und nie endende Vordergrundbefehle stoppt. Abschalten mit `KUMI_LOOP_GUARD=off`. Details: [docs/13-loop-guard.md](docs/13-loop-guard.md).

## Dokumentation
- Planung: [Lastenheft mit MoSCoW](docs/01-lastenheft.md) · [Pflichtenheft](docs/02-pflichtenheft.md) · [Projektplan](docs/03-projektplan.md) · [Teststrategie](docs/04-teststrategie.md) · [Projektvertrag](CONTEXT.md) · [Journal](02-journal.md) · [Quellen/Skills](docs/05-quellen-und-skillinventar.md)
- Änderung: [Änderung 1 Ausgaben & Buchhaltung](docs/12-change-ausgaben.md)
- Nachweise: [AP1](docs/07-ap1-qs.md) · [AP2](docs/08-ap2-qs.md) · [AP3](docs/09-ap3-qs-e2e.md) · [AP4](docs/10-ap4-qs-e2e.md) · [AP5](docs/11-ap5-qs-e2e.md) · [AP6](docs/14-ap6-qs-e2e.md) · [AP7](docs/15-ap7-gesamtprobe.md) · [AP8](docs/16-ap8-abgabe.md) · [SOLL S1–S4](docs/17-soll-qs.md)
- Diagramme: [Architektur](docs/architecture.md) · [Datenmodell](docs/er-diagram.md) · [Klassen](docs/class-diagram.md) · [Sequenz](docs/sequence-anmeldung.md) · [Aktivität](docs/activity-anmeldung.md)
- Entscheidungen: [ADR-001 Stack](docs/adr/ADR-001-lokaler-stack.md) · [ADR-002 Köche](docs/adr/ADR-002-koeche-als-esser.md) · [ADR-003 Absage](docs/adr/ADR-003-absage.md) · [ADR-004 Namen](docs/adr/ADR-004-namensvetter.md) · [ADR-005 Frist](docs/adr/ADR-005-frist.md) · [ADR-006 Formularschutz](docs/adr/ADR-006-sitzungsgebundene-formulare.md) · [ADR-007 Ausgaben/CSV](docs/adr/ADR-007-ausgaben-und-csv.md) · [ADR-008 SOLL](docs/adr/ADR-008-soll-umfang.md) · [ADR-009 Abnahme-Haken](docs/adr/ADR-009-haken-durch-modell.md)

Repository: [TBU-Filehouse/Kulinarischer-Mittwoch](https://github.com/TBU-Filehouse/Kulinarischer-Mittwoch) (privat).

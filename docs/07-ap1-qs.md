# AP1 — Umsetzung und QS-Nachweis
Stand 22.10.2026 · Umfang: technisches Grundgerüst und Persistenz, nicht das fertige Produkt.

## Ergebnis
- Python 3.14.7; virtuelle Umgebung .venv; installierte Abhängigkeiten exakt fixiert.
- Flask 3.1.3, tzdata 2026.5; pytest 9.1.1 für Entwicklung.
- `python -m app` bindet an 127.0.0.1:5000, ohne Debugger oder Reloader. GET / zeigt den offenen AP1-Stand, GET /health prüft DB-Erreichbarkeit.
- SQLite-Tabellen wednesday, cook und registration; beim Start nur CREATE TABLE IF NOT EXISTS. FK, UNIQUE und Enum-Constraints aktiv. Datumsschlüssel explizit NOT NULL.
- Standardpfad am Projektroot statt am aktuellen Arbeitsverzeichnis; absolute Testüberschreibung möglich, relative Pfade abgewiesen.

## Unabhängige Gegenproben
14 Tests in tests/test_ap1.py, vom Hauptlauf unabhängig vom ausführenden Agenten geschrieben und ausgeführt:
1. Leere temporäre Datenbank initialisiert alle Tabellen; GET / und /health erfolgreich; POST / nicht erlaubt.
2. Wiederholte Initialisierung erhält alle gespeicherten Entitäten.
3.–7. Fünf unzulässige Schreibfälle: ungültiger FK, doppelter Kochname, doppelte Essensanmeldung, unbekannte Ernährungsform, unbekannte Gerichtkennzeichnung. Jeweils keine Beschädigung des Bestands.
8. Derselbe Name an anderem Mittwoch ist zulässig.
9. Standardpfad bleibt bei anderem Arbeitsverzeichnis am Projektroot; echte Produkt-DB wird dabei durch Ersetzen der Initialisierung nicht berührt.
10. Relativer DB-Override wird abgewiesen.
11. Nicht beschreibbarer DB-Pfad schlägt sichtbar fehl; bestehende Datei bleibt unverändert.
12. Echter OS-Prozess läuft aus anderem Arbeitsverzeichnis, empfängt HTTP-Anfragen und wird beendet; nach Start eines zweiten Prozesses sind Gericht, Koch und Essensanmeldung exakt identisch. Testbefüllung ausschließlich per SQL in temporärer Datei.
13. Fehlende Europe/Berlin-Zone führt zu klarer tzdata-Meldung, bevor eine DB geschrieben wird.
14. NULL-Datum wird abgewiesen.

Die letzte Gegenprobe war zuerst rot: SQLite ließ bei TEXT PRIMARY KEY einen NULL-Wert zu. Ergänzung NOT NULL korrigiert die Ursache; der Test bleibt als Regression erhalten. Kochgrenze und Frist gehören AP2, fachliche Formulare AP4/AP5.

## Mechanische Absicherung
```powershell
.\.venv\Scripts\python.exe scripts/check.py
```
Prüft pip check und pytest, speichert .harness/result.json mit Source-Hash vorher/nachher, Zeitpunkt, Exit-Codes und Laufzeiten. Technischer Exit 0 nur bei grünen Stufen und unverändertem Quellstand; Produktabnahme separat false.

Gegenprobe des Prüfers: temporären garantiert fehlschlagenden Test hinzugefügt. Harness meldete Exit 1, technisch_erfolgreich=false und produkt_abgenommen=false. Negativen Bericht nach .harness/negative-probe.json gesichert, Test wieder entfernt und normalen Check erneut ausgeführt. Ergebnisdateien sind lokal ignoriert, keine Produktdaten enthalten.

## Grenzen und nächster Schritt
Kein vollständiger M8-Bedienfall, da fachliche Eingabeformulare fehlen. Keine M1–M7-Abnahme; keine Hooks/CI und keine Prüfung der Claude-Plugins. Kein Repository initialisiert, kein Commit/Push/Deployment. AP2 beginnt nach diesem geprüften Grundgerüst.

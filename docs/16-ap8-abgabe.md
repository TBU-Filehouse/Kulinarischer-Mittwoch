# AP8 — Abgabe
Stand 22.10.2026. Abgabestand technisch geprüft; fachliche Abnahme durch eine Person offen.

## README-Start in sauberem Ordner (D1)
Ein Prüfskript im Scratchpad (nicht im Repository) kopierte alle Repository-Dateien (`git ls-files -co --exclude-standard`, 73 Dateien) in einen leeren Ordner ohne `.venv`, ohne `data/` und ohne Testartefakte und führte genau die drei README-Befehle aus:
- `py -m venv .venv` → Exit 0
- `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` → Exit 0
- `.\.venv\Scripts\python.exe -m app` → Start auf dem README-Standardport 5000
Danach lieferten `/health`, `/`, eine Mittwoch-Detailseite, die Einkaufsübersicht, der Monatsreport und der CSV-Download jeweils Status 200 (CSV als `text/csv`). `data/app.db` wurde in der Kopie neu angelegt; die App wurde anschließend beendet. Im Projektordner selbst entstand keine Datenbank.
Grenze: Die Installation nutzte Internet und den vorhandenen Python-Launcher dieses Rechners. Ein anderer Rechner ist nicht geprüft.

## Abnahme vorbereitet
[03-abnahme-checkliste.md](../03-abnahme-checkliste.md) ist jetzt ein ausfüllbares Protokoll für die prüfende Person: Vorbereitung, je Fall konkrete Eingaben und Sollwerte (Blattzahlen von Änderung 1 eingeschlossen), Spalten für Ist, Datum und Person, Abgabepunkte D1–D5 und ein Ergebnisfeld. Kein Haken ist gesetzt. Die bisherige Fassung bleibt eingeklappt darunter erhalten.
Ehrliche Grenzen für die Abnahme: Die Sekundengrenze der Frist (A-M6) und direkte Serveranfragen lassen sich von Hand nicht sinnvoll prüfen; sie sind automatisch belegt. Der Excel-Doppelklick (A5) ist nur von Hand prüfbar.

## Abgabestand
README neu gegliedert: Status, drei Startbefehle, Funktionsumfang, QS, Loop-Guard, Dokumentation. Veraltete Zwischenstände („Einkauf folgt mit AP6“, „Hookdiagnose zurückgestellt“) sind entfernt; die Nachweise der einzelnen Pakete bleiben verlinkt. Gesamtharness auf dem Endstand siehe Journal. Gesichert als Commit im Repository TBU-Filehouse/Kulinarischer-Mittwoch.

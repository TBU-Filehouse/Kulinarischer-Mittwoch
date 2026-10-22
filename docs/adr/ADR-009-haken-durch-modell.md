# ADR-009: Das Modell darf Abnahme-Haken setzen, nur mit eigenem Nachweis
**Status:** beschlossen · 22.10.2026

## Kontext
Bisher galt (G7, Checklisten-Kopf): Haken setzt nur die prüfende Person, das Modell nie. Am 22.10.2026 gegen 16:45 hob der Nutzer das für die Abnahme-Checkliste ausdrücklich auf: „jetzt lockerst du das adr nur für die abnahme liste darfst du hacken setzten“.

## Entscheidung
Nur in `03-abnahme-checkliste.md` darf das Modell Haken setzen, und nur für Fälle, die es **selbst in der laufenden App** ausgeführt hat (`scripts/abnahme_lauf.py` gegen `python -m app` mit echter Uhr und eigener Datenbank, oder ein gleichwertig belegter Einzelschritt wie der Excel-Doppelklick). In der Ist-Spalte stehen Datum, Code-Stand, Methode und Ergebnis. Fälle ohne vollständigen Nachweis bleiben offen und nennen die Lücke. Fehlschläge werden als Fehlschlag eingetragen, nie geglättet. Die Unterschrift im Ergebnisfeld bleibt der Person vorbehalten.

## Alternativen
Alle Haken weiter der Person überlassen verworfen: ausdrücklich anders entschieden. Haken allein auf Basis der automatischen Testsuite verworfen: die Checkliste verlangt die Ausführung in der laufenden App. Pauschal alle Haken setzen verworfen: G7 („keine Erfolgsmeldung ohne Nachweis“) bleibt gültig.

## Konsequenzen
Ein Modell-Haken ist ein technischer Abnahmenachweis, keine fachliche Freigabe durch das Team. G7 gilt weiter für alles außerhalb dieser Checkliste.

# ADR-003: Absage erhält Daten und beendet aktive Buchungen
**Status:** für diese Planung entschieden, Umsetzung offen · 22.10.2026

## Kontext
S3 ist Sollumfang; Umgang mit bestehenden Anmeldungen ist bewusst offen.

## Entscheidung
Absage mit Pflichtgrund speichern; Köche und Anmeldungen erhalten und nur lesbar anzeigen. Aktive Einkaufszahl ist 0, historische Zahl getrennt sichtbar. Absage auch nach Buchungsschluss möglich. Für diese Abgabe keine Wiederöffnung.

## Alternativen
Alle Daten löschen verworfen: Verlust von Planung und Nachvollziehbarkeit. Anmeldungen unverändert als aktive Portionen zählen verworfen: falsche Bestellung. Wiederöffnung verworfen: weitere Frist-/Wartelistenregeln im engen Zeitfenster.

## Konsequenzen
Eigenständiger Absageweg als Ausnahme zur Schreibsperre nötig; normale Buchungen bleiben gesperrt. Ohne Login kann keine sichere Koch-/Organisationsberechtigung nachgewiesen werden.

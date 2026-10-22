# AP4 — Köche, Gericht und QS/E2E
Stand 22.10.2026. AP4 technisch geprüft; Gesamtproduktabnahme offen.

## Ergebnis
Koch eintragen/austragen, maximal zwei pro Mittwoch, Namensvergleich trim+casefold. Gericht mit Titel/Beschreibung/Kennzeichnung speichern und bearbeiten. Erfolg erst nach Commit, dann 303 zur Detailseite. Gerichtänderung erhält bestehende Köche und Essensanmeldungen. Alle drei Änderungen sind ab Dienstag 12 Uhr Berlin serverseitig gesperrt.
WednesdayService beginnt BEGIN IMMEDIATE, liest danach die Clock und prüft aktuellen Zustand vor Änderung. Rollback und Schließen bei Fehlern. Austragen bindet Datum und ID. Köche erhöhen die Essenszahl ausschließlich durch separate Anmeldung in AP5.

## Gegenproben
33 Fälle in tests/test_writes.py prüfen gültige Formulare, Zwei-Koch-Grenze, Namensduplikate, Platzfreigabe, drei Gerichttypen, Feldgrenzen, Roundtrip und Datenerhalt.
Echte Thread-Rennen belegen maximal zwei Köche und einen Gewinner bei normalisierten Doppelnamen. Während eines Schreiblocks überschreitet die Testzeit die Frist: Nach Lock-Erhalt wird die Änderung abgelehnt. Ein isolierter Trigger provoziert Abbruch nach lazy Anlage; alles wird zurückgerollt.
CSRF auf allen drei Routen, fremde Sitzung/Origin/Host, Unicode-Token, genaue Frist, Datum/ID, GET-405, SQL/XSS und DB-Ausfall ohne Erfolg oder interne Details geprüft. Ein 1-MiB-Request erhält 413 ohne Echo. Maximal zulässige Unicode-Felder passen.
Ein weiterer Test in tests/test_qs.py sichert Unicode-Ausgabe des Prüfers unter Windows.

## Echte Browser-E2E
Sieben neue Fälle, zusammen 15:
1. Koch eintragen, Duplikatfehler, zweiter Koch, Austragen und Platz wiederverwenden.
2.–4. Alle drei Gerichttypen speichern, bearbeiten, neu laden und im Monatskalender sehen.
5. Geschlossene Mittwoche zeigen keine Schreibformulare.
6. Formulare bei 375 px ausfüllen und speichern; kein Dokumentoverflow.
7. Über das Formular gespeicherte HTML-/Scripttexte bleiben Text.
Jeder Browsertest verwendet einen eigenen Serverprozess mit temporärer SQLite-Datei und fester Testzeit. Keine Produktdaten oder HTTP-Mocks. Mobilbild: test-results/ap4-mobile-forms.png.

## Befunde und Korrekturen
Rote/grüne Gegenproben für Unicode-Token-500, falsche GET-Routenzuordnung, ungespeicherten Entwurf im gespeicherten Summary und fremden Host. Unabhängiges Review fand fehlende HTTP-Bodygrenze: auf 16 KiB begrenzt und 413-Seite ergänzt; Reviewer prüfte nach. Ein maximal gültiges Emoji-Gericht war URL-kodiert 13.530 Byte groß und wurde akzeptiert. Keine offenen AP4-Reviewbefunde.
Ein alter E2E-Selektor wurde durch das neue Textarea mehrdeutig; auf das gespeicherte Beschreibungselement präzisiert. Ein Windows-Unicodefehler im Harness wurde separat rot/grün geprüft und korrigiert.
[ADR-006](adr/ADR-006-sitzungsgebundene-formulare.md) begründet den Formularschutz.

## Wiederholen
    .\.venv\Scripts\python.exe scripts/check.py

124 Logik-/HTTP- und 15 Chromium-Fälle: insgesamt 139. JSON .harness/result.json mit Source-Hash vorher/nachher, Einzelstufen und produkt_abgenommen=false. JUnit und Fehlertraces unter test-results/.

## Grenze
M2/M3 technisch belegt, gesamte Fachabnahme offen. AP5 Essen-Anmeldung und AP6 Einkauf fehlen weiterhin. Kein Login hinzugefügt, keine laufenden Hooks/Settings verändert.

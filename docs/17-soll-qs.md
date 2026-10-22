# SOLL S1–S4 und Entscheidung B — QS und E2E
Stand 22.10.2026. Technisch geprüft; fachliche Abnahme durch eine Person offen.

## Umfang
- **S1** Kochstatus „Köche gesucht“ / „1 Koch fehlt“ / „komplett“ auf Detailseite und im Kalender, abgeleitet aus der Kochanzahl.
- **S2** Portionslimit (1–999 oder unbegrenzt) mit Warteliste. Bestätigt sind die ersten N Anmeldungen nach Zeitpunkt; Nachrücken bei Abmeldung oder Erhöhung ergibt sich daraus. Senken unter die Zahl der Bestätigten wird abgewiesen. Einkauf und Kosten pro Person zählen nur Bestätigte.
- **S3** Absage mit Pflichtgrund, auch nach der Frist, nicht für vergangene Mittwoche, endgültig. Daten bleiben, Planungsänderungen gesperrt. Einkauf zeigt aktiv 0 und die Zahl vor der Absage; der Report markiert „abgesagt“. Ausgaben bleiben möglich.
- **S4** Vergangene Mittwoche sind nur lesbar (Hinweis, keine Planungsformulare, direkte POSTs 409). Der Kalender zeigt je Mittwoch „Anmeldung offen“, „Anmeldung geschlossen“, „Vergangen“ oder „Abgesagt“ und behebt damit den Nutzerbefund aus dem Test.
- **Entscheidung B** (Nachtrag zu ADR-005): Nach der Frist darf ein fehlender Koch nur für die Abrechnung nachgetragen werden; eigener Weg, nur Hinzufügen, höchstens zwei, kein Austragen, nicht bei Absage.
Entscheidungen: [ADR-008](adr/ADR-008-soll-umfang.md), [ADR-005 Nachtrag](adr/ADR-005-frist.md).

## Nachweis
- tests/test_should.py: 21 Fälle, vor der Umsetzung geschrieben und rot gesehen. Umsetzung durch Sonnet mit begrenzten Dateien, Abnahme im Hauptlauf (Stichprobe: Limit-Senkung, Sperren innerhalb der Transaktion, Reihenfolge der Warteliste).
- tests/e2e/test_should_browser.py: 2 Chromium-Fälle (Nachrücken, Absage auf 375 px, Kalenderstatus), vor der Umsetzung rot.
- tests/test_cook_backfill.py: 11 Fälle für B, vor der Umsetzung rot. Ein Fall war anfangs ohne Funktion grün, weil er den Erfolg des Nachtragens nicht prüfte; verschärft, dann rot, dann grün.
- tests/e2e/test_cook_backfill_browser.py: Nachtragen und Ausgabe am vergangenen Mittwoch im Browser; nach der Umsetzung geschrieben, kein Test-zuerst-Nachweis.

## Bewusst angepasste Bestandstests
- test_registrations.py: „nach der Frist gar kein Formular“ wurde zu „keine Koch-, Gericht-, Anmelde- oder Portionsformulare“, weil die Absage nach der Frist erlaubt sein muss (ADR-003/008).
- e2e/test_calendar_browser.py: Die Mittwoch-Zelle hat 4 statt 3 Detailzeilen (neuer Status); die Prüfung auf abgeschnittenen Text bleibt und ist grün.
- e2e/test_write_browser.py und e2e/test_registration_browser.py: am vergangenen 21.10. „0 Formulare“ wurde zu „genau 1 Formular, und zwar das Nachtrage-Formular“ (Entscheidung B).
Jede dieser Änderungen bildet eine ausdrücklich beschlossene Verhaltensänderung ab; keine prüft weniger als die beschlossene Regel.

## Wiederholen
    .\.venv\Scripts\python.exe scripts/check.py

269 Logik-/HTTP- und 29 Chromium-Fälle: insgesamt 298.

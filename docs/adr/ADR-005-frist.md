# ADR-005: Dienstagsschluss sperrt auch Koch-Ein- und Austragen
**Status:** für diese Planung entschieden, Umsetzung offen · 22.10.2026

## Kontext
M6 sperrt Essen-An-/Abmeldungen ab Dienstag 12 Uhr deutscher Zeit; Kochfrist ist ausdrücklich offen.

## Entscheidung
Ab exakt Dienstag 12:00 Europe/Berlin vor dem Mittwoch sind Koch-Ein-/Austragen und normale Bearbeitung einschließlich Gericht gesperrt. S3-Absage bleibt als begründete Ausnahme möglich.

## Alternativen
Köche unbegrenzt ändern lassen verworfen: Einkauf und Verantwortung könnten nach Planungsabschluss wegbrechen. Sonderfrist Mittwochmorgen verworfen: weitere Zeitregel ohne Aufgabenbasis.

## Konsequenzen
Vorhersehbarer eingefrorener Plan; spätere reale Kochabsagen brauchen bei implementiertem S3 eine Terminabsage. Direkte Serveranfragen müssen dieselbe Sperre einhalten. Uhrzeit als zoniertes Kalenderdatum berechnen, nie mit festem UTC-Offset.

## Nachtrag 22.10.2026 — Koch für die Abrechnung nachtragen (Entscheidung B)
Anlass: Der Nutzertest zeigte, dass ein Mittwoch ohne rechtzeitig eingetragenen Koch nie abgerechnet werden kann, weil Ausgaben einen Koch des Mittwochs verlangen (Änderung 1, A2) und diese ADR Köche nach der Frist sperrt. Die Aufgabenblätter selbst sperren nach der Frist nur die Essen-An-/Abmeldung (M6); die Kochfrist ist eine Projektentscheidung.
Entscheidung (nach Abwägung gegen eine reine Hinweis-Lösung vom Nutzer bestätigt): Ein eigener Weg `POST /wednesdays/{date}/cooks/backfill` erlaubt **nach** der Frist, auch an vergangenen Mittwochen, **nur das Hinzufügen** eines fehlenden Kochs. Höchstens zwei Köche, Doppelnamen verboten, Austragen bleibt gesperrt, abgesagte Mittwoche bleiben gesperrt, vor der Frist wird der Weg abgewiesen. Die normale Koch-Eintragung bleibt nach der Frist gesperrt.
Warum das den Zweck dieser ADR nicht schwächt: Geschützt war die Planungssicherheit des Einkaufs. Nachtragen kann nichts wegbrechen lassen, und Köche zählen nicht als Essende (ADR-002); die Einkaufszahlen bleiben unverändert (Test).
Verworfen: reine Hinweis-Lösung (Lücke bliebe, Belege gingen wieder per Mail); freier Name bei „ausgelegt von“ (verletzt A2); Kochfrist allgemein aufheben (lockert mehr als nötig).

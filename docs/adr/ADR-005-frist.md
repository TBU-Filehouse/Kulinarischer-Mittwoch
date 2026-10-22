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

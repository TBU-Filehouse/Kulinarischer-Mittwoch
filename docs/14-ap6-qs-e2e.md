# AP6 — Einkaufsübersicht (M7), QS und E2E
Stand 22.10.2026. AP6 technisch geprüft; Gesamtproduktabnahme offen.

## Ergebnis
`GET /wednesdays/{date}/shopping` zeigt Personen gesamt, die drei disjunkten Ernährungsformen (alles/vegetarisch/vegan) und alle Allergien/Hinweise mit Anzeigenamen, dazu das Gericht. Erreichbar über den Link „Einkaufsübersicht“ auf der Detailseite. Nur lesend: legt keine Datensätze an und bleibt auch nach der Frist lesbar. Gezählt werden ausschließlich Essen-Anmeldungen; Köche ohne eigene Anmeldung zählen nicht (ADR-002). Keine erfundenen Zutatenmengen.
Gesamtzahl, Kategorien und Hinweise kommen aus einer einzigen Abfrage, damit sie nicht auseinanderlaufen können (Lehre aus dem AP5-Review).

## Gegenproben
13 Fälle in tests/test_shopping.py, vor der Umsetzung geschrieben und rot gesehen (Route fehlte): Teststrategie-Bestand 2 alles + 1 vegetarisch + 1 vegan = 4 mit Koch ohne Anmeldung, Hinweis „keine Nüsse“ genau einmal mit Namen, leerer Mittwoch mit Nullen ohne Datensatzanlage, Abmeldung senkt Zahlen und entfernt Hinweis, Lesbarkeit nach Frist, Gericht sichtbar, ungültige/Nicht-Mittwoch-Daten 400, Escaping, Link von der Detailseite, POST nicht erlaubt.
Ein Chromium-Fall (tests/e2e/test_shopping_browser.py) legt den Bestand über die echten Formulare an, folgt dem Link und prüft Zahlen, Hinweis und 375 px ohne Überlauf (test-results/ap6-mobile-shopping.png). Er wurde vor der Umsetzung geschrieben und war rot (Link fehlte).

## Wiederholen
    .\.venv\Scripts\python.exe scripts/check.py

233 Logik-/HTTP- und 25 Chromium-Fälle: insgesamt 258.

## Grenze
M7 technisch belegt. Damit sind alle MUSS-Bausteine M1–M8 und Änderung 1 gebaut (MS2 MUSS-Durchstich technisch erreicht). Offen: AP7 integrierte Gesamtprobe mit Prozessneustart, AP8 Abgabe, Excel-Doppelklick und fachliche Abnahme durch eine Person.

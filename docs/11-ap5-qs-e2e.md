# AP5 — Essen-An-/Abmeldung, QS und E2E
Stand 22.10.2026. AP5 technisch geprüft; Gesamtproduktabnahme offen.

## Ergebnis
Auf der Detailseite können sich Personen mit Name, Ernährungsform (alles/vegetarisch/vegan) und optionalem Allergie-/Hinweistext zum Essen anmelden und wieder abmelden. Die Liste zeigt Name, Ernährungsform und Hinweis; die Anmeldezahl auf Detail und Monatskalender folgt sofort.
Routen: `POST /wednesdays/{date}/registrations` und `POST /wednesdays/{date}/registrations/{id}/remove`. Erfolg 303 auf die Detailseite, ungültige Eingabe 400, fremde/unbekannte ID 404, Doppelname oder geschlossene Frist 409, Datenbankfehler 500 ohne interne Details.
`WednesdayService.add_registration/remove_registration` folgen dem AP4-Muster: BEGIN IMMEDIATE, Uhr erst nach Lock lesen, Frist und Namensbestand in derselben Transaktion prüfen, lazy Mittwoch-Anlage, UNIQUE(date, normalized_name) als zweite Sperre gegen Rennen. Abmeldung löscht den Datensatz (Must-Ausbau laut Pflichtenheft); danach darf derselbe Name vor Frist erneut buchen. Köche zählen weiterhin nur mit eigener Essensanmeldung (ADR-002). Hinweis leer → NULL, sonst getrimmt, höchstens 1000 Zeichen. Keine Schemaänderung, keine neuen Abhängigkeiten.

## Gegenproben (Logik/HTTP)
30 Fälle in tests/test_registrations.py; die ersten 25 vor der Implementierung geschrieben und rot gesehen (Service-Methode und Routen fehlten), danach grün:
- jede Ernährungsform ohne Hinweis, Hinweis getrimmt und angezeigt, fehlendes Hinweisfeld optional;
- „ Anna “/„anna“ am selben Tag 409 mit erhaltenem Entwurf, anderer Mittwoch erlaubt, Namensvetter mit Zusatz erlaubt;
- leere/zu lange Namen, ungültige Ernährungsform, Hinweis mit 1001 Zeichen → 400 ohne lazy Anlage;
- Abmeldung senkt Zahl, Wiederanmeldung danach erlaubt; fremdes Datum/unbekannte ID 404 ohne Änderung;
- Koch darf zusätzlich essen, Kochliste erhöht die Zahl nicht;
- Winter 27.10.2026 10:59:59 UTC erlaubt / 11:00 UTC gesperrt, Sommer 23.06.2026 09:59:59 / 10:00 UTC; An- und Abmeldung per direktem POST 409, Formulare ausgeblendet, Daten bleiben lesbar;
- CSRF fehlend/falsch auf beiden Routen 403, GET 405, Nicht-Mittwoch 400, SQL-/HTML-Text sicher, DB-Ausfall 500 ohne Details, maximale Unicode-Eingabe passt unter das 16-KiB-Limit;
- echtes Thread-Rennen „ Anna “/„ANNA“ mit genau einem Gewinner; umgangene Vorprüfung wird über UNIQUE auf DuplicateNameError abgebildet.

## Echte Browser-E2E
Sechs neue Chromium-Fälle in tests/e2e/test_registration_browser.py, eigener Serverprozess mit temporärer DB und fester Testzeit:
1. Drei Ernährungsformen mit/ohne Hinweis anmelden, abmelden, Zahl auf Detail und im Monatskalender.
2. Doppelname abgewiesen, Entwurf bleibt; anderer Mittwoch erlaubt.
3. Koch und Essender getrennt gezählt.
4. Geschlossener Mittwoch ohne Formulare.
5. 375 px mit langem Hinweis ohne Dokumentüberlauf (test-results/ap5-mobile-registration.png).
6. HTML/Script in Name/Hinweis bleibt Text.
Diese Browserfälle wurden nach der Implementierung geschrieben und sind kein Test-zuerst-Nachweis.

## Befunde und Korrekturen
- Ein AP3-Browsertest erwartete ausdrücklich „kein Anmeldeformular“ als damalige Bereichsgrenze. AP5 hebt diese Grenze bewusst auf; die Erwartung prüft jetzt, dass gespeicherte Anmeldungen gelistet werden.
- In dieser Arbeitsumgebung fehlte der Playwright-Chromium-Cache; per dokumentiertem `playwright install chromium` nachinstalliert, nichts im Repository.

## Unabhängiges Review
Read-only Review durch günstigeres Modell (Sonnet): keine kritischen oder hohen Befunde. Umgesetzt mit Test zuerst (rot, dann grün):
- Doppelnamenmeldung sprach von „Rolle“; jetzt „bereits zum Essen angemeldet“.
- Browser senden Textarea-Umbrüche als CRLF, zählen sie aber als ein Zeichen; ein gültiger 1000-Zeichen-Hinweis wurde abgelehnt. CRLF wird vor Kürzen und Längenprüfung zu LF normalisiert.
Drei Lückentests ergänzt, die sofort grün waren und bestehendes Verhalten absichern: Entwurf bleibt bei 400 erhalten, Koch- und Essensentwurf bleiben getrennt, Koch-ID entfernt keine Anmeldung.
Bewusst offen gelassen: Detailanzeige liest Zahl und Liste in getrennten Statements (bestehendes Muster, nur kurzzeitige Anzeigeabweichung möglich); ungültige Eingabe nach Frist ergibt 400 statt 409, ohne Änderung, wie bei Köchen.

## Wiederholen
    .\.venv\Scripts\python.exe scripts/check.py

154 Logik-/HTTP- und 21 Chromium-Fälle: insgesamt 175. Bericht .harness/result.json mit Source-Hash, Einzelstufen und produkt_abgenommen=false.

## Grenze
M4/M5/M6 technisch belegt; fachliche Abnahme durch eine prüfende Person offen. AP6 Einkaufsübersicht folgt als nächster Bauabschnitt, danach AP7/AP8.

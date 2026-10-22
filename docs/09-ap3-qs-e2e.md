# AP3 — Monatskalender, Details und echte Browser-E2E
Stand22.10.2026. Technischer AP3-Leseumfang geprüft; gesamtes Produkt nicht abgenommen.

## Gebaut
Deutscher Monatskalender mit Montag zuerst und deutlich markierten Mittwochen. Vormonat/Folgemonat, Heute und Monatseingabe; dynamisch berechnete Termine im Python-Datumsbereich1–9999. Details zeigen Datum, Gericht/Beschreibung/Kennzeichnung, Köche, Anmeldezahl und Dienstagsschluss in Europe/Berlin. Leere Termine werden lesend dargestellt, nicht beim Anzeigen gespeichert. Monatszellen zeigen gespeicherte Daten ohne Koch-/Essenden-Zählprodukt. Fremder Text bleibt escaped.

routes.py bündelt den kleinen Blueprint statt einer zusätzlichen leeren calendar_view.py. Repository-Verbindungen schließen zuverlässig. CLOCK ist pro App injizierbar und wird pro Darstellung einmal gelesen.

## Echte E2E
Chromium öffnet die laufende Flask-App über HTTP; die App liest SQLite. Keine HTTP-Mocks. Testserver in eigenem Prozess mit ausschließlich temporärer DB, fiktiven Daten und festem22.10.2026-Zeitpunkt. Acht Fälle:
1. Dezember2026 → Januar2027 → zurück, Wochentagsreihenfolge.
2. Monatseingabe Februar2012, Schalt-Mittwoch29.02 öffnen und zurück.
3.24-mal auf Folgemonat klicken, Oktober2028, bisher nicht angelegten25.10 öffnen.
4. Vorhandenes Gericht, zwei Köche, drei Anmeldungen: Count3 und vollständige Details.
5. Ungültige Monat-/Datum-URL: verständliche400-Seite.
6. Script-/HTML-Eingaben werden angezeigt, nicht ausgeführt; keine Browser-JavaScript-Fehler.
7. Kalender/Details bei375px ohne horizontales Dokumentoverflow; Kalender darf innerhalb seiner eigenen Region scrollen.
8. Mittwoch-Angaben werden auch bei375px vollständig umgebrochen, nicht mit Ellipsis abgeschnitten.

25 weitere HTTP-Fälle prüfen Validierung, Randmonate, Berliner Standardmonat, einmaligen Clock-Aufruf, leere GETs ohne DB-Anlage, Fristanzeige und isolierten Start ohne Zeitzonendaten. Mit65 bestehenden Fällen insgesamt98:90Logik/HTTP +8Browser.

## Gefundene und korrigierte Fehler
- HTTP-Lauf: Calendar-API irrtümlich auf Modulebene aufgerufen. Explizite Calendar(MONDAY)-Instanz behebt Laufzeitfehler und schützt Wochenanfang vor globalem Zustand.
- Screenshot/Browser: nowrap/ellipsis kürzte Essenszahlen und Texte. Roter Browsertest belegt, CSS-Wrapping korrigiert, Gegenprobe grün.
- Frischer Prozess: Routenimport las Zeitzonendaten vor verständlicher Startup-Prüfung. Roter Subprozess-Test belegt; Import hinter expliziten Guard verschoben, Gegenprobe grün.

## Wiederholen und Artefakte
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe scripts/check.py
```
Drei getrennte Stufen mit Exit-Codes: dependencies, logic_http, browser_e2e. Fehlender Browser/Plugin ist Fehler, kein Skip. JSON .harness/result.json mit Source-Hash vorher/nachher und produkt_abgenommen=false. JUnit test-results/logic-http.xml und test-results/e2e.xml; Fehlertrace/Screenshot unter test-results/e2e/. Ansichtsbilder: test-results/ap3-desktop-calendar.png, ap3-mobile-calendar.png und ap3-detail.png.

## Superpowers und ECC
Angewendet: Superpowers using-superpowers, TDD für neue Regressionsfälle, systematic-debugging, verification-before-completion und requesting-code-review; ECC e2e-testing. Unabhängiger read-only Reviewer fand keine offenen AP3-Befunde. Die zusätzliche Startguard-Gegenprobe des Hauptlaufs fand danach den oben dokumentierten Fehler; korrigiert und erneut geprüft.
Der Frameworkwunsch traf während der Implementierung ein. Frühere Codearbeit wird nicht rückwirkend als vollständiger Test-zuerst-Zyklus ausgegeben. Keine Installation/Änderung von Plugins, Hooks oder laufenden Settings aus dieser Skillnutzung ableiten.

## Offene Produktgrenze
AP4: Koch-/Gerichtformulare samt Transaktionen, CSRF und E2E-Schreibablauf. AP5: Essensanmeldung und direkte POST-Fristsperre. AP6: Einkaufsübersicht. M1-Buchbarkeit ist erst mit diesen Abläufen vollständig geprüft; aktueller AP3-Nachweis deckt das Lesen ab. S5-Mobilumfang bislang nur Kalender/Details, keine Abnahme ungebauter Formulare. Kein Commit/Push/Deployment.

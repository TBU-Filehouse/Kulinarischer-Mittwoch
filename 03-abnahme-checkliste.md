# Abnahme-Checkliste
Stand 22.10.2026 · **Alle Softwarefälle offen: Anwendung noch nicht gebaut.**
Erst nach tatsächlicher Ausführung abhaken. Für jeden Fall Ist-Ergebnis, Datum/Uhrzeit, Code-Stand und Beleg ergänzen. Die Tabelle allein ist kein Nachweis.

## MUSS
- [ ] A-M1 / AP3: Monatskalender zeigt Datum, Köche, Gericht, Anmeldezahl und hervorgehobene Mittwoche. Dezember/Januar, Schaltjahr und Mittwoch 24 Monate später prüfen. Vor Frist ohne vorbereiteten Datensatz buchbar.
- [ ] A-M2 / AP4: 0 → 1 → 2 Köche; dritter wird abgewiesen. Austragen vor Frist öffnet Platz. Doppelname und gleichzeitige dritte Buchungen verändern Zustand nicht unzulässig.
- [ ] A-M3 / AP4: Titel/Beschreibung und alle drei Gerichtkennzeichnungen speichern/neu laden. Leerer Titel und ungültige Kennzeichnung werden zurückgewiesen.
- [ ] A-M4 / AP5: Mit Name und jeder Ernährungsform anmelden; Hinweis optional; Abmeldung entfernt die Person aus der aktiven Zahl.
- [ ] A-M5 / AP2/AP5: „ Anna “ und „anna“ am selben Tag kollidieren. Anderer Mittwoch erlaubt. Zwei Namensvetter mit sichtbarem Zusatz möglich. Nach Abmeldung kann derselbe Name vor Frist erneut buchen.
- [ ] A-M6 / AP2/AP5: 27.10.2026 11:59:59 Berlin erlaubt; ab 12:00 gesperrt für 28.10.2026. Dasselbe für 23.06.2026/24.06.2026. UTC-Soll 11:00 bzw. 10:00. Direktes POST und alte offene Browserseite umgehen Sperre nicht; Zustand sichtbar. Koch-Ein-/Austragen ebenfalls gesperrt.
- [ ] A-M7 / AP6: Fiktiver Bestand 2 alles + 1 vegetarisch + 1 vegan ergibt 4. Hinweise mit Namen vollständig; Koch ohne separate Essen-Anmeldung erhöht Zahl nicht.
- [ ] A-M8 / AP1/AP7: Köche, Gericht und Anmeldungen anlegen; Prozess wirklich beenden, neu starten, Daten identisch. Neues Browserfenster liest selben Serverbestand. Kein In-Memory-Ersatz.

## SOLL (nur als erfüllt markieren, wenn gebaut und geprüft)
- [ ] A-S1: 0 Köche „Köche gesucht“, 1 „1 Koch fehlt“, 2 „komplett“.
- [ ] A-S2: Limit 2 → dritte Person wartet; Abmeldung rückt älteste Person nach. Einkauf zählt nur bestätigte Personen. Gleichzeitige Anfragen überschreiten Limit nicht. Nach Frist weder Abmeldung noch Nachrücken; Limit unter bestehende Zahl abweisen.
- [ ] A-S3: Absage benötigt Grund, erhält Daten, sperrt Buchungen; Einkaufsansicht zeigt abgesagt/aktive Zahl 0. Absage auch nach Frist möglich; kein Wiederöffnen.
- [ ] A-S4: Vergangenheit lesbar, direkte Änderungen serverseitig gesperrt.
- [ ] A-S5: Bei 375 px Breite sind Kalender, Formulare, Fehlermeldungen und Aktionen bedienbar.

## Abgabe
- [ ] D1: Code und README vorhanden; frischer Start in höchstens drei dokumentierten Befehlen tatsächlich geprüft.
- [ ] D2: 02-journal.md mit tatsächlichem Vorgehen, Entscheidungen, Prompt-Highlights und etwaigen Abweichungen gefüllt.
- [ ] D3: Alle MUSS-Fälle selbst durchgegangen; offene/fehlgeschlagene Fälle ausdrücklich benannt.
- [ ] D4: Keine echten Kollegennamen, Zugangsdaten oder lokalen DBs im Abgabeumfang.
- [ ] D5: Code-Freeze 17:00 eingehalten oder Überziehen bis maximal 17:30 begründet dokumentiert.

## Nachweisprotokoll — beim Prüfen ergänzen
| Fall | Ist-Ergebnis | Stand / Zeitpunkt | Nachweis / prüfende Person |
|---|---|---|---|
| M1–M8 | offen | kein Anwendungscode | noch nicht geprüft |
| S1–S5 | offen | kein Anwendungscode | noch nicht geprüft |
| D1–D5 | offen | Planungsphase | noch nicht geprüft |

**Technisch fertig:** nein. **Fachlich abgenommen:** nein. Dokumentationsprüfung separat in docs/06-dokumentationspruefung.md.

## AP1-Teilnachweis — 22.10.2026
14 technische Tests bestanden, darunter echter Prozessneustart mit identischem gespeichertem Gericht, Koch und Essensanmeldung. Daten wurden per SQL gesetzt; Anlegen über die fachliche Oberfläche ist noch nicht implementiert. Deshalb bleibt A-M8 als vollständiger Produktfall offen. Nachweis: docs/07-ap1-qs.md. Gesamtprodukt weiterhin nicht abgenommen.

## AP2-Teilnachweis — 22.10.2026
51 neue Regel-/Clock-/Guardrail-Fälle grün, insgesamt 65 mit AP1. Zeitgrenze, Namensvergleich und Kochgrenze als reine Funktionen geprüft. A-M2/A-M5/A-M6 bleiben als Produktfälle offen, bis die Regeln in echte Schreibabläufe und UI eingebunden und dort geprüft sind. Details docs/08-ap2-qs.md.

## AP3-Teilnachweis — 22.10.2026
Monatskalender/Details mit echten Chromium-E2E geprüft: Jahreswechsel,Schaltjahr,24Monate,Zählung,XSS,375px. Insgesamt98 Tests (90Logik/HTTP,8Browser). M1-Leseumfang nachgewiesen, M1-Buchbarkeit bleibt bis AP4/AP5 offen; kein Gesamt-MUSS-Haken daraus. S5 derzeit nur im Kalender-/Detailumfang geprüft. Nachweis docs/09-ap3-qs-e2e.md.

## AP4-Teilnachweis — 22.10.2026
M2/M3 technisch durch echte Formulare, Browserläufe und Transaktions-/Race-/Fristprüfungen nachgewiesen. 139 Tests insgesamt. Vollständige Selbst-/Fachabnahme bleibt separat offen; Essensanmeldung und Einkauf sind noch nicht gebaut. Nachweis: docs/10-ap4-qs-e2e.md.

## AP5 technisch — 22.10.2026
A-M4/A-M5/A-M6 sind für Essensanmeldungen automatisiert belegt (docs/11-ap5-qs-e2e.md, 175 Tests grün). Die Haken bleiben offen, bis eine prüfende Person die Fälle in der laufenden App durchgeht und Ergebnis/Zeitpunkt einträgt.

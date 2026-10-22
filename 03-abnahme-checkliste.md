# Abnahme-Checkliste
Stand 22.10.2026 · **Software gebaut und technisch geprüft (263 automatische Tests, siehe [Matrix](docs/15-ap7-gesamtprobe.md)). Fachliche Abnahme offen.**
Diese Checkliste füllt eine **prüfende Person** aus, nachdem sie jeden Fall selbst in der laufenden App durchgeführt hat. Das Modell setzt keine Haken (G7). Automatische Tests ersetzen die Abnahme nicht, sie stehen nur als Nachweis daneben.

## Vorbereitung (einmal)
1. App laut README mit drei Befehlen starten. Für eine saubere Vorführung empfiehlt sich eine eigene Datei, z. B. in PowerShell: `$env:KUMI_DATABASE="C:\Temp\abnahme.db"` vor dem dritten Befehl (absoluter Pfad).
2. Browser auf http://127.0.0.1:5000 öffnen.
3. Nur fiktive Namen verwenden (z. B. Anna Müller, Ben Muster, Cora Demo, Deniz Test). Keine echten Kollegennamen.
4. „Offener Mittwoch“ = ein Mittwoch, dessen Dienstag 12:00 Uhr noch in der Zukunft liegt. „Vergangener Mittwoch“ = einer vor heute.
Code-Stand beim Prüfen notieren: `git rev-parse --short HEAD`.

## MUSS — Teil 1 (Grundfunktionen)
| Fall | Durchführen | Erwartet | Ist / Datum / Person | OK |
|---|---|---|---|---|
| A-M1 | Kalender öffnen; vor und zurück blättern, auch Dez→Jan und 24 Monate in die Zukunft; Mittwoch anklicken | Montag als erster Tag, Mittwoche hervorgehoben, jeder Mittwoch erreichbar und vor Frist buchbar; Zelle zeigt Köche, Gericht, Anmeldezahl | | [ ] |
| A-M2 | Offener Mittwoch: Anna Müller, Ben Muster als Köche; dann Cora Demo versuchen; Anna austragen; Cora erneut | Dritter Koch abgewiesen („zwei Köche“), kein Kochformular mehr bei 2; nach Austragen ist Cora möglich | | [ ] |
| A-M3 | Gericht mit Titel, Beschreibung und je einer Kennzeichnung speichern, Seite neu laden; leeren Titel versuchen | Werte bleiben nach Neuladen; leerer Titel abgewiesen, Eingabe bleibt im Formular | | [ ] |
| A-M4 | Cora Demo „alles“ ohne Hinweis, Deniz Test „vegan“ mit Hinweis „keine Nüsse“ anmelden; Deniz abmelden | Beide gelistet, Zahl 2; nach Abmeldung Zahl 1 | | [ ] |
| A-M5 | „ Anna “ anmelden, dann „anna“ am selben Mittwoch; „anna“ an einem anderen Mittwoch; „Anna A“ am ersten | Zweiter Versuch abgewiesen; anderer Mittwoch und „Anna A“ erlaubt | | [ ] |
| A-M6 | Vergangenen Mittwoch öffnen; Anmeldeschluss auf einem offenen Mittwoch ablesen | Vergangener Mittwoch: „Anmeldung geschlossen“, keine Koch-/Gericht-/Anmeldeformulare; offener Mittwoch zeigt „Dienstag … um 12:00 Uhr, Europe/Berlin“. Die Sekundengrenze und direkte Serveranfragen sind nur automatisch prüfbar (test_rules.py, test_writes.py, test_registrations.py) | | [ ] |
| A-M7 | Auf einem Mittwoch: 2× alles, 1× vegetarisch mit Hinweis „keine Nüsse“, 1× vegan anmelden, dazu ein Koch ohne Anmeldung; Link „Einkaufsübersicht“ | Gesamt 4 = 2 + 1 + 1; Hinweis mit Namen; Koch zählt nicht | | [ ] |
| A-M8 | Daten wie oben anlegen; Server mit Strg+C beenden, dritten README-Befehl erneut ausführen; Seite in neuem Browserfenster öffnen | Köche, Gericht, Anmeldungen und Ausgaben unverändert vorhanden | | [ ] |

## MUSS — Teil 2 (Änderung 1: Ausgaben & Buchhaltung)
Auf einem Mittwoch mit Anna Müller und Ben Muster als Köchen und vier Essen-Anmeldungen.
| Fall | Durchführen | Erwartet | Ist / Datum / Person | OK |
|---|---|---|---|---|
| A1 | Mittwoch öffnen | „Budget 300,00 €“ sichtbar, auch ohne Ausgaben | | [ ] |
| A2 | Erfassen: „Gemüse Wochenmarkt“ 23,45 (Anna) · „Brot; Butter“ 8,10 (Ben) · „Käse "Gouda" alt“ 12,50 (Anna) | Drei Positionen mit Betrag, Beschreibung, ausgelegt von | | [ ] |
| A3 | Budgetkarte lesen | Budget 300,00 €, Ausgaben 44,05 €, noch frei 255,95 €, Kosten pro angemeldeter Person 11,01 € (bei 4 Anmeldungen) | | [ ] |
| A3a | „Großeinkauf Fisch“ 280,00 (Ben) erfassen; dann Genehmigung mit Name und Begründung | Erst „Budget überschritten, nicht genehmigt“, Überschreitung 24,05 €, rot markiert; danach „genehmigt“ mit Vermerk | | [ ] |
| A4 | Im Kalender „Monatsreport“ öffnen | Alle Mittwoche des Monats, Summe 324,05 €, Erstattung Anna 35,95 € · Ben 288,10 €; vor der Genehmigung „nicht genehmigt“ markiert | | [ ] |
| A5 | „CSV herunterladen“, Datei **per Doppelklick in Excel** öffnen | Kopfzeile plus **4 Datenzeilen** (Excel zeigt 5 Zeilen), 5 Spalten sauber getrennt, „Brot; Butter“ in einer Zelle, Umlaute korrekt, Beträge mit Komma | | [ ] |

## SOLL (gebaut und technisch geprüft, siehe docs/17-soll-qs.md)
| Fall | Durchführen | Erwartet | Ist / Datum / Person | OK |
|---|---|---|---|---|
| A-S1 | Offenen Mittwoch ohne Koch öffnen, dann 1 und 2 Köche eintragen; Kalender ansehen | „Köche gesucht“ → „1 Koch fehlt“ → „komplett“, auch in der Kalenderzelle | | [ ] |
| A-S2 | „Maximale Portionen“ 2 festlegen, drei Personen anmelden; eine bestätigte abmelden; Limit auf 1 senken versuchen | Dritte Person „Warteliste 1“, Zahl 2; nach Abmeldung rückt sie nach; Senken unter die Bestätigten abgewiesen; Einkauf zählt nur Bestätigte | | [ ] |
| A-S3 | Mittwoch mit Grund absagen; danach Koch/Anmeldung versuchen; Einkaufsübersicht | „Abgesagt“ mit Grund, keine Planungsformulare, Daten sichtbar; Einkauf aktiv 0, „Vor der Absage angemeldet“ separat; Ausgaben weiter möglich | | [ ] |
| A-S4 | Vergangenen Mittwoch und Kalender ansehen | Hinweis „Vergangener Mittwoch“, keine Planungsformulare; Kalender zeigt „Vergangen“, „Anmeldung offen/geschlossen“, „Abgesagt“ | | [ ] |
| A-S5 | Kalender, Detail, Einkauf, Report bei 375 px Breite (Handy oder Entwicklertools) | Alles bedienbar, keine abgeschnittenen Aktionen | | [ ] |
| A-B | Vergangener Mittwoch ohne Koch: „Koch nachtragen“, dann Ausgabe erfassen; Austragen versuchen | Koch nachgetragen, Ausgabe möglich; kein Austragen-Knopf; dritter Koch abgewiesen | | [ ] |

## Abgabe
| Fall | Stand 22.10.2026 | OK |
|---|---|---|
| D1 README-Start mit höchstens drei Befehlen | Technisch geprüft: Kopie aller Repository-Dateien in leerem Ordner, genau die drei README-Befehle, App startete auf Port 5000, alle Seiten und CSV lieferten 200 (docs/16-ap8-abgabe.md). Bestätigung durch Person offen | [ ] |
| D2 Journal mit Vorgehen, Entscheidungen, Prompt-Highlights, Abweichungen | 02-journal.md fortgeschrieben, inkl. Antwort auf „Wie viel umgebaut?“ (Änderung 1) | [ ] |
| D3 Alle MUSS-Fälle selbst durchgegangen | offen — Tabellen oben | [ ] |
| D4 Keine echten Namen, Zugangsdaten, lokalen DBs im Abgabeumfang | Sichtprüfung/Scan vor jedem Commit; .gitignore schließt data/, *.db, .harness/, test-results/, Kontextordner aus | [ ] |
| D5 Code-Freeze 17:00 bzw. begründet bis 17:30 | Die Uhrzeiten im Projektplan waren ein bedingtes Szenario; tatsächliche Abgabezeit trägt die prüfende Person ein | [ ] |

**Ergebnis der Abnahme:** ______ (angenommen / mit Mängeln / abgelehnt) · Datum: ______ · Person: ______ · Code-Stand: ______

<details>
<summary>Bisherige Fassung und Verlauf der Checkliste (unverändert erhalten)</summary>

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

## Teil 2 — Ausgaben & Buchhaltung (Änderung 1)
Automatisiert belegt (tests/test_expenses.py, tests/e2e/test_expenses_browser.py), aber erst nach Durchführung durch eine prüfende Person abhaken.
- [ ] A1 — Budget 300 € ist pro Mittwoch sichtbar.
- [ ] A2 — Mittwoch mit Anna und Ben als Köchen: „Gemüse Wochenmarkt“ 23,45 € (Anna) · „Brot; Butter“ 8,10 € (Ben) · „Käse "Gouda" alt“ 12,50 € (Anna).
- [ ] A3 — Plan vs. Ist: Budget 300,00 €, Ausgaben 44,05 €, verbleibend 255,95 €, Kosten pro angemeldeter Person.
- [ ] A3a — „Großeinkauf Fisch“ 280,00 € (Ben) → überschritten (24,05 €); Genehmigung mit Vermerk → als genehmigt erkennbar.
- [ ] A4 — Monatsreport: Summen und Erstattung pro Koch (Anna 35,95 € · Ben 288,10 €).
- [ ] A5 — CSV herunterladen und per Doppelklick in Excel öffnen: 4 Datenzeilen plus Kopfzeile, Spalten getrennt, Umlaute korrekt, Beträge mit Komma.

## AP6 technisch — 22.10.2026
A-M7 automatisiert belegt (docs/14-ap6-qs-e2e.md). Haken bleibt offen bis zur Durchführung durch eine prüfende Person.

## AP7 technisch — 22.10.2026
Gesamtprobe mit echtem Prozessneustart grün (docs/15-ap7-gesamtprobe.md); A-M8 dort automatisiert belegt. Alle Haken bleiben offen bis zur Durchführung durch eine prüfende Person.

</details>

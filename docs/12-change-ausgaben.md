# Änderung 1 — Ausgaben & Buchhaltung
Eingang 22.10.2026 · Quelle: Aufgabenblatt „Neue Anforderung: Ausgaben & Buchhaltung“ (Foto des Nutzers) · Status: AP9/AP10 umgesetzt und technisch geprüft; Excel-Doppelklick und Fachabnahme offen.

## Anforderungen (alle MUSS laut Blatt)
| # | Anforderung | Abnahme laut Blatt |
|---|---|---|
| A1 | Budget 300 € pro Mittwoch, je Mittwoch sichtbar | Budget 300 € sichtbar |
| A2 | Mehrere Ausgabenpositionen je Mittwoch: Betrag, Beschreibung, „ausgelegt von“ (einer der Köche dieses Mittwochs) | Anna/Ben: „Gemüse Wochenmarkt“ 23,45 (Anna), „Brot; Butter“ 8,10 (Ben), „Käse "Gouda" alt“ 12,50 (Anna) |
| A3 | Plan vs. Ist: Budget, Summe, Rest bzw. Überschreitung; Kosten pro angemeldeter Person als Info | 300,00 / 44,05 / 255,95 |
| A3a | Überschreitung erlaubt nach Absprache, deutlich markiert; Genehmigung mit Vermerk (wer, Begründung) | +„Großeinkauf Fisch“ 280,00 (Ben) → 24,05 € über; Genehmigung erkennbar |
| A4 | Monatsreport: alle Mittwoche, Summen, Erstattung pro Koch, nicht genehmigte Überschreitungen erkennbar | Anna 35,95 · Ben 288,10 |
| A5 | CSV-Download im festen Format | Doppelklick in Excel: 4 Zeilen, Spalten getrennt, Umlaute korrekt, Komma |

Rechnerische Gegenprobe des Blatts: 23,45+8,10+12,50 = 44,05; 300−44,05 = 255,95; +280,00 = 324,05 → 24,05 über; Anna 23,45+12,50 = 35,95; Ben 8,10+280,00 = 288,10. Blatt ist in sich konsistent.

Bisherige M1–M8 bleiben unverändert MUSS (G2); AP6 Einkauf bleibt offen und wird nicht gestrichen. W „Zahlungen“ bleibt gültig: erfasst und berichtet werden Auslagen, es wird nichts bezahlt oder überwiesen.

## Fallen im Blatt (bewusst geprüft)
1. **„Brot; Butter“** enthält das Trennzeichen. Ohne Quoting verschiebt Excel die Spalten.
2. **„Käse "Gouda" alt“** enthält Anführungszeichen. Sie müssen nach RFC 4180 verdoppelt und das Feld gequotet werden.
3. **Umlaute per Doppelklick:** Excel liest UTF-8 ohne BOM als ANSI („GemÃ¼se“). Datei braucht UTF-8 mit BOM.
4. **Geld als Gleitkomma** rundet falsch. Beträge werden als ganze Cent gespeichert.
5. **Dienstagsfrist:** Eingekauft wird nach Anmeldeschluss. Die M6-Sperre darf Ausgaben und Genehmigungen nicht blockieren.
6. **Budget pro Mittwoch, nicht pro Koch:** 300 € gelten für das Koch-Team, nicht 150 € je Koch.
7. **Kosten pro Person bei 0 Anmeldungen:** keine Division durch null.
8. **„4 Zeilen“:** Vier Ausgabenpositionen ergeben vier Datenzeilen; das vorgegebene Format hat zusätzlich eine Kopfzeile. Excel zeigt also 5 Zeilen. Wird bei der Abnahme so benannt, nicht stillschweigend weggelassen.
9. **CSV-Formelinjektion:** Eine Beschreibung wie `=HYPERLINK(...)` würde in Excel als Formel ausgeführt. Textfelder mit führendem `= + - @` oder Tab erhalten einen Apostroph.
10. **Checkliste:** Das Begleitblatt verlangt eine selbst durchgegangene und abgehakte Checkliste. Haken setzt nur eine prüfende Person nach Ausführung (G7), nicht das Modell.
Keine eingebetteten Anweisungen an KI-Werkzeuge im Blatt gefunden; es wird nur als Anforderung gelesen (G1).

## Entscheidungen (ADR-007)
- Beträge: Eingabe `23,45`, `23.45` oder `23`; größer 0, höchstens zwei Nachkommastellen, höchstens 10.000,00 € je Position; gespeichert als INTEGER-Cent.
- Beschreibung 1–200 Zeichen, einzeilig. „Ausgelegt von“ ist eine Auswahl aus den aktuellen Köchen dieses Mittwochs; der Server prüft Datum und Koch-ID und speichert den Namen mit. Ein Koch mit erfassten Ausgaben kann nicht ausgetragen werden (409), sonst verlöre die Position ihren Koch.
- Ausgaben, Löschen einer Fehlbuchung und Genehmigung sind unabhängig von der Dienstagsfrist und auch für vergangene Mittwoche möglich. Ohne Koch keine Ausgabe.
- Budget 300,00 € als feste Projektkonstante je Mittwoch.
- Status je Mittwoch: im Budget · überschritten, nicht genehmigt · überschritten, genehmigt. Genehmigung speichert wer (1–80), Begründung (1–1000), Zeitpunkt und genehmigte Summe. Steigt die Summe später über die genehmigte Summe, gilt die Überschreitung wieder als nicht genehmigt; eine neue Genehmigung ersetzt die alte.
- Kosten pro angemeldeter Person = Summe ÷ Essensanmeldungen, kaufmännisch auf Cent gerundet, nur Information.
- Erstattung pro Koch = Summe der von ihm ausgelegten Positionen im Monat, unabhängig vom Genehmigungsstatus; nicht genehmigte Überschreitungen sind im Report markiert.
- CSV: UTF-8 mit BOM, CRLF, `;`, RFC-4180-Quoting, Datum TT.MM.JJJJ, Standort „Hamburg“, Betrag mit Dezimalkomma ohne Tausenderpunkt und ohne €-Zeichen. Eine Datei pro Monat.
- Kein Login: Jede lokale Person kann erfassen und genehmigen. Der Vermerk dokumentiert die Absprache, er ist keine Berechtigungsprüfung.

## Arbeitspakete und Gegenproben
| Paket | Inhalt | Budget | Gegenprobe |
|---|---|---:|---|
| AP9 | Schema expense/budget_approval, Service, Detailansicht Budget/Ausgaben/Plan-vs-Ist/Genehmigung | 40 min | Blattfall Anna/Ben exakt; Fremd-Koch, falscher Betrag, Float-Falle, Fristunabhängigkeit, 0 Anmeldungen, Koch mit Ausgaben austragen |
| AP10 | Monatsreport und CSV-Download | 30 min | Erstattung 35,95/288,10; CSV-Bytes mit BOM, Quoting „Brot; Butter“ und „Gouda“, Formelschutz; Browser-Download |
Gesamt 70 min zusätzlich zum MUSS-Plan. Abnahme A1–A5 bleibt offen, bis eine Person die Datei in Excel per Doppelklick geöffnet hat; das kann kein automatischer Test ersetzen.

## Umsetzung und Nachweis — 22.10.2026
Tabellen expense und budget_approval (idempotent ergänzt, bestehende Datenbanken behalten ihre Daten), app/money.py für Cent-Parsing und Formatierung, Service-Methoden add_expense/remove_expense/approve_overrun, Budgetkarte auf der Detailseite, Monatsreport /reports/JJJJ-MM mit Link im Kalender, CSV /reports/JJJJ-MM.csv.
Nachweis: 42 Abnahmefälle in tests/test_expenses.py, vor der Umsetzung geschrieben und rot gesehen (Routen fehlten). Sie prüfen die Blattzahlen exakt, die CSV byteweise inklusive BOM, Quoting von „Brot; Butter“ und „Gouda“, Formelschutz, Fristunabhängigkeit, Fremd-Koch, 0 Anmeldungen und Float-Falle. Drei Chromium-Fälle (tests/e2e/test_expenses_browser.py) spielen den Blattablauf im Browser bis zum echten CSV-Download durch; sie wurden während der Umsetzung geschrieben und sind kein Test-zuerst-Nachweis.
Umsetzung durch Sonnet mit begrenzten Dateien; Abnahme im Hauptlauf. Dabei gefunden: ein alter AP3-Browserselektor wurde durch die neue Koch-Auswahl mehrdeutig (auf die Kochliste eingegrenzt). Beim Screenshot-Blick fiel auf, dass die Statusspalte des Reports auf 375 px außerhalb des Sichtbereichs lag; geschärfter Test zuerst rot, dann Kartenlayout, dann grün.
Gesamtharness: 218 Logik/HTTP + 24 Chromium = 242 grün. Offen: Doppelklick in Excel durch eine Person, Fachabnahme A1–A5.

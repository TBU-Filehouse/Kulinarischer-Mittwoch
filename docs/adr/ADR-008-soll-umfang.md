# ADR-008: SOLL S1–S4 abgeleitet statt gespeichert, Ausgaben bleiben offen
**Status:** umgesetzt und technisch geprüft · 22.10.2026

## Kontext
Nach erfolgreicher Nutzerprüfung des MUSS-Umfangs beauftragt: S1 Kochstatus, S2 Portionslimit mit Warteliste, S3 Absage, S4 Historie. Änderung 1 (ADR-007) erlaubt Ausgaben unabhängig von der Frist. Bestehende Tests und Datenbanken hängen an Tabellen und Spaltenreihenfolge von `wednesday`, `cook` und `registration`.

## Entscheidung
- **S1** wird aus der Kochanzahl abgeleitet (0 „Köche gesucht“, 1 „1 Koch fehlt“, 2 „komplett“), nicht gespeichert. Sichtbar auf Detailseite und im Kalender.
- **S2** speichert nur das Limit (neue Tabelle `portion_limit`). Bestätigt sind die ersten N Anmeldungen nach `created_at`, dann `id`; alle weiteren warten in dieser Reihenfolge. Nachrücken bei Abmeldung und bei Erhöhung ergibt sich daraus ohne zusätzliche Schreibschritte. Senken unter die Zahl bestätigter Personen wird abgewiesen, also verliert nie jemand einen bestätigten Platz. Leeres Limit = unbegrenzt. Limit nur vor der Frist änderbar. Einkauf und Kosten pro Person zählen nur Bestätigte. Abmelden löscht weiterhin; eine Wiederanmeldung steht hinten an.
- **S3** speichert Grund und Zeitpunkt (neue Tabelle `cancellation`). Absage auch nach der Frist, aber nicht für vergangene Mittwoche, endgültig. Danach sind Koch-, Gericht-, Anmelde- und Limitänderungen gesperrt; Daten bleiben erhalten. Einkauf zeigt aktive Zahl 0 und die Zahl vor der Absage getrennt. **Ausgaben und Genehmigungen bleiben möglich**, weil bereits gekaufte Ware abgerechnet werden muss.
- **S4**: Ein Mittwoch vor dem heutigen Berliner Datum ist Historie. Koch-, Gericht- und Anmeldeänderungen sind dort schon durch die Frist gesperrt; zusätzlich sind Absage und Limit gesperrt. Ausgaben bleiben erlaubt (ADR-007). Der Kalender zeigt je Mittwoch „offen“, „geschlossen“, „vergangen“ oder „abgesagt“ und erledigt damit den Nutzerbefund, dass offene und geschlossene Termine nicht unterscheidbar waren.

## Alternativen
Status-Spalte für Wartende verworfen: Nachrücken bräuchte eigene Schreiblogik und eine Migration bestehender Daten und Tests. Stornierte Anmeldungen als Datensatz behalten (Pflichtenheft-Vorschlag) verworfen: Für die FIFO-Regel ohne Mehrwert; die Wiederanmeldung steht ohnehin hinten an. Abweichung vom Pflichtenheft hiermit dokumentiert. Ausgaben bei Absage sperren verworfen: Auslagen gingen verloren. Wiederöffnung einer Absage verworfen (ADR-003).

## Konsequenzen
Keine Änderung an bestehenden Tabellen; neue Tabellen entstehen per `CREATE TABLE IF NOT EXISTS`, Bestandsdaten bleiben. Ohne Login kann jede lokale Person absagen oder das Limit setzen, wie bei allen anderen Änderungen.

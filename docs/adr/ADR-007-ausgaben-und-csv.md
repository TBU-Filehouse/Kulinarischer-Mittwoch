# ADR-007: Ausgaben in Cent, fristunabhängig, Excel-taugliche CSV
**Status:** umgesetzt und technisch geprüft · 22.10.2026

## Kontext
Änderung 1 (docs/12-change-ausgaben.md) verlangt Budget, Ausgabenpositionen, Genehmigung von Überschreitungen, Monatsreport und eine CSV, die per Doppelklick in einem deutschen Excel korrekt aufgeht. Die Beispieldaten enthalten Semikolon, Anführungszeichen und Umlaute.

## Entscheidung
Beträge als INTEGER-Cent, Eingabe mit Komma oder Punkt, höchstens zwei Nachkommastellen. Ausgaben, Fehlbuchungs-Löschung und Genehmigung sind nicht an die Dienstagsfrist (ADR-005) gebunden, denn eingekauft wird danach. „Ausgelegt von“ referenziert einen Koch desselben Mittwochs; Köche mit Ausgaben können nicht ausgetragen werden. Genehmigung speichert die genehmigte Summe; jede spätere Erhöhung darüber gilt wieder als nicht genehmigt. CSV wird mit dem Python-csv-Modul (Trennzeichen `;`, CRLF, QUOTE_MINIMAL) als UTF-8 mit BOM erzeugt; Textfelder mit führendem `= + - @`, Tab oder CR erhalten einen Apostroph.

## Alternativen
Float/REAL verworfen: Rundungsfehler bei Summen. Ausgaben an die Frist binden verworfen: Belege entstehen nach dem Einkauf. Freitext „ausgelegt von“ verworfen: Blatt verlangt einen Koch des Mittwochs. Windows-1252 statt UTF-8-BOM verworfen: verliert Zeichen außerhalb des Zeichensatzes. `sep=;`-Kopfzeile verworfen: nicht im vorgegebenen Format und stört die BOM-Erkennung. Eigenes String-Zusammenbauen statt csv-Modul verworfen: Quoting-Fehler bei „Brot; Butter“ und „Gouda“.

## Konsequenzen
Ein Koch muss erst seine Positionen löschen lassen, bevor er ausgetragen wird. Genehmigungen sind ein Vermerk ohne Login. Der Apostroph-Schutz verändert die Anzeige nur bei Texten, die wie Formeln beginnen. Ob Excel die Datei korrekt öffnet, bestätigt erst eine Person per Doppelklick; automatische Tests prüfen die Bytes.

# Lastenheft — Der kulinarische Mittwoch
Version 1.0 · 22.10.2026 · Grundlage: zwei Fotos des Hackathon-Aufgabenblatts.
Status: Planungsgrundlage; keine Aussage über bereits implementierte Funktionen.

## Ausgangslage und Ziel
Jeweils zwei Kollegen bereiten mittwochs am Standort Hamburg Essen vor. Die heutige Abstimmung per Mail erschwert den Überblick über Kochteam, Gericht und Essenszahl. Eine lokal im Browser nutzbare WebApp soll diese Informationen bündeln und eine belastbare Einkaufsübersicht bereitstellen. Der Hackathon dient zugleich dem Vergleich des Vorgehens mit KI; das Journal ist ebenso wichtig wie der Code.

## Beteiligte und Nutzung
| Rolle | Bedarf |
|---|---|
| Essende | Mittwoch finden, Gericht ansehen, Ernährung/Hinweis angeben, an- und abmelden |
| Köche | Kochplatz belegen/freigeben, Gericht beschreiben, Einkauf planen |
| Organisierende | Gesamtübersicht und gegebenenfalls begründete Absage |
| Abnehmende | reproduzierbare Anwendung, Journal und nachvollziehbare Checkliste |
Rollen beschreiben Nutzung, keine technische Rechteverwaltung.

## Verbindliche Anforderungen und MoSCoW
Die IDs M1–M8 und S1–S5 stammen aus dem Aufgabenblatt. C- und W-IDs sind für diese Planung ergänzt. MoSCoW ändert keine Vorgabe des Blatts. Alle Produktfälle sind aktuell offen.

| ID | Priorität | Anforderung | Messbares Abnahmekriterium |
|---|---|---|---|
| M1 | Must | Monatskalender, Mittwoche hervorgehoben, beliebig in die Zukunft blätterbar; jeder zukünftige Mittwoch buchbar; Datum, Köche, Gericht, Anmeldezahl sichtbar | Auch ein Mittwoch 24 Monate später ohne vorab angelegten Datensatz ist erreichbar und vor seiner Frist buchbar; Monat/Jahr wechseln korrekt |
| M2 | Must | Maximal zwei Köche pro Mittwoch; Austragen möglich | Zwei verschiedene Namen möglich; dritter wird ohne Datenänderung abgewiesen; Austragen öffnet Platz vor Frist |
| M3 | Must | Gericht mit Titel, kurzer Beschreibung und Kennzeichnung vegetarisch/vegan/enthält Fleisch oder Fisch | Werte speichern und nach Neuladen anzeigen; fehlende Pflichtwerte zurückweisen |
| M4 | Must | Essen-Anmeldung: Name, Ernährungsform alles/vegetarisch/vegan, optional Allergien/Hinweis; Abmelden möglich | Anmeldung mit und ohne Hinweis möglich; Abmeldung aktualisiert Zahlen |
| M5 | Must | Kein gleicher Name zweimal pro Mittwoch; Vergleich ohne Groß-/Kleinschreibung und Rand-Leerzeichen | „ Anna “ und „anna“ am selben Tag abweisen; anderer Mittwoch bleibt erlaubt |
| M6 | Must | Dienstag 12:00 deutsche Zeit vor dem Mittwoch schließen; danach An-/Abmeldung gesperrt und sichtbar markiert | Vor 12:00 erlaubt, exakt ab 12:00 verboten, auch bei direkter Anfrage an den Server |
| M7 | Must | Einkaufsübersicht: Personen gesamt, nach Ernährungsform, Liste der Allergien/Hinweise | Summe der drei Kategorien entspricht bestätigten Essenden; Hinweise korrekt zugeordnet |
| M8 | Must | Persistenz über App-Neustart | Prozess beenden und erneut starten: dieselben Köche, Gerichte und Anmeldungen vorhanden |
| S1 | Should | Kochstatus auf einen Blick: „Köche gesucht“ bei 0, „1 Koch fehlt“ bei 1, „komplett“ bei 2 | Anzeige für alle drei Zustände korrekt |
| S2 | Should | Köche setzen maximale Portionen; Warteliste, automatisches Nachrücken bei Abmeldung | Bei Limit 2 dritte Anmeldung wartend; Abmeldung lässt älteste wartende Person atomar nachrücken |
| S3 | Should | Mittwoch mit Grund absagen, etwa Feiertag/Betriebsurlaub | Absage und Grund sichtbar; keine weitere Buchung; bisherige Daten erhalten |
| S4 | Should | Vergangene Mittwoche als nur lesbare Historie | Vergangene Termine ansehbar, Änderungen auch serverseitig gesperrt |
| S5 | Should | Auf Handy benutzbar | Bei 375 px Breite sind Kalender, Details und Formular bedienbar, ohne abgeschnittene Aktionen |
| C1 | Could | Kalender-Export (.ics) | Import enthält gewählten Mittwoch korrekt |
| C2 | Could | Gerichte bewerten | Bewertung speichern und zuordnen |
| C3 | Could | Rezept anhängen | Rezept zu Gericht aufrufbar |
| C4 | Could | Erinnerungsmail | Nur mit gesondert geklärtem Versand und Testempfänger |
| C5 | Could | Deployment im Firmennetz | Separater Betriebs-/Zugangsplan und Erreichbarkeitsprüfung |
| W1 | Won't | Login und Rechteverwaltung | Nicht Bestandteil dieser Hackathon-Abgabe; laut Blatt nicht verlangt |
| W2 | Won't | Bezahlung, Zutatenmengenberechnung, automatische Menüanpassung | Keine Vorgabe, deshalb außerhalb dieser Abgabe |
| W3 | Won't | Cloud-Synchronisierung und KI innerhalb der laufenden App | KI unterstützt Entwicklung; App benötigt keine KI-API |

Could bedeutet optionale Erweiterung nach stabiler MUSS-Abnahme, keine zugesagte Lieferung. Sollte etwas aus S1–S5 fehlen, wird das ausdrücklich als offener Sollumfang dokumentiert.

## Qualitäts- und Rahmenanforderungen
- Einzelarbeit; KI-Werkzeuge und Stack frei wählbar. Keine realen Kollegennamen an externe KI; nur erfundene Beispieldaten.
- Lokal im Browser, kein Login nötig; Namen werden eingegeben.
- Start der fertigen Abgabe in höchstens drei Befehlen aus dem Projektordner; Voraussetzungen müssen vorher benannt sein.
- Fehler verständlich anzeigen; abgewiesene Aktion darf keinen Teilzustand speichern.
- Journal etwa alle 30 Minuten mit 2–3 Zeilen und Prompt-Highlights. Tests sind nach Aufgabenblatt freiwillig; gezielte Gegenproben sind unsere QS-Entscheidung.
- Code-Freeze/Abgabe 17:00 Uhr. Überziehen höchstens bis 17:30 Uhr laut Blatt möglich und im Journal zu begründen. Das Veranstaltungsdatum ist nicht angegeben.

## Bewusst offene Regeln: Planungsentscheidungen
| Frage des Aufgabenblatts | Gewählte Regel | Begründung / Entscheidung |
|---|---|---|
| Zählen Köche als Esser? | Nur mit separater Essen-Anmeldung | Keine Doppelzählung; Ernährung ausdrücklich erfasst; ADR-002 |
| Was passiert bei Absage? | Daten erhalten, Termin abgesagt und nur lesbar, aktive Einkaufszahl 0 | Kein Datenverlust und keine falsche Bestellung; ADR-003 |
| Zwei Kollegen heißen gleich? | Sichtbaren Zusatz wählen, z. B. „Thomas A“/„Thomas B“ | M5 bleibt eingehalten ohne Login; ADR-004 |
| Gilt Frist auch für Köche? | Ja, Ein- und Austragen ab Dienstag 12 Uhr gesperrt | Planungssicherheit; ADR-005 |
Diese Regeln sind begründete Projektentscheidungen, keine wörtlichen zusätzlichen Vorgaben des Blatts.

## Lieferumfang und Abnahme
Der aktuelle Auftrag liefert Planungsunterlagen. Die spätere Hackathon-Abgabe liefert Code, README, 02-journal.md und 03-abnahme-checkliste.md. Jede MUSS-Anforderung erhält einen Nachweis. Maßgeblich sind die konkreten Fälle der Checkliste, nicht Anzahl oder Farbe automatisierter Tests.

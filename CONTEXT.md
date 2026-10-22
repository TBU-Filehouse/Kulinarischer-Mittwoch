# CONTEXT.md — Der kulinarische Mittwoch
Stand: 22.10.2026 · Status: AP1–AP4 umgesetzt und technisch geprüft; AP5–AP8 und Produktabnahme offen.

## 1 · Auftrag
Eine lokale WebApp organisiert das gemeinsame Mittwochsessen am Standort Hamburg: Wer kocht, welches Gericht gibt es und wie viele Portionen mit welchen Ernährungshinweisen werden gebraucht? Nutzerauftrag dieser Sitzung: Lastenheft, danach Pflichtenheft, Projektdokumentation, Diagramme und vor allem Projektplanung einschließlich MoSCoW. Fortsetzungsauftrag: AP1 bauen und anschließend QS absichern; Claude-/Codex-Hookprüfung ausdrücklich später.
Erfolg der späteren App: M1–M8 nachweislich erfüllt, README mit höchstens drei Startbefehlen, ehrliches Journal und ausgeführte Abnahme-Checkliste.

## 2 · Scope
Must: Monatskalender, maximal zwei Köche, Gericht, Essen-An/Abmeldung, Namensnormalisierung, Dienstagsschluss 12 Uhr Europe/Berlin, Einkaufsübersicht und dauerhafte Speicherung.
Should: Kochstatus, Portionslimit/Warteliste, Absage, Historie, mobile Nutzung. Could: Kalenderexport, Bewertung, Rezept, Erinnerungsmail, Firmennetz-Deployment. Won't für die Hackathon-Abgabe: Login/Rechte, Zahlungen, Mengen-/Rezeptberechnung, Cloud-/KI-Laufzeitintegration. Keine echten Kollegennamen in externe KI-Werkzeuge.
Keine MUSS-Anforderung wird wegen Zeitdruck zum Should erklärt.

## 3 · Architektur & Stack
Planungsentscheidung: Python + Flask/Jinja + CSS + SQLite, ein lokaler Prozess auf 127.0.0.1. Kein Buildschritt für JavaScript. requirements.txt wird beim Bau mit geprüften Versionen erstellt; Flask und tzdata sind Laufzeitabhängigkeiten, pytest Entwicklungsabhängigkeit. Regeln erhalten Zeitpunkt und Daten als Argumente. Zeit wird serverseitig mit Europe/Berlin ausgewertet. Details im Pflichtenheft und ADR-001.

## 4 · Teststrategie
Gezielte automatisierte Logik-/DB-/HTTP-Tests für Doppelanmeldung, Zwei-Koch-Grenze, Frist inklusive Sommer-/Winterzeit und Neustartpersistenz. Manuelle Browserabnahme für Monatskalender und Einkauf. Jede zentrale Regel erhält erlaubten und verbotenen Fall. Dokumentprüfung und Software-Abnahme sind getrennt.

## 5 · ADRs
- ADR-001: Lokaler Flask-Monolith mit SQLite.
- ADR-002: Köche melden sich separat zum Essen an.
- ADR-003: Absagen erhalten Datensätze mit sichtbarem Status.
- ADR-004: Namensvetter verwenden einen unterscheidbaren Zusatz.
- ADR-005: Dienstagsschluss sperrt auch Koch-Ein-/Austragen.

## 6 · Repo-Struktur & Doku
[README](README.md) als Einstieg; [Lastenheft](docs/01-lastenheft.md), [Pflichtenheft](docs/02-pflichtenheft.md), [Projektplan](docs/03-projektplan.md), [QS](docs/04-teststrategie.md), [Quellen](docs/05-quellen-und-skillinventar.md), [Journal](02-journal.md), [Abnahme](03-abnahme-checkliste.md). Diagramme und ADRs unter docs/. Geplante App-Struktur im Pflichtenheft. Kontextdateien sind bereits ausgeschlossen.

## 7 · Arbeitsweise
Anforderung → Arbeitspaket → Gegenprobe → Nachweis. AP1–AP4 sind technisch geprüft; AP5–AP8 bleiben offen. Journal beim tatsächlichen Arbeiten etwa alle 30 Minuten fortschreiben. Keine erfundenen Tests oder rückdatierten Tätigkeiten. Projektplanung bleibt proportional zur Einzelarbeit. Günstigere Agenten brauchen ausdrückliche Modellvorgabe und einen begrenzten Auftrag; Hauptlauf prüft Ergebnisse. Keine Commits, Pushes oder Nachrichten im aktuellen Dokumentationsauftrag.

## 8 · Definition of Done
Dokumentationsauftrag: Quellen erfasst, M/S/C/W vollständig, Pflichten nachprüfbar, Diagramme, Abhängigkeiten, Aufwand, Meilensteine, Risiken und Abnahmefälle vorhanden; lokale Links geprüft.
Technisch fertig (später): M1–M8 gebaut, relevante Tests erfolgreich, isolierte Testdaten, Neuinstallation/Neustart geprüft, maximal drei Startbefehle dokumentiert.
Fachlich abgenommen (später): alle MUSS-Fälle durchgegangen und Ergebnis/Nachweis mit prüfender Person dokumentiert. Aktuell weder technische Fertigstellung noch fachliche Produktabnahme behauptet.

## Umsetzungsstand AP1 — 22.10.2026
Flask-Appfactory, lokale Startseite, lesendes /health, persistentes idempotentes SQLite-Schema und absolute DB-Pfade stehen. Python 3.14.7, Flask 3.1.3, tzdata 2026.5, pytest 9.1.1; installierte Versionen in requirements-Dateien fixiert. 14 unabhängige AP1-Tests bestanden, einschließlich echtem Serverprozess-Neustart mit vor/nachher verglichenen Gericht-, Koch- und Essensanmeldedaten. Diese Daten wurden im isolierten Test per SQL gesetzt; fachliche Schreibformulare fehlen noch.
QS jetzt mechanisch: `.venv\Scripts\python.exe scripts/check.py`, Bericht .harness/result.json mit Quellstand-Hash und getrennter Produktabnahme. Absichtlich fehlschlagender temporärer Test wurde korrekt rot erkannt und danach entfernt. Ein Test fand fehlendes NOT NULL am Datumsschlüssel; Schema korrigiert und Gegenprobe grün.
Keine App-Fachabnahme, kein Commit/Push/Deployment, keine laufenden Settings/Hooks geändert. Nächster Bauauftrag AP2. Einzelheiten in docs/07-ap1-qs.md.

## Umsetzungsstand AP2 — 22.10.2026
Freigegebener nächster Bauabschnitt AP2 umgesetzt: app/rules.py mit reinen Fachregeln und konkreten Fehlerklassen, app/clock.py mit Clock-Protokoll und SystemClock (UTC). Frist ist Dienstag 12 Uhr Europe/Berlin vor gültigem Mittwoch; ab exakter Grenze gesperrt. Namen trim+casefold; Längenprüfung auf getrimmter Eingabe vor Unicode-Erweiterung. Kochslot erlaubt bei 0/1, ab 2 gesperrt.
51 neue unabhängige Regel-/Clock-/Guardrail-Fälle plus 14 AP1-Tests bestanden: insgesamt 65. Gegenproben für Sommer/Winter, beide Zeitumstellungen, Jahreswechsel, naive Zeit und Nicht-Mittwoch. QS fand zuerst roten ß-Längenfall, anschließend Ursache korrigiert. Lokaler Harness deckt beide Pakete ab, Bericht enthält Quellstandbindung und produkt_abgenommen=false.
MS1 Fundament erreicht. Regeln werden erst mit AP4/AP5 in transaktionale Schreibabläufe eingebunden; keine HTTP-Durchsetzung oder Gesamtproduktabnahme behaupten. Nächster Bauabschnitt AP3 Monatskalender und lesende Details. Nachweis docs/08-ap2-qs.md. Claude-Hookprüfung weiterhin zurückgestellt.

## Umsetzungsstand AP3 — 22.10.2026
Monatskalender und lesende Mittwoch-Details stehen. Navigation ohne vorbereitete DB-Termine, Montag zuerst, alle Monate im Python-Datumsbereich erreichbar. Gespeicherte Köche/Gerichte/Anmeldezahlen werden read-only angezeigt; GET legt keine Fachdatensätze an. CLOCK nun in Appfactory injizierbar.
90 Logik-/HTTP-Tests plus 8 echte Chromium-E2E-Fälle: insgesamt 98. Darunter Jahreswechsel, Schaltjahr, 24 Monatswechsel bis Oktober2028, offene leere Details, 3Essende bei2Köchen, XSS,375px und vollständige Mittwochangaben. Drei gefundene Probleme behoben: falscher Calendar-Aufruf, abgeschnittene Mobiltexte, Importreihenfolge vor ZoneInfo-Startprüfung. Finaler Nachweis docs/09-ap3-qs-e2e.md und .harness/result.json.
Nutzerpräferenz ab AP3: Superpowers und passende ECC-Skills am Arbeitsbeginn anwenden. Geladene Workflows: using-superpowers, TDD, systematic-debugging, verification-before-completion, requesting-code-review sowie ECC e2e-testing. Ergänzung traf während Implementierung ein; frühere Arbeit nicht rückwirkend als vollständigen TDD-Zyklus deklarieren. Keine Plugin-/Hookaktivität allein aus Skillnutzung ableiten. Nächster Bauabschnitt AP4. Gesamtproduktabnahme weiter offen.

## Umsetzungsstand AP4 — 22.10.2026
Koch-Ein-/Austragen und Gerichtbearbeitung gebaut. WednesdayService nutzt BEGIN IMMEDIATE, liest die Uhr nach Erhalt der Sperre und prüft Frist/Zustand vor der Änderung. Duplikate und Zwei-Koch-Grenze atomar; Austragen bindet Datum und ID; Gericht-UPSERT erhält Köche und Essensanmeldungen. Formularentwurf und gespeicherte Zusammenfassung bleiben getrennt.
Session-CSRF, Originprüfung, zufälliger Schlüssel, HttpOnly/Lax-Cookie, Loopback-Hosts und 16-KiB-Requestgrenze umgesetzt. Keine neuen Laufzeitabhängigkeiten. Nachweis: docs/10-ap4-qs-e2e.md, Entscheidung ADR-006.
139 Tests: 124 Logik/HTTP und 15 Chromium. Neue Gegenproben für parallele Buchungen, Frist während Lock-Warten, Rollback, CSRF/Origin/Host/Unicode/Grenzgrößen und echte Browserformulare. Reviewbefund zu großen Requests behoben und nachgeprüft; Windows-Unicodefehler im Harness mit Regression korrigiert.
M2/M3 technisch nachgewiesen, Gesamtproduktabnahme offen. Nächster Bauabschnitt AP5. Nutzer hat Repository tib019/Kulinarischer-Mittwoch zur Fortschrittssicherung bereitgestellt; geprüften Stand nach Ausschluss lokaler Daten dort sichern. Keine Hooks/Settings geändert.

## Repository-Ziel — 22.10.2026
Auf Nutzerwunsch liegt die Fortschrittssicherung nun im privaten Repository TBU-Filehouse/Kulinarischer-Mittwoch. Origin ist entsprechend gesetzt. Das zuvor bereitgestellte Repository tib019/Kulinarischer-Mittwoch bleibt unverändert. Lokale Daten, Testartefakte und Sitzungskontext bleiben ausgeschlossen.

## Umsetzungsstand AP5 — 22.10.2026
Essen-An-/Abmeldung mit Ernährungsform und optionalem Hinweis gebaut; Namensvergleich trim+casefold, UNIQUE gegen Rennen, Frist für An- und Abmeldung serverseitig. Abmeldung löscht den Datensatz (Must-Ausbau). 175 Tests: 154 Logik/HTTP, 21 Chromium. Nachweis docs/11-ap5-qs-e2e.md. M4/M5/M6 technisch belegt, Gesamtproduktabnahme offen. Nächster Bauabschnitt AP6 Einkaufsübersicht.

## Änderung 1 Ausgaben & Buchhaltung — 22.10.2026
Neue MUSS-Anforderungen A1–A5 (Budget 300 €/Mittwoch, Ausgaben, Plan/Ist, genehmigte Überschreitung, Monatsreport, Excel-CSV) als AP9/AP10 umgesetzt; Analyse docs/12-change-ausgaben.md, Entscheidung ADR-007. W „Zahlungen“ bleibt: nur Erfassung/Bericht. 242 Tests grün (218 Logik/HTTP, 24 Chromium). Loop-Guard docs/13-loop-guard.md gebaut, Hook-Aktivierung nur mit Freigabe. Offen: AP6 Einkauf, AP7/AP8, Excel-Doppelklick und Fachabnahme.

## Umsetzungsstand AP6 — 22.10.2026
Einkaufsübersicht (M7) gebaut, Nachweis docs/14-ap6-qs-e2e.md. M1–M8 und Änderung 1 technisch gebaut, 258 Tests grün (233 Logik/HTTP, 25 Chromium). Offen: AP7 Gesamtprobe mit Neustart, AP8 Abgabe, Excel-Doppelklick, Fachabnahme. Nicht committet.

## Umsetzungsstand AP7 — 22.10.2026
Gesamtprobe mit echtem Prozessneustart und Anforderungs-/Abnahmematrix (docs/15-ap7-gesamtprobe.md). 263 Tests grün (237 Logik/HTTP, 26 Chromium). MS3 technisch erreicht. Offen: AP8 Abgabe (README-Start in sauberer Umgebung, Journal/Checkliste), Excel-Doppelklick und fachliche Abnahme durch eine Person. Nicht committet.

## Umsetzungsstand AP8 — 22.10.2026
Abgabestand: README-Start in sauberem Ordner geprüft, Checkliste als Abnahmeprotokoll vorbereitet, README neu gegliedert (docs/16-ap8-abgabe.md). AP1–AP8 und Änderung 1 technisch abgeschlossen. **Offen: fachliche Abnahme durch eine Person, Excel-Doppelklick.** SOLL S1–S4 nicht gebaut.

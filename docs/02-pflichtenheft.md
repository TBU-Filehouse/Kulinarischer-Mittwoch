# Pflichtenheft — Der kulinarische Mittwoch
Version 1.0 · 22.10.2026 · Umsetzungsvorschlag zum Lastenheft. Alles hier ist geplant, noch nicht implementiert.

## Lösungsaufbau
Ein Python-Prozess liefert servergerenderte HTML-Seiten mit Flask/Jinja und CSS; SQLite speichert den fachlichen Zustand in data/app.db. App bindet lokal an 127.0.0.1:5000. Browser ist Darstellung, der Server entscheidet über Regeln. Keine externe Laufzeit-API. Geplante Abhängigkeiten: Flask, tzdata; Entwicklung: pytest. Python-Ziel 3.12 oder neuer, konkrete installierte Version und kompatible Paketversionen vor AP1 prüfen und fixieren.

| Baustein | Verantwortung |
|---|---|
| routes.py | HTTP lesen, Formulare validieren, Status/Fehler darstellen |
| services.py / WednesdayService | Änderungsablauf, Zeitprüfung, Transaktionen |
| rules.py | Reine Regeln: Name, Frist, Kochgrenze, optional Kapazität; now wird übergeben |
| repository.py / SQLiteRepository | Parametrisierte SQL-Zugriffe, Schema, Transaktionsgrenzen |
| clock.py / Clock | Echte UTC-Zeit liefern, im Test ersetzbar |
| templates/ + static/ | Monatskalender, Detail, Formular, Einkaufsübersicht |

## Geplante Struktur
```text
app/
  __init__.py  __main__.py  routes.py  services.py
  rules.py  repository.py  clock.py  schema.sql
  templates/  static/
tests/
  test_rules.py  test_repository.py  test_http.py
scripts/check.py
requirements.txt
requirements-dev.txt
data/app.db                 # ignoriert, nie Testziel
docs/                       # liegt bereits vor
```

## Datenvertrag
| Entität | Felder / Integrität |
|---|---|
| Wednesday | date als ISO-Datum PRIMARY KEY; dish_title, dish_description, dish_type nullable bis Gericht erfasst; optional cancelled, cancellation_reason, max_portions |
| Cook | id, date FK, display_name, normalized_name; UNIQUE(date, normalized_name); maximal zwei aktive Einträge pro Tag |
| Registration | id, date FK, display_name, normalized_name, diet, note, created_at UTC; optional status confirmed/waitlisted/cancelled; UNIQUE(date, normalized_name) |
Kalender erzeugt Datumszellen rechnerisch; fehlender Wednesday-Datensatz bedeutet leeren, erreichbaren Mittwoch. Lazy-Anlage beim ersten Speichern; keine endliche Liste zukünftiger Termine. Buchung ist vor Frist auch ohne fertiges Gericht oder zwei Köche erlaubt; fehlende Planung bleibt sichtbar.

Cook und Registration sind getrennt. Ein Kochname darf auch als Essender vorkommen, zählt aber erst dort mit. Name wird außen getrimmt, für den Schlüssel per casefold verglichen; innere Leerzeichen bleiben erhalten. Leere Namen verboten. Namenszusätze sind sichtbar und werden normal mitverglichen. Keine echte Identitätsprüfung.
Im Must-Ausbau kann Essen-Abmeldung den Eintrag löschen. Mit S2 bleibt eine stornierte Registration erhalten; Wiederanmeldung reaktiviert denselben Schlüssel und bekommt einen neuen Wartelistenzeitpunkt. Kein zweiter aktiver Datensatz. FK-Prüfung aktivieren; Enumerationen per Validierung und CHECK absichern.

## Funktionsverträge
| Anforderung | Umsetzung | Fehler / Gegenprobe |
|---|---|---|
| M1 | GET /?month=YYYY-MM; Monatswechsel ohne Buchungs-Vorbelegung; Wochenbeginn Montag; Mittwoch hervorgehoben; Detail GET /wednesdays/YYYY-MM-DD | Ungültiger Monat/Tag → 400, unpassender Wochentag → 400; Januar/Dezember und Schaltjahr prüfen |
| M2 | POST /wednesdays/{date}/cooks und POST /wednesdays/{date}/cooks/{id}/remove | BEGIN IMMEDIATE; Frist und aktuellen Kochstand in Transaktion prüfen; dritter Koch/Duplikat → 409, keine Teiländerung |
| M3 | POST /wednesdays/{date}/dish mit Titel/Beschreibung/dish_type | Leerwerte/ungültige Kennzeichnung → 400; nach Frist Gericht aus Planungssicherheitsgründen ebenfalls nur lesbar |
| M4/M5 | POST /wednesdays/{date}/registrations und POST /wednesdays/{date}/registrations/{id}/remove | Name trim+casefold; UNIQUE schützt auch gleichzeitige Anfragen; Konflikt → 409; Erfolg → 303 auf Detail |
| M6 | Alle Änderungsrouten prüfen serverseitige Frist; UI zeigt Schlusszeit und geschlossenen Zustand | now >= cutoff bedeutet gesperrt, auch bei offener alter Browserseite; → 409 und keine Änderung |
| M7 | GET /wednesdays/{date}/shopping; bestätigte Essende zählen; Kategorien alles/vegetarisch/vegan disjunkt | Kategorien ergeben Gesamtzahl; Hinweise als Text mit Anzeigename; keine erfundenen Zutatenmengen |
| M8 | Lokale SQLite-Datei unabhängig vom aktuellen Arbeitsverzeichnis am Projektroot auflösen; Schema beim ersten Start idempotent | App-Neustart löscht nichts; Schemafehler sichtbar; DB-Fehler ohne Erfolgsmeldung |
IDs im Pfad immer gegen das zugehörige Datum prüfen; fremde/nicht vorhandene Zuordnung → 404. Fehlerstatus erscheinen als verständliche HTML-Meldung. Kein Login: Jeder lokale Nutzer könnte Einträge ändern; dies entspricht dem Demo-Umfang, nicht einer Zugriffsgarantie.

## Zeitregel
Für Mittwoch D: lokales Datum D minus einen Kalendertag, Uhrzeit 12:00 in ZoneInfo('Europe/Berlin'); danach zu UTC für Vergleich konvertieren. Server-Host-Zeitzone ist unerheblich. Keine festen UTC+1/+2-Offsets und kein pauschales „24 Stunden vorher“. now wird pro Änderung einmal vom Server erfasst und innerhalb der Transaktion geprüft.
Gegenproben: 28.10.2026 → Schluss 27.10.2026 12:00 CET = 11:00 UTC; 24.06.2026 → Schluss 23.06.2026 12:00 CEST = 10:00 UTC. Jeweils eine Sekunde vorher erlaubt, exakt und danach gesperrt. Der heutige Mittwoch wird als nicht mehr buchbar angezeigt, weil sein Dienstagsschluss vorbei ist.
Für Windows tzdata als explizite Abhängigkeit; fehlt die Zone, Startfehler mit Installationshinweis, keine stille UTC-Ausweichlösung.

## Should-Ausbaustufen
- S1: Kochstatus rein aus 0/1/2 ableiten, nicht redundant speichern.
- S5: CSS Grid, Formlabels, sichtbarer Fokus, ausreichend große Aktionen, Kalenderübersicht auf 375 px testen. Kein separates Mobilprodukt.
- S4: vergangene Termine anhand Berliner Datum nur lesbar; Grenze in Service, nicht nur ausgeblendete Schaltflächen.
- S3: eigener Absage-POST mit Pflichtgrund; Absage auch nach Buchungsschluss zulässig, da ein Essen tatsächlich ausfallen kann. Abgesagt ist endgültig für diese Abgabe; keine Wiederöffnung. Daten bleiben erhalten, normale Mutationen gesperrt; Einkaufsansicht zeigt „abgesagt“, aktive Zahl 0 und historische Zahlen getrennt.
- S2: max_portions positive ganze Zahl oder unbegrenzt; nur vor Frist setzbar. Senkung unter bestätigte Zahl ablehnen. Bei voller Kapazität FIFO-Warteliste nach created_at, dann id. Abmeldung und Nachrücken in derselben Transaktion, ausschließlich vor Frist; wartende Personen zählen nicht im Einkauf. Erhöhung rückt atomar passend viele nach. Köche beanspruchen nur mit bestätigter Essen-Anmeldung Portionen.
S3 erhält einen ausdrücklichen Ausnahmeweg von der normalen Schreibsperre; der Kochslot und Essensanmeldungen bleiben trotzdem geschlossen.

## Validierung und lokale Betriebsgrenze
Namen 1–80, Gerichttitel 1–120, Beschreibung 1–1000, Hinweise/Absagegrund bis 1000 Zeichen als Projektentscheidung; Hinweis optional, Absagegrund bei S3 nicht leer. Text im Template escapen, kein HTML aus Eingaben; SQL parametrisieren. POST für Änderungen und CSRF-Schutz/Origin-Prüfung beim Bau konkret festlegen und testen. Debugger standardmäßig aus. Keine realen Daten für Vorführung, kein Internet-Deployment im Must.

## Geplanter Start und Prüflauf
Voraussetzungen: Python mit pip und Internet für erstmalige Installation; danach lokale Nutzung ohne externe API. Aus dem Projektroot sollen nach Implementierung genau diese drei Befehle reichen:
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app
```
Diese Dateien/Module existieren aktuell noch nicht; die Befehle sind ein Zielvertrag. Für Entwicklung zusätzlich requirements-dev.txt und `python -m pytest`; AP7 erstellt einen zusammenfassenden Check. Kein bestandener Softwaretest wird aus dieser Dokumentation abgeleitet.

## Nachweisführung
M1–M8 → Lastenheft → AP1–AP8 im Projektplan → A-M1 bis A-M8 in der Abnahme. Teststrategie beschreibt erlaubte und verbotene Fälle. Änderungen am Umfang im Journal und CONTEXT dokumentieren; ersetzte Entscheidung durch neuen ADR oder datierten Nachtrag erhalten.

## Nachtrag AP1 — 22.10.2026
AP1 ist umgesetzt: Flask/SQLite-Grundgerüst, idempotentes Schema und Drei-Befehle-Start. routes/services/rules und fachliche Benutzerabläufe sind weiterhin geplant. Aktuelle Startanleitung in README.md; ursprünglicher Zielvertrag oben bleibt als Plan lesbar. Ein erster lokaler QS-Check ist vorgezogen eingerichtet; AP7 führt ihn später für den Gesamtumfang weiter. Nachweis in 07-ap1-qs.md.

## Nachtrag AP2 — 22.10.2026
rules.py und clock.py sind umgesetzt; APIs und Nachweise stehen in 08-ap2-qs.md. Der 80-Zeichen-Grenzwert gilt für den getrimmten Anzeigenamen vor casefold; der Vergleichsschlüssel darf durch Unicode-Faltung länger werden. Verwendete Zeitpunkte müssen zonierte datetime-Werte sein, Termine reine date-Werte für Mittwoche. Clock ist als Protokoll austauschbar; Einbindung in Service und Schreibtransaktionen folgt AP4/AP5. Kalender/Detail folgt AP3.

## Nachtrag AP3 — 22.10.2026
Kalender/Details über Blueprint in routes.py und Jinja-Templates umgesetzt. Kein zusätzliches calendar_view.py nötig: für diesen kleinen Leseumfang genügt der Blueprint mit Repository-Lesefunktionen. Keine leere Abstraktionshülle angelegt. Getrennte Cook-Abfrage und skalare Essenszählung verhindern Zählprodukte. Monat/Jahr strikt validiert, Montag explizit gesetzt, Datumgrenzen1/9999 ohne überlaufende Nachbarmonate. Appfactory prüft ZoneInfo vor Import zonenabhängiger Routen.
Browser-E2E und Grenzen dokumentiert in 09-ap3-qs-e2e.md. Keine Fachformulare oder Buchungsaktionen vorhanden; diese bleiben AP4/AP5.

## Nachtrag AP4 — 22.10.2026
Die drei Koch-/Gericht-POST-Routen sind implementiert. WednesdayService kapselt atomare Änderungen und nimmt Datenbankpfad/Clock entgegen. Detail-Repository erhält die bisherige cooks-Liste und ergänzt cook_entries mit IDs. Nach Fehlern bleiben Entwürfe editierbar; die Zusammenfassung zeigt ausschließlich gespeicherte Daten.
Session-CSRF und vorhandener Origin werden geprüft. Zufälliger App-Schlüssel oder KUMI_SECRET_KEY, Loopback-Hosts und 16-KiB-Bodylimit; größte gültige Unicode-Eingaben separat geprüft. Siehe ADR-006 und 10-ap4-qs-e2e.md. Essensanmeldung bleibt AP5.

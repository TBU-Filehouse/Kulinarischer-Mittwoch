# Aktivitätsdiagramm: Anmeldung (geplant)
Alle Schritte sind geplant. S2 (Limit/Warteliste) und S3 (Absage) sind Should-Umfang.

```mermaid
flowchart TD
    Start([Start]) --> Submit["Formular absenden"]
    Submit --> Begin["BEGIN IMMEDIATE; now aus Clock erfassen"]
    Begin --> Valid{"Name, Datum und Eingaben gueltig?"}
    Valid -->|Nein| Invalid["400 und ROLLBACK"]
    Valid -->|Ja| Lock{"Frist ab Dienstag 12 Uhr erreicht?"}
    Lock -->|Ja| Locked["409 und ROLLBACK"]
    Lock -->|Nein| Cancel{"Abgesagt? (S3)"}
    Cancel -->|Ja| Locked
    Cancel -->|Nein| Duplicate{"Name bereits aktiv belegt?"}
    Duplicate -->|Ja| Conflict["409 und ROLLBACK"]
    Duplicate -->|Nein| Capacity{"Kein Limit oder freie Portion?"}
    Capacity -->|Ja| Confirm["Status confirmed"]
    Capacity -->|Nein| Queue["Status waitlisted (S2)"]
    Confirm --> Save["Speichern mit UNIQUE(date, normalized_name)"]
    Queue --> Save
    Save --> Success{"Speichern erfolgreich?"}
    Success -->|Nein| Conflict
    Success -->|Ja| Commit["COMMIT und 303 auf Detail"]
    Invalid --> Ende([Ende])
    Locked --> Ende
    Conflict --> Ende
    Commit --> Ende
```

Frist und Zustand werden vor der fachlichen Änderung innerhalb der Transaktion geprüft; vorab sichtbare UI-Sperren ersetzen diese Prüfung nicht. Köche belegen nur über ihre separate bestätigte Essen-Anmeldung Portionen. Eine vor Frist stornierte Anmeldung darf nach Pflichtenheft denselben Schlüssel reaktivieren.

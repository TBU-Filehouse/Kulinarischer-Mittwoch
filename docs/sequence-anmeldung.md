# Sequenzdiagramm: Anmeldung (geplant)
Planungsstand; keine implementierte Funktion. Zeit, Absage und Integrität werden serverseitig geprüft.

```mermaid
sequenceDiagram
    actor Gast
    participant Route as Flask-Route
    participant Service as WednesdayService
    participant Rules as rules.py
    participant Repo as SQLiteRepository
    participant DB as SQLite
    Gast->>Route: Formular absenden
    Route->>Service: register(form)
    Service->>Repo: Transaktion beginnen
    Repo->>DB: BEGIN IMMEDIATE
    Service->>Service: now einmal aus Clock erfassen
    Service->>Rules: Frist und Name validieren
    Rules-->>Service: erlaubt oder gesperrt
    alt ab Dienstag 12 Uhr oder ungueltig
        Service->>Repo: rollback()
        Repo->>DB: ROLLBACK
        Service-->>Route: 400 oder 409, keine Aenderung
    else vor Frist und gueltig
        Service->>Repo: Termin und Anmeldungen laden
        Repo->>DB: SELECT
        DB-->>Repo: aktueller Zustand
        Repo-->>Service: Daten
        alt Termin abgesagt (S3)
            Service->>Repo: rollback()
            Repo->>DB: ROLLBACK
            Service-->>Route: 409, abgesagt
        else Termin offen
            Service->>Rules: Bestaetigung oder Warteliste (S2) bestimmen
            Rules-->>Service: confirmed oder optional waitlisted
            Service->>Repo: Anmeldung speichern
            Repo->>DB: INSERT mit UNIQUE-Schluessel
            alt Namenskonflikt oder Speicherfehler
                DB-->>Repo: Fehler
                Service->>Repo: rollback()
                Repo->>DB: ROLLBACK
                Service-->>Route: Fehler, keine Erfolgsmeldung
            else gespeichert
                DB-->>Repo: erfolgreich
                Service->>Repo: commit()
                Repo->>DB: COMMIT
                Service-->>Route: 303 auf Detailseite
            end
        end
    end
    Route-->>Gast: Ergebnis anzeigen
```

Die Fristprüfung liegt innerhalb der Schreibtransaktion vor jeder fachlichen Datenänderung. UNIQUE(date, normalized_name) verhindert Doppelanmeldungen auch bei parallelen Anfragen. Ohne S2 besteht kein Portionslimit; mit S2 zählt ausschließlich confirmed für den Einkauf. Warteliste/Absage sind Should-Umfang und hier keine Fertigmeldung.

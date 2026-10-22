# ER-Diagramm (geplant)

Das Modell bildet Mittwochstermine, separat erfasste Köche und Essensanmeldungen ab. Es beschreibt den geplanten Datenbestand, nicht eine bereits gebaute Datenbank.

```mermaid
erDiagram
    WEDNESDAY ||--o{ COOK : hat
    WEDNESDAY ||--o{ REGISTRATION : hat

    WEDNESDAY {
        date date PK
        string dish_title
        string dish_description
        enum dish_type "vegan | vegetarisch | fleisch_fisch"
        boolean cancelled
        string cancellation_reason "optional"
        int max_portions "optional"
    }
    COOK {
        int id PK
        date date FK
        string display_name
        string normalized_name "UNIQUE(date, normalized_name)"
    }
    REGISTRATION {
        int id PK
        date date FK
        string display_name
        string normalized_name "UNIQUE(date, normalized_name)"
        enum diet "alles | vegetarisch | vegan"
        string note "optional"
        enum status "confirmed | waitlisted | cancelled"
        datetime created_at
    }
```

Ein Cook-Datensatz bedeutet **keine** Essensanmeldung und wird nicht auf die Portionszahl angerechnet. Wer als Koch mitessen möchte, benötigt zusätzlich eine `REGISTRATION`. Pro Mittwoch sind höchstens zwei Köche erlaubt; die Prüfung erfolgt innerhalb der Service-Transaktion. `normalized_name` wird durch Trimmen und Casefolding gebildet. Namensvetter müssen einen unterscheidenden Zusatz verwenden.

Eine Absage setzt den Mittwoch auf abgesagt und erhält die zugehörigen Datensätze lesbar. Eine Warteliste ist ein optionales Should-Feature: FIFO-Nachrücken bei frei werdenden Portionen ist nur vor der Anmeldefrist vorgesehen.

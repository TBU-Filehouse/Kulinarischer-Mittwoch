# Klassendiagramm (geplant)

Das Diagramm zeigt die Verantwortlichkeiten des vorgesehenen Entwurfs. Es ist keine Beschreibung vorhandener Implementierungsklassen.

```mermaid
classDiagram
    class Wednesday {
        +date date
        +string dish_title
        +string dish_description
        +DishType dish_type
        +bool cancelled
        +string? cancellation_reason
        +int? max_portions
    }
    class Cook {
        +int id
        +date date
        +string display_name
        +string normalized_name
    }
    class Registration {
        +int id
        +date date
        +string display_name
        +string normalized_name
        +Diet diet
        +string? note
        +RegistrationStatus status
        +datetime created_at
    }
    class Rules {
        <<module>>
        +is_locked(now, wednesday_date) bool
        +normalize_name(display_name) string
        +can_add_cook(cooks) bool
        +registration_capacity(registrations, max_portions) int
    }
    class WednesdayService {
        +create_or_update_wednesday(data, now)
        +register(data, now)
        +cancel_registration(data, now)
        +add_cook(data, now)
        +remove_cook(data, now)
    }
    class Repository {
        +get_wednesday(date)
        +save_wednesday(wednesday)
        +list_cooks(date)
        +list_registrations(date)
        +save_cook(cook)
        +save_registration(registration)
    }
    class SQLiteDatabase {
        <<SQLite>>
        +transaction()
    }

    Wednesday "1" o-- "0..2" Cook : separate cook entries
    Wednesday "1" o-- "0..*" Registration : meal registrations
    WednesdayService --> Rules : checks before mutation
    WednesdayService --> Repository : transaction boundary
    Repository --> SQLiteDatabase : persistence
```

`Rules` erhält `now` als Eingabe und entscheidet die Sperre an der exakten Grenze Dienstag 12:00 Europe/Berlin vor dem zugehörigen Mittwoch. Der Service prüft die Sperre innerhalb der Transaktion vor jeder fachlichen Datenänderung und führt alle zustandsabhängigen Prüfungen und Änderungen atomar aus. Datenbank-UNIQUE-Bedingungen auf `(date, normalized_name)` sichern parallele oder doppelte Einträge zusätzlich ab. Köche zählen nicht automatisch als Essensanmeldungen.

Die Warteliste und das FIFO-Nachrücken sind optionale Should-Features und werden hier nicht als umgesetzt dargestellt.

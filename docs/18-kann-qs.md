# QS-Notiz KANN C1–C3 (ADR-010)
Stand 22.10.2026, Branch `feat/kann-c1-c3`. Nur technische Prüfung; Produktabnahme (Checkliste) ist nicht erfolgt.

## Lauf
`scripts/check.py` im Worktree: Exit 0, `technisch erfolgreich: True`. G5-Scan 86 Dateien, 0 Funde (die Namenssperrliste fehlt im Worktree, die Namensprüfung wurde dabei übersprungen). `pip check` ohne Fehler. Logik/HTTP: 349 Tests bestanden (davon 51 in `tests/test_could.py`). Chromium-E2E: 31 Tests bestanden (davon 2 in `tests/e2e/test_could_browser.py`).

## Was welcher Test belegt
| Anforderung | Nachweis |
|---|---|
| C1 Export gültiger Mittwoch | `test_c1_valid_wednesday_exports_all_day_event`: Content-Type, Dateiname, nur CRLF, `DTSTART`/`DTEND`, UID, `DTSTAMP` aus der injizierten Uhr, Escaping von Komma und Semikolon im Titel, Köche und Beschreibung |
| C1 Zeilenfaltung | `test_c1_long_lines_are_folded_at_75_octets` (kein Zeichen zerschnitten) |
| C1 offenes Gericht, keine Schreibwirkung | `test_c1_open_dish_and_no_row_created` |
| C1 ungültig / Nicht-Mittwoch | `test_c1_invalid_or_non_wednesday_rejected_like_detail` (4 Fälle, gleicher Status 400 wie Detailseite) |
| C1 Absage | `test_c1_cancelled_wednesday_is_marked_cancelled` (`STATUS:CANCELLED`, Grund) |
| C1 24 Monate voraus ohne Datensatz | `test_c1_far_future_date_without_record_works` (2028-10-25, keine Zeile angelegt) |
| C1 Link | `test_c1_detail_page_links_the_export`; Browser: `test_recipe_is_saved_and_opened_via_link_and_ics_link_serves_calendar` ruft den Link per `page.request.get` ab (`text/calendar`) |
| C3 positiv | `test_c3_save_and_read_recipe_after_reload` (neue Sitzung, HTML-Maskierung, Zeitstempel aus Uhr), `…update_replaces_recipe`, `…4000_characters_is_accepted`; Browser: speichern, über „Rezept ansehen“ öffnen, `pre-wrap`, maskiert |
| C3 negativ, DB unverändert | leer, nur Leerraum, 4001 Zeichen, Feld fehlt, ohne Gericht, nach Frist (Uhr injiziert, Grenze 12:00 Berlin), abgesagt, ohne/falscher CSRF-Token, Nicht-Mittwoch; fehlendes Rezept liefert 404 ohne neue Zeile |
| C2 positiv | `test_c2_two_ratings_average_and_list` (Durchschnitt 3,5 aus 2 Bewertungen, Namen getrimmt, Kommentar maskiert), `…average_one_decimal_german_comma_half_up` (5 Fälle), `…past_wednesday_can_be_rated_and_survives_new_session`, `…meal_day_early_morning_berlin_is_allowed` (00:30 Berlin bei noch gestrigem UTC-Datum) |
| C2 negativ, DB unverändert | zukünftiger Mittwoch (auch 23:30 Berlin am Vortag), ohne Gericht, abgesagt, Sterne `0 6 x` und weitere (8 Fälle), leerer/zu langer Name, Kommentar 501 Zeichen, Doppelname in anderer Schreibweise (`' anna demo '`, `ANNA DEMO`), ohne/falscher CSRF-Token, Nicht-Mittwoch |
| Bestands-Datenbank | `test_new_tables_are_added_to_an_existing_database`: alte DB ohne `recipe`/`rating` behält ihre Zeile und bekommt die Tabellen |

## Nicht geprüft / Grenzen
- Bewertung im Browser: nicht getestet. Der E2E-Testserver läuft auf der festen Uhr 2026-10-22 und kann keinen vergangenen Mittwoch mit Gericht halten (Gerichte sind nur vor der Frist änderbar); Bewertung ist deshalb nur über die HTTP-Tests belegt.
- Import der `.ics`-Datei in einen echten Kalenderclient (Outlook, Google, Apple) nicht ausprobiert; geprüft ist nur der Dateiinhalt gegen die RFC-5545-Regeln aus ADR-010.
- Rezept nahe 4000 Zeichen mit vielen Umlauten kann das 16-KB-Formularlimit überschreiten (siehe ADR-010); nicht getestet.
- C4 und C5 sind nicht gebaut (ADR-010).

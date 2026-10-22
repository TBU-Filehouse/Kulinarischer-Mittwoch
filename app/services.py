"""Transactional write operations for Wednesday planning."""

import sqlite3
from datetime import date
from pathlib import Path

from .clock import Clock
from .repository import connect_database
from .rules import (
    CookLimitError,
    DuplicateNameError,
    InvalidInputError,
    ensure_cook_slot,
    ensure_name_available,
    ensure_open,
    normalize_name,
    validate_wednesday,
)


class NotFoundError(LookupError):
    """A requested record does not belong to the supplied Wednesday."""


_DISH_TYPES = frozenset({"vegan", "vegetarisch", "fleisch_fisch"})
_DIETS = frozenset({"alles", "vegetarisch", "vegan"})
_DUPLICATE_REGISTRATION = "Dieser Name ist für diesen Mittwoch bereits zum Essen angemeldet."


class WednesdayService:
    """Apply validated, atomic changes to one SQLite database."""

    def __init__(self, database_path: str | Path, clock: Clock):
        self.database_path = database_path
        self.clock = clock

    def add_cook(self, day: date, display_name: str) -> int:
        normalized_name = normalize_name(display_name)
        trimmed_name = display_name.strip()
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            ensure_open(now, valid_day)
            existing = connection.execute(
                "SELECT display_name FROM cook WHERE date = ? ORDER BY id",
                (valid_day.isoformat(),),
            ).fetchall()
            ensure_name_available(trimmed_name, (row["display_name"] for row in existing))
            ensure_cook_slot(len(existing))
            connection.execute(
                "INSERT OR IGNORE INTO wednesday(date) VALUES(?)", (valid_day.isoformat(),)
            )
            cursor = connection.execute(
                "INSERT INTO cook(date, display_name, normalized_name) VALUES(?, ?, ?)",
                (valid_day.isoformat(), trimmed_name, normalized_name),
            )
            cook_id = cursor.lastrowid
            connection.commit()
            return cook_id
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            if "cook.date, cook.normalized_name" in str(exc) or "UNIQUE constraint failed: cook" in str(exc):
                raise DuplicateNameError("Dieser Name ist für Mittwoch und Rolle bereits vergeben.") from exc
            raise InvalidInputError("Der Koch konnte wegen eines Datenkonflikts nicht eingetragen werden.") from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def remove_cook(self, day: date, cook_id: int) -> None:
        if isinstance(cook_id, bool) or not isinstance(cook_id, int) or cook_id < 1:
            raise InvalidInputError("Die Koch-ID ist ungültig.")
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            ensure_open(now, valid_day)
            row = connection.execute(
                "SELECT id FROM cook WHERE id = ? AND date = ?",
                (cook_id, valid_day.isoformat()),
            ).fetchone()
            if row is None:
                raise NotFoundError("Dieser Koch ist für den angegebenen Mittwoch nicht eingetragen.")
            connection.execute("DELETE FROM cook WHERE id = ? AND date = ?", (cook_id, valid_day.isoformat()))
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def add_registration(self, day: date, display_name: str, diet: str, note: str | None) -> int:
        normalized_name = normalize_name(display_name)
        trimmed_name = display_name.strip()
        if not isinstance(diet, str) or diet not in _DIETS:
            raise InvalidInputError("Bitte wählen Sie eine gültige Ernährungsform.")
        if note is not None and not isinstance(note, str):
            raise InvalidInputError("Der Hinweis muss Text sein.")
        # Browsers submit textarea line breaks as CRLF but count them as one character.
        trimmed_note = (note or "").replace("\r\n", "\n").strip() or None
        if trimmed_note is not None and len(trimmed_note) > 1000:
            raise InvalidInputError("Der Hinweis darf nach dem Kürzen höchstens 1000 Zeichen haben.")
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            ensure_open(now, valid_day)
            existing = connection.execute(
                "SELECT display_name FROM registration WHERE date = ? ORDER BY id",
                (valid_day.isoformat(),),
            ).fetchall()
            try:
                ensure_name_available(trimmed_name, (row["display_name"] for row in existing))
            except DuplicateNameError as exc:
                raise DuplicateNameError(_DUPLICATE_REGISTRATION) from exc
            connection.execute(
                "INSERT OR IGNORE INTO wednesday(date) VALUES(?)", (valid_day.isoformat(),)
            )
            cursor = connection.execute(
                """INSERT INTO registration(date, display_name, normalized_name, diet, note)
                   VALUES(?, ?, ?, ?, ?)""",
                (valid_day.isoformat(), trimmed_name, normalized_name, diet, trimmed_note),
            )
            registration_id = cursor.lastrowid
            connection.commit()
            return registration_id
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            if "UNIQUE constraint failed: registration" in str(exc):
                raise DuplicateNameError(_DUPLICATE_REGISTRATION) from exc
            raise InvalidInputError("Die Anmeldung konnte wegen eines Datenkonflikts nicht gespeichert werden.") from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def remove_registration(self, day: date, registration_id: int) -> None:
        if isinstance(registration_id, bool) or not isinstance(registration_id, int) or registration_id < 1:
            raise InvalidInputError("Die Anmelde-ID ist ungültig.")
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            ensure_open(now, valid_day)
            deleted = connection.execute(
                "DELETE FROM registration WHERE id = ? AND date = ?",
                (registration_id, valid_day.isoformat()),
            ).rowcount
            if deleted != 1:
                raise NotFoundError("Diese Anmeldung gehört nicht zum angegebenen Mittwoch.")
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def save_dish(self, day: date, title: str, description: str, dish_type: str) -> None:
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
            raise InvalidInputError("Der Gerichttitel muss nach dem Kürzen 1 bis 120 Zeichen haben.")
        if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1000:
            raise InvalidInputError("Die Beschreibung muss nach dem Kürzen 1 bis 1000 Zeichen haben.")
        if not isinstance(dish_type, str) or dish_type not in _DISH_TYPES:
            raise InvalidInputError("Bitte wählen Sie eine gültige Kennzeichnung.")
        trimmed_title = title.strip()
        trimmed_description = description.strip()
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            ensure_open(now, valid_day)
            connection.execute(
                """INSERT INTO wednesday(date, dish_title, dish_description, dish_type)
                   VALUES(?, ?, ?, ?)
                   ON CONFLICT(date) DO UPDATE SET
                     dish_title = excluded.dish_title,
                     dish_description = excluded.dish_description,
                     dish_type = excluded.dish_type""",
                (valid_day.isoformat(), trimmed_title, trimmed_description, dish_type),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise InvalidInputError("Das Gericht konnte wegen eines Datenkonflikts nicht gespeichert werden.") from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

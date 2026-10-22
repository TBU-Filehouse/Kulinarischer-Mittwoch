"""Transactional write operations for Wednesday planning."""

import re
import sqlite3
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from datetime import timezone

from .clock import Clock
from .money import BUDGET_CENTS, parse_amount_cents
from .repository import connect_database
from .rules import (
    CookLimitError,
    DuplicateNameError,
    InvalidInputError,
    RuleViolation,
    ensure_cook_slot,
    ensure_name_available,
    ensure_open,
    is_locked,
    normalize_name,
    validate_wednesday,
)


class NotFoundError(LookupError):
    """A requested record does not belong to the supplied Wednesday."""


class ExpenseConflictError(RuleViolation):
    """The operation conflicts with existing expenses or the budget state."""


class WednesdayCancelledError(RuleViolation):
    """The Wednesday has been cancelled; meal planning is frozen."""


class PastWednesdayError(RuleViolation):
    """The Wednesday lies in the past and is read-only history."""


class BackfillNotNeededError(RuleViolation):
    """Before the deadline, cooks use the normal registration instead of the backfill."""


class PortionLimitError(RuleViolation):
    """The new portion limit would drop people who are already confirmed."""


class RatingNotYetOpenError(RuleViolation):
    """Ratings are possible from the day of the meal on, not before."""


_BERLIN = ZoneInfo("Europe/Berlin")
_LIMIT_PATTERN = re.compile(r"[0-9]{1,3}", re.ASCII)


def _ensure_not_past(now, day: date) -> None:
    if day < now.astimezone(_BERLIN).date():
        raise PastWednesdayError("Dieser Mittwoch liegt in der Vergangenheit und ist nur noch lesbar.")


def _ensure_not_cancelled(connection: sqlite3.Connection, day: date) -> None:
    if connection.execute(
        "SELECT 1 FROM cancellation WHERE date = ?", (day.isoformat(),)
    ).fetchone() is not None:
        raise WednesdayCancelledError("Dieser Mittwoch wurde abgesagt; Änderungen sind nicht mehr möglich.")


_DISH_TYPES = frozenset({"vegan", "vegetarisch", "fleisch_fisch"})
_DIETS = frozenset({"alles", "vegetarisch", "vegan"})
_DUPLICATE_REGISTRATION = "Dieser Name ist für diesen Mittwoch bereits zum Essen angemeldet."


class WednesdayService:
    """Apply validated, atomic changes to one SQLite database."""

    def __init__(self, database_path: str | Path, clock: Clock):
        self.database_path = database_path
        self.clock = clock

    def add_cook(self, day: date, display_name: str, backfill: bool = False) -> int:
        """Add a cook; ``backfill`` adds a missing cook after the deadline for accounting only (ADR-005)."""
        normalized_name = normalize_name(display_name)
        trimmed_name = display_name.strip()
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            if not backfill:
                ensure_open(now, valid_day)
            elif not is_locked(now, valid_day):
                raise BackfillNotNeededError("Vor dem Anmeldeschluss bitte das normale Formular zum Eintragen nutzen.")
            _ensure_not_cancelled(connection, valid_day)
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
            _ensure_not_cancelled(connection, valid_day)
            row = connection.execute(
                "SELECT id FROM cook WHERE id = ? AND date = ?",
                (cook_id, valid_day.isoformat()),
            ).fetchone()
            if row is None:
                raise NotFoundError("Dieser Koch ist für den angegebenen Mittwoch nicht eingetragen.")
            has_expenses = connection.execute(
                "SELECT 1 FROM expense WHERE cook_id = ? LIMIT 1", (cook_id,)
            ).fetchone()
            if has_expenses is not None:
                raise ExpenseConflictError(
                    "Dieser Koch hat noch Ausgaben erfasst. Bitte zuerst die Ausgaben löschen."
                )
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
            _ensure_not_cancelled(connection, valid_day)
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
            _ensure_not_cancelled(connection, valid_day)
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
            _ensure_not_cancelled(connection, valid_day)
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

    def set_portion_limit(self, day: date, raw_value: str) -> None:
        """Set or clear (blank) the portion limit; waitlist positions are derived."""
        if not isinstance(raw_value, str):
            raise InvalidInputError("Das Portionslimit muss Text sein.")
        value = raw_value.strip()
        limit = None
        if value:
            if not _LIMIT_PATTERN.fullmatch(value) or not 1 <= int(value) <= 999:
                raise InvalidInputError("Das Portionslimit muss eine ganze Zahl von 1 bis 999 sein.")
            limit = int(value)
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            iso = valid_day.isoformat()
            _ensure_not_past(now, valid_day)
            _ensure_not_cancelled(connection, valid_day)
            ensure_open(now, valid_day)
            if limit is None:
                connection.execute("DELETE FROM portion_limit WHERE date = ?", (iso,))
            else:
                total = connection.execute(
                    "SELECT COUNT(*) FROM registration WHERE date = ?", (iso,)
                ).fetchone()[0]
                current = connection.execute(
                    "SELECT max_portions FROM portion_limit WHERE date = ?", (iso,)
                ).fetchone()
                confirmed = total if current is None else min(total, current["max_portions"])
                if limit < confirmed:
                    raise PortionLimitError(
                        f"Das Limit kann nicht unter die Zahl der bestätigten Anmeldungen ({confirmed}) gesenkt werden."
                    )
                connection.execute("INSERT OR IGNORE INTO wednesday(date) VALUES(?)", (iso,))
                connection.execute(
                    """INSERT INTO portion_limit(date, max_portions) VALUES(?, ?)
                       ON CONFLICT(date) DO UPDATE SET max_portions = excluded.max_portions""",
                    (iso, limit),
                )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise InvalidInputError("Das Limit konnte wegen eines Datenkonflikts nicht gespeichert werden.") from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def cancel_wednesday(self, day: date, reason: str) -> None:
        """Cancel a Wednesday for good; data stays, meal changes are frozen."""
        if not isinstance(reason, str) or not 1 <= len(reason.replace("\r\n", "\n").strip()) <= 1000:
            raise InvalidInputError("Der Absagegrund muss nach dem Kürzen 1 bis 1000 Zeichen haben.")
        trimmed = reason.replace("\r\n", "\n").strip()
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            _ensure_not_past(now, valid_day)
            _ensure_not_cancelled(connection, valid_day)
            cancelled_at = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            connection.execute(
                "INSERT OR IGNORE INTO wednesday(date) VALUES(?)", (valid_day.isoformat(),)
            )
            connection.execute(
                "INSERT INTO cancellation(date, reason, cancelled_at) VALUES(?, ?, ?)",
                (valid_day.isoformat(), trimmed, cancelled_at),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise InvalidInputError("Die Absage konnte wegen eines Datenkonflikts nicht gespeichert werden.") from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def add_expense(self, day: date, amount: str, description: str, cook_id: str) -> int:
        """Book one expense position; independent of the registration deadline."""
        amount_cents = parse_amount_cents(amount)
        if not isinstance(description, str):
            raise InvalidInputError("Die Beschreibung muss Text sein.")
        trimmed = description.strip()
        if not 1 <= len(trimmed) <= 200 or "\r" in trimmed or "\n" in trimmed:
            raise InvalidInputError("Die Beschreibung muss 1 bis 200 Zeichen in einer Zeile haben.")
        if not isinstance(cook_id, str) or not re.fullmatch(r"[0-9]{1,18}", cook_id, re.ASCII):
            raise InvalidInputError("Bitte wählen Sie, wer die Ausgabe ausgelegt hat.")
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            valid_day = validate_wednesday(day)
            cook = connection.execute(
                "SELECT id, display_name FROM cook WHERE id = ? AND date = ?",
                (int(cook_id), valid_day.isoformat()),
            ).fetchone()
            if cook is None:
                raise InvalidInputError("Ausgelegt von muss ein Koch dieses Mittwochs sein.")
            connection.execute(
                "INSERT OR IGNORE INTO wednesday(date) VALUES(?)", (valid_day.isoformat(),)
            )
            cursor = connection.execute(
                """INSERT INTO expense(date, cook_id, paid_by_name, description, amount_cents)
                   VALUES(?, ?, ?, ?, ?)""",
                (valid_day.isoformat(), cook["id"], cook["display_name"], trimmed, amount_cents),
            )
            expense_id = cursor.lastrowid
            connection.commit()
            return expense_id
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise InvalidInputError("Die Ausgabe konnte wegen eines Datenkonflikts nicht gespeichert werden.") from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def remove_expense(self, day: date, expense_id: int) -> None:
        if isinstance(expense_id, bool) or not isinstance(expense_id, int) or expense_id < 1:
            raise InvalidInputError("Die Ausgaben-ID ist ungültig.")
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            valid_day = validate_wednesday(day)
            deleted = connection.execute(
                "DELETE FROM expense WHERE id = ? AND date = ?",
                (expense_id, valid_day.isoformat()),
            ).rowcount
            if deleted != 1:
                raise NotFoundError("Diese Ausgabe gehört nicht zum angegebenen Mittwoch.")
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def approve_overrun(self, day: date, approved_by: str, reason: str) -> None:
        if not isinstance(approved_by, str) or not 1 <= len(approved_by.strip()) <= 80:
            raise InvalidInputError("Der Name der genehmigenden Person muss 1 bis 80 Zeichen haben.")
        if not isinstance(reason, str) or not 1 <= len(reason.replace("\r\n", "\n").strip()) <= 1000:
            raise InvalidInputError("Die Begründung muss 1 bis 1000 Zeichen haben.")
        approver = approved_by.strip()
        trimmed_reason = reason.replace("\r\n", "\n").strip()
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            total = connection.execute(
                "SELECT COALESCE(SUM(amount_cents), 0) FROM expense WHERE date = ?",
                (valid_day.isoformat(),),
            ).fetchone()[0]
            if total <= BUDGET_CENTS:
                raise ExpenseConflictError("Das Budget ist nicht überschritten; es gibt nichts zu genehmigen.")
            approved_at = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            connection.execute(
                """INSERT INTO budget_approval(date, approved_by, reason, approved_total_cents, approved_at)
                   VALUES(?, ?, ?, ?, ?)
                   ON CONFLICT(date) DO UPDATE SET
                     approved_by = excluded.approved_by,
                     reason = excluded.reason,
                     approved_total_cents = excluded.approved_total_cents,
                     approved_at = excluded.approved_at""",
                (valid_day.isoformat(), approver, trimmed_reason, total, approved_at),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise InvalidInputError("Die Genehmigung konnte wegen eines Datenkonflikts nicht gespeichert werden.") from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def save_recipe(self, day: date, text: str) -> None:
        """Attach or replace the free-text recipe of an existing dish (C3, ADR-010)."""
        if not isinstance(text, str):
            raise InvalidInputError("Das Rezept muss Text sein.")
        # Browsers submit textarea line breaks as CRLF but count them as one character.
        trimmed = text.replace("\r\n", "\n").strip()
        if not 1 <= len(trimmed) <= 4000:
            raise InvalidInputError("Das Rezept muss nach dem Kürzen 1 bis 4000 Zeichen haben.")
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            iso = valid_day.isoformat()
            ensure_open(now, valid_day)
            _ensure_not_cancelled(connection, valid_day)
            dish = connection.execute(
                "SELECT dish_title FROM wednesday WHERE date = ?", (iso,)
            ).fetchone()
            if dish is None or not dish["dish_title"]:
                raise InvalidInputError("Bitte zuerst das Gericht eintragen; das Rezept gehört zu einem Gericht.")
            updated_at = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            connection.execute(
                """INSERT INTO recipe(date, text, updated_at) VALUES(?, ?, ?)
                   ON CONFLICT(date) DO UPDATE SET
                     text = excluded.text, updated_at = excluded.updated_at""",
                (iso, trimmed, updated_at),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise InvalidInputError("Das Rezept konnte wegen eines Datenkonflikts nicht gespeichert werden.") from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def add_rating(self, day: date, display_name: str, stars: str, comment: str | None) -> int:
        """Rate the dish from the meal day on; one rating per name and Wednesday (C2, ADR-010)."""
        normalized_name = normalize_name(display_name)
        trimmed_name = display_name.strip()
        if not isinstance(stars, str) or not re.fullmatch(r"[1-5]", stars, re.ASCII):
            raise InvalidInputError("Bitte vergeben Sie 1 bis 5 Sterne.")
        if comment is not None and not isinstance(comment, str):
            raise InvalidInputError("Der Kommentar muss Text sein.")
        trimmed_comment = (comment or "").replace("\r\n", "\n").strip() or None
        if trimmed_comment is not None and len(trimmed_comment) > 500:
            raise InvalidInputError("Der Kommentar darf nach dem Kürzen höchstens 500 Zeichen haben.")
        connection = connect_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock.now()
            valid_day = validate_wednesday(day)
            iso = valid_day.isoformat()
            _ensure_not_cancelled(connection, valid_day)
            if valid_day > now.astimezone(_BERLIN).date():
                raise RatingNotYetOpenError("Bewertungen sind erst ab dem Tag des Essens möglich.")
            dish = connection.execute(
                "SELECT dish_title FROM wednesday WHERE date = ?", (iso,)
            ).fetchone()
            if dish is None or not dish["dish_title"]:
                raise InvalidInputError("Ohne eingetragenes Gericht kann nichts bewertet werden.")
            existing = connection.execute(
                "SELECT display_name FROM rating WHERE date = ? ORDER BY id", (iso,)
            ).fetchall()
            try:
                ensure_name_available(trimmed_name, (row["display_name"] for row in existing))
            except DuplicateNameError as exc:
                raise DuplicateNameError("Dieser Name hat diesen Mittwoch bereits bewertet.") from exc
            cursor = connection.execute(
                """INSERT INTO rating(date, display_name, normalized_name, stars, comment)
                   VALUES(?, ?, ?, ?, ?)""",
                (iso, trimmed_name, normalized_name, int(stars), trimmed_comment),
            )
            rating_id = cursor.lastrowid
            connection.commit()
            return rating_id
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            if "UNIQUE constraint failed: rating" in str(exc):
                raise DuplicateNameError("Dieser Name hat diesen Mittwoch bereits bewertet.") from exc
            raise InvalidInputError("Die Bewertung konnte wegen eines Datenkonflikts nicht gespeichert werden.") from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

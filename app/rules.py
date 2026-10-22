"""Pure domain rules for Wednesday meal planning."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable
from zoneinfo import ZoneInfo


class RuleViolation(ValueError):
    """Base class for invalid or disallowed domain operations."""


class InvalidInputError(RuleViolation):
    """An input does not satisfy the domain's format or range rules."""


class DuplicateNameError(RuleViolation):
    """A name is already in use for the same Wednesday and role."""


class CookLimitError(RuleViolation):
    """The Wednesday already has the maximum number of cooks."""


class RegistrationClosedError(RuleViolation):
    """The registration deadline for the Wednesday has passed."""


_BERLIN = ZoneInfo("Europe/Berlin")


def validate_wednesday(wednesday_date: date) -> date:
    """Return a pure date when it is a Wednesday, otherwise reject it."""
    if type(wednesday_date) is not date:
        raise InvalidInputError("Es muss ein reines Datum angegeben werden.")
    if wednesday_date.weekday() != 2:
        raise InvalidInputError("Das Datum muss ein Mittwoch sein.")
    return wednesday_date


def normalize_name(display_name: str) -> str:
    """Normalize a display name for comparisons without changing its spacing."""
    if not isinstance(display_name, str):
        raise InvalidInputError("Der Name muss Text sein.")
    trimmed = display_name.strip()
    if not 1 <= len(trimmed) <= 80:
        raise InvalidInputError("Der Name muss nach dem Kürzen 1 bis 80 Zeichen haben.")
    return trimmed.casefold()


def ensure_name_available(display_name: str, existing_names: Iterable[str]) -> str:
    """Return the normalized name unless an existing name matches it."""
    normalized = normalize_name(display_name)
    try:
        duplicate = any(normalize_name(existing) == normalized for existing in existing_names)
    except TypeError as exc:
        raise InvalidInputError("Die vorhandenen Namen müssen iterierbar sein.") from exc
    if duplicate:
        raise DuplicateNameError("Dieser Name ist für Mittwoch und Rolle bereits vergeben.")
    return normalized


def registration_deadline(wednesday_date: date) -> datetime:
    """Return Tuesday at noon in Berlin before the given Wednesday."""
    valid_date = validate_wednesday(wednesday_date)
    try:
        tuesday = valid_date - timedelta(days=1)
    except OverflowError as exc:
        raise InvalidInputError("Für dieses Datum kann keine Frist berechnet werden.") from exc
    return datetime.combine(tuesday, time(12, 0), tzinfo=_BERLIN)


def _utc_instant(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidInputError("Der Zeitpunkt muss ein zoniertes Datum mit Uhrzeit sein.")
    try:
        offset = value.utcoffset()
        if value.tzinfo is None or offset is None:
            raise InvalidInputError("Der Zeitpunkt muss eine gültige Zeitzone enthalten.")
        return value.astimezone(timezone.utc)
    except (OverflowError, TypeError, ValueError) as exc:
        if isinstance(exc, InvalidInputError):
            raise
        raise InvalidInputError("Der Zeitpunkt muss eine gültige Zeitzone enthalten.") from exc


def is_locked(now: datetime, wednesday_date: date) -> bool:
    """Whether the supplied instant is at or after the Berlin deadline."""
    current_instant = _utc_instant(now)
    deadline_instant = registration_deadline(wednesday_date).astimezone(timezone.utc)
    return current_instant >= deadline_instant


def ensure_open(now: datetime, wednesday_date: date) -> None:
    """Raise when the registration window has closed."""
    if is_locked(now, wednesday_date):
        raise RegistrationClosedError("Die Anmeldefrist ist geschlossen.")


def ensure_cook_slot(existing_count: int) -> None:
    """Allow a cook registration only while fewer than two cooks exist."""
    if isinstance(existing_count, bool) or not isinstance(existing_count, int) or existing_count < 0:
        raise InvalidInputError("Die Zahl vorhandener Köche muss eine nichtnegative ganze Zahl sein.")
    if existing_count >= 2:
        raise CookLimitError("Für diesen Mittwoch sind bereits zwei Köche eingetragen.")

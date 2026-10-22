"""Exact money helpers: amounts are integer cents, never floats."""

import re

from .rules import InvalidInputError

BUDGET_CENTS = 30000
MAX_AMOUNT_CENTS = 1_000_000
_AMOUNT_PATTERN = re.compile(r"[0-9]{1,5}(?:[.,][0-9]{1,2})?", re.ASCII)


def parse_amount_cents(raw: str) -> int:
    """Parse '23,45' / '23.45' / '23' into cents with integer arithmetic."""
    if not isinstance(raw, str):
        raise InvalidInputError("Der Betrag muss Text sein.")
    text = raw.strip()
    if not _AMOUNT_PATTERN.fullmatch(text):
        raise InvalidInputError("Bitte geben Sie einen Betrag wie 23,45 an (höchstens zwei Nachkommastellen).")
    whole, _, fraction = text.replace(",", ".").partition(".")
    cents = int(whole) * 100 + int(fraction.ljust(2, "0") or "0")
    if not 0 < cents <= MAX_AMOUNT_CENTS:
        raise InvalidInputError("Der Betrag muss größer als 0 und höchstens 10.000,00 € sein.")
    return cents


def format_plain(cents: int) -> str:
    """'1234,56' without thousands separator (CSV)."""
    sign = "-" if cents < 0 else ""
    euros, rest = divmod(abs(cents), 100)
    return f"{sign}{euros},{rest:02d}"


def format_euro(cents: int) -> str:
    """German display format '1.234,56 €'."""
    sign = "-" if cents < 0 else ""
    euros, rest = divmod(abs(cents), 100)
    return f"{sign}{euros:,}".replace(",", ".") + f",{rest:02d} €"


def cost_per_person_cents(total_cents: int, count: int) -> int | None:
    """Total divided by persons, rounded half-up; None without registrations."""
    if count <= 0:
        return None
    return (2 * total_cents + count) // (2 * count)


def budget_status(total_cents: int, approved_total_cents: int | None) -> str:
    if total_cents <= BUDGET_CENTS:
        return "Im Budget"
    if approved_total_cents is not None and approved_total_cents >= total_cents:
        return "Budget überschritten, genehmigt"
    return "Budget überschritten, nicht genehmigt"

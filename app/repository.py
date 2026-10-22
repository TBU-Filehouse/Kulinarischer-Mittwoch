"""SQLite-Verbindungen und idempotente Datenbankinitialisierung."""

import sqlite3
from datetime import date
from pathlib import Path


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect_database(path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with named-row access and FK checks enabled.

    The caller owns the connection and must close it when finished.
    """
    database_path = Path(path)
    if not database_path.is_absolute():
        raise ValueError("Der Datenbankpfad muss absolut sein.")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(path: str | Path) -> None:
    """Create the AP1 schema if needed, preserving all existing rows."""
    connection = connect_database(path)
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)
    finally:
        connection.close()


def _confirmed_count(total: int, limit: int | None) -> int:
    """Confirmed registrations are the first `limit` ones; no limit confirms everyone."""
    return total if limit is None else min(total, limit)


def _portion_limit(connection: sqlite3.Connection, day: str) -> int | None:
    row = connection.execute(
        "SELECT max_portions FROM portion_limit WHERE date = ?", (day,)
    ).fetchone()
    return row["max_portions"] if row else None


def get_calendar_entries(path: str | Path, first_day: date, last_day: date) -> dict[str, dict]:
    """Read planned details and independent counts for persisted dates in a range.

    Dates without a Wednesday row are intentionally omitted; callers derive all
    calendar days from the calendar itself. Cook and registration counts use
    scalar subqueries so their rows can never multiply each other.
    """
    connection = connect_database(path)
    try:
        rows = connection.execute(
            """SELECT w.date, w.dish_title, w.dish_description, w.dish_type,
                      (SELECT COUNT(*) FROM registration r WHERE r.date = w.date) AS registration_count,
                      (SELECT max_portions FROM portion_limit p WHERE p.date = w.date) AS max_portions,
                      EXISTS(SELECT 1 FROM cancellation c WHERE c.date = w.date) AS cancelled
               FROM wednesday w WHERE w.date BETWEEN ? AND ? ORDER BY w.date""",
            (first_day.isoformat(), last_day.isoformat()),
        ).fetchall()
        cooks_by_date: dict[str, list[str]] = {}
        cook_rows = connection.execute(
            "SELECT date, display_name FROM cook WHERE date BETWEEN ? AND ? ORDER BY date, id",
            (first_day.isoformat(), last_day.isoformat()),
        ).fetchall()
        for row in cook_rows:
            cooks_by_date.setdefault(row["date"], []).append(row["display_name"])
        return {
            row["date"]: {
                "dish_title": row["dish_title"],
                "dish_description": row["dish_description"],
                "dish_type": row["dish_type"],
                "cooks": cooks_by_date.get(row["date"], []),
                "registration_count": _confirmed_count(row["registration_count"], row["max_portions"]),
                "cancelled": bool(row["cancelled"]),
            }
            for row in rows
        }
    finally:
        connection.close()


def get_wednesday_details(path: str | Path, wednesday_date: date) -> dict:
    """Read one date's details without creating a missing Wednesday row."""
    day = wednesday_date.isoformat()
    connection = connect_database(path)
    try:
        wednesday = connection.execute(
            "SELECT dish_title, dish_description, dish_type FROM wednesday WHERE date = ?",
            (day,),
        ).fetchone()
        cooks = connection.execute(
            "SELECT display_name FROM cook WHERE date = ? ORDER BY id", (day,)
        ).fetchall()
        cook_entries = connection.execute(
            "SELECT id, display_name FROM cook WHERE date = ? ORDER BY id", (day,)
        ).fetchall()
        max_portions = _portion_limit(connection, day)
        cancellation = connection.execute(
            "SELECT reason FROM cancellation WHERE date = ?", (day,)
        ).fetchone()
        registration_entries = connection.execute(
            "SELECT id, display_name, diet, note FROM registration WHERE date = ? ORDER BY created_at, id",
            (day,),
        ).fetchall()
        expense_entries = connection.execute(
            """SELECT id, description, amount_cents, paid_by_name FROM expense
               WHERE date = ? ORDER BY id""",
            (day,),
        ).fetchall()
        approval = connection.execute(
            """SELECT approved_by, reason, approved_total_cents, approved_at
               FROM budget_approval WHERE date = ?""",
            (day,),
        ).fetchone()
        recipe = connection.execute("SELECT text FROM recipe WHERE date = ?", (day,)).fetchone()
        rating_entries = connection.execute(
            "SELECT id, display_name, stars, comment FROM rating WHERE date = ? ORDER BY id", (day,)
        ).fetchall()
        entries = [dict(row) for row in registration_entries]
        waitlist_position = 0
        for index, entry in enumerate(entries):
            if max_portions is None or index < max_portions:
                entry["status"] = "confirmed"
                entry["waitlist_position"] = None
            else:
                waitlist_position += 1
                entry["status"] = "waitlisted"
                entry["waitlist_position"] = waitlist_position
        return {
            "dish_title": wednesday["dish_title"] if wednesday else None,
            "dish_description": wednesday["dish_description"] if wednesday else None,
            "dish_type": wednesday["dish_type"] if wednesday else None,
            "cooks": [row["display_name"] for row in cooks],
            "cook_entries": [
                {"id": row["id"], "display_name": row["display_name"]}
                for row in cook_entries
            ],
            "registration_count": len(entries) - waitlist_position,
            "waitlist_count": waitlist_position,
            "registration_entries": entries,
            "max_portions": max_portions,
            "cancelled": cancellation is not None,
            "cancellation_reason": cancellation["reason"] if cancellation else None,
            "expense_entries": [dict(row) for row in expense_entries],
            "expense_total_cents": sum(row["amount_cents"] for row in expense_entries),
            "approval": dict(approval) if approval else None,
            "recipe_text": recipe["text"] if recipe else None,
            "rating_entries": [dict(row) for row in rating_entries],
        }
    finally:
        connection.close()


def get_month_report_data(path: str | Path, first_day: date, last_day: date) -> dict:
    """Read expenses, approvals and cooks of a month without writing anything."""
    connection = connect_database(path)
    try:
        bounds = (first_day.isoformat(), last_day.isoformat())
        expenses = connection.execute(
            """SELECT id, date, description, amount_cents, paid_by_name FROM expense
               WHERE date BETWEEN ? AND ? ORDER BY date, id""",
            bounds,
        ).fetchall()
        approvals = connection.execute(
            """SELECT date, approved_by, reason, approved_total_cents FROM budget_approval
               WHERE date BETWEEN ? AND ?""",
            bounds,
        ).fetchall()
        cooks = connection.execute(
            "SELECT date, display_name FROM cook WHERE date BETWEEN ? AND ? ORDER BY date, id",
            bounds,
        ).fetchall()
        cancelled = connection.execute(
            "SELECT date FROM cancellation WHERE date BETWEEN ? AND ?", bounds
        ).fetchall()
        return {
            "cancelled": {row["date"] for row in cancelled},
            "expenses": [dict(row) for row in expenses],
            "approvals": {row["date"]: dict(row) for row in approvals},
            "cooks": [(row["date"], row["display_name"]) for row in cooks],
        }
    finally:
        connection.close()


def get_shopping_data(path: str | Path, wednesday_date: date) -> dict:
    """Read registrations for the shopping overview without creating rows.

    One query feeds total, per-diet counts and notes, so they cannot disagree.
    """
    day = wednesday_date.isoformat()
    connection = connect_database(path)
    try:
        dish = connection.execute(
            "SELECT dish_title, dish_type FROM wednesday WHERE date = ?", (day,)
        ).fetchone()
        registrations = connection.execute(
            "SELECT display_name, diet, note FROM registration WHERE date = ? ORDER BY created_at, id",
            (day,),
        ).fetchall()
        max_portions = _portion_limit(connection, day)
        cancelled = connection.execute(
            "SELECT 1 FROM cancellation WHERE date = ?", (day,)
        ).fetchone() is not None
    finally:
        connection.close()
    confirmed = registrations if max_portions is None else registrations[:max_portions]
    historical = len(confirmed)
    if cancelled:
        confirmed = []
    counts = {"alles": 0, "vegetarisch": 0, "vegan": 0}
    for row in confirmed:
        counts[row["diet"]] += 1
    return {
        "cancelled": cancelled,
        "historical_total": historical,
        "dish_title": dish["dish_title"] if dish else None,
        "dish_type": dish["dish_type"] if dish else None,
        "total": len(confirmed),
        "counts": counts,
        "notes": [
            {"name": row["display_name"], "note": row["note"]}
            for row in confirmed if row["note"]
        ],
    }

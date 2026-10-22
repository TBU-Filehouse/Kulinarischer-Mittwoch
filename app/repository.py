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
                      (SELECT COUNT(*) FROM registration r WHERE r.date = w.date) AS registration_count
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
                "registration_count": row["registration_count"],
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
        registration_count = connection.execute(
            "SELECT COUNT(*) FROM registration WHERE date = ?", (day,)
        ).fetchone()[0]
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
        return {
            "dish_title": wednesday["dish_title"] if wednesday else None,
            "dish_description": wednesday["dish_description"] if wednesday else None,
            "dish_type": wednesday["dish_type"] if wednesday else None,
            "cooks": [row["display_name"] for row in cooks],
            "cook_entries": [
                {"id": row["id"], "display_name": row["display_name"]}
                for row in cook_entries
            ],
            "registration_count": registration_count,
            "registration_entries": [dict(row) for row in registration_entries],
            "expense_entries": [dict(row) for row in expense_entries],
            "expense_total_cents": sum(row["amount_cents"] for row in expense_entries),
            "approval": dict(approval) if approval else None,
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
        return {
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
    finally:
        connection.close()
    counts = {"alles": 0, "vegetarisch": 0, "vegan": 0}
    for row in registrations:
        counts[row["diet"]] += 1
    return {
        "dish_title": dish["dish_title"] if dish else None,
        "dish_type": dish["dish_type"] if dish else None,
        "total": len(registrations),
        "counts": counts,
        "notes": [
            {"name": row["display_name"], "note": row["note"]}
            for row in registrations if row["note"]
        ],
    }

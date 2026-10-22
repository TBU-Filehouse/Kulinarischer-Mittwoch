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
        }
    finally:
        connection.close()

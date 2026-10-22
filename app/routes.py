"""Calendar pages and protected Wednesday planning forms."""

import calendar
import re
import sqlite3
from datetime import date
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException

from .repository import get_calendar_entries, get_wednesday_details
from .rules import (
    CookLimitError,
    DuplicateNameError,
    InvalidInputError,
    RegistrationClosedError,
    is_locked,
    registration_deadline,
)
from .services import NotFoundError, WednesdayService
from .csrf import get_csrf_token, validate_csrf_request


calendar_blueprint = Blueprint("calendar", __name__)
_BERLIN = ZoneInfo("Europe/Berlin")
_MONTH_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}", re.ASCII)
_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", re.ASCII)
_MONTH_NAMES = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)
_WEEKDAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
_DISH_TYPES = {
    "vegan": "Vegan",
    "vegetarisch": "Vegetarisch",
    "fleisch_fisch": "Fleisch oder Fisch",
}
_DIETS = {
    "alles": "Isst alles",
    "vegetarisch": "Vegetarisch",
    "vegan": "Vegan",
}


def _local_now():
    """Read the configured clock exactly once and return Berlin local time."""
    return current_app.config["CLOCK"].now().astimezone(_BERLIN)


def _parse_month(value: str) -> tuple[int, int]:
    if not _MONTH_PATTERN.fullmatch(value):
        raise ValueError
    year, month = int(value[:4]), int(value[5:7])
    if not 1 <= year <= 9999 or not 1 <= month <= 12:
        raise ValueError
    return year, month


def _parse_wednesday(value: str) -> date:
    if not _DATE_PATTERN.fullmatch(value):
        raise ValueError
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value or parsed.weekday() != 2:
        raise ValueError
    return parsed


def _bad_request(message: str):
    return render_template("error.html", message=message, back_url=url_for("calendar.index")), 400


def _detail_page(day: date, status: int = 200, error_message: str | None = None,
                 form_values: dict | None = None):
    now = _local_now()
    details = get_wednesday_details(current_app.config["DATABASE"], day)
    deadline = registration_deadline(day)
    values = form_values or {}
    return render_template(
        "detail.html",
        date_heading=f"Mittwoch, {day.day:02d}.{day.month:02d}.{day.year:04d}",
        day_value=day.isoformat(),
        month_value=f"{day.year:04d}-{day.month:02d}",
        title=details["dish_title"],
        description=details["dish_description"],
        form_title=values.get("title", details["dish_title"]),
        form_description=values.get("description", details["dish_description"]),
        selected_dish_type=values.get("dish_type", details["dish_type"]),
        dish_type=_DISH_TYPES.get(details["dish_type"]),
        cooks=details["cooks"],
        cook_entries=details["cook_entries"],
        form_cook_name=values.get("name", ""),
        registration_count=details["registration_count"],
        registration_entries=[
            {**entry, "diet_label": _DIETS[entry["diet"]]}
            for entry in details["registration_entries"]
        ],
        diets=_DIETS,
        form_registration_name=values.get("registration_name", ""),
        selected_diet=values.get("diet", ""),
        form_note=values.get("note", ""),
        csrf_token=get_csrf_token(),
        error_message=error_message,
        deadline_heading=(
            f"Dienstag, {deadline.day:02d}.{deadline.month:02d}.{deadline.year:04d} um 12:00 Uhr"
        ),
        locked=is_locked(now, day),
    ), status


def _write_error(day: date, error: Exception, form_values: dict | None = None):
    if isinstance(error, NotFoundError):
        status = 404
    elif isinstance(error, InvalidInputError):
        status = 400
    else:
        status = 409
    return _detail_page(day, status, str(error), form_values)


def _database_error():
    return render_template(
        "error.html",
        message="Die Änderung konnte wegen eines Datenbankfehlers nicht gespeichert werden. Bitte versuchen Sie es später erneut.",
        back_url=url_for("calendar.index"),
    ), 500


@calendar_blueprint.errorhandler(403)
def forbidden(error: HTTPException):
    return render_template(
        "error.html",
        message="Die Formularprüfung ist fehlgeschlagen. Bitte laden Sie die Seite neu und versuchen Sie es erneut.",
        back_url=url_for("calendar.index"),
    ), 403


@calendar_blueprint.errorhandler(405)
def method_not_allowed(error: HTTPException):
    return render_template(
        "error.html",
        message="Diese Aktion ist über diese Anfrage nicht verfügbar.",
        back_url=url_for("calendar.index"),
    ), 405


@calendar_blueprint.errorhandler(413)
def form_too_large(error: HTTPException):
    return render_template(
        "error.html",
        message="Das Formular ist zu groß. Bitte kürzen Sie die Eingaben und versuchen Sie es erneut.",
        back_url=url_for("calendar.index"),
    ), 413


@calendar_blueprint.get("/")
def index():
    now = _local_now()
    today = now.date()
    supplied_month = request.args.get("month")
    if supplied_month is None:
        year, month = today.year, today.month
    else:
        try:
            year, month = _parse_month(supplied_month)
        except ValueError:
            return _bad_request("Bitte wählen Sie einen gültigen Monat im Format JJJJ-MM.")

    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    entries = get_calendar_entries(current_app.config["DATABASE"], first_day, last_day)
    month_grid = []
    for week in calendar.Calendar(firstweekday=calendar.MONDAY).monthdayscalendar(year, month):
        cells = []
        for day_number in week:
            if day_number == 0:
                cells.append(None)
                continue
            day = date(year, month, day_number)
            iso_day = day.isoformat()
            data = entries.get(iso_day, {})
            is_wednesday = day.weekday() == 2
            cells.append({
                "day": day_number,
                "iso": iso_day,
                "wednesday": is_wednesday,
                "weekday": _WEEKDAYS[day.weekday()],
                "link": url_for("calendar.wednesday_detail", day_value=iso_day) if is_wednesday else None,
                "cooks": data.get("cooks", []),
                "dish_title": data.get("dish_title"),
                "registration_count": data.get("registration_count", 0),
            })
        month_grid.append(cells)

    previous_month = f"{year - 1:04d}-12" if month == 1 and year > 1 else (
        f"{year:04d}-{month - 1:02d}" if month > 1 else None
    )
    next_month = f"{year + 1:04d}-01" if month == 12 and year < 9999 else (
        f"{year:04d}-{month + 1:02d}" if month < 12 else None
    )
    return render_template(
        "calendar.html",
        year=year,
        month=month,
        month_name=_MONTH_NAMES[month - 1],
        month_value=f"{year:04d}-{month:02d}",
        today_month=f"{today.year:04d}-{today.month:02d}",
        previous_month=previous_month,
        next_month=next_month,
        weeks=month_grid,
        weekdays=_WEEKDAYS,
    )


@calendar_blueprint.get("/wednesdays/<day_value>")
def wednesday_detail(day_value: str):
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")

    response, _ = _detail_page(day)
    return response


@calendar_blueprint.post("/wednesdays/<day_value>/cooks")
def add_cook(day_value: str):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    name = request.form.get("name", "")
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).add_cook(day, name)
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, DuplicateNameError, CookLimitError, RegistrationClosedError) as exc:
        return _write_error(day, exc, {"name": name})
    flash("Der Koch wurde eingetragen.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/cooks/<int:cook_id>/remove")
def remove_cook(day_value: str, cook_id: int):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).remove_cook(day, cook_id)
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, RegistrationClosedError, NotFoundError) as exc:
        return _write_error(day, exc)
    flash("Der Koch wurde ausgetragen.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/registrations")
def add_registration(day_value: str):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    values = {
        "registration_name": request.form.get("name", ""),
        "diet": request.form.get("diet", ""),
        "note": request.form.get("note", ""),
    }
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).add_registration(
            day, values["registration_name"], values["diet"], values["note"]
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, DuplicateNameError, RegistrationClosedError) as exc:
        return _write_error(day, exc, values)
    flash("Die Essen-Anmeldung wurde gespeichert.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/registrations/<int:registration_id>/remove")
def remove_registration(day_value: str, registration_id: int):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).remove_registration(
            day, registration_id
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, RegistrationClosedError, NotFoundError) as exc:
        return _write_error(day, exc)
    flash("Die Essen-Anmeldung wurde entfernt.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/dish")
def save_dish(day_value: str):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    values = {
        "title": request.form.get("title", ""),
        "description": request.form.get("description", ""),
        "dish_type": request.form.get("dish_type", ""),
    }
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).save_dish(
            day, values["title"], values["description"], values["dish_type"]
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, RegistrationClosedError) as exc:
        return _write_error(day, exc, values)
    flash("Das Gericht wurde gespeichert.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)

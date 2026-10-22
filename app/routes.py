"""Calendar pages and protected Wednesday planning forms."""

import calendar
import csv
import io
import re
import sqlite3
from datetime import date, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException

from .money import BUDGET_CENTS, budget_status, cost_per_person_cents, format_euro, format_plain
from .repository import get_calendar_entries, get_month_report_data, get_shopping_data, get_wednesday_details
from .rules import (
    CookLimitError,
    DuplicateNameError,
    InvalidInputError,
    RegistrationClosedError,
    is_locked,
    registration_deadline,
)
from .services import (
    BackfillNotNeededError,
    ExpenseConflictError,
    NotFoundError,
    PastWednesdayError,
    PortionLimitError,
    RatingNotYetOpenError,
    WednesdayCancelledError,
    WednesdayService,
)
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


_COOK_STATUS = ("Köche gesucht", "1 Koch fehlt", "komplett")
_CALENDAR_STATUS = {
    "open": "Anmeldung offen",
    "closed": "Anmeldung geschlossen",
    "past": "Vergangen",
    "cancelled": "Abgesagt",
}


def _cook_status(count: int) -> str:
    return _COOK_STATUS[min(max(count, 0), 2)]


def _portion_label(limit: int | None) -> str:
    if limit is None:
        return "unbegrenzt"
    return "1 Portion" if limit == 1 else f"{limit} Portionen"


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


def _rating_summary(ratings: list[dict]) -> dict:
    """Average with one decimal place (half up, German comma) and count; None without ratings."""
    count = len(ratings)
    if count == 0:
        return {"count": 0, "average": None, "label": "Noch keine Bewertungen"}
    tenths = (sum(entry["stars"] for entry in ratings) * 20 + count) // (2 * count)
    average = f"{tenths // 10},{tenths % 10}"
    noun = "Bewertung" if count == 1 else "Bewertungen"
    return {"count": count, "average": average, "label": f"Ø {average} von 5 Sternen ({count} {noun})"}


def _ics_escape(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return (value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n"))


def _ics_fold(line: str) -> str:
    """Fold a content line at 75 octets without splitting UTF-8 characters (RFC 5545, 3.1)."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    parts: list[str] = []
    current = ""
    limit = 75
    for char in line:
        if len(current.encode("utf-8")) + len(char.encode("utf-8")) > limit:
            parts.append(current)
            current = char
            limit = 74  # continuation lines start with one space
        else:
            current += char
    parts.append(current)
    return "\r\n ".join(parts)


def _detail_page(day: date, status: int = 200, error_message: str | None = None,
                 form_values: dict | None = None):
    now = _local_now()
    details = get_wednesday_details(current_app.config["DATABASE"], day)
    deadline = registration_deadline(day)
    values = form_values or {}
    total = details["expense_total_cents"]
    approval = details["approval"]
    per_person = cost_per_person_cents(total, details["registration_count"])
    budget_state = budget_status(total, approval["approved_total_cents"] if approval else None)
    locked = is_locked(now, day)
    cancelled = details["cancelled"]
    is_past = day < now.date()
    ratings = details["rating_entries"]
    return render_template(
        "detail.html",
        ics_url=url_for("calendar.calendar_ics", day_value=day.isoformat()),
        recipe_url=url_for("calendar.recipe_page", day_value=day.isoformat()),
        has_recipe=details["recipe_text"] is not None,
        can_edit_recipe=not locked and not cancelled and bool(details["dish_title"]),
        form_recipe_text=values.get("recipe_text", details["recipe_text"] or ""),
        show_ratings=bool(details["dish_title"]) or bool(ratings),
        can_rate=not cancelled and bool(details["dish_title"]) and day <= now.date(),
        rating_summary=_rating_summary(ratings),
        rating_entries=ratings,
        form_rating_name=values.get("rating_name", ""),
        selected_stars=values.get("stars", ""),
        form_rating_comment=values.get("rating_comment", ""),
        cook_status=_cook_status(len(details["cook_entries"])),
        portion_limit_label=_portion_label(details["max_portions"]),
        form_max_portions=values.get(
            "max_portions", "" if details["max_portions"] is None else str(details["max_portions"])
        ),
        form_cancel_reason=values.get("cancel_reason", ""),
        waitlist_count=details["waitlist_count"],
        cancelled=cancelled,
        cancellation_reason=details["cancellation_reason"],
        is_past=is_past,
        can_edit_meal=not locked and not cancelled,
        can_cancel=not cancelled and not is_past,
        budget_total=format_euro(BUDGET_CENTS),
        expense_sum=format_euro(total),
        budget_remaining=format_euro(BUDGET_CENTS - total),
        budget_over_amount=format_euro(total - BUDGET_CENTS),
        over_budget=total > BUDGET_CENTS,
        budget_status=budget_state,
        approved=budget_state == "Budget überschritten, genehmigt",
        approval=approval,
        cost_per_person=format_euro(per_person) if per_person is not None else "keine Anmeldungen",
        expense_entries=[
            {**entry, "amount_label": format_euro(entry["amount_cents"])}
            for entry in details["expense_entries"]
        ],
        form_expense_amount=values.get("expense_amount", ""),
        form_expense_description=values.get("expense_description", ""),
        selected_expense_cook=values.get("expense_cook_id", ""),
        form_approved_by=values.get("approved_by", ""),
        form_approval_reason=values.get("approval_reason", ""),
        report_url=url_for("calendar.monthly_report", month_value=f"{day.year:04d}-{day.month:02d}"),
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
        form_backfill_name=values.get("backfill_name", ""),
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
        locked=locked,
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
            if data.get("cancelled"):
                cell_status = "cancelled"
            elif day < today:
                cell_status = "past"
            elif is_wednesday and is_locked(now, day):
                cell_status = "closed"
            else:
                cell_status = "open"
            cells.append({
                "day": day_number,
                "iso": iso_day,
                "wednesday": is_wednesday,
                "weekday": _WEEKDAYS[day.weekday()],
                "link": url_for("calendar.wednesday_detail", day_value=iso_day) if is_wednesday else None,
                "cooks": data.get("cooks", []),
                "dish_title": data.get("dish_title"),
                "registration_count": data.get("registration_count", 0),
                "status": cell_status,
                "status_label": _CALENDAR_STATUS[cell_status],
                "cook_status": _cook_status(len(data.get("cooks", []))),
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
        report_url=url_for("calendar.monthly_report", month_value=f"{year:04d}-{month:02d}"),
    )


@calendar_blueprint.get("/wednesdays/<day_value>")
def wednesday_detail(day_value: str):
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")

    response, _ = _detail_page(day)
    return response


@calendar_blueprint.get("/wednesdays/<day_value>/calendar.ics")
def calendar_ics(day_value: str):
    """C1: all-day calendar entry for one Wednesday (ADR-010); reads only, creates no rows."""
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    details = get_wednesday_details(current_app.config["DATABASE"], day)
    title = details["dish_title"]
    description = []
    if details["cooks"]:
        description.append("Köche: " + ", ".join(details["cooks"]))
    if details["dish_description"]:
        description.append(details["dish_description"])
    if details["cancelled"]:
        description.append("Abgesagt: " + details["cancellation_reason"])
    stamp = current_app.config["CLOCK"].now().astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    iso = day.isoformat()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Kulinarischer Mittwoch//DE",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:kumi-{iso}@localhost",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{day.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{(day + timedelta(days=1)).strftime('%Y%m%d')}",
        "SUMMARY:" + _ics_escape("Kulinarischer Mittwoch: " + (title or "Gericht noch offen")),
    ]
    if description:
        lines.append("DESCRIPTION:" + _ics_escape("\n".join(description)))
    if details["cancelled"]:
        lines.append("STATUS:CANCELLED")
    lines += ["END:VEVENT", "END:VCALENDAR"]
    body = "".join(_ics_fold(line) + "\r\n" for line in lines)
    return Response(
        body.encode("utf-8"),
        mimetype="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="kulinarischer-mittwoch-{iso}.ics"'},
    )


@calendar_blueprint.get("/wednesdays/<day_value>/recipe")
def recipe_page(day_value: str):
    """C3: show the recipe attached to the dish of one Wednesday."""
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    details = get_wednesday_details(current_app.config["DATABASE"], day)
    if details["recipe_text"] is None:
        return render_template(
            "error.html",
            message="Für diesen Mittwoch ist kein Rezept hinterlegt.",
            back_url=url_for("calendar.wednesday_detail", day_value=day.isoformat()),
        ), 404
    return render_template(
        "recipe.html",
        date_heading=f"Mittwoch, {day.day:02d}.{day.month:02d}.{day.year:04d}",
        day_value=day.isoformat(),
        dish_title=details["dish_title"],
        recipe_text=details["recipe_text"],
    )


@calendar_blueprint.post("/wednesdays/<day_value>/recipe")
def save_recipe(day_value: str):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    values = {"recipe_text": request.form.get("recipe", "")}
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).save_recipe(
            day, values["recipe_text"]
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, RegistrationClosedError, WednesdayCancelledError) as exc:
        return _write_error(day, exc, values)
    flash("Das Rezept wurde gespeichert.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/ratings")
def add_rating(day_value: str):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    values = {
        "rating_name": request.form.get("name", ""),
        "stars": request.form.get("stars", ""),
        "rating_comment": request.form.get("comment", ""),
    }
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).add_rating(
            day, values["rating_name"], values["stars"], values["rating_comment"]
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, DuplicateNameError, RatingNotYetOpenError, WednesdayCancelledError) as exc:
        return _write_error(day, exc, values)
    flash("Die Bewertung wurde gespeichert.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.get("/wednesdays/<day_value>/shopping")
def shopping(day_value: str):
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    data = get_shopping_data(current_app.config["DATABASE"], day)
    return render_template(
        "shopping.html",
        date_heading=f"Mittwoch, {day.day:02d}.{day.month:02d}.{day.year:04d}",
        day_value=day.isoformat(),
        dish_title=data["dish_title"],
        dish_type=_DISH_TYPES.get(data["dish_type"]),
        total=data["total"],
        diet_rows=[(key, _DIETS[key], data["counts"][key]) for key in ("alles", "vegetarisch", "vegan")],
        notes=data["notes"],
        cancelled=data["cancelled"],
        historical_total=data["historical_total"],
    )


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
    except (InvalidInputError, DuplicateNameError, CookLimitError, RegistrationClosedError,
            WednesdayCancelledError) as exc:
        return _write_error(day, exc, {"name": name})
    flash("Der Koch wurde eingetragen.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/cooks/backfill")
def backfill_cook(day_value: str):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    name = request.form.get("name", "")
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).add_cook(
            day, name, backfill=True
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, DuplicateNameError, CookLimitError, BackfillNotNeededError,
            WednesdayCancelledError) as exc:
        return _write_error(day, exc, {"backfill_name": name})
    flash("Der Koch wurde für die Abrechnung nachgetragen.", "success")
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
    except (InvalidInputError, RegistrationClosedError, NotFoundError, ExpenseConflictError,
            WednesdayCancelledError) as exc:
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
    except (InvalidInputError, DuplicateNameError, RegistrationClosedError, WednesdayCancelledError) as exc:
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
    except (InvalidInputError, RegistrationClosedError, NotFoundError, WednesdayCancelledError) as exc:
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
    except (InvalidInputError, RegistrationClosedError, WednesdayCancelledError) as exc:
        return _write_error(day, exc, values)
    flash("Das Gericht wurde gespeichert.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/portions")
def set_portion_limit(day_value: str):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    values = {"max_portions": request.form.get("max_portions", "")}
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).set_portion_limit(
            day, values["max_portions"]
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, RegistrationClosedError, WednesdayCancelledError,
            PastWednesdayError, PortionLimitError) as exc:
        return _write_error(day, exc, values)
    flash("Das Portionslimit wurde gespeichert.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/cancel")
def cancel_wednesday(day_value: str):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    values = {"cancel_reason": request.form.get("reason", "")}
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).cancel_wednesday(
            day, values["cancel_reason"]
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, WednesdayCancelledError, PastWednesdayError) as exc:
        return _write_error(day, exc, values)
    flash("Der Mittwoch wurde abgesagt.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/expenses")
def add_expense(day_value: str):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    values = {
        "expense_amount": request.form.get("amount", ""),
        "expense_description": request.form.get("description", ""),
        "expense_cook_id": request.form.get("cook_id", ""),
    }
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).add_expense(
            day, values["expense_amount"], values["expense_description"], values["expense_cook_id"]
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, ExpenseConflictError) as exc:
        return _write_error(day, exc, values)
    flash("Die Ausgabe wurde erfasst.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/expenses/<int:expense_id>/remove")
def remove_expense(day_value: str, expense_id: int):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).remove_expense(
            day, expense_id
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, NotFoundError) as exc:
        return _write_error(day, exc)
    flash("Die Ausgabe wurde gelöscht.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


@calendar_blueprint.post("/wednesdays/<day_value>/approval")
def approve_overrun(day_value: str):
    validate_csrf_request()
    try:
        day = _parse_wednesday(day_value)
    except ValueError:
        return _bad_request("Bitte geben Sie ein gültiges Mittwoch-Datum im Format JJJJ-MM-TT an.")
    values = {
        "approved_by": request.form.get("approved_by", ""),
        "approval_reason": request.form.get("reason", ""),
    }
    try:
        WednesdayService(current_app.config["DATABASE"], current_app.config["CLOCK"]).approve_overrun(
            day, values["approved_by"], values["approval_reason"]
        )
    except sqlite3.Error:
        return _database_error()
    except (InvalidInputError, ExpenseConflictError) as exc:
        return _write_error(day, exc, values)
    flash("Die Überschreitung wurde genehmigt.", "success")
    return redirect(url_for("calendar.wednesday_detail", day_value=day.isoformat()), code=303)


def _csv_text(value: str) -> str:
    return "'" + value if value[:1] in ("=", "+", "-", "@", "\t", "\r") else value


@calendar_blueprint.get("/reports/<month_value>")
def monthly_report(month_value: str):
    is_csv = month_value.endswith(".csv")
    try:
        year, month = _parse_month(month_value[:-4] if is_csv else month_value)
    except ValueError:
        return _bad_request("Bitte wählen Sie einen gültigen Monat im Format JJJJ-MM.")
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    data = get_month_report_data(current_app.config["DATABASE"], first_day, last_day)
    month_key = f"{year:04d}-{month:02d}"

    if is_csv:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Datum", "Standort", "Beschreibung", "Ausgelegt_von", "Betrag"])
        for expense in data["expenses"]:
            iso = expense["date"]
            writer.writerow([
                f"{iso[8:10]}.{iso[5:7]}.{iso[0:4]}",
                "Hamburg",
                _csv_text(expense["description"]),
                _csv_text(expense["paid_by_name"]),
                format_plain(expense["amount_cents"]),
            ])
        return Response(
            ("\ufeff" + buffer.getvalue()).encode("utf-8"),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="ausgaben-{month_key}.csv"'},
        )

    totals: dict[str, int] = {}
    reimbursement: dict[str, dict] = {}
    for expense in data["expenses"]:
        totals[expense["date"]] = totals.get(expense["date"], 0) + expense["amount_cents"]
        entry = reimbursement.setdefault(
            expense["paid_by_name"].casefold(), {"name": expense["paid_by_name"], "cents": 0}
        )
        entry["cents"] += expense["amount_cents"]
    cooks_by_date: dict[str, list[str]] = {}
    for iso, name in data["cooks"]:
        cooks_by_date.setdefault(iso, []).append(name)

    rows = []
    for week in calendar.Calendar(firstweekday=calendar.MONDAY).monthdayscalendar(year, month):
        for day_number in week:
            if day_number == 0 or date(year, month, day_number).weekday() != 2:
                continue
            day = date(year, month, day_number)
            iso = day.isoformat()
            total = totals.get(iso, 0)
            approval = data["approvals"].get(iso)
            status = budget_status(total, approval["approved_total_cents"] if approval else None)
            rows.append({
                "iso": iso,
                "label": f"{day.day:02d}.{day.month:02d}.{day.year:04d}",
                "cooks": ", ".join(cooks_by_date.get(iso, [])),
                "total": format_euro(total),
                "budget": format_euro(BUDGET_CENTS),
                "over": format_euro(total - BUDGET_CENTS) if total > BUDGET_CENTS else None,
                "status": {"Im Budget": "Im Budget",
                           "Budget überschritten, genehmigt": "genehmigt"}.get(status, "nicht genehmigt"),
                "cancelled": iso in data["cancelled"],
                "unapproved": status == "Budget überschritten, nicht genehmigt",
                "link": url_for("calendar.wednesday_detail", day_value=iso),
            })
    return render_template(
        "report.html",
        month_name=_MONTH_NAMES[month - 1],
        year=year,
        month_value=month_key,
        rows=rows,
        report_total=format_euro(sum(totals.values())),
        reimbursements=[
            {"name": entry["name"], "amount": format_euro(entry["cents"])}
            for entry in sorted(reimbursement.values(), key=lambda item: item["name"].casefold())
        ],
        csv_url=url_for("calendar.monthly_report", month_value=f"{month_key}.csv"),
    )

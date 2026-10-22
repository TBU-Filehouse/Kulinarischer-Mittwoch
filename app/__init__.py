"""Flask-Anwendung für den kulinarischen Mittwoch."""

import os
import secrets
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import Flask, jsonify

from .clock import SystemClock
from .repository import initialize_database


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "app.db"


def _absolute_database_path(value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError("DATABASE muss ein absoluter Dateipfad sein.")
    return path


def create_app(test_config: dict | None = None) -> Flask:
    """Create the app and initialize its configured SQLite database."""
    try:
        ZoneInfo("Europe/Berlin")
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError(
            "Die Zeitzone Europe/Berlin ist nicht verfügbar. "
            "Installieren Sie die Abhängigkeit mit "
            "'.venv\\Scripts\\python.exe -m pip install tzdata'."
        ) from exc

    app = Flask(__name__)
    configured_database = os.environ.get("KUMI_DATABASE", str(DEFAULT_DATABASE))
    configured_secret = os.environ.get("KUMI_SECRET_KEY") or secrets.token_bytes(32)
    app.config.from_mapping(
        DATABASE=str(_absolute_database_path(configured_database)),
        PORT=5000,
        CLOCK=SystemClock(),
        SECRET_KEY=configured_secret,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        TRUSTED_HOSTS=["localhost", "127.0.0.1", "[::1]"],
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config is not None:
        app.config.update(test_config)
    # Keep the per-app secret source explicit, including when test settings are supplied.
    app.config["SECRET_KEY"] = configured_secret
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["DATABASE"] = _absolute_database_path(app.config["DATABASE"])

    # Import zone-dependent routes only after the explicit startup check above.
    from .routes import calendar_blueprint

    initialize_database(app.config["DATABASE"])
    app.register_blueprint(calendar_blueprint)

    @app.get("/health")
    def health():
        from .repository import connect_database

        connection = connect_database(app.config["DATABASE"])
        try:
            connection.execute("SELECT 1").fetchone()
        finally:
            connection.close()
        return jsonify(status="ok")

    return app

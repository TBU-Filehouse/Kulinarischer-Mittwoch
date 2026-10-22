"""Session-bound CSRF tokens and same-origin checks for form posts."""

import hmac
import secrets
from urllib.parse import urlsplit

from flask import abort, request, session


_SESSION_KEY = "csrf_token"


def get_csrf_token() -> str:
    """Return the current session token, creating one when needed."""
    token = session.get(_SESSION_KEY)
    if not isinstance(token, str):
        token = secrets.token_urlsafe(32)
        session[_SESSION_KEY] = token
    return token


def validate_csrf_request() -> None:
    """Reject a missing, incorrect, cross-session, or foreign-origin post."""
    origin = request.headers.get("Origin")
    if origin is not None and not _same_origin(origin, request.host_url):
        abort(403)
    expected = session.get(_SESSION_KEY)
    supplied = request.form.get("csrf_token", "")
    if (
        not isinstance(expected, str)
        or not isinstance(supplied, str)
        or not hmac.compare_digest(expected.encode("utf-8"), supplied.encode("utf-8"))
    ):
        abort(403)


def _same_origin(origin: str, host_url: str) -> bool:
    try:
        supplied = urlsplit(origin)
        target = urlsplit(host_url)
        if (supplied.scheme.lower() not in {"http", "https"}
                or supplied.username is not None or supplied.password is not None
                or supplied.path not in {"", "/"} or supplied.query or supplied.fragment):
            return False
        return (
            supplied.scheme.lower() == target.scheme.lower()
            and supplied.netloc.casefold() == target.netloc.casefold()
        )
    except ValueError:
        return False

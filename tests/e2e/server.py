"""Isolated server used only by browser tests, never by normal application startup."""
from datetime import datetime, timezone
from pathlib import Path
import sys

from app import create_app
from test_calendar import seed_calendar


class FixedClock:
    def now(self):
        return datetime(2026, 10, 22, 12, tzinfo=timezone.utc)


if __name__ == '__main__':
    path = Path(sys.argv[1])
    app = create_app({'DATABASE': str(path), 'CLOCK': FixedClock()})
    seed_calendar(path)
    app.run(host='127.0.0.1', port=int(sys.argv[2]), debug=False, use_reloader=False)

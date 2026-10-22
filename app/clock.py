"""Injectable source of current time for application services."""

from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """Interface implemented by production and test clocks."""

    def now(self) -> datetime:
        """Return the current timezone-aware instant."""


class SystemClock:
    """Production clock returning the current instant in UTC."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

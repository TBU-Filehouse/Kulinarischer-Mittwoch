"""Independent AP2 oracles: examples, rejection cases, exact UTC boundaries."""
import ast
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.clock import SystemClock
from app.rules import (
    CookLimitError, DuplicateNameError, InvalidInputError, RegistrationClosedError,
    ensure_cook_slot, ensure_name_available, ensure_open, is_locked,
    normalize_name, registration_deadline, validate_wednesday,
)


@pytest.mark.parametrize('day,utc', [
    (date(2026, 10, 28), datetime(2026, 10, 27, 11, tzinfo=timezone.utc)),
    (date(2026, 6, 24), datetime(2026, 6, 23, 10, tzinfo=timezone.utc)),
    (date(2026, 3, 25), datetime(2026, 3, 24, 11, tzinfo=timezone.utc)),
    (date(2026, 4, 1), datetime(2026, 3, 31, 10, tzinfo=timezone.utc)),
    (date(2026, 10, 21), datetime(2026, 10, 20, 10, tzinfo=timezone.utc)),
    (date(2025, 1, 1), datetime(2024, 12, 31, 11, tzinfo=timezone.utc)),
])
def test_deadline_matches_independent_utc_oracles(day, utc):
    cutoff = registration_deadline(day)
    assert cutoff.astimezone(timezone.utc) == utc
    assert cutoff.tzinfo.key == 'Europe/Berlin'
    assert cutoff.hour == 12 and cutoff.minute == 0
    assert is_locked(utc - timedelta(microseconds=1), day) is False
    assert ensure_open(utc - timedelta(microseconds=1), day) is None
    for now in (utc, utc + timedelta(microseconds=1), utc + timedelta(days=1)):
        assert is_locked(now, day) is True
        with pytest.raises(RegistrationClosedError):
            ensure_open(now, day)


def test_equivalent_offsets_have_same_closed_status():
    day = date(2026, 10, 28)
    for now in (
        datetime(2026, 10, 27, 12, tzinfo=ZoneInfo('Europe/Berlin')),
        datetime(2026, 10, 27, 7, tzinfo=timezone(timedelta(hours=-4))),
        datetime(2026, 10, 27, 16, 30, tzinfo=timezone(timedelta(hours=5, minutes=30))),
    ):
        assert is_locked(now, day) is True


@pytest.mark.parametrize('invalid', [
    date(2026, 10, 26), date(2026, 10, 27), date(2026, 10, 29),
    date(2026, 10, 30), date(2026, 10, 31), date(2026, 11, 1),
    '2026-10-28', None, datetime(2026, 10, 28, tzinfo=timezone.utc),
])
def test_only_plain_wednesday_dates_are_valid(invalid):
    with pytest.raises(InvalidInputError):
        validate_wednesday(invalid)
    with pytest.raises(InvalidInputError):
        registration_deadline(invalid)


def test_calendar_accepts_leap_day_wednesday_and_far_future():
    for day in (date(2026, 10, 28), date(2012, 2, 29), date(9999, 12, 29)):
        assert validate_wednesday(day) == day


@pytest.mark.parametrize('invalid', [datetime(2026, 10, 27, 11), None, date(2026, 10, 27), 'now'])
def test_naive_or_non_datetime_now_rejected(invalid):
    with pytest.raises(InvalidInputError):
        is_locked(invalid, date(2026, 10, 28))


@pytest.mark.parametrize('raw,expected', [
    (' Anna ', 'anna'), ('ANNA', 'anna'), ('\tAnna\n', 'anna'),
    ('Straße', 'strasse'), ('Thomas A', 'thomas a'),
    ('Thomas  A', 'thomas  a'), (' ÄNNE ', 'änne'), ('A' * 80, 'a' * 80),
])
def test_name_normalization_contract(raw, expected):
    assert normalize_name(raw) == expected


@pytest.mark.parametrize('invalid', ['', '  \t\n ', 'x' * 81, None, 42, True])
def test_invalid_names_are_rejected(invalid):
    with pytest.raises(InvalidInputError):
        normalize_name(invalid)


def test_duplicates_and_name_suffixes_without_mutating_input():
    names = [' Anna ', 'Thomas A']
    original = names.copy()
    with pytest.raises(DuplicateNameError):
        ensure_name_available('ANNA', names)
    assert ensure_name_available('Thomas B', names) == 'thomas b'
    assert ensure_name_available('Ben Muster', names) == 'ben muster'
    assert names == original
    # The caller scopes this collection to the selected Wednesday and role.
    assert ensure_name_available('anna', []) == 'anna'


@pytest.mark.parametrize('count', [0, 1])
def test_first_and_second_cook_are_allowed(count):
    assert ensure_cook_slot(count) is None


@pytest.mark.parametrize('count', [2, 3, 100])
def test_third_or_more_cooks_are_rejected(count):
    with pytest.raises(CookLimitError):
        ensure_cook_slot(count)


@pytest.mark.parametrize('count', [-1, 1.5, '1', None, True, False])
def test_invalid_cook_count_rejected(count):
    with pytest.raises(InvalidInputError):
        ensure_cook_slot(count)


def test_system_clock_provides_current_aware_utc():
    before = datetime.now(timezone.utc)
    result = SystemClock().now()
    after = datetime.now(timezone.utc)
    assert result.utcoffset() == timedelta(0)
    assert before <= result <= after


def test_injected_time_changes_outcome_without_real_clock():
    class FakeClock:
        def __init__(self, value):
            self.value = value
        def now(self):
            return self.value
    clock = FakeClock(datetime(2026, 10, 27, 10, 59, 59, tzinfo=timezone.utc))
    assert is_locked(clock.now(), date(2026, 10, 28)) is False
    clock.value = datetime(2026, 10, 27, 11, tzinfo=timezone.utc)
    assert is_locked(clock.now(), date(2026, 10, 28)) is True


def test_rules_do_not_import_io_frameworks_or_read_current_time():
    # Mechanical guardrail for G4, beyond a prose instruction.
    source = Path(__file__).resolve().parents[1] / 'app' / 'rules.py'
    tree = ast.parse(source.read_text(encoding='utf-8-sig'))
    allowed = {'datetime', 'zoneinfo', 'typing', 'collections', '__future__'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split('.')[0] in allowed for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module and node.module.split('.')[0] in allowed
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {'now', 'today', 'utcnow', 'open'}
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {'open', 'eval', 'exec', '__import__'}

def test_name_length_applies_before_casefold_expansion():
    # 80 visible input characters are valid even when casefold doubles their length.
    assert normalize_name(' ß' + 'ß' * 79 + ' ') == 'ss' * 80

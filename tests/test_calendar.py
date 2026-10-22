"""AP3 HTTP acceptance tests with a fixed server clock and isolated database."""
from contextlib import closing
from datetime import datetime, timezone
import sqlite3

import pytest
from app import create_app


class FixedClock:
    def __init__(self, value):
        self.value = value
        self.calls = 0
    def now(self):
        self.calls += 1
        return self.value


@pytest.fixture
def calendar_app(tmp_path):
    clock = FixedClock(datetime(2026, 10, 22, 12, tzinfo=timezone.utc))
    app = create_app({'DATABASE': str(tmp_path / 'calendar.db'), 'TESTING': True, 'CLOCK': clock})
    return app, clock


def test_month_calendar_and_empty_detail_exist(calendar_app):
    app, _ = calendar_app
    with app.test_client() as client:
        response = client.get('/?month=2026-10')
        assert response.status_code == 200
        assert 'Oktober 2026' in response.get_data(as_text=True)
        assert '/wednesdays/2026-10-28' in response.get_data(as_text=True)
        detail = client.get('/wednesdays/2026-10-28')
        assert detail.status_code == 200
        assert 'Mittwoch, 28.10.2026' in detail.get_data(as_text=True)
    with closing(sqlite3.connect(app.config['DATABASE'])) as connection:
        assert connection.execute('SELECT COUNT(*) FROM wednesday').fetchone()[0] == 0

@pytest.mark.parametrize('value', ['2026-00','2026-13','0000-01','2026-1','26-10','2026-10x','', '２０２６-１０'])
def test_invalid_months_get_useful_400(calendar_app, value):
    app, _ = calendar_app
    with app.test_client() as client:
        response = client.get('/', query_string={'month': value})
        assert response.status_code == 400
        assert 'text/html' in response.content_type


@pytest.mark.parametrize('value', ['2026-10-27','2026-02-30','20261028','2026-W44-3','0000-01-01'])
def test_invalid_detail_dates_are_rejected(calendar_app, value):
    app, _ = calendar_app
    with app.test_client() as client:
        assert client.get('/wednesdays/' + value).status_code == 400


@pytest.mark.parametrize('month', ['0001-01','9999-12','2012-02','2026-12','2027-01','2028-10'])
def test_calendar_handles_month_boundaries_without_overflow(calendar_app, month):
    app, _ = calendar_app
    with app.test_client() as client:
        assert client.get('/', query_string={'month': month}).status_code == 200


def test_default_month_comes_from_berlin_and_clock_read_once(calendar_app):
    app, clock = calendar_app
    clock.value = datetime(2026, 12, 31, 23, 30, tzinfo=timezone.utc)
    clock.calls = 0
    with app.test_client() as client:
        response = client.get('/')
    assert 'Januar 2027' in response.get_data(as_text=True)
    assert clock.calls == 1


def test_empty_far_future_gets_do_not_create_rows(calendar_app):
    app, _ = calendar_app
    with app.test_client() as client:
        for path in ('/?month=2028-10','/wednesdays/2028-10-25'):
            assert client.get(path).status_code == 200
    with closing(sqlite3.connect(app.config['DATABASE'])) as connection:
        assert connection.execute('SELECT COUNT(*) FROM wednesday').fetchone()[0] == 0


def seed_calendar(path):
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            'INSERT INTO wednesday(date,dish_title,dish_description,dish_type) VALUES(?,?,?,?)',
            ('2026-10-28', 'Gemüse-Curry', 'Mit Reis und frischen Kräutern', 'vegan'),
        )
        for name in ('Anna Beispiel','Ben Muster'):
            connection.execute('INSERT INTO cook(date,display_name,normalized_name) VALUES(?,?,?)',
                               ('2026-10-28',name,name.casefold()))
        for name in ('Cora Demo','Deniz Test','Elli Beispiel'):
            connection.execute('INSERT INTO registration(date,display_name,normalized_name,diet) VALUES(?,?,?,?)',
                               ('2026-10-28',name,name.casefold(),'vegan'))
        connection.execute(
            'INSERT INTO wednesday(date,dish_title,dish_description,dish_type) VALUES(?,?,?,?)',
            ('2026-11-04', '<script>window.E2E_INJECTED=true</script>',
             '<img src=x onerror="window.E2E_INJECTED=true">', 'vegetarisch'),
        )
        connection.commit()


def test_persisted_summaries_escape_user_text_and_do_not_multiply_counts(calendar_app):
    app, _ = calendar_app
    seed_calendar(app.config['DATABASE'])
    with app.test_client() as client:
        month = client.get('/?month=2026-10').get_data(as_text=True)
        detail = client.get('/wednesdays/2026-10-28').get_data(as_text=True)
        assert 'Gemüse-Curry' in month
        assert 'Anna Beispiel' in detail and 'Ben Muster' in detail
        assert 'Mit Reis und frischen Kräutern' in detail
        malicious = client.get('/wednesdays/2026-11-04').get_data(as_text=True)
        assert '<script>window.E2E_INJECTED=true</script>' not in malicious
        assert '&lt;script&gt;' in malicious


def test_detail_changes_status_at_exact_server_deadline(calendar_app):
    app, clock = calendar_app
    with app.test_client() as client:
        clock.value = datetime(2026,10,27,10,59,59,tzinfo=timezone.utc)
        before = client.get('/wednesdays/2026-10-28').get_data(as_text=True)
        clock.value = datetime(2026,10,27,11,tzinfo=timezone.utc)
        after = client.get('/wednesdays/2026-10-28').get_data(as_text=True)
    assert 'Anmeldung offen' in before
    assert 'Anmeldung geschlossen' in after

def test_missing_timezone_is_guarded_even_on_fresh_module_import(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    script = '''
import zoneinfo
import sys
def missing_zone(key):
    raise zoneinfo.ZoneInfoNotFoundError(key)
zoneinfo.ZoneInfo = missing_zone
from app import create_app
try:
    create_app({'DATABASE': sys.argv[1]})
except RuntimeError as exc:
    assert 'tzdata' in str(exc)
    print('guarded')
else:
    raise AssertionError('missing timezone accepted')
'''
    path=tmp_path / 'no-zone.db'
    result=subprocess.run([sys.executable,'-c',script,str(path)],
                          cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    assert 'guarded' in result.stdout
    assert not path.exists()

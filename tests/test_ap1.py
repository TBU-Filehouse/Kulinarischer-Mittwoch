"""AP1 acceptance probes. All databases live in pytest temporary directories."""
from contextlib import closing
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from app import create_app
from app.repository import connect_database, initialize_database

ROOT = Path(__file__).resolve().parents[1]


def snapshot(path):
    with closing(sqlite3.connect(path)) as connection:
        return {
            table: connection.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall()
            for table in ('wednesday', 'cook', 'registration')
        }


def seed(path):
    # Independent SQL oracle, deliberately not application write helpers.
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            'INSERT INTO wednesday(date,dish_title,dish_description,dish_type) VALUES(?,?,?,?)',
            ('2026-10-28', 'Testgericht', 'Fiktive Beschreibung', 'vegan'),
        )
        connection.execute(
            'INSERT INTO cook(date,display_name,normalized_name) VALUES(?,?,?)',
            ('2026-10-28', 'Anna Beispiel', 'anna beispiel'),
        )
        connection.execute(
            'INSERT INTO registration(date,display_name,normalized_name,diet,note) VALUES(?,?,?,?,?)',
            ('2026-10-28', 'Ben Muster', 'ben muster', 'vegan', 'Fiktiver Hinweis'),
        )
        connection.commit()


def test_factory_initializes_and_serves_read_only_scaffold(tmp_path):
    path = tmp_path / 'nested' / 'test.db'
    app = create_app({'DATABASE': str(path), 'TESTING': True})
    assert path.is_file()
    assert snapshot(path) == {'wednesday': [], 'cook': [], 'registration': []}
    assert app.debug is False
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        assert 'Der kulinarische Mittwoch' in response.get_data(as_text=True)
        assert client.get('/health').get_json()['status'] == 'ok'
        assert client.post('/').status_code == 405


def test_reinitialization_preserves_all_rows(tmp_path):
    path = tmp_path / 'persist.db'
    initialize_database(path)
    seed(path)
    expected = snapshot(path)
    assert all(expected.values())
    initialize_database(path)
    create_app({'DATABASE': str(path), 'TESTING': True})
    assert snapshot(path) == expected


@pytest.mark.parametrize('statement,params', [
    ('INSERT INTO cook(date,display_name,normalized_name) VALUES(?,?,?)',
     ('2026-11-04', 'Cora Demo', 'cora demo')),
    ('INSERT INTO cook(date,display_name,normalized_name) VALUES(?,?,?)',
     ('2026-10-28', 'Anna Beispiel', 'anna beispiel')),
    ('INSERT INTO registration(date,display_name,normalized_name,diet) VALUES(?,?,?,?)',
     ('2026-10-28', 'Ben Muster', 'ben muster', 'vegan')),
    ('INSERT INTO registration(date,display_name,normalized_name,diet) VALUES(?,?,?,?)',
     ('2026-10-28', 'Cora Demo', 'cora demo', 'ungültig')),
    ('UPDATE wednesday SET dish_type=? WHERE date=?', ('ungültig', '2026-10-28')),
])
def test_database_rejects_invalid_writes_without_damage(tmp_path, statement, params):
    path = tmp_path / 'constraints.db'
    initialize_database(path)
    seed(path)
    expected = snapshot(path)
    connection = connect_database(path)
    try:
        assert connection.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            with connection:
                connection.execute(statement, params)
    finally:
        connection.close()
    assert snapshot(path) == expected


def test_different_wednesday_allows_same_name(tmp_path):
    path = tmp_path / 'separate.db'
    initialize_database(path)
    seed(path)
    connection = connect_database(path)
    try:
        with connection:
            connection.execute('INSERT INTO wednesday(date) VALUES(?)', ('2026-11-04',))
            connection.execute(
                'INSERT INTO registration(date,display_name,normalized_name,diet) VALUES(?,?,?,?)',
                ('2026-11-04', 'Ben Muster', 'ben muster', 'alles'),
            )
    finally:
        connection.close()
    assert len(snapshot(path)['registration']) == 2


def test_default_database_is_root_relative_without_touching_real_database(monkeypatch, tmp_path):
    # Replace initialization so this probe never creates or writes data/app.db.
    import app
    captured = []
    monkeypatch.setattr(app, 'initialize_database', lambda path: captured.append(Path(path)))
    monkeypatch.delenv('KUMI_DATABASE', raising=False)
    monkeypatch.chdir(tmp_path)
    instance = create_app({'TESTING': True})
    assert Path(instance.config['DATABASE']) == ROOT / 'data' / 'app.db'
    assert captured == [ROOT / 'data' / 'app.db']


def test_relative_database_override_is_rejected(monkeypatch):
    monkeypatch.setenv('KUMI_DATABASE', 'relative.db')
    with pytest.raises((ValueError, RuntimeError)):
        create_app({'TESTING': True})


def test_invalid_database_path_fails_visibly(tmp_path):
    # A regular file cannot be used as the parent directory of a database.
    blocked = tmp_path / 'file'
    blocked.write_text('do not overwrite', encoding='utf-8')
    with pytest.raises((OSError, sqlite3.Error, ValueError, RuntimeError)):
        create_app({'DATABASE': str(blocked / 'test.db'), 'TESTING': True})
    assert blocked.read_text(encoding='utf-8') == 'do not overwrite'


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def start_server(path, port, cwd, log_path):
    env = os.environ.copy()
    env.update(KUMI_DATABASE=str(path), KUMI_PORT=str(port), PYTHONPATH=str(ROOT))
    output = log_path.open('wb')
    process = subprocess.Popen(
        [sys.executable, '-m', 'app'], cwd=cwd, env=env,
        stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )
    output.close()
    try:
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail('App exited: ' + log_path.read_text(encoding='utf-8', errors='replace'))
            try:
                with urlopen(f'http://127.0.0.1:{port}/health', timeout=0.5) as response:
                    assert response.status == 200
                return process
            except (URLError, TimeoutError, ConnectionError):
                time.sleep(0.05)
        pytest.fail('Local app did not become ready within 12 seconds')
    except BaseException:
        stop_server(process)
        raise


def stop_server(process):
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def test_real_process_restart_preserves_database_from_other_cwd(tmp_path):
    path = tmp_path / 'restart' / 'test.db'
    port = free_port()
    first = start_server(path, port, tmp_path, tmp_path / 'first.log')
    try:
        seed(path)
        expected = snapshot(path)
        with urlopen(f'http://127.0.0.1:{port}/', timeout=2) as response:
            assert 'Der kulinarische Mittwoch' in response.read().decode('utf-8')
    finally:
        stop_server(first)
    assert first.poll() is not None  # Actual OS process termination, not a new factory.
    second = start_server(path, port, tmp_path, tmp_path / 'second.log')
    try:
        assert snapshot(path) == expected
        assert len(expected['cook']) == 1
        assert len(expected['registration']) == 1
    finally:
        stop_server(second)


def test_missing_timezone_fails_with_actionable_message(monkeypatch, tmp_path):
    import app
    from zoneinfo import ZoneInfoNotFoundError
    def missing_zone(key):
        raise ZoneInfoNotFoundError(key)
    monkeypatch.setattr(app, 'ZoneInfo', missing_zone)
    path = tmp_path / 'zone.db'
    with pytest.raises(RuntimeError, match='tzdata'):
        create_app({'DATABASE': str(path), 'TESTING': True})
    assert not path.exists()


def test_primary_date_cannot_be_null(tmp_path):
    path = tmp_path / 'primary.db'
    initialize_database(path)
    connection = connect_database(path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            with connection:
                connection.execute('INSERT INTO wednesday(date) VALUES(NULL)')
    finally:
        connection.close()

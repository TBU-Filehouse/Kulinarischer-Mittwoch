"""A real Chromium -> HTTP server -> temporary SQLite fixture."""
from pathlib import Path
import os
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def e2e_url(tmp_path_factory):
    folder = tmp_path_factory.mktemp('browser-server')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join((str(ROOT),str(ROOT / 'tests')))
    log_path = folder / 'server.log'
    with log_path.open('wb') as log:
        process = subprocess.Popen(
            [sys.executable, str(ROOT / 'tests/e2e/server.py'),str(folder / 'test.db'),str(port)],
            cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),
        )
    base = f'http://127.0.0.1:{port}'
    try:
        deadline = time.monotonic()+15
        while True:
            if process.poll() is not None:
                pytest.fail('Test server exited: '+log_path.read_text(encoding='utf-8',errors='replace'))
            try:
                with urlopen(base+'/health',timeout=.5) as response:
                    if response.status==200:
                        break
            except (URLError,TimeoutError,ConnectionError):
                if time.monotonic()>=deadline:
                    pytest.fail('Test server readiness timed out')
                time.sleep(.05)
        yield base
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture(autouse=True)
def reject_browser_errors(page):
    errors=[]
    page.on('pageerror',lambda error: errors.append(str(error)))
    yield
    assert not errors, 'Browser errors: '+repr(errors)

"""AP7: full MUSS flow in a real browser against the real `python -m app`, then a real restart.

Uses the production entry point with the real system clock, but an isolated database
(KUMI_DATABASE in a temp folder) — data/app.db is never touched.
"""
from datetime import datetime, timedelta
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

ROOT=Path(__file__).resolve().parents[2]
ARTIFACTS=ROOT/'test-results'


def target_wednesday():
    """A Wednesday at least 8 days ahead in Berlin, so its deadline is open on any run date."""
    start=datetime.now(ZoneInfo('Europe/Berlin')).date()+timedelta(days=8)
    return start+timedelta(days=(2-start.weekday())%7)


class AppProcess:
    """Production entry point `python -m app` on a fixed port and an isolated database."""

    def __init__(self,folder):
        self.folder=folder
        self.database=folder/'gesamtprobe.db'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            self.port=sock.getsockname()[1]
        self.url=f'http://127.0.0.1:{self.port}'
        self.process=None
        self.starts=0

    def start(self):
        env=os.environ.copy()
        env.update(KUMI_DATABASE=str(self.database),KUMI_PORT=str(self.port),PYTHONPATH=str(ROOT))
        env.pop('KUMI_SECRET_KEY',None)  # Realistic default: a new random session key per start.
        self.starts+=1
        log_path=self.folder/f'server-{self.starts}.log'
        with log_path.open('wb') as log:
            self.process=subprocess.Popen([sys.executable,'-m','app'],cwd=self.folder,env=env,
                                          stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        deadline=time.monotonic()+15
        while True:
            if self.process.poll() is not None:
                pytest.fail('App exited during start: '+log_path.read_text(encoding='utf-8',errors='replace'))
            try:
                with urlopen(self.url+'/health',timeout=.5) as response:
                    if response.status==200:
                        return
            except (URLError,TimeoutError,ConnectionError):
                if time.monotonic()>=deadline:
                    pytest.fail('App readiness timed out')
                time.sleep(.05)

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()  # Hard stop: committed SQLite data must survive.
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)


@pytest.fixture
def app_process(tmp_path):
    server=AppProcess(tmp_path)
    server.start()
    yield server
    server.stop()


def add_cook(page,name):
    page.get_by_label('Dein Name',exact=True).fill(name)
    page.get_by_role('button',name='Als Koch eintragen',exact=True).click()
    expect(page.locator('.cook-list')).to_contain_text(name)


def register(page,name,diet,note=''):
    page.get_by_label('Name für das Essen',exact=True).fill(name)
    page.get_by_label('Ernährungsform',exact=True).select_option(diet)
    page.get_by_label('Allergien/Hinweis (optional)',exact=True).fill(note)
    page.get_by_role('button',name='Zum Essen anmelden',exact=True).click()
    expect(page.locator('.registration-list')).to_contain_text(name)


def add_expense(page,amount,description,cook):
    page.get_by_label('Betrag (€)',exact=True).fill(amount)
    page.get_by_label('Beschreibung der Ausgabe',exact=True).fill(description)
    page.get_by_label('Ausgelegt von',exact=True).select_option(label=cook)
    page.get_by_role('button',name='Ausgabe erfassen',exact=True).click()
    expect(page.get_by_role('status').first).to_be_visible()


def snapshot(page,base,day):
    """Read every user-visible figure the acceptance cases rely on."""
    page.goto(f'{base}/wednesdays/{day.isoformat()}')
    figures={
        'cooks':page.locator('.cook-list').inner_text(),
        'dish':page.locator('.dish-card h3').inner_text(),
        'registrations':page.locator('.count-number').first.inner_text(),
        'list':page.locator('.registration-list').inner_text(),
        'sum':page.locator('#expense-sum').inner_text(),
        'over':page.locator('#budget-over').inner_text(),
        'status':page.locator('#budget-status').inner_text(),
        'approval':page.locator('#approval-note').inner_text(),
    }
    page.goto(f'{base}/wednesdays/{day.isoformat()}/shopping')
    figures['shopping']=[page.locator(f'#shopping-{key}').inner_text() for key in ('total','alles','vegetarisch','vegan')]
    figures['notes']=page.locator('.shopping-notes').inner_text()
    page.goto(f'{base}/reports/{day:%Y-%m}')
    figures['report_total']=page.locator('#report-total').inner_text()
    figures['anna']=page.locator('[data-reimbursement="Anna Müller"]').inner_text()
    figures['ben']=page.locator('[data-reimbursement="Ben Muster"]').inner_text()
    with page.expect_download() as info:
        page.get_by_role('link',name='CSV herunterladen').click()
    figures['csv']=Path(info.value.path()).read_bytes()
    return figures


def test_full_flow_survives_real_process_restart(page,browser,app_process):
    day=target_wednesday()
    base=app_process.url

    # Calendar -> Wednesday
    page.goto(f'{base}/?month={day:%Y-%m}')
    page.locator(f'[data-date="{day.isoformat()}"] a').first.click()
    expect(page.get_by_text('Anmeldung offen',exact=True)).to_be_visible()
    # Cooks -> dish
    add_cook(page,'Anna Müller')
    add_cook(page,'Ben Muster')
    page.get_by_label('Gerichttitel',exact=True).fill('Fischcurry')
    page.get_by_label('Beschreibung',exact=True).fill('Mit Reis und Gemüse')
    page.get_by_label('Kennzeichnung',exact=True).select_option('fleisch_fisch')
    page.get_by_role('button',name='Gericht speichern',exact=True).click()
    expect(page.locator('.dish-card h3')).to_have_text('Fischcurry')
    # Meal registrations (test strategy dataset)
    register(page,'Cora Demo','alles')
    register(page,'Deniz Test','alles')
    register(page,'Elli Beispiel','vegetarisch','keine Nüsse')
    register(page,'Finn Probe','vegan')
    # Expenses from the accounting sheet, overrun, approval
    add_expense(page,'23,45','Gemüse Wochenmarkt','Anna Müller')
    add_expense(page,'8,10','Brot; Butter','Ben Muster')
    add_expense(page,'12,50','Käse "Gouda" alt','Anna Müller')
    expect(page.locator('#budget-remaining')).to_have_text('255,95 €')
    add_expense(page,'280,00','Großeinkauf Fisch','Ben Muster')
    page.get_by_label('Genehmigt von',exact=True).fill('Gina Leitung')
    page.get_by_label('Begründung',exact=True).fill('Fischtag abgesprochen')
    page.get_by_role('button',name='Überschreitung genehmigen',exact=True).click()
    expect(page.locator('#budget-status')).to_have_text('Budget überschritten, genehmigt')
    page.goto(f'{base}/wednesdays/{day.isoformat()}')  # This form stays open across the restart.

    before=snapshot(page.context.new_page(),base,day)
    assert before['shopping']==['4','2','1','1']
    assert before['sum']=='324,05 €' and before['over']=='24,05 €'
    assert '35,95 €' in before['anna'] and '288,10 €' in before['ben']
    assert before['csv'].decode('utf-8-sig').count(f'{day:%d.%m.%Y};Hamburg;')==4

    # Real restart: stop the process, start the production entry point again on the same file and port.
    app_process.stop()
    app_process.start()
    fresh=browser.new_context(accept_downloads=True)
    try:
        after=snapshot(fresh.new_page(),base,day)
    finally:
        fresh.close()
    assert after==before, 'Data visible after restart differs from before'

    # The form opened before the restart carries a token of the old session key: rejected, nothing changes.
    page.get_by_label('Name für das Essen',exact=True).fill('Gast Alt')
    page.get_by_label('Ernährungsform',exact=True).select_option('alles')
    page.get_by_role('button',name='Zum Essen anmelden',exact=True).click()
    expect(page.get_by_text('Formularprüfung ist fehlgeschlagen',exact=False)).to_be_visible()
    check=browser.new_context()
    try:
        view=check.new_page()
        view.goto(f'{base}/wednesdays/{day.isoformat()}')
        expect(view.locator('.count-number').first).to_have_text('4')
        expect(view.locator('.registration-list')).not_to_contain_text('Gast Alt')
        ARTIFACTS.mkdir(exist_ok=True)
        view.screenshot(path=str(ARTIFACTS/'ap7-after-restart.png'),full_page=True)
    finally:
        check.close()

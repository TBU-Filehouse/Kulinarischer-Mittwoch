"""Acceptance run (ADR-009): play every checklist row in Chromium against the real `python -m app`.

Real system clock, fresh database in a temp folder (never data/app.db), one real restart for A-M8.
Writes test-results/abnahme-protokoll.json and prints one line per check. Exit 1 if any check fails.
Dates assume a run on 22.10.2026; other dates shift which Wednesdays are open or past.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OPEN, SHEET, OTHER, SHOP, STATUS, WAIT, CANCEL, PAST = (
    '2026-10-28', '2026-11-04', '2026-11-25', '2026-12-02', '2026-12-09', '2026-11-11', '2026-11-18', '2026-10-21')
results: dict[str, list] = {}


class App:
    def __init__(self, folder: Path):
        self.folder, self.db = folder, folder / 'abnahme.db'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.url, self.process = f'http://127.0.0.1:{self.port}', None

    def start(self):
        env = {**os.environ, 'KUMI_DATABASE': str(self.db), 'KUMI_PORT': str(self.port), 'PYTHONPATH': str(ROOT)}
        env.pop('KUMI_SECRET_KEY', None)
        self.process = subprocess.Popen([sys.executable, '-m', 'app'], cwd=self.folder, env=env,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        for _ in range(150):
            try:
                with urlopen(self.url + '/health', timeout=.5):
                    return
            except OSError:
                time.sleep(.1)
        raise RuntimeError('App startet nicht')

    def stop(self):
        self.process.terminate()
        self.process.wait(timeout=10)


def check(case, description, function):
    try:
        function()
        results.setdefault(case, []).append([description, True, ''])
        print(f'PASS {case}: {description}')
    except Exception as exc:  # noqa: BLE001 - record and continue with the next check.
        results.setdefault(case, []).append([description, False, str(exc).splitlines()[0][:200]])
        print(f'FAIL {case}: {description} -> {str(exc).splitlines()[0][:200]}')


def main():
    folder = Path(tempfile.mkdtemp(prefix='kumi-abnahme-'))
    app = App(folder)
    app.start()
    base = app.url
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))

        def go(day=None, path=''):
            page.goto(f'{base}/wednesdays/{day}{path}' if day else base + path)

        def cook(name):
            page.get_by_label('Dein Name', exact=True).fill(name)
            page.get_by_role('button', name='Als Koch eintragen', exact=True).click()

        def register(name, diet='alles', note=''):
            page.get_by_label('Name für das Essen', exact=True).fill(name)
            page.get_by_label('Ernährungsform', exact=True).select_option(diet)
            page.get_by_label('Allergien/Hinweis (optional)', exact=True).fill(note)
            page.get_by_role('button', name='Zum Essen anmelden', exact=True).click()

        def direct_post(day, suffix, form):
            go(OPEN)
            token = page.locator('input[name="csrf_token"]').first.get_attribute('value')
            return page.request.post(f'{base}/wednesdays/{day}/{suffix}', form={**form, 'csrf_token': token},
                                     headers={'Origin': base}, max_redirects=0).status

        def expense(amount, text, who):
            page.get_by_label('Betrag (€)', exact=True).fill(amount)
            page.get_by_label('Beschreibung der Ausgabe', exact=True).fill(text)
            page.get_by_label('Ausgelegt von', exact=True).select_option(label=who)
            page.get_by_role('button', name='Ausgabe erfassen', exact=True).click()
            expect(page.get_by_role('status').first).to_be_visible()

        # A-M1 -------------------------------------------------------------------------------
        def m1():
            page.goto(base + '/?month=2026-12')
            assert page.locator('thead th').first.inner_text().strip() == 'Montag'
            page.get_by_role('link', name='Folgemonat').click()
            expect(page.locator('h1')).to_have_text('Januar 2027')
            page.get_by_role('link', name='Vormonat').click()
            expect(page.locator('h1')).to_have_text('Dezember 2026')
            page.goto(base + '/?month=2028-10')
            page.locator('td.wednesday a').first.click()
            expect(page.get_by_text('Anmeldung offen', exact=True)).to_be_visible()
        check('A-M1', 'Montag zuerst, Dez→Jan→zurück, Mittwoch Okt. 2028 (24 Monate) offen', m1)

        # A-M2 -------------------------------------------------------------------------------
        def m2():
            go(OPEN); cook('Anna Müller'); cook('Ben Muster')
            expect(page.get_by_text('Alle zwei Kochplätze sind belegt.', exact=True)).to_be_visible()
            assert direct_post(OPEN, 'cooks', {'name': 'Cora Demo'}) == 409
            go(OPEN); page.get_by_role('button', name='Anna Müller als Koch austragen', exact=True).click()
            cook('Cora Demo')
            expect(page.locator('.cook-list')).to_contain_text('Cora Demo')
            expect(page.locator('.cook-list')).not_to_contain_text('Anna Müller')
        check('A-M2', '2 Köche, dritter (direkter POST) 409, Austragen öffnet Platz für Cora', m2)

        # A-M3 -------------------------------------------------------------------------------
        def m3():
            for kind in ('vegan', 'vegetarisch', 'fleisch_fisch'):
                go(OPEN)
                page.get_by_label('Gerichttitel', exact=True).fill(f'Gericht {kind}')
                page.get_by_label('Beschreibung', exact=True).fill('Mit Reis')
                page.get_by_label('Kennzeichnung', exact=True).select_option(kind)
                page.get_by_role('button', name='Gericht speichern', exact=True).click()
                page.reload()
                expect(page.get_by_label('Gerichttitel', exact=True)).to_have_value(f'Gericht {kind}')
                expect(page.get_by_label('Kennzeichnung', exact=True)).to_have_value(kind)
            assert direct_post(OPEN, 'dish', {'title': '', 'description': 'x', 'dish_type': 'vegan'}) == 400
        check('A-M3', 'Alle drei Kennzeichnungen speichern/neu laden; leerer Titel 400', m3)

        # A-M4 -------------------------------------------------------------------------------
        def m4():
            go(OPEN); register('Cora Demo'); register('Deniz Test', 'vegan', 'keine Nüsse')
            expect(page.locator('.count-number').first).to_have_text('2')
            page.get_by_role('button', name='Deniz Test vom Essen abmelden', exact=True).click()
            expect(page.locator('.count-number').first).to_have_text('1')
        check('A-M4', 'Anmeldung mit/ohne Hinweis, Abmeldung senkt Zahl 2→1', m4)

        # A-M5 -------------------------------------------------------------------------------
        def m5():
            go(OPEN); register(' Anna ')
            register('anna'); expect(page.get_by_role('alert')).to_be_visible()
            go(OPEN); register('Anna A'); expect(page.locator('.registration-list')).to_contain_text('Anna A')
            go(OTHER); register('anna'); expect(page.locator('.registration-list')).to_contain_text('anna')
        check('A-M5', '„ Anna “/„anna“ abgewiesen, „Anna A“ und anderer Mittwoch erlaubt', m5)

        # A-M6 -------------------------------------------------------------------------------
        def m6():
            go(PAST)
            expect(page.get_by_text('Anmeldung geschlossen', exact=True).first).to_be_visible()
            for action in ('cooks', 'dish', 'registrations'):
                expect(page.locator(f'form[action="/wednesdays/{PAST}/{action}"]')).to_have_count(0)
            assert direct_post(PAST, 'registrations', {'name': 'Spät', 'diet': 'alles'}) == 409
            go(OPEN); expect(page.get_by_text('Dienstag, 27.10.2026 um 12:00 Uhr')).to_be_visible()
        check('A-M6', 'Vergangener Mittwoch gesperrt (auch direkter POST 409), Frist 27.10. 12:00 sichtbar', m6)

        # A-M7 -------------------------------------------------------------------------------
        def m7():
            go(SHOP); cook('Elli Beispiel')
            for name, diet, note in (('Anna Müller', 'alles', ''), ('Ben Muster', 'alles', ''),
                                     ('Cora Demo', 'vegetarisch', 'keine Nüsse'), ('Deniz Test', 'vegan', '')):
                register(name, diet, note)
            page.get_by_role('link', name='Einkaufsübersicht').click()
            totals = [page.locator(f'#shopping-{key}').inner_text() for key in ('total', 'alles', 'vegetarisch', 'vegan')]
            assert totals == ['4', '2', '1', '1'], totals
            expect(page.locator('[data-note-name="Cora Demo"]')).to_contain_text('keine Nüsse')
        check('A-M7', 'Einkauf 4 = 2+1+1, Hinweis mit Namen, Koch zählt nicht', m7)

        # Change 1: A1-A4 ----------------------------------------------------------------------
        def a1():
            go(SHEET); expect(page.locator('#budget-total')).to_have_text('300,00 €')
        check('A1', 'Budget 300,00 € sichtbar', a1)

        def a2_a3():
            go(SHEET); cook('Anna Müller'); cook('Ben Muster')
            for name in ('Cora Demo', 'Deniz Test', 'Elli Beispiel', 'Finn Probe'):
                register(name)
            expense('23,45', 'Gemüse Wochenmarkt', 'Anna Müller')
            expense('8,10', 'Brot; Butter', 'Ben Muster')
            expense('12,50', 'Käse "Gouda" alt', 'Anna Müller')
            expect(page.locator('.expense-list, #expense-sum').first).to_be_visible()
            for element, value in (('#expense-sum', '44,05 €'), ('#budget-remaining', '255,95 €'), ('#cost-per-person', '11,01 €')):
                expect(page.locator(element)).to_have_text(value)
        check('A2/A3', 'Drei Blattpositionen erfasst; Plan vs. Ist 300,00 / 44,05 / 255,95, Kosten pro Person 11,01 €', a2_a3)

        def a3a():
            go(SHEET); expense('280,00', 'Großeinkauf Fisch', 'Ben Muster')
            expect(page.locator('#budget-over')).to_have_text('24,05 €')
            expect(page.locator('#budget-status')).to_have_text('Budget überschritten, nicht genehmigt')
            page.get_by_label('Genehmigt von', exact=True).fill('Gina Leitung')
            page.get_by_label('Begründung', exact=True).fill('Fischtag abgesprochen')
            page.get_by_role('button', name='Überschreitung genehmigen', exact=True).click()
            expect(page.locator('#budget-status')).to_have_text('Budget überschritten, genehmigt')
        check('A3a', 'Überschreitung 24,05 € markiert, Genehmigung mit Vermerk erkennbar', a3a)

        def a4():
            page.goto(base + '/reports/2026-11')
            expect(page.locator('#report-total')).to_have_text('324,05 €')
            expect(page.locator('[data-reimbursement="Anna Müller"]')).to_contain_text('35,95 €')
            expect(page.locator('[data-reimbursement="Ben Muster"]')).to_contain_text('288,10 €')
        check('A4', 'Monatsreport 324,05 €, Erstattung Anna 35,95 € · Ben 288,10 €', a4)

        def a5_download():
            page.goto(base + '/reports/2026-11')
            with page.expect_download() as info:
                page.get_by_role('link', name='CSV herunterladen').click()
            target = ROOT / 'test-results' / 'abnahme-ausgaben-2026-11.csv'
            target.parent.mkdir(exist_ok=True)
            info.value.save_as(str(target))
            raw = target.read_bytes()
            assert raw.startswith(b'\xef\xbb\xbf') and raw.decode('utf-8-sig').count('\r\n') == 5
        check('A5', 'CSV-Download (BOM, Kopf + 4 Zeilen) gespeichert für den Excel-Doppelklick', a5_download)

        # SOLL ------------------------------------------------------------------------------
        def s1():
            go(STATUS)
            for label, name in (('Köche gesucht', None), ('1 Koch fehlt', 'Anna Müller'), ('komplett', 'Ben Muster')):
                if name:
                    cook(name)
                expect(page.locator('#cook-status')).to_have_text(label)
            page.goto(base + '/?month=2026-12')
            expect(page.locator(f'[data-date="{STATUS}"]')).to_contain_text('komplett')
        check('A-S1', 'Köche gesucht → 1 Koch fehlt → komplett, auch im Kalender', s1)

        def s2():
            go(WAIT)
            page.get_by_label('Maximale Portionen', exact=True).fill('2')
            page.get_by_role('button', name='Portionen festlegen', exact=True).click()
            for name in ('Anna Müller', 'Ben Muster', 'Cora Demo'):
                register(name)
            expect(page.locator('[data-registration-status="waitlisted"]')).to_contain_text('Cora Demo')
            expect(page.get_by_text('Warteliste 1')).to_be_visible()
            page.get_by_role('button', name='Anna Müller vom Essen abmelden', exact=True).click()
            expect(page.locator('[data-registration-status="waitlisted"]')).to_have_count(0)
            register('Deniz Test')
            page.get_by_label('Maximale Portionen', exact=True).fill('1')
            page.get_by_role('button', name='Portionen festlegen', exact=True).click()
            expect(page.get_by_role('alert')).to_be_visible()
            page.goto(f'{base}/wednesdays/{WAIT}/shopping')
            expect(page.locator('#shopping-total')).to_have_text('2')
        check('A-S2', 'Limit 2: Warteliste 1, Nachrücken, Senken unter Bestätigte abgewiesen, Einkauf 2', s2)

        def s3():
            go(CANCEL); cook('Anna Müller'); register('Cora Demo')
            page.get_by_label('Absagegrund', exact=True).fill('Betriebsurlaub')
            page.get_by_role('button', name='Mittwoch absagen', exact=True).click()
            expect(page.locator('#cancellation-note')).to_contain_text('Betriebsurlaub')
            expect(page.get_by_role('button', name='Zum Essen anmelden', exact=True)).to_have_count(0)
            expense('9,99', 'Schon gekauft', 'Anna Müller')
            page.goto(f'{base}/wednesdays/{CANCEL}/shopping')
            expect(page.locator('#shopping-total')).to_have_text('0')
            expect(page.locator('#shopping-historical')).to_have_text('1')
        check('A-S3', 'Absage mit Grund, Formulare weg, Ausgabe weiter möglich, Einkauf 0 / vorher 1', s3)

        def s4():
            go(PAST); expect(page.get_by_text('Vergangener Mittwoch', exact=False)).to_be_visible()
            page.goto(base + '/?month=2026-10')
            expect(page.locator(f'[data-date="{PAST}"]')).to_have_attribute('data-status', 'past')
            expect(page.locator(f'[data-date="{OPEN}"]')).to_have_attribute('data-status', 'open')
            page.goto(base + '/?month=2026-11')
            expect(page.locator(f'[data-date="{CANCEL}"]')).to_have_attribute('data-status', 'cancelled')
        check('A-S4', 'Historie-Hinweis; Kalender: vergangen/offen/abgesagt', s4)

        def s5():
            page.set_viewport_size({'width': 375, 'height': 812})
            for path in ('/?month=2026-11', f'/wednesdays/{SHEET}', f'/wednesdays/{SHOP}/shopping', '/reports/2026-11'):
                page.goto(base + path)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), path
            page.set_viewport_size({'width': 1280, 'height': 900})
        check('A-S5', '375 px: Kalender, Detail, Einkauf, Report ohne Seitenüberlauf', s5)

        def backfill():
            go(PAST)
            page.get_by_label('Name des Kochs', exact=True).fill('Anna Müller')
            page.get_by_role('button', name='Koch nachtragen', exact=True).click()
            expect(page.get_by_role('button', name='Anna Müller als Koch austragen', exact=True)).to_have_count(0)
            expense('23,45', 'Nachgereichter Beleg', 'Anna Müller')
            page.get_by_label('Name des Kochs', exact=True).fill('Ben Muster')
            page.get_by_role('button', name='Koch nachtragen', exact=True).click()
            assert direct_post(PAST, 'cooks/backfill', {'name': 'Cora Demo'}) == 409
        check('A-B', 'Vergangener Mittwoch: Koch nachgetragen, Ausgabe gebucht, kein Austragen, dritter 409', backfill)

        # A-M8: real restart --------------------------------------------------------------------
        def m8():
            app.stop(); app.start()
            fresh = browser.new_context()
            view = fresh.new_page()
            view.goto(f'{base}/wednesdays/{SHOP}/shopping')
            expect(view.locator('#shopping-total')).to_have_text('4')
            view.goto(f'{base}/wednesdays/{SHEET}')
            expect(view.locator('#expense-sum')).to_have_text('324,05 €')
            expect(view.locator('.cook-list')).to_contain_text('Ben Muster')
            fresh.close()
        check('A-M8', 'Echter Neustart von python -m app, neuer Browserkontext: Daten identisch', m8)

        def no_js_errors():
            assert not errors, errors
        check('Browser', 'Keine JavaScript-Fehler im gesamten Lauf', no_js_errors)
        browser.close()
    app.stop()
    report = {'zeitpunkt': datetime.now().isoformat(timespec='seconds'), 'basis': base, 'faelle': results}
    out = ROOT / 'test-results' / 'abnahme-protokoll.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    failed = [case for case, checks in results.items() if not all(ok for _, ok, _ in checks)]
    print(f'Abnahmelauf: {len(results)} Fälle, fehlgeschlagen: {failed or "keine"}')
    return 1 if failed else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())

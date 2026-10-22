"""Browser -> real forms -> report -> CSV download for change 1 (A1-A5)."""
import csv
import io
from pathlib import Path

from playwright.sync_api import expect

ARTIFACTS=Path(__file__).resolve().parents[2]/'test-results'
DAY='2026-11-11'
EXPECTED_CSV=('﻿Datum;Standort;Beschreibung;Ausgelegt_von;Betrag\r\n'
              '11.11.2026;Hamburg;Gemüse Wochenmarkt;Anna Müller;23,45\r\n'
              '11.11.2026;Hamburg;"Brot; Butter";Ben Muster;8,10\r\n'
              '11.11.2026;Hamburg;"Käse ""Gouda"" alt";Anna Müller;12,50\r\n'
              '11.11.2026;Hamburg;Großeinkauf Fisch;Ben Muster;280,00\r\n').encode('utf-8')


def add_cook(page,name):
    page.get_by_label('Dein Name',exact=True).fill(name)
    page.get_by_role('button',name='Als Koch eintragen',exact=True).click()


def register(page,name):
    page.get_by_label('Name für das Essen',exact=True).fill(name)
    page.get_by_label('Ernährungsform',exact=True).select_option('alles')
    page.get_by_role('button',name='Zum Essen anmelden',exact=True).click()


def add_expense(page,amount,description,cook):
    page.get_by_label('Betrag (€)',exact=True).fill(amount)
    page.get_by_label('Beschreibung der Ausgabe',exact=True).fill(description)
    page.get_by_label('Ausgelegt von',exact=True).select_option(label=cook)
    page.get_by_role('button',name='Ausgabe erfassen',exact=True).click()
    expect(page.get_by_role('status').first).to_be_visible()


def test_sheet_flow_budget_approval_report_and_csv_download(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/'+DAY)
    expect(page.locator('#budget-total')).to_have_text('300,00 €')
    expect(page.get_by_role('button',name='Ausgabe erfassen',exact=True)).to_have_count(0)  # No cook yet.
    add_cook(page,'Anna Müller')
    add_cook(page,'Ben Muster')
    for name in ('Cora Demo','Deniz Test','Elli Beispiel','Finn Probe'):
        register(page,name)
    add_expense(page,'23,45','Gemüse Wochenmarkt','Anna Müller')
    add_expense(page,'8,10','Brot; Butter','Ben Muster')
    add_expense(page,'12,50','Käse "Gouda" alt','Anna Müller')
    expect(page.locator('#expense-sum')).to_have_text('44,05 €')
    expect(page.locator('#budget-remaining')).to_have_text('255,95 €')
    expect(page.locator('#cost-per-person')).to_have_text('11,01 €')
    expect(page.locator('#budget-status')).to_have_text('Im Budget')
    add_expense(page,'280,00','Großeinkauf Fisch','Ben Muster')
    expect(page.locator('#budget-over')).to_have_text('24,05 €')
    expect(page.locator('#budget-status')).to_have_text('Budget überschritten, nicht genehmigt')
    page.get_by_label('Genehmigt von',exact=True).fill('Cora Demo')
    page.get_by_label('Begründung',exact=True).fill('Fischtag mit Team abgesprochen')
    page.get_by_role('button',name='Überschreitung genehmigen',exact=True).click()
    expect(page.locator('#budget-status')).to_have_text('Budget überschritten, genehmigt')
    expect(page.locator('#approval-note')).to_contain_text('Cora Demo')

    page.goto(e2e_url+'/?month=2026-11')
    page.locator('a[href="/reports/2026-11"]').first.click()
    expect(page.locator('#report-total')).to_have_text('324,05 €')
    expect(page.locator('[data-reimbursement="Anna Müller"]')).to_contain_text('35,95 €')
    expect(page.locator('[data-reimbursement="Ben Muster"]')).to_contain_text('288,10 €')
    expect(page.locator(f'[data-report-date="{DAY}"]')).not_to_contain_text('nicht genehmigt')
    with page.expect_download() as info:
        page.get_by_role('link',name='CSV herunterladen').click()
    download=info.value
    assert download.suggested_filename=='ausgaben-2026-11.csv'
    data=Path(download.path()).read_bytes()
    assert data==EXPECTED_CSV
    parsed=list(csv.reader(io.StringIO(data.decode('utf-8-sig'),newline=''),delimiter=';'))
    assert len(parsed)==5 and {len(line) for line in parsed}=={5}


def test_expense_position_can_be_deleted_and_cook_with_expense_stays(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/'+DAY)
    add_cook(page,'Anna Müller')
    add_expense(page,'5,00','Fehlbuchung','Anna Müller')
    page.get_by_role('button',name='Anna Müller als Koch austragen',exact=True).click()
    expect(page.get_by_role('alert')).to_be_visible()
    page.goto(e2e_url+'/wednesdays/'+DAY)
    page.get_by_role('button',name='Fehlbuchung löschen',exact=True).click()
    expect(page.locator('#expense-sum')).to_have_text('0,00 €')


def test_report_on_mobile_without_overflow(page,e2e_url):
    page.set_viewport_size({'width':375,'height':812})
    page.goto(e2e_url+'/wednesdays/'+DAY)
    add_cook(page,'Anna Müller')
    add_expense(page,'280,00','Großeinkauf Fisch für das ganze Team mit langem Text','Anna Müller')
    add_expense(page,'30,00','Gewürze','Anna Müller')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.goto(e2e_url+'/reports/2026-11')
    expect(page.locator(f'[data-report-date="{DAY}"]')).to_contain_text('nicht genehmigt')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    status=page.locator(f'[data-report-date="{DAY}"] td').last  # Must be readable without sideways scrolling.
    expect(status).to_be_in_viewport()
    box=status.bounding_box()
    assert box['x']>=0 and box['x']+box['width']<=375
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS/'change1-mobile-report.png'),full_page=True)

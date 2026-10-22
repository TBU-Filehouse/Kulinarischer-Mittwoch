"""Browser checks for SOLL S1-S4: status in calendar, waitlist, cancellation."""
from pathlib import Path

from playwright.sync_api import expect

ARTIFACTS=Path(__file__).resolve().parents[2]/'test-results'
DAY='2026-11-11'  # Test server clock 2026-10-22: open.


def register(page,name):
    page.get_by_label('Name für das Essen',exact=True).fill(name)
    page.get_by_label('Ernährungsform',exact=True).select_option('alles')
    page.get_by_role('button',name='Zum Essen anmelden',exact=True).click()


def test_waitlist_promotion_and_cook_status(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/'+DAY)
    expect(page.locator('#cook-status')).to_have_text('Köche gesucht')
    page.get_by_label('Dein Name',exact=True).fill('Anna Müller')
    page.get_by_role('button',name='Als Koch eintragen',exact=True).click()
    expect(page.locator('#cook-status')).to_have_text('1 Koch fehlt')
    page.get_by_label('Maximale Portionen',exact=True).fill('1')
    page.get_by_role('button',name='Portionen festlegen',exact=True).click()
    expect(page.locator('#portion-limit')).to_have_text('1 Portion')
    register(page,'Cora Demo')
    register(page,'Deniz Test')
    expect(page.locator('[data-registration-status="waitlisted"]')).to_contain_text('Deniz Test')
    page.get_by_role('button',name='Cora Demo vom Essen abmelden',exact=True).click()
    expect(page.locator('[data-registration-status="confirmed"]')).to_contain_text('Deniz Test')
    expect(page.locator('[data-registration-status="waitlisted"]')).to_have_count(0)


def test_cancel_with_reason_on_mobile_and_calendar_status(page,e2e_url):
    page.set_viewport_size({'width':375,'height':812})
    page.goto(e2e_url+'/wednesdays/'+DAY)
    page.get_by_label('Absagegrund',exact=True).fill('Betriebsurlaub')
    page.get_by_role('button',name='Mittwoch absagen',exact=True).click()
    expect(page.locator('#cancellation-note')).to_contain_text('Betriebsurlaub')
    expect(page.get_by_role('button',name='Zum Essen anmelden',exact=True)).to_have_count(0)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.goto(e2e_url+'/?month=2026-11')
    expect(page.locator(f'[data-date="{DAY}"]')).to_have_attribute('data-status','cancelled')
    expect(page.locator('[data-date="2026-11-18"]')).to_have_attribute('data-status','open')
    page.goto(e2e_url+'/?month=2026-10')
    expect(page.locator('[data-date="2026-10-21"]')).to_have_attribute('data-status','past')
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS/'soll-mobile-calendar.png'),full_page=True)

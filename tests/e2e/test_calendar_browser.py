from pathlib import Path
import re
from playwright.sync_api import expect

ARTIFACTS = Path(__file__).resolve().parents[2] / 'test-results'


class CalendarPage:
    def __init__(self,page,base):
        self.page,self.base=page,base
    def open(self,month):
        self.page.goto(self.base+'/?month='+month)
    def choose(self,month):
        self.page.get_by_label('Monat auswählen',exact=True).fill(month)
        self.page.get_by_role('button',name='Anzeigen',exact=True).click()
    def next(self):
        self.page.get_by_role('link',name='Folgemonat',exact=True).click()
    def previous(self):
        self.page.get_by_role('link',name='Vormonat',exact=True).click()
    def open_wednesday(self,label):
        self.page.get_by_role('link',name='Mittwoch, '+label,exact=True).click()


def test_year_change_and_back_in_browser(page,e2e_url):
    calendar=CalendarPage(page,e2e_url)
    calendar.open('2026-12')
    expect(page.get_by_role('heading',name='Dezember 2026',exact=True)).to_be_visible()
    calendar.next()
    expect(page.get_by_role('heading',name='Januar 2027',exact=True)).to_be_visible()
    calendar.previous()
    expect(page.get_by_role('heading',name='Dezember 2026',exact=True)).to_be_visible()
    assert [text.strip() for text in page.locator('thead th').all_text_contents()]==['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag']


def test_month_form_leap_day_detail_and_return(page,e2e_url):
    calendar=CalendarPage(page,e2e_url)
    calendar.open('2026-10')
    calendar.choose('2012-02')
    expect(page.get_by_role('heading',name='Februar 2012',exact=True)).to_be_visible()
    expect(page.locator('[data-date="2012-02-29"]')).to_have_class(re.compile('wednesday'))
    calendar.open_wednesday('29.02.2012')
    expect(page.get_by_role('heading',name='Mittwoch, 29.02.2012',exact=True)).to_be_visible()
    expect(page.get_by_text('Anmeldung geschlossen',exact=True)).to_be_visible()
    page.get_by_role('link',name=re.compile('Zum Monatskalender')).click()
    expect(page.get_by_role('heading',name='Februar 2012',exact=True)).to_be_visible()


def test_twenty_four_months_without_precreated_dates(page,e2e_url):
    calendar=CalendarPage(page,e2e_url)
    calendar.open('2026-10')
    for _ in range(24):
        calendar.next()
    expect(page.get_by_role('heading',name='Oktober 2028',exact=True)).to_be_visible()
    calendar.open_wednesday('25.10.2028')
    expect(page.get_by_role('heading',name='Mittwoch, 25.10.2028',exact=True)).to_be_visible()
    expect(page.get_by_text('Anmeldung offen',exact=True)).to_be_visible()


def test_summaries_details_and_read_only_status(page,e2e_url):
    calendar=CalendarPage(page,e2e_url)
    calendar.open('2026-10')
    card=page.locator('[data-date="2026-10-28"]')
    expect(card).to_contain_text('Gemüse-Curry')
    expect(card).to_contain_text('Anmeldungen 3')
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS/'ap3-desktop-calendar.png'),full_page=True)
    calendar.open_wednesday('28.10.2026')
    cooks=page.locator('.cook-list')  # Names also appear as "Ausgelegt von" options since change 1.
    expect(cooks.get_by_text('Anna Beispiel',exact=True)).to_be_visible()
    expect(cooks.get_by_text('Ben Muster',exact=True)).to_be_visible()
    expect(page.locator('.description')).to_have_text('Mit Reis und frischen Kräutern')
    expect(page.locator('.registration-list')).to_contain_text('Cora Demo')  # AP5 lists persisted registrations.
    expect(page.locator('.count-number')).to_have_text('3')
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS/'ap3-detail.png'),full_page=True)


def test_bad_url_displays_error_and_not_browser_exception(page,e2e_url):
    response=page.goto(e2e_url+'/?month=2026-13')
    assert response.status==400
    expect(page.locator('h1')).to_be_visible()
    response=page.goto(e2e_url+'/wednesdays/2026-10-27')
    assert response.status==400


def test_untrusted_text_does_not_execute(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/2026-11-04')
    expect(page.get_by_text('<script>window.E2E_INJECTED=true</script>',exact=True)).to_be_visible()
    assert page.evaluate('window.E2E_INJECTED === undefined') is True
    expect(page.locator('script')).to_have_count(0)
    expect(page.locator('img[onerror]')).to_have_count(0)


def test_mobile_month_and_detail_are_usable(page,e2e_url):
    page.set_viewport_size({'width':375,'height':812})
    calendar=CalendarPage(page,e2e_url)
    calendar.open('2026-10')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS/'ap3-mobile-calendar.png'),full_page=True)
    calendar.open_wednesday('28.10.2026')
    expect(page.get_by_role('heading',name='Mittwoch, 28.10.2026',exact=True)).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')


def test_wednesday_summary_is_not_truncated_at_mobile_width(page,e2e_url):
    page.set_viewport_size({'width':375,'height':812})
    page.goto(e2e_url+'/?month=2026-10')
    summaries=page.locator('[data-date="2026-10-28"] .day-detail')
    assert summaries.count()==3
    assert summaries.evaluate_all('(nodes) => nodes.every(n => n.scrollWidth <= n.clientWidth)'), 'Wednesday summary text is clipped'

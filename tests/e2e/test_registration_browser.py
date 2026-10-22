"""Browser -> real forms -> Flask services -> SQLite for AP5 meal registrations."""
from pathlib import Path
import re

from playwright.sync_api import expect

ARTIFACTS=Path(__file__).resolve().parents[2]/'test-results'
DAY='2026-11-11'


def register(page,name,diet,note=''):
    page.get_by_label('Name für das Essen',exact=True).fill(name)
    page.get_by_label('Ernährungsform',exact=True).select_option(diet)
    page.get_by_label('Allergien/Hinweis (optional)',exact=True).fill(note)
    page.get_by_role('button',name='Zum Essen anmelden',exact=True).click()


def test_register_each_diet_with_and_without_note_then_unregister(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/'+DAY)
    register(page,' Anna Beispiel ','alles')
    expect(page.get_by_role('status')).to_be_visible()
    register(page,'Ben Muster','vegetarisch','keine Nüsse')
    register(page,'Cora Demo','vegan')
    entries=page.locator('.registration-list')
    expect(entries).to_contain_text('Anna Beispiel')
    expect(entries).to_contain_text('Isst alles')
    expect(entries).to_contain_text('Hinweis: keine Nüsse')
    expect(page.locator('.count-number')).to_have_text('3')
    page.get_by_role('button',name='Ben Muster vom Essen abmelden',exact=True).click()
    expect(entries).not_to_contain_text('Ben Muster')
    expect(page.locator('.count-number')).to_have_text('2')
    page.get_by_role('link',name=re.compile('Zum Monatskalender')).click()
    expect(page.locator(f'[data-date="{DAY}"]')).to_contain_text('Anmeldungen 2')


def test_duplicate_name_is_rejected_and_draft_kept(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/'+DAY)
    register(page,'Anna Beispiel','alles')
    register(page,'  ANNA beispiel ','vegan','Laktose')
    expect(page.get_by_role('alert')).to_be_visible()
    expect(page.get_by_label('Allergien/Hinweis (optional)',exact=True)).to_have_value('Laktose')
    expect(page.locator('.count-number')).to_have_text('1')
    page.goto(e2e_url+'/wednesdays/2026-11-18')
    register(page,'anna beispiel','alles')  # Another Wednesday stays allowed.
    expect(page.locator('.count-number')).to_have_text('1')


def test_cook_and_eater_are_counted_separately(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/'+DAY)
    page.get_by_label('Dein Name',exact=True).fill('Deniz Test')
    page.get_by_role('button',name='Als Koch eintragen',exact=True).click()
    expect(page.locator('.count-number')).to_have_text('0')
    register(page,'Deniz Test','vegetarisch')
    expect(page.locator('.count-number')).to_have_text('1')


def test_closed_wednesday_shows_registrations_without_forms(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/2026-10-21')
    expect(page.get_by_text('Anmeldung geschlossen',exact=True)).to_be_visible()
    expect(page.get_by_role('button',name='Zum Essen anmelden',exact=True)).to_have_count(0)
    # Decision B (ADR-005 addendum): the only form left is the accounting backfill for a missing cook.
    expect(page.locator('form')).to_have_count(1)
    expect(page.locator('form.backfill-form')).to_have_count(1)


def test_mobile_registration_without_overflow(page,e2e_url):
    page.set_viewport_size({'width':375,'height':812})
    page.goto(e2e_url+'/wednesdays/'+DAY)
    register(page,'Elli Beispiel','vegan','Sehr langer Hinweis '+'ohneUmbruchMöglichkeit'*8)
    expect(page.locator('.registration-list')).to_contain_text('Elli Beispiel')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS/'ap5-mobile-registration.png'),full_page=True)


def test_registration_text_is_displayed_not_executed(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/'+DAY)
    register(page,'<img src=x onerror="window.PWNED=true">','alles','<script>window.PWNED=true</script>')
    expect(page.locator('.registration-list')).to_contain_text('<script>window.PWNED=true</script>')
    assert page.evaluate('window.PWNED === undefined') is True
    expect(page.locator('script,img[onerror]')).to_have_count(0)

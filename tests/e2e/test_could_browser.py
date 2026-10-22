"""Browser checks for KANN C1 (.ics link) and C3 (recipe). Ratings: see tests/test_could.py.

The browser test server runs on a fixed clock at 2026-10-22 and cannot hold a past Wednesday with a
dish, so rating (only possible from the meal day on) is covered by the HTTP tests instead.
"""
from playwright.sync_api import expect

DAY = '2026-11-11'  # Test server clock 2026-10-22: open.


def save_dish(page, title):
    page.get_by_label('Gerichttitel', exact=True).fill(title)
    page.get_by_label('Beschreibung', exact=True).fill('Mit Brot')
    page.get_by_label('Kennzeichnung', exact=True).select_option('vegan')
    page.get_by_role('button', name='Gericht speichern', exact=True).click()


def test_recipe_is_saved_and_opened_via_link_and_ics_link_serves_calendar(page, e2e_url):
    page.goto(e2e_url + '/wednesdays/' + DAY)
    expect(page.locator('#recipe-text')).to_have_count(0)   # no dish yet: no recipe form
    expect(page.locator('#recipe-link')).to_have_count(0)
    save_dish(page, 'Kürbissuppe, mild')
    expect(page.get_by_role('status')).to_contain_text('Das Gericht wurde gespeichert.')
    page.locator('#recipe-text').fill('1. Kürbis würfeln\n2. <b>Kochen</b>')
    page.get_by_role('button', name='Rezept speichern', exact=True).click()
    expect(page.get_by_role('status')).to_contain_text('Das Rezept wurde gespeichert.')
    page.locator('#recipe-link').click()
    expect(page.locator('#page-title')).to_have_text('Kürbissuppe, mild')
    expect(page.locator('#recipe-body')).to_have_text('1. Kürbis würfeln\n2. <b>Kochen</b>')
    assert page.locator('#recipe-body b').count() == 0   # escaped, not interpreted
    assert page.evaluate("getComputedStyle(document.querySelector('#recipe-body')).whiteSpace") == 'pre-wrap'

    page.goto(e2e_url + '/wednesdays/' + DAY)
    link = page.locator('#ics-link')
    expect(link).to_have_text('Termin als .ics herunterladen')
    response = page.request.get(e2e_url + link.get_attribute('href'))
    assert response.status == 200
    assert response.headers['content-type'] == 'text/calendar; charset=utf-8'
    assert 'attachment' in response.headers['content-disposition']
    body = response.text()
    assert 'DTSTART;VALUE=DATE:20261111' in body
    assert 'SUMMARY:Kulinarischer Mittwoch: Kürbissuppe\\, mild' in body


def test_recipe_text_that_is_too_long_shows_error_in_browser(page, e2e_url):
    page.goto(e2e_url + '/wednesdays/2026-11-18')
    save_dish(page, 'Eintopf')
    area = page.locator('#recipe-text')
    area.evaluate("el => { el.removeAttribute('maxlength'); el.value = 'a'.repeat(4001); }")
    page.get_by_role('button', name='Rezept speichern', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('1 bis 4000 Zeichen')
    expect(page.locator('#recipe-link')).to_have_count(0)

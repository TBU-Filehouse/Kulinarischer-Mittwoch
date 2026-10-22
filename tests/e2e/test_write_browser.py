"""Browser -> real forms -> Flask services -> SQLite for AP4."""
from pathlib import Path
import re

import pytest
from playwright.sync_api import expect

ARTIFACTS=Path(__file__).resolve().parents[2]/'test-results'
DAY='2026-11-11'


def add_cook(page,name):
    page.get_by_label('Dein Name',exact=True).fill(name)
    page.get_by_role('button',name='Als Koch eintragen',exact=True).click()


def test_cook_duplicate_two_slots_remove_and_reuse(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/'+DAY)
    add_cook(page,' Anna Beispiel ')
    expect(page.get_by_role('status')).to_be_visible()
    expect(page.locator('.cook-list')).to_contain_text('Anna Beispiel')
    add_cook(page,'ANNA BEISPIEL')
    expect(page.get_by_role('alert')).to_be_visible()
    page.goto(e2e_url+'/wednesdays/'+DAY)
    add_cook(page,'Ben Muster')
    expect(page.get_by_text('Alle zwei Kochplätze sind belegt.',exact=True)).to_be_visible()
    expect(page.get_by_role('button',name='Als Koch eintragen',exact=True)).to_have_count(0)
    page.get_by_role('button',name='Anna Beispiel als Koch austragen',exact=True).click()
    add_cook(page,'Cora Demo')
    expect(page.locator('.cook-list')).not_to_contain_text('Anna Beispiel')
    expect(page.locator('.cook-list')).to_contain_text('Ben Muster')
    expect(page.locator('.cook-list')).to_contain_text('Cora Demo')
    expect(page.locator('.count-number')).to_have_text('0')


@pytest.mark.parametrize('kind,label',[('vegan','Vegan'),('vegetarisch','Vegetarisch'),('fleisch_fisch','Fleisch oder Fisch')])
def test_save_edit_dish_and_see_month_summary(page,e2e_url,kind,label):
    page.goto(e2e_url+'/wednesdays/'+DAY)
    page.get_by_label('Gerichttitel',exact=True).fill('Kürbissuppe')
    page.get_by_label('Beschreibung',exact=True).fill('Mit frischem Brot')
    page.get_by_label('Kennzeichnung',exact=True).select_option(kind)
    page.get_by_role('button',name='Gericht speichern',exact=True).click()
    expect(page.get_by_role('status')).to_be_visible()
    expect(page.get_by_role('heading',name='Kürbissuppe',exact=True)).to_be_visible()
    expect(page.locator('.dish-type')).to_have_text(label)
    page.reload()
    expect(page.get_by_label('Gerichttitel',exact=True)).to_have_value('Kürbissuppe')
    expect(page.get_by_label('Beschreibung',exact=True)).to_have_value('Mit frischem Brot')
    page.get_by_label('Gerichttitel',exact=True).fill('Kürbissuppe mit Brot')
    page.get_by_role('button',name='Gericht speichern',exact=True).click()
    page.get_by_role('link',name=re.compile('Zum Monatskalender')).click()
    expect(page.locator('[data-date="2026-11-11"]')).to_contain_text('Kürbissuppe mit Brot')


def test_closed_wednesday_has_no_write_form(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/2026-10-21')
    expect(page.get_by_text('Anmeldung geschlossen',exact=True)).to_be_visible()
    expect(page.locator('form')).to_have_count(0)
    expect(page.get_by_role('button',name='Gericht speichern',exact=True)).to_have_count(0)


def test_mobile_forms_save_without_overflow(page,e2e_url):
    page.set_viewport_size({'width':375,'height':812})
    page.goto(e2e_url+'/wednesdays/'+DAY)
    add_cook(page,'Deniz Test')
    page.get_by_label('Gerichttitel',exact=True).fill('Ofengemüse')
    page.get_by_label('Beschreibung',exact=True).fill('Mit Reis')
    page.get_by_label('Kennzeichnung',exact=True).select_option('vegan')
    page.get_by_role('button',name='Gericht speichern',exact=True).click()
    expect(page.get_by_role('heading',name='Ofengemüse',exact=True)).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS/'ap4-mobile-forms.png'),full_page=True)


def test_form_input_is_displayed_as_text_not_script(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/'+DAY)
    page.get_by_label('Gerichttitel',exact=True).fill('<script>window.PWNED=true</script>')
    page.get_by_label('Beschreibung',exact=True).fill('<img src=x onerror="window.PWNED=true">')
    page.get_by_label('Kennzeichnung',exact=True).select_option('vegan')
    page.get_by_role('button',name='Gericht speichern',exact=True).click()
    expect(page.get_by_role('heading',name='<script>window.PWNED=true</script>',exact=True)).to_be_visible()
    assert page.evaluate('window.PWNED === undefined') is True
    expect(page.locator('script,img[onerror]')).to_have_count(0)

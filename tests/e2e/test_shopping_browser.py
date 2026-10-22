"""Browser -> registrations -> shopping overview for AP6 (M7)."""
from pathlib import Path

from playwright.sync_api import expect

ARTIFACTS=Path(__file__).resolve().parents[2]/'test-results'
DAY='2026-11-11'


def register(page,name,diet,note=''):
    page.get_by_label('Name für das Essen',exact=True).fill(name)
    page.get_by_label('Ernährungsform',exact=True).select_option(diet)
    page.get_by_label('Allergien/Hinweis (optional)',exact=True).fill(note)
    page.get_by_role('button',name='Zum Essen anmelden',exact=True).click()


def test_strategy_dataset_in_shopping_overview_on_mobile(page,e2e_url):
    page.set_viewport_size({'width':375,'height':812})
    page.goto(e2e_url+'/wednesdays/'+DAY)
    page.get_by_label('Dein Name',exact=True).fill('Elli Beispiel')
    page.get_by_role('button',name='Als Koch eintragen',exact=True).click()
    register(page,'Anna Beispiel','alles')
    register(page,'Ben Muster','alles')
    register(page,'Cora Demo','vegetarisch','keine Nüsse')
    register(page,'Deniz Test','vegan')
    page.get_by_role('link',name='Einkaufsübersicht').click()
    expect(page.locator('#shopping-total')).to_have_text('4')
    expect(page.locator('#shopping-alles')).to_have_text('2')
    expect(page.locator('#shopping-vegetarisch')).to_have_text('1')
    expect(page.locator('#shopping-vegan')).to_have_text('1')
    expect(page.locator('[data-note-name="Cora Demo"]')).to_contain_text('keine Nüsse')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    ARTIFACTS.mkdir(exist_ok=True)
    page.screenshot(path=str(ARTIFACTS/'ap6-mobile-shopping.png'),full_page=True)

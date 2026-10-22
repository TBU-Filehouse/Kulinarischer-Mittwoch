"""Decision B in the browser: past Wednesday without cook -> backfill -> expense booked."""
from playwright.sync_api import expect

PAST='2026-10-21'  # Test server clock 2026-10-22: past, no cook in the seed.


def test_backfill_cook_then_book_expense_on_past_wednesday(page,e2e_url):
    page.goto(e2e_url+'/wednesdays/'+PAST)
    expect(page.get_by_role('button',name='Ausgabe erfassen',exact=True)).to_have_count(0)
    page.get_by_label('Name des Kochs',exact=True).fill('Anna Müller')
    page.get_by_role('button',name='Koch nachtragen',exact=True).click()
    expect(page.locator('.cook-list')).to_contain_text('Anna Müller')
    expect(page.get_by_role('button',name='Anna Müller als Koch austragen',exact=True)).to_have_count(0)
    expect(page.locator('form.backfill-form')).to_have_count(1)  # One cook slot is still free.
    page.get_by_label('Betrag (€)',exact=True).fill('23,45')
    page.get_by_label('Beschreibung der Ausgabe',exact=True).fill('Gemüse Wochenmarkt')
    page.get_by_label('Ausgelegt von',exact=True).select_option(label='Anna Müller')
    page.get_by_role('button',name='Ausgabe erfassen',exact=True).click()
    expect(page.locator('#expense-sum')).to_have_text('23,45 €')

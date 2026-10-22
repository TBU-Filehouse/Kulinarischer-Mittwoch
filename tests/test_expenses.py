"""Change 1 acceptance (A1-A5): budget, expenses, approval, monthly report and CSV.

Numbers come verbatim from the accounting sheet; see docs/12-change-ausgaben.md.
"""
import csv
from datetime import datetime, timezone
import io
import re

import pytest

from test_writes import TokenParser, rows, token_for, write_app  # noqa: F401  (fixture reuse)

DAY='2026-06-03'
BEFORE_DEADLINE=datetime(2026,5,1,10,tzinfo=timezone.utc)
AFTER_SHOPPING=datetime(2026,6,10,10,tzinfo=timezone.utc)  # Tuesday deadline long passed.
SHEET=[('23,45','Gemüse Wochenmarkt','Anna Müller'),
       ('8,10','Brot; Butter','Ben Muster'),
       ('12,50','Käse "Gouda" alt','Anna Müller')]


def text(html,element_id):
    match=re.search(rf'id="{element_id}"[^>]*>\s*([^<]*?)\s*<',html)
    assert match,f'#{element_id} missing'
    return match.group(1)


def cooks_by_name(app):
    return {row[2]:row[0] for row in rows(app,'cook')}


def setup_team(app,clock,client,day=DAY,registrations=('Cora Demo','Deniz Test','Elli Beispiel','Finn Probe')):
    clock.value=BEFORE_DEADLINE
    token=token_for(client,day)
    for name in ('Anna Müller','Ben Muster'):
        assert client.post(f'/wednesdays/{day}/cooks',data={'name':name,'csrf_token':token}).status_code==303
    for name in registrations:
        assert client.post(f'/wednesdays/{day}/registrations',data={
            'name':name,'diet':'alles','csrf_token':token}).status_code==303
    clock.value=AFTER_SHOPPING
    return token


def add_expense(client,app,token,amount,description,cook_name,day=DAY):
    return client.post(f'/wednesdays/{day}/expenses',data={
        'amount':amount,'description':description,
        'cook_id':str(cooks_by_name(app)[cook_name]),'csrf_token':token})


def add_sheet(client,app,token):
    for amount,description,cook in SHEET:
        assert add_expense(client,app,token,amount,description,cook).status_code==303


# A1 / A2 / A3 -----------------------------------------------------------------

def test_budget_visible_on_empty_wednesday(write_app):
    app,_=write_app
    with app.test_client() as client:
        html=client.get('/wednesdays/2026-10-28').get_data(as_text=True)
    assert text(html,'budget-total')=='300,00 €'
    assert text(html,'expense-sum')=='0,00 €'
    assert text(html,'budget-remaining')=='300,00 €'
    assert text(html,'cost-per-person')=='keine Anmeldungen'
    assert rows(app,'wednesday')==[]  # Reading never creates data.


def test_sheet_example_plan_vs_actual_after_deadline(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client)
        add_sheet(client,app,token)
        html=client.get('/wednesdays/'+DAY).get_data(as_text=True)
    assert [(row[4],row[5],row[3]) for row in rows(app,'expense')]==[
        ('Gemüse Wochenmarkt',2345,'Anna Müller'),('Brot; Butter',810,'Ben Muster'),('Käse "Gouda" alt',1250,'Anna Müller')]
    assert text(html,'budget-total')=='300,00 €'
    assert text(html,'expense-sum')=='44,05 €'
    assert text(html,'budget-remaining')=='255,95 €'
    assert text(html,'cost-per-person')=='11,01 €'  # 44,05 / 4 registrations
    assert text(html,'budget-status')=='Im Budget'
    assert 'Käse &#34;Gouda&#34; alt' in html or 'Käse &quot;Gouda&quot; alt' in html


@pytest.mark.parametrize('raw,cents',[('23,45',2345),('23.45',2345),('23',2300),('0,1',10),(' 7,05 ',705),('10000',1000000)])
def test_amount_formats_are_stored_as_exact_cents(write_app,raw,cents):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=())
        assert add_expense(client,app,token,raw,'Einkauf','Anna Müller').status_code==303
    assert rows(app,'expense')[0][5]==cents


@pytest.mark.parametrize('raw',['','0','0,00','-1','1,234','1.000,00','abc','1e3','NaN','10000,01','٣'])
def test_invalid_amounts_are_rejected_without_rows(write_app,raw):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=())
        assert add_expense(client,app,token,raw,'Einkauf','Anna Müller').status_code==400
    assert rows(app,'expense')==[]


def test_float_trap_cents_add_up_exactly(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=('Cora Demo','Deniz Test','Elli Beispiel'))
        add_expense(client,app,token,'0,10','A','Anna Müller')
        add_expense(client,app,token,'0,20','B','Ben Muster')
        html=client.get('/wednesdays/'+DAY).get_data(as_text=True)
    assert text(html,'expense-sum')=='0,30 €'
    assert text(html,'cost-per-person')=='0,10 €'


@pytest.mark.parametrize('description',['','   ','x'*201,'Zeile\nzwei'])
def test_invalid_description_rejected(write_app,description):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=())
        assert add_expense(client,app,token,'5',description,'Anna Müller').status_code==400
    assert rows(app,'expense')==[]


def test_paid_by_must_be_a_cook_of_this_wednesday(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=())
        clock.value=BEFORE_DEADLINE
        client.post('/wednesdays/2026-06-10/cooks',data={'name':'Gina Fremd','csrf_token':token})
        clock.value=AFTER_SHOPPING
        foreign=cooks_by_name(app)['Gina Fremd']
        for cook_id in (str(foreign),'9999','','abc'):
            assert client.post(f'/wednesdays/{DAY}/expenses',data={
                'amount':'5','description':'Einkauf','cook_id':cook_id,'csrf_token':token}).status_code==400
    assert rows(app,'expense')==[]


def test_wednesday_without_cooks_cannot_book_and_shows_no_expense_form(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client,'2026-10-28')
        html=client.get('/wednesdays/2026-10-28').get_data(as_text=True)
        assert client.post('/wednesdays/2026-10-28/expenses',data={
            'amount':'5','description':'Einkauf','cook_id':'1','csrf_token':token}).status_code==400
    assert 'action="/wednesdays/2026-10-28/expenses"' not in html
    assert rows(app,'expense')==[] and rows(app,'wednesday')==[]


def test_expense_form_is_offered_after_deadline_but_meal_forms_are_not(write_app):
    app,clock=write_app
    with app.test_client() as client:
        setup_team(app,clock,client,registrations=())
        html=client.get('/wednesdays/'+DAY).get_data(as_text=True)
    assert f'action="/wednesdays/{DAY}/expenses"' in html
    assert f'action="/wednesdays/{DAY}/registrations"' not in html
    assert f'action="/wednesdays/{DAY}/cooks"' not in html


def test_remove_expense_and_wrong_date_or_id(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=())
        add_sheet(client,app,token)
        first=rows(app,'expense')[0][0]
        assert client.post(f'/wednesdays/2026-06-10/expenses/{first}/remove',data={'csrf_token':token}).status_code==404
        assert client.post(f'/wednesdays/{DAY}/expenses/9999/remove',data={'csrf_token':token}).status_code==404
        assert client.post(f'/wednesdays/{DAY}/expenses/{first}/remove',data={'csrf_token':token}).status_code==303
        html=client.get('/wednesdays/'+DAY).get_data(as_text=True)
    assert len(rows(app,'expense'))==2
    assert text(html,'expense-sum')=='20,60 €'


def test_cook_with_expenses_cannot_be_removed(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=())
        add_expense(client,app,token,'5','Einkauf','Anna Müller')
        clock.value=BEFORE_DEADLINE
        anna=cooks_by_name(app)['Anna Müller']
        assert client.post(f'/wednesdays/{DAY}/cooks/{anna}/remove',data={'csrf_token':token}).status_code==409
        ben=cooks_by_name(app)['Ben Muster']
        assert client.post(f'/wednesdays/{DAY}/cooks/{ben}/remove',data={'csrf_token':token}).status_code==303
    assert [row[2] for row in rows(app,'cook')]==['Anna Müller']


def test_all_new_write_routes_require_csrf(write_app):
    app,_=write_app
    with app.test_client() as client:
        token_for(client)
        for suffix,fields in (('expenses',{'amount':'5','description':'x','cook_id':'1'}),
                              ('expenses/1/remove',{}),('approval',{'approved_by':'x','reason':'y'})):
            assert client.post('/wednesdays/2026-10-28/'+suffix,data=fields).status_code==403
        assert client.get('/wednesdays/2026-10-28/expenses').status_code==405
    assert rows(app,'wednesday')==[]


def test_expense_text_is_escaped(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=())
        add_expense(client,app,token,'5','<script>alert(1)</script>','Anna Müller')
        html=client.get('/wednesdays/'+DAY).get_data(as_text=True)
    assert '<script>alert(1)</script>' not in html and '&lt;script&gt;' in html


# A3a ----------------------------------------------------------------------------

def test_overrun_marked_then_approved_then_reopened_by_new_expense(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client)
        add_sheet(client,app,token)
        assert client.post(f'/wednesdays/{DAY}/approval',data={
            'approved_by':'Cora Demo','reason':'Nicht nötig','csrf_token':token}).status_code==409  # Nothing to approve yet.
        assert add_expense(client,app,token,'280,00','Großeinkauf Fisch','Ben Muster').status_code==303
        html=client.get('/wednesdays/'+DAY).get_data(as_text=True)
        assert text(html,'expense-sum')=='324,05 €'
        assert text(html,'budget-over')=='24,05 €'
        assert text(html,'budget-status')=='Budget überschritten, nicht genehmigt'
        assert 'id="budget-remaining"' not in html
        for fields in ({'approved_by':'','reason':'Fischtag'},{'approved_by':'Cora Demo','reason':' '},
                       {'approved_by':'x'*81,'reason':'Fischtag'},{'approved_by':'Cora Demo','reason':'x'*1001}):
            assert client.post(f'/wednesdays/{DAY}/approval',data={**fields,'csrf_token':token}).status_code==400
        assert client.post(f'/wednesdays/{DAY}/approval',data={
            'approved_by':' Cora Demo ','reason':' Fischtag mit Team abgesprochen ','csrf_token':token}).status_code==303
        html=client.get('/wednesdays/'+DAY).get_data(as_text=True)
        assert text(html,'budget-status')=='Budget überschritten, genehmigt'
        note=re.search(r'id="approval-note"[^>]*>(.*?)</',html,re.S).group(1)
        assert 'Cora Demo' in note and 'Fischtag mit Team abgesprochen' in note
        assert rows(app,'budget_approval')[0][1:4]==('Cora Demo','Fischtag mit Team abgesprochen',32405)
        add_expense(client,app,token,'1,00','Zitronen','Anna Müller')
        html=client.get('/wednesdays/'+DAY).get_data(as_text=True)
        assert text(html,'budget-status')=='Budget überschritten, nicht genehmigt'


def test_exactly_on_budget_is_not_an_overrun(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=())
        add_expense(client,app,token,'300,00','Alles','Anna Müller')
        html=client.get('/wednesdays/'+DAY).get_data(as_text=True)
    assert text(html,'budget-status')=='Im Budget' and text(html,'budget-remaining')=='0,00 €'


# A4 -----------------------------------------------------------------------------

def sheet_with_fish(client,app,clock):
    token=setup_team(app,clock,client)
    add_sheet(client,app,token)
    add_expense(client,app,token,'280,00','Großeinkauf Fisch','Ben Muster')
    return token


def test_monthly_report_sums_reimbursement_and_unapproved_marker(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=sheet_with_fish(client,app,clock)
        response=client.get('/reports/2026-06')
        assert response.status_code==200
        html=response.get_data(as_text=True)
        for day in ('2026-06-03','2026-06-10','2026-06-17','2026-06-24'):
            assert f'data-report-date="{day}"' in html
        row=re.search(r'data-report-date="2026-06-03".*?</tr>',html,re.S).group(0)
        assert '324,05 €' in row and '24,05 €' in row and 'nicht genehmigt' in row
        anna=re.search(r'data-reimbursement="Anna Müller".*?</tr>',html,re.S).group(0)
        ben=re.search(r'data-reimbursement="Ben Muster".*?</tr>',html,re.S).group(0)
        assert '35,95 €' in anna and '288,10 €' in ben
        assert text(html,'report-total')=='324,05 €'
        assert 'href="/reports/2026-06.csv"' in html
        client.post(f'/wednesdays/{DAY}/approval',data={'approved_by':'Cora Demo','reason':'Fischtag','csrf_token':token})
        row=re.search(r'data-report-date="2026-06-03".*?</tr>',client.get('/reports/2026-06').get_data(as_text=True),re.S).group(0)
    assert 'nicht genehmigt' not in row and 'genehmigt' in row


def test_report_validates_month_and_reads_without_writing(write_app):
    app,_=write_app
    with app.test_client() as client:
        assert client.get('/reports/2026-13').status_code==400
        assert client.get('/reports/abc').status_code==400
        assert client.get('/reports/2026-13.csv').status_code==400
        assert client.get('/reports/2026-07').status_code==200
    assert rows(app,'wednesday')==[]


def test_calendar_links_to_monthly_report(write_app):
    app,_=write_app
    with app.test_client() as client:
        html=client.get('/?month=2026-06').get_data(as_text=True)
    assert 'href="/reports/2026-06"' in html


# A5 -----------------------------------------------------------------------------

EXPECTED_CSV=('﻿Datum;Standort;Beschreibung;Ausgelegt_von;Betrag\r\n'
              '03.06.2026;Hamburg;Gemüse Wochenmarkt;Anna Müller;23,45\r\n'
              '03.06.2026;Hamburg;"Brot; Butter";Ben Muster;8,10\r\n'
              '03.06.2026;Hamburg;"Käse ""Gouda"" alt";Anna Müller;12,50\r\n'
              '03.06.2026;Hamburg;Großeinkauf Fisch;Ben Muster;280,00\r\n')


def test_csv_bytes_match_accounting_format_exactly(write_app):
    app,clock=write_app
    with app.test_client() as client:
        sheet_with_fish(client,app,clock)
        response=client.get('/reports/2026-06.csv')
    assert response.status_code==200
    assert response.mimetype=='text/csv'
    assert 'attachment' in response.headers['Content-Disposition']
    assert 'ausgaben-2026-06.csv' in response.headers['Content-Disposition']
    assert response.data==EXPECTED_CSV.encode('utf-8')
    parsed=list(csv.reader(io.StringIO(response.data.decode('utf-8-sig'),newline=''),delimiter=';'))
    assert len(parsed)==5 and all(len(line)==5 for line in parsed)  # Header + 4 positions.
    assert parsed[2][2]=='Brot; Butter' and parsed[3][2]=='Käse "Gouda" alt'


def test_csv_only_contains_the_requested_month_and_empty_month_has_header(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=())
        add_expense(client,app,token,'5','Juni','Anna Müller')
        clock.value=BEFORE_DEADLINE
        client.post('/wednesdays/2026-07-01/cooks',data={'name':'Ben Muster','csrf_token':token})
        clock.value=AFTER_SHOPPING
        add_expense(client,app,token,'7','Juli','Ben Muster',day='2026-07-01')
        june=client.get('/reports/2026-06.csv').data.decode('utf-8-sig')
        august=client.get('/reports/2026-08.csv').data
    assert 'Juni' in june and 'Juli' not in june
    assert august=='﻿Datum;Standort;Beschreibung;Ausgelegt_von;Betrag\r\n'.encode('utf-8')


@pytest.mark.parametrize('description',['=HYPERLINK("http://x")','+49 Pfand','-5 Rabatt','@SUMME'])
def test_csv_neutralises_spreadsheet_formulas(write_app,description):
    app,clock=write_app
    with app.test_client() as client:
        token=setup_team(app,clock,client,registrations=())
        add_expense(client,app,token,'5',description,'Anna Müller')
        data=client.get('/reports/2026-06.csv').data.decode('utf-8-sig')
    parsed=list(csv.reader(io.StringIO(data,newline=''),delimiter=';'))
    assert parsed[1][2]=="'"+description

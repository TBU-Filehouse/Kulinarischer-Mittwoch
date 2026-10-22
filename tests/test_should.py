"""SOLL S1-S4 acceptance (ADR-008): cook status, portion limit with waitlist, cancellation, history."""
from contextlib import closing
from datetime import datetime, timezone
import re
import sqlite3

import pytest

from test_writes import rows, token_for, write_app  # noqa: F401  (fixture reuse)

OPEN='2026-10-28'      # Clock 2026-10-22 12:00 UTC: deadline 27.10. 12:00 Berlin still ahead.
PAST='2026-10-21'
WEDNESDAY_MORNING=datetime(2026,10,28,8,tzinfo=timezone.utc)  # 28.10. is today: closed, not past.


def text(html,element_id):
    match=re.search(rf'id="{element_id}"[^>]*>\s*([^<]*?)\s*<',html)
    assert match,f'#{element_id} missing'
    return match.group(1)


def post(client,token,day,suffix,**fields):
    return client.post(f'/wednesdays/{day}/{suffix}',data={**fields,'csrf_token':token})


def register(client,token,name,day=OPEN,diet='alles'):
    return post(client,token,day,'registrations',name=name,diet=diet)


def detail(client,day=OPEN):
    return client.get(f'/wednesdays/{day}').get_data(as_text=True)


def statuses(html):
    """[(name, 'confirmed'|'waitlisted')] in list order."""
    items=re.findall(r'<li[^>]*data-registration-status="(confirmed|waitlisted)"[^>]*>(.*?)</li>',html,re.S)
    return [(re.search(r'registration-name">([^<]*)<',body).group(1),status) for status,body in items]


def calendar_cell(client,day):
    html=client.get('/?month='+day[:7]).get_data(as_text=True)
    match=re.search(rf'<td[^>]*data-date="{day}"[^>]*>.*?</td>',html,re.S)
    assert match,'calendar cell missing'
    return match.group(0)


def seed_cook(app,day,name='Anna Müller'):
    with closing(sqlite3.connect(app.config['DATABASE'])) as connection:
        connection.execute('INSERT OR IGNORE INTO wednesday(date) VALUES(?)',(day,))
        connection.execute('INSERT INTO cook(date,display_name,normalized_name) VALUES(?,?,?)',(day,name,name.casefold()))
        connection.commit()
        return connection.execute('SELECT id FROM cook WHERE date=? AND display_name=?',(day,name)).fetchone()[0]


# S1 ------------------------------------------------------------------------------

def test_s1_cook_status_for_zero_one_two_in_detail_and_calendar(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        expected=['Köche gesucht','1 Koch fehlt','komplett']
        for count,label in enumerate(expected):
            if count:
                post(client,token,OPEN,'cooks',name=f'Koch {count}')
            assert text(detail(client),'cook-status')==label
            assert label in calendar_cell(client,OPEN)
        cook=rows(app,'cook')[0][0]
        post(client,token,OPEN,'cooks/%d/remove'%cook)
        assert text(detail(client),'cook-status')=='1 Koch fehlt'


# S4 ------------------------------------------------------------------------------

def test_s4_calendar_marks_past_open_and_closed(write_app):
    app,clock=write_app
    with app.test_client() as client:
        assert 'data-status="past"' in calendar_cell(client,PAST)
        assert 'data-status="open"' in calendar_cell(client,OPEN)
        assert 'Anmeldung offen' in calendar_cell(client,OPEN)
        assert 'Vergangen' in calendar_cell(client,PAST)
        clock.value=WEDNESDAY_MORNING
        assert 'data-status="closed"' in calendar_cell(client,OPEN)
        assert 'Anmeldung geschlossen' in calendar_cell(client,OPEN)
    assert rows(app,'wednesday')==[]


def test_s4_past_wednesday_is_read_only_history_but_expenses_stay_possible(write_app):
    app,_=write_app
    cook=seed_cook(app,PAST)
    with app.test_client() as client:
        token=token_for(client)
        html=detail(client,PAST)
        assert 'Vergangener Mittwoch' in html
        for suffix in ('cooks','registrations','dish','portions','cancel'):
            assert f'action="/wednesdays/{PAST}/{suffix}"' not in html
        for suffix,fields in (('cooks',{'name':'Ben'}),('registrations',{'name':'Ben','diet':'alles'}),
                              ('dish',{'title':'T','description':'D','dish_type':'vegan'}),
                              ('portions',{'max_portions':'5'}),('cancel',{'reason':'Zu spät'}),
                              (f'cooks/{cook}/remove',{})):
            assert post(client,token,PAST,suffix,**fields).status_code==409, suffix
        assert post(client,token,PAST,'expenses',amount='5',description='Beleg',cook_id=str(cook)).status_code==303
    assert rows(app,'cancellation')==[] and rows(app,'portion_limit')==[]
    assert len(rows(app,'cook'))==1 and len(rows(app,'expense'))==1


# S3 ------------------------------------------------------------------------------

def setup_planned(client,app,token):
    post(client,token,OPEN,'cooks',name='Anna Müller')
    post(client,token,OPEN,'dish',title='Curry',description='Mit Reis',dish_type='vegan')
    for name in ('Cora Demo','Deniz Test','Elli Beispiel'):
        register(client,token,name)


@pytest.mark.parametrize('reason',['','   ','x'*1001])
def test_s3_cancel_requires_a_reason(write_app,reason):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert post(client,token,OPEN,'cancel',reason=reason).status_code==400
    assert rows(app,'cancellation')==[]


def test_s3_cancel_keeps_data_blocks_changes_and_is_final(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        setup_planned(client,app,token)
        before=(rows(app,'wednesday'),rows(app,'cook'),rows(app,'registration'))
        assert post(client,token,OPEN,'cancel',reason=' Feiertag ').status_code==303
        html=detail(client)
        assert 'Abgesagt' in html and 'Feiertag' in text(html,'cancellation-note')
        for suffix in ('cooks','registrations','dish','portions','cancel'):
            assert f'action="/wednesdays/{OPEN}/{suffix}"' not in html
        cook=rows(app,'cook')[0][0]
        registration=rows(app,'registration')[0][0]
        for suffix,fields in (('cooks',{'name':'Ben'}),('registrations',{'name':'Ben','diet':'alles'}),
                              ('dish',{'title':'T','description':'D','dish_type':'vegan'}),
                              ('portions',{'max_portions':'5'}),(f'cooks/{cook}/remove',{}),
                              (f'registrations/{registration}/remove',{}),('cancel',{'reason':'Nochmal'})):
            assert post(client,token,OPEN,suffix,**fields).status_code==409, suffix
        assert 'data-status="cancelled"' in calendar_cell(client,OPEN)
    assert (rows(app,'wednesday'),rows(app,'cook'),rows(app,'registration'))==before
    assert rows(app,'cancellation')[0][:2]==(OPEN,'Feiertag')


def test_s3_cancel_after_deadline_allowed_but_not_for_past(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=token_for(client)
        clock.value=WEDNESDAY_MORNING
        assert post(client,token,OPEN,'cancel',reason='Betriebsurlaub').status_code==303
        assert post(client,token,PAST,'cancel',reason='Zu spät').status_code==409
    assert [row[0] for row in rows(app,'cancellation')]==[OPEN]


def test_s3_shopping_shows_zero_active_and_historical_count(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        setup_planned(client,app,token)
        post(client,token,OPEN,'cancel',reason='Feiertag')
        html=client.get(f'/wednesdays/{OPEN}/shopping').get_data(as_text=True)
    assert text(html,'shopping-total')=='0'
    assert text(html,'shopping-historical')=='3'
    assert 'abgesagt' in html.lower()


def test_s3_expenses_stay_possible_and_report_marks_cancelled(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        setup_planned(client,app,token)
        post(client,token,OPEN,'cancel',reason='Feiertag')
        cook=rows(app,'cook')[0][0]
        assert post(client,token,OPEN,'expenses',amount='12,50',description='Schon gekauft',cook_id=str(cook)).status_code==303
        report=client.get('/reports/2026-10').get_data(as_text=True)
    row=re.search(rf'data-report-date="{OPEN}".*?</tr>',report,re.S).group(0)
    assert 'abgesagt' in row.lower() and '12,50 €' in row


# S2 ------------------------------------------------------------------------------

@pytest.mark.parametrize('value',['0','-1','abc','2.5','1000',' '])
def test_s2_invalid_limits_rejected(write_app,value):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        status=post(client,token,OPEN,'portions',max_portions=value).status_code
    assert status==(303 if value==' ' else 400)  # Blank means "unlimited" and is valid.
    assert rows(app,'portion_limit')==[]


def test_s2_limit_two_puts_third_on_waitlist_and_counts_only_confirmed(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert post(client,token,OPEN,'portions',max_portions='2').status_code==303
        for name in ('Anna','Ben','Cora'):
            assert register(client,token,name).status_code==303
        html=detail(client)
        assert statuses(html)==[('Anna','confirmed'),('Ben','confirmed'),('Cora','waitlisted')]
        assert text(html,'portion-limit')=='2 Portionen'
        assert '<p class="count-number">2</p>' in html
        assert 'Warteliste 1' in html
        shopping=client.get(f'/wednesdays/{OPEN}/shopping').get_data(as_text=True)
        assert text(shopping,'shopping-total')=='2'
        cook=seed_cook(app,OPEN,'Koch Eins')
        post(client,token,OPEN,'expenses',amount='10,00',description='Einkauf',cook_id=str(cook))
        assert text(detail(client),'cost-per-person')=='5,00 €'
    assert rows(app,'portion_limit')==[(OPEN,2)]


def test_s2_unregister_promotes_oldest_waiting_in_fifo_order(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        post(client,token,OPEN,'portions',max_portions='1')
        for name in ('Anna','Ben','Cora'):
            register(client,token,name)
        anna=[row[0] for row in rows(app,'registration') if row[2]=='Anna'][0]
        assert post(client,token,OPEN,f'registrations/{anna}/remove').status_code==303
        html=detail(client)
        assert statuses(html)==[('Ben','confirmed'),('Cora','waitlisted')]
        assert 'Warteliste 1' in html
        register(client,token,'anna')  # Re-registration queues at the end.
        assert statuses(detail(client))[-1]==('anna','waitlisted')


def test_s2_raising_or_clearing_limit_promotes_lowering_below_confirmed_rejected(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        post(client,token,OPEN,'portions',max_portions='2')
        for name in ('Anna','Ben','Cora','Deniz'):
            register(client,token,name)
        assert post(client,token,OPEN,'portions',max_portions='1').status_code==409
        assert rows(app,'portion_limit')==[(OPEN,2)]
        assert post(client,token,OPEN,'portions',max_portions='3').status_code==303
        assert [s for _,s in statuses(detail(client))]==['confirmed']*3+['waitlisted']
        assert post(client,token,OPEN,'portions',max_portions='').status_code==303
        html=detail(client)
        assert [s for _,s in statuses(html)]==['confirmed']*4
        assert text(html,'portion-limit')=='unbegrenzt'
    assert rows(app,'portion_limit')==[]


def test_s2_limit_locked_after_deadline_and_requires_csrf(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert client.post(f'/wednesdays/{OPEN}/portions',data={'max_portions':'2'}).status_code==403
        assert client.post(f'/wednesdays/{OPEN}/cancel',data={'reason':'x'}).status_code==403
        clock.value=WEDNESDAY_MORNING
        assert post(client,token,OPEN,'portions',max_portions='2').status_code==409
    assert rows(app,'portion_limit')==[]


def test_s2_without_limit_everyone_is_confirmed(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        for name in ('Anna','Ben','Cora'):
            register(client,token,name)
        html=detail(client)
    assert [s for _,s in statuses(html)]==['confirmed']*3
    assert text(html,'portion-limit')=='unbegrenzt'

"""AP4 acceptance: write contracts, isolated database, real CSRF session token."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timezone
from html.parser import HTMLParser
import sqlite3
import threading

import pytest
from app import create_app


class FixedClock:
    def __init__(self,value):
        self.value=value
        self.calls=0
    def now(self):
        self.calls+=1
        return self.value


class TokenParser(HTMLParser):
    token=None
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if tag=='input' and values.get('name')=='csrf_token':
            self.token=values.get('value')


@pytest.fixture
def write_app(tmp_path):
    clock=FixedClock(datetime(2026,10,22,12,tzinfo=timezone.utc))
    app=create_app({'DATABASE':str(tmp_path/'writes.db'),'TESTING':True,'CLOCK':clock})
    return app,clock


def token_for(client,day='2026-10-28'):
    parser=TokenParser()
    parser.feed(client.get('/wednesdays/'+day).get_data(as_text=True))
    assert parser.token,'Writable detail needs a CSRF-protected form'
    return parser.token


def rows(app,table):
    with closing(sqlite3.connect(app.config['DATABASE'])) as connection:
        return connection.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall()


def test_add_remove_cook_real_form_contract(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        response=client.post('/wednesdays/2026-10-28/cooks',data={'name':' Anna Beispiel ','csrf_token':token})
        assert response.status_code==303
        assert response.headers['Location'].endswith('/wednesdays/2026-10-28')
        cooks=rows(app,'cook')
        assert len(cooks)==1 and cooks[0][2:] == ('Anna Beispiel','anna beispiel')
        response=client.post(f'/wednesdays/2026-10-28/cooks/{cooks[0][0]}/remove',data={'csrf_token':token})
        assert response.status_code==303
        assert rows(app,'cook')==[]

@pytest.mark.parametrize('name',['','   ','x'*81])
def test_invalid_cook_name_does_not_create_wednesday(write_app,name):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert client.post('/wednesdays/2026-10-28/cooks',data={'name':name,'csrf_token':token}).status_code==400
    assert rows(app,'wednesday')==[] and rows(app,'cook')==[]


def test_cook_duplicate_limit_and_slot_reuse(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        url='/wednesdays/2026-10-28/cooks'
        assert client.post(url,data={'name':' Anna ','csrf_token':token}).status_code==303
        assert client.post(url,data={'name':'anna','csrf_token':token}).status_code==409
        assert client.post(url,data={'name':'Ben','csrf_token':token}).status_code==303
        expected=rows(app,'cook')
        assert client.post(url,data={'name':'Cora','csrf_token':token}).status_code==409
        assert rows(app,'cook')==expected
        assert client.post(url+f'/{expected[0][0]}/remove',data={'csrf_token':token}).status_code==303
        assert client.post(url,data={'name':'Cora','csrf_token':token}).status_code==303
    assert len(rows(app,'cook'))==2
    assert rows(app,'registration')==[]  # Cooks do not automatically count as meals.


@pytest.mark.parametrize('kind',['vegan','vegetarisch','fleisch_fisch'])
def test_dish_roundtrip_preserves_cooks_and_registration(write_app,kind):
    app,clock=write_app
    with app.test_client() as client:
        token=token_for(client)
        client.post('/wednesdays/2026-10-28/cooks',data={'name':'Anna Beispiel','csrf_token':token})
        cooks=rows(app,'cook')
        with closing(sqlite3.connect(app.config['DATABASE'])) as connection:
            connection.execute('INSERT INTO registration(date,display_name,normalized_name,diet) VALUES(?,?,?,?)',
                               ('2026-10-28','Cora Demo','cora demo','vegan'))
            connection.commit()
        registrations=rows(app,'registration')
        clock.calls=0
        response=client.post('/wednesdays/2026-10-28/dish',data={
            'title':' Gemüse-Curry ','description':' Mit Reis ','dish_type':kind,'csrf_token':token})
        assert response.status_code==303
        assert clock.calls==1
        assert rows(app,'wednesday')[0][1:]==('Gemüse-Curry','Mit Reis',kind)
        assert rows(app,'cook')==cooks and rows(app,'registration')==registrations
        text=client.get('/wednesdays/2026-10-28').get_data(as_text=True)
        assert 'Gemüse-Curry' in text and 'Mit Reis' in text


@pytest.mark.parametrize('fields',[
    {'title':'','description':'Text','dish_type':'vegan'},
    {'title':'x'*121,'description':'Text','dish_type':'vegan'},
    {'title':'Titel','description':'   ','dish_type':'vegan'},
    {'title':'Titel','description':'x'*1001,'dish_type':'vegan'},
    {'title':'Titel','description':'Text','dish_type':'unknown'},
])
def test_invalid_dish_is_atomic_without_lazy_insert(write_app,fields):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert client.post('/wednesdays/2026-10-28/dish',data={**fields,'csrf_token':token}).status_code==400
    assert rows(app,'wednesday')==[]


@pytest.mark.parametrize('bad_token',[None,'incorrect'])
def test_csrf_missing_or_wrong_is_rejected_without_mutation(write_app,bad_token):
    app,_=write_app
    with app.test_client() as client:
        token_for(client)
        data={'name':'Anna'}
        if bad_token is not None:
            data['csrf_token']=bad_token
        assert client.post('/wednesdays/2026-10-28/cooks',data=data).status_code==403
    assert rows(app,'wednesday')==[]


def test_csrf_cross_session_and_foreign_origin_rejected(write_app):
    app,_=write_app
    with app.test_client() as first:
        token=token_for(first)
        second=app.test_client()
        token_for(second)
        assert second.post('/wednesdays/2026-10-28/cooks',data={'name':'Anna','csrf_token':token}).status_code==403
        assert first.post('/wednesdays/2026-10-28/cooks',data={'name':'Anna','csrf_token':token},
                          headers={'Origin':'https://foreign.invalid'}).status_code==403
    assert rows(app,'wednesday')==[]


@pytest.mark.parametrize('instant',[
    datetime(2026,10,27,11,tzinfo=timezone.utc),
    datetime(2026,10,27,11,0,1,tzinfo=timezone.utc),
    datetime(2026,6,23,10,tzinfo=timezone.utc),
])
def test_direct_posts_at_deadline_are_blocked_and_forms_hidden(write_app,instant):
    app,clock=write_app
    day='2026-06-24' if instant.month==6 else '2026-10-28'
    clock.value=datetime(2026,1,1,tzinfo=timezone.utc)
    with app.test_client() as client:
        token=token_for(client,day)
        client.post(f'/wednesdays/{day}/cooks',data={'name':'Anna','csrf_token':token})
        cook=rows(app,'cook')[0]
        expected=rows(app,'wednesday'),rows(app,'cook')
        clock.value=instant
        for suffix,data in (
            ('cooks',{'name':'Ben'}),
            (f'cooks/{cook[0]}/remove',{}),
            ('dish',{'title':'Curry','description':'Reis','dish_type':'vegan'}),
        ):
            assert client.post(f'/wednesdays/{day}/'+suffix,data={**data,'csrf_token':token}).status_code==409
        html=client.get('/wednesdays/'+day).get_data(as_text=True)
        # Change 1: expense forms stay available after the deadline; M6 forms must not.
        for suffix in ('cooks','dish','registrations',f'cooks/{cook[0]}/remove'):
            assert f'action="/wednesdays/{day}/{suffix}"' not in html
    assert (rows(app,'wednesday'),rows(app,'cook'))==expected


def test_remove_wrong_date_and_unknown_id_do_not_remove_other_cook(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        client.post('/wednesdays/2026-10-28/cooks',data={'name':'Anna','csrf_token':token})
        expected=rows(app,'cook')
        assert client.post(f'/wednesdays/2026-11-04/cooks/{expected[0][0]}/remove',data={'csrf_token':token}).status_code==404
        assert client.post('/wednesdays/2026-10-28/cooks/9999/remove',data={'csrf_token':token}).status_code==404
    assert rows(app,'cook')==expected


def test_non_wednesday_and_get_write_routes_rejected(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert client.post('/wednesdays/2026-10-27/cooks',data={'name':'Anna','csrf_token':token}).status_code==400
        assert client.get('/wednesdays/2026-10-28/cooks').status_code==405
    assert rows(app,'wednesday')==[]


def test_cook_names_and_dishes_are_sql_safe_and_html_escaped(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert client.post('/wednesdays/2026-10-28/cooks',data={
            'name':"Robert'); DROP TABLE cook;--",'csrf_token':token}).status_code==303
        assert client.post('/wednesdays/2026-10-28/dish',data={
            'title':'<script>alert(1)</script>','description':'<b>Reis</b>',
            'dish_type':'vegan','csrf_token':token}).status_code==303
        html=client.get('/wednesdays/2026-10-28').get_data(as_text=True)
        assert '&lt;script&gt;' in html and '<script>alert(1)</script>' not in html
        assert '&lt;b&gt;Reis&lt;/b&gt;' in html
    assert len(rows(app,'cook'))==1


def test_concurrent_cooks_cannot_exceed_two(write_app):
    from app.services import WednesdayService
    from app.rules import CookLimitError
    from datetime import date
    app,clock=write_app
    barrier=threading.Barrier(3)
    def add(name):
        barrier.wait(timeout=5)
        try:
            WednesdayService(app.config['DATABASE'],clock).add_cook(date(2026,10,28),name)
            return 'ok'
        except CookLimitError:
            return 'full'
    with ThreadPoolExecutor(max_workers=3) as pool:
        outcomes=list(pool.map(add,['Anna','Ben','Cora']))
    assert sorted(outcomes)==['full','ok','ok']
    assert len(rows(app,'cook'))==2


def test_concurrent_duplicate_name_has_one_winner(write_app):
    from app.services import WednesdayService
    from app.rules import DuplicateNameError
    from datetime import date
    app,clock=write_app
    barrier=threading.Barrier(2)
    def add(name):
        barrier.wait(timeout=5)
        try:
            WednesdayService(app.config['DATABASE'],clock).add_cook(date(2026,10,28),name)
            return 'ok'
        except DuplicateNameError:
            return 'duplicate'
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(add,[' Anna ','ANNA']))
    assert sorted(outcomes)==['duplicate','ok']
    assert len(rows(app,'cook'))==1

def test_fristsperre_is_checked_after_waiting_for_write_lock(write_app,monkeypatch):
    from app import services
    from app.rules import RegistrationClosedError
    from datetime import date
    app,clock=write_app
    clock.value=datetime(2026,10,27,10,59,59,tzinfo=timezone.utc)
    real_connect=services.connect_database
    begin_attempted=threading.Event()
    def observed_connect(path):
        connection=real_connect(path)
        connection.set_trace_callback(lambda sql:begin_attempted.set() if sql.upper().startswith('BEGIN IMMEDIATE') else None)
        return connection
    monkeypatch.setattr(services,'connect_database',observed_connect)
    blocker=sqlite3.connect(app.config['DATABASE'])
    blocker.execute('BEGIN IMMEDIATE')
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(services.WednesdayService(app.config['DATABASE'],clock).add_cook,date(2026,10,28),'Anna')
            try:
                assert begin_attempted.wait(timeout=3)
                assert clock.calls==0,'Clock was read before acquiring the write lock'
                clock.value=datetime(2026,10,27,11,tzinfo=timezone.utc)
            finally:
                blocker.rollback()
            with pytest.raises(RegistrationClosedError):
                future.result(timeout=5)
    finally:
        blocker.close()
    assert rows(app,'cook')==[] and rows(app,'wednesday')==[]


def test_database_abort_rolls_back_lazy_wednesday(write_app):
    app,_=write_app
    with closing(sqlite3.connect(app.config['DATABASE'])) as connection:
        connection.executescript("CREATE TRIGGER reject_cook BEFORE INSERT ON cook BEGIN SELECT RAISE(ABORT,'test failure'); END;")
    with app.test_client() as client:
        token=token_for(client)
        response=client.post('/wednesdays/2026-10-28/cooks',data={'name':'Anna','csrf_token':token})
        assert response.status_code in (400,409)
    assert rows(app,'cook')==[] and rows(app,'wednesday')==[]


def test_non_ascii_csrf_token_is_forbidden_not_server_error(write_app):
    app,_=write_app
    with app.test_client() as client:
        token_for(client)
        assert client.post('/wednesdays/2026-10-28/cooks',data={'name':'Anna','csrf_token':'☃'}).status_code==403
    assert rows(app,'wednesday')==[]


def test_invalid_dish_edit_keeps_saved_summary_separate_from_draft(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        client.post('/wednesdays/2026-10-28/dish',data={
            'title':'Gespeichertes Gericht','description':'Mit Reis','dish_type':'vegan','csrf_token':token})
        response=client.post('/wednesdays/2026-10-28/dish',data={
            'title':'Nicht gespeichert','description':'','dish_type':'vegan','csrf_token':token})
        assert response.status_code==400
        html=response.get_data(as_text=True)
        assert '<h3>Gespeichertes Gericht</h3>' in html
        assert 'value="Nicht gespeichert"' in html  # Unsaved input remains editable.
        assert rows(app,'wednesday')[0][1]=='Gespeichertes Gericht'

def test_local_app_rejects_untrusted_host_before_serving_forms(write_app):
    app,_=write_app
    with app.test_client() as client:
        response=client.get('/wednesdays/2026-10-28',base_url='http://foreign.invalid')
        assert response.status_code==400
        assert b'name="csrf_token"' not in response.data

def test_all_write_routes_require_csrf(write_app):
    app,_=write_app
    with app.test_client() as client:
        for suffix,fields in (
            ('cooks',{'name':'Anna'}),('cooks/1/remove',{}),
            ('dish',{'title':'Curry','description':'Reis','dish_type':'vegan'}),
        ):
            assert client.post('/wednesdays/2026-10-28/'+suffix,data=fields).status_code==403
    assert rows(app,'wednesday')==[]


def test_database_failure_has_no_success_or_internal_details(write_app,monkeypatch):
    from app import services
    app,_=write_app
    def unavailable(path):
        raise sqlite3.OperationalError('sensitive-internal-path')
    with app.test_client() as client:
        token=token_for(client)
        monkeypatch.setattr(services,'connect_database',unavailable)
        for suffix,fields in (
            ('cooks',{'name':'Anna'}),('cooks/1/remove',{}),
            ('dish',{'title':'Curry','description':'Reis','dish_type':'vegan'}),
        ):
            response=client.post('/wednesdays/2026-10-28/'+suffix,data={**fields,'csrf_token':token})
            assert response.status_code==500
            html=response.get_data(as_text=True)
            assert 'sensitive-internal-path' not in html
            assert 'gespeichert werden' in html
    assert rows(app,'wednesday')==[]

def test_oversized_http_form_is_rejected_without_echo_or_mutation(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        response=client.post('/wednesdays/2026-10-28/cooks',data={'name':'z'*(1024*1024),'csrf_token':token})
        assert response.status_code==413
        assert len(response.data)<8192
        assert b'z'*100 not in response.data
    assert rows(app,'wednesday')==[]

def test_maximum_valid_unicode_dish_fits_request_limit(write_app):
    app,_=write_app
    title=chr(0x1FAD6)*120
    description=chr(0x1FAD6)*1000
    with app.test_client() as client:
        token=token_for(client)
        response=client.post('/wednesdays/2026-10-28/dish',data={
            'title':title,'description':description,'dish_type':'vegan','csrf_token':token})
        assert response.status_code==303
    assert rows(app,'wednesday')[0][1:3]==(title,description)

"""AP5 acceptance: meal registration contracts (M4/M5/M6) on an isolated database."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date, datetime, timezone
import sqlite3
import threading

import pytest

from test_writes import TokenParser, rows, token_for, write_app  # noqa: F401  (fixture reuse)

URL='/wednesdays/2026-10-28/registrations'


def register(client,token,day='2026-10-28',**fields):
    data={'name':'Anna Beispiel','diet':'alles','note':'',**fields,'csrf_token':token}
    return client.post(f'/wednesdays/{day}/registrations',data=data)


@pytest.mark.parametrize('diet',['alles','vegetarisch','vegan'])
def test_register_each_diet_without_note(write_app,diet):
    app,clock=write_app
    with app.test_client() as client:
        token=token_for(client)
        clock.calls=0
        response=register(client,token,name=' Anna Beispiel ',diet=diet)
        assert response.status_code==303
        assert response.headers['Location'].endswith('/wednesdays/2026-10-28')
        assert clock.calls==1
    registration=rows(app,'registration')
    assert len(registration)==1
    assert registration[0][1:6]==('2026-10-28','Anna Beispiel','anna beispiel',diet,None)


def test_register_with_note_is_trimmed_and_shown(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert register(client,token,name='Cora Demo',diet='vegan',note='  keine Nüsse  ').status_code==303
        html=client.get('/wednesdays/2026-10-28').get_data(as_text=True)
    assert rows(app,'registration')[0][5]=='keine Nüsse'
    assert 'Cora Demo' in html and 'keine Nüsse' in html
    assert '<p class="count-number">1</p>' in html


def test_same_name_same_day_conflicts_other_day_allowed(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert register(client,token,name=' Anna ').status_code==303
        expected=rows(app,'registration')
        response=register(client,token,name='anna',diet='vegan')
        assert response.status_code==409
        assert 'value="anna"' in response.get_data(as_text=True)  # Draft stays editable.
        assert rows(app,'registration')==expected
        assert register(client,token,day='2026-11-04',name='anna').status_code==303
        assert register(client,token,name='Anna A').status_code==303  # Visible suffix for namesakes.
    assert len(rows(app,'registration'))==3


@pytest.mark.parametrize('fields',[
    {'name':''},{'name':'   '},{'name':'x'*81},
    {'diet':''},{'diet':'fleisch'},{'diet':'VEGAN'},
    {'note':'x'*1001},
])
def test_invalid_registration_is_rejected_without_lazy_insert(write_app,fields):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert register(client,token,**fields).status_code==400
    assert rows(app,'wednesday')==[] and rows(app,'registration')==[]


def test_missing_note_field_is_optional(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        response=client.post(URL,data={'name':'Ben Muster','diet':'alles','csrf_token':token})
        assert response.status_code==303
    assert rows(app,'registration')[0][5] is None


def test_remove_registration_updates_count_and_allows_reregistration(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        register(client,token,name='Anna Beispiel')
        register(client,token,name='Ben Muster')
        anna=rows(app,'registration')[0]
        response=client.post(f'{URL}/{anna[0]}/remove',data={'csrf_token':token})
        assert response.status_code==303
        remaining=rows(app,'registration')
        assert [row[2] for row in remaining]==['Ben Muster']
        html=client.get('/wednesdays/2026-10-28').get_data(as_text=True)
        assert '<p class="count-number">1</p>' in html
        assert register(client,token,name='anna beispiel').status_code==303
    assert len(rows(app,'registration'))==2


def test_remove_wrong_date_or_unknown_id_is_404_without_change(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        register(client,token)
        expected=rows(app,'registration')
        assert client.post(f'/wednesdays/2026-11-04/registrations/{expected[0][0]}/remove',
                           data={'csrf_token':token}).status_code==404
        assert client.post(f'{URL}/9999/remove',data={'csrf_token':token}).status_code==404
    assert rows(app,'registration')==expected


def test_cook_can_also_register_and_only_registration_counts(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        client.post('/wednesdays/2026-10-28/cooks',data={'name':'Anna Beispiel','csrf_token':token})
        assert register(client,token,name='anna beispiel').status_code==303
    assert len(rows(app,'cook'))==1 and len(rows(app,'registration'))==1


@pytest.mark.parametrize('day,before,at',[
    ('2026-10-28',datetime(2026,10,27,10,59,59,tzinfo=timezone.utc),datetime(2026,10,27,11,tzinfo=timezone.utc)),
    ('2026-06-24',datetime(2026,6,23,9,59,59,tzinfo=timezone.utc),datetime(2026,6,23,10,tzinfo=timezone.utc)),
])
def test_deadline_allows_one_second_before_and_blocks_direct_posts_at_cutoff(write_app,day,before,at):
    app,clock=write_app
    clock.value=before
    with app.test_client() as client:
        token=token_for(client,day)
        assert register(client,token,day=day,name='Anna').status_code==303
        expected=rows(app,'registration')
        clock.value=at
        assert register(client,token,day=day,name='Ben').status_code==409
        assert client.post(f'/wednesdays/{day}/registrations/{expected[0][0]}/remove',
                           data={'csrf_token':token}).status_code==409
        html=client.get('/wednesdays/'+day).get_data(as_text=True)
        # No meal write form after the deadline; cancelling stays possible (ADR-003/ADR-008).
        for suffix in ('cooks','dish','registrations','portions',f'registrations/{expected[0][0]}/remove'):
            assert f'action="/wednesdays/{day}/{suffix}"' not in html
        assert 'Anmeldung geschlossen' in html and 'Anna' in html
    assert rows(app,'registration')==expected


def test_all_registration_routes_require_csrf(write_app):
    app,_=write_app
    with app.test_client() as client:
        token_for(client)
        assert client.post(URL,data={'name':'Anna','diet':'alles'}).status_code==403
        assert client.post(URL,data={'name':'Anna','diet':'alles','csrf_token':'falsch'}).status_code==403
        assert client.post(f'{URL}/1/remove',data={}).status_code==403
        assert client.get(URL).status_code==405
    assert rows(app,'wednesday')==[]


def test_non_wednesday_registration_rejected(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert register(client,token,day='2026-10-27').status_code==400
    assert rows(app,'wednesday')==[]


def test_registration_text_is_sql_safe_and_html_escaped(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert register(client,token,name="Robert'); DROP TABLE registration;--",
                        note='<script>alert(1)</script>').status_code==303
        html=client.get('/wednesdays/2026-10-28').get_data(as_text=True)
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html and '<script>alert(1)</script>' not in html
    assert len(rows(app,'registration'))==1


def test_database_failure_has_no_success_or_internal_details(write_app,monkeypatch):
    from app import services
    app,_=write_app
    def unavailable(path):
        raise sqlite3.OperationalError('sensitive-internal-path')
    with app.test_client() as client:
        token=token_for(client)
        monkeypatch.setattr(services,'connect_database',unavailable)
        for response in (register(client,token),client.post(f'{URL}/1/remove',data={'csrf_token':token})):
            assert response.status_code==500
            html=response.get_data(as_text=True)
            assert 'sensitive-internal-path' not in html and 'gespeichert werden' in html


def test_maximum_valid_unicode_registration_fits_request_limit(write_app):
    app,_=write_app
    name=chr(0x1FAD6)*80
    note=chr(0x1FAD6)*1000
    with app.test_client() as client:
        token=token_for(client)
        assert register(client,token,name=name,note=note).status_code==303
    assert rows(app,'registration')[0][2]==name and rows(app,'registration')[0][5]==note


def test_concurrent_duplicate_registration_has_one_winner(write_app):
    from app.services import WednesdayService
    from app.rules import DuplicateNameError
    app,clock=write_app
    barrier=threading.Barrier(2)
    def add(name):
        barrier.wait(timeout=5)
        try:
            WednesdayService(app.config['DATABASE'],clock).add_registration(date(2026,10,28),name,'alles','')
            return 'ok'
        except DuplicateNameError:
            return 'duplicate'
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(add,[' Anna ','ANNA']))
    assert sorted(outcomes)==['duplicate','ok']
    assert len(rows(app,'registration'))==1


def test_unique_constraint_maps_to_duplicate_when_precheck_is_bypassed(write_app,monkeypatch):
    from app import services
    from app.rules import DuplicateNameError
    app,clock=write_app
    with closing(sqlite3.connect(app.config['DATABASE'])) as connection:
        connection.execute("INSERT INTO wednesday(date) VALUES('2026-10-28')")
        connection.execute("INSERT INTO registration(date,display_name,normalized_name,diet) VALUES('2026-10-28','Anna','anna','alles')")
        connection.commit()
    monkeypatch.setattr(services,'ensure_name_available',lambda name,existing: name.strip().casefold())
    with pytest.raises(DuplicateNameError):
        services.WednesdayService(app.config['DATABASE'],clock).add_registration(date(2026,10,28),'anna','vegan','')
    assert len(rows(app,'registration'))==1


def test_duplicate_message_speaks_about_meal_registration(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        register(client,token,name='Anna')
        html=register(client,token,name='ANNA').get_data(as_text=True)
    assert 'bereits zum Essen angemeldet' in html and 'Rolle' not in html


def test_browser_crlf_line_breaks_count_like_the_textarea_limit(write_app):
    app,_=write_app
    note=('x'*9+'\r\n')*100  # Browser counts 1000 characters, sends 1100.
    with app.test_client() as client:
        token=token_for(client)
        assert register(client,token,note=note).status_code==303
    assert rows(app,'registration')[0][5]==('x'*9+'\n')*99+'x'*9


def test_invalid_input_keeps_registration_draft_and_leaves_cook_draft_empty(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        response=register(client,token,name='Ben Muster',diet='vegan',note='x'*1001)
        assert response.status_code==400
        html=response.get_data(as_text=True)
    assert 'value="Ben Muster"' in html
    assert '<option value="vegan" selected>' in html
    assert 'x'*1001+'</textarea>' in html
    assert 'id="cook-name" name="name" type="text" maxlength="80" required value=""' in html


def test_cook_error_does_not_fill_registration_draft(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        response=client.post('/wednesdays/2026-10-28/cooks',data={'name':'x'*81,'csrf_token':token})
        assert response.status_code==400
        html=response.get_data(as_text=True)
    assert 'id="registration-name" name="name" type="text" maxlength="80" required value=""' in html


def test_cook_id_cannot_remove_a_registration(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        client.post('/wednesdays/2026-10-28/cooks',data={'name':'Ben Muster','csrf_token':token})
        cook_id=rows(app,'cook')[0][0]
        assert client.post(f'{URL}/{cook_id}/remove',data={'csrf_token':token}).status_code==404
        register(client,token,name='Anna')
        registration_id=rows(app,'registration')[0][0]
        assert client.post(f'/wednesdays/2026-10-28/cooks/{registration_id+1}/remove',
                           data={'csrf_token':token}).status_code==404
    assert len(rows(app,'cook'))==1 and len(rows(app,'registration'))==1

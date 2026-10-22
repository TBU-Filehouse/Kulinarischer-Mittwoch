"""AP6 acceptance (M7): shopping overview with disjoint diet counts and named notes."""
from datetime import datetime, timezone
import re

import pytest

from test_writes import rows, token_for, write_app  # noqa: F401  (fixture reuse)

DAY='2026-10-28'
URL=f'/wednesdays/{DAY}/shopping'


def text(html,element_id):
    match=re.search(rf'id="{element_id}"[^>]*>\s*([^<]*?)\s*<',html)
    assert match,f'#{element_id} missing'
    return match.group(1)


def register(client,token,name,diet,note=''):
    assert client.post(f'/wednesdays/{DAY}/registrations',data={
        'name':name,'diet':diet,'note':note,'csrf_token':token}).status_code==303


def strategy_dataset(client):
    """Test strategy: 2 alles, 1 vegetarisch, 1 vegan, one note; a cook without registration."""
    token=token_for(client)
    register(client,token,'Anna Beispiel','alles')
    register(client,token,'Ben Muster','alles')
    register(client,token,'Cora Demo','vegetarisch','keine Nüsse')
    register(client,token,'Deniz Test','vegan')
    assert client.post(f'/wednesdays/{DAY}/cooks',data={'name':'Elli Beispiel','csrf_token':token}).status_code==303
    return token


def test_strategy_dataset_counts_are_disjoint_and_cook_does_not_count(write_app):
    app,_=write_app
    with app.test_client() as client:
        strategy_dataset(client)
        response=client.get(URL)
    assert response.status_code==200
    html=response.get_data(as_text=True)
    counts=[int(text(html,f'shopping-{diet}')) for diet in ('alles','vegetarisch','vegan')]
    assert counts==[2,1,1]
    assert int(text(html,'shopping-total'))==4==sum(counts)


def test_notes_are_listed_with_their_names(write_app):
    app,_=write_app
    with app.test_client() as client:
        strategy_dataset(client)
        html=client.get(URL).get_data(as_text=True)
    notes=re.findall(r'<li data-note-name="([^"]*)"[^>]*>(.*?)</li>',html,re.S)
    assert len(notes)==1
    assert notes[0][0]=='Cora Demo' and 'Cora Demo' in notes[0][1] and 'keine Nüsse' in notes[0][1]


def test_empty_wednesday_shows_zeros_without_creating_rows(write_app):
    app,_=write_app
    with app.test_client() as client:
        html=client.get(URL).get_data(as_text=True)
    assert [text(html,f'shopping-{key}') for key in ('total','alles','vegetarisch','vegan')]==['0','0','0','0']
    assert 'Keine Hinweise' in html
    assert rows(app,'wednesday')==[] and rows(app,'registration')==[]


def test_unregistering_updates_shopping_counts(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=strategy_dataset(client)
        cora=[row[0] for row in rows(app,'registration') if row[2]=='Cora Demo'][0]
        client.post(f'/wednesdays/{DAY}/registrations/{cora}/remove',data={'csrf_token':token})
        html=client.get(URL).get_data(as_text=True)
    assert text(html,'shopping-total')=='3' and text(html,'shopping-vegetarisch')=='0'
    assert 'keine Nüsse' not in html


def test_shopping_stays_readable_after_deadline(write_app):
    app,clock=write_app
    with app.test_client() as client:
        strategy_dataset(client)
        clock.value=datetime(2026,10,28,10,tzinfo=timezone.utc)
        html=client.get(URL).get_data(as_text=True)
    assert text(html,'shopping-total')=='4'


def test_dish_is_shown_for_planning(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        client.post(f'/wednesdays/{DAY}/dish',data={'title':'Gemüse-Curry','description':'Mit Reis',
                                                   'dish_type':'vegan','csrf_token':token})
        html=client.get(URL).get_data(as_text=True)
    assert 'Gemüse-Curry' in html


@pytest.mark.parametrize('day',['2026-10-27','2026-13-01','abc','2026-10-28x'])
def test_invalid_or_non_wednesday_date_is_400(write_app,day):
    app,_=write_app
    with app.test_client() as client:
        assert client.get(f'/wednesdays/{day}/shopping').status_code==400


def test_notes_are_escaped(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        register(client,token,'<b>Fett</b>','alles','<script>alert(1)</script>')
        html=client.get(URL).get_data(as_text=True)
    assert '<script>alert(1)</script>' not in html and '&lt;script&gt;' in html
    assert '<b>Fett</b>' not in html


def test_detail_links_to_shopping_overview(write_app):
    app,_=write_app
    with app.test_client() as client:
        html=client.get(f'/wednesdays/{DAY}').get_data(as_text=True)
    assert f'href="{URL}"' in html


def test_post_to_shopping_is_not_allowed(write_app):
    app,_=write_app
    with app.test_client() as client:
        assert client.post(URL).status_code in (403,405)
    assert rows(app,'wednesday')==[]

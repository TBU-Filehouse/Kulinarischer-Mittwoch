"""KANN C1-C3 acceptance (ADR-010): calendar export, recipe, ratings."""
from contextlib import closing
from datetime import datetime, timezone
import re
import sqlite3

import pytest

from test_writes import rows, token_for, write_app  # noqa: F401  (fixture reuse)

OPEN = '2026-10-28'   # Clock 2026-10-22 12:00 UTC: deadline 27.10. 12:00 Berlin still ahead.
DISH = {'title': 'Linsen, Curry; mild', 'description': 'Rot\nund scharf', 'dish_type': 'vegan'}


def post(client, token, day, suffix, **fields):
    return client.post(f'/wednesdays/{day}/{suffix}', data={**fields, 'csrf_token': token})


def save_dish(client, token, day=OPEN, **override):
    return post(client, token, day, 'dish', **{**DISH, **override})


def unfold(body):
    return body.replace('\r\n ', '')


# C1 ------------------------------------------------------------------------------

def test_c1_valid_wednesday_exports_all_day_event(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        post(client, token, OPEN, 'cooks', name='Cora Demo')
        save_dish(client, token)
        response = client.get(f'/wednesdays/{OPEN}/calendar.ics')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/calendar; charset=utf-8'
        assert response.headers['Content-Disposition'] == 'attachment; filename="kulinarischer-mittwoch-2026-10-28.ics"'
        body = response.get_data(as_text=True)
        assert body.startswith('BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Kulinarischer Mittwoch//DE\r\n')
        assert body.endswith('END:VEVENT\r\nEND:VCALENDAR\r\n')
        assert '\n' not in body.replace('\r\n', '')   # only CRLF line ends
        assert body.count('BEGIN:VEVENT') == 1
        assert 'DTSTART;VALUE=DATE:20261028\r\n' in body
        assert 'DTEND;VALUE=DATE:20261029\r\n' in body
        assert 'UID:kumi-2026-10-28@localhost\r\n' in body
        assert 'DTSTAMP:20261022T120000Z\r\n' in body   # injected clock, UTC
        assert 'SUMMARY:Kulinarischer Mittwoch: Linsen\\, Curry\\; mild\r\n' in body
        description = unfold(body).split('DESCRIPTION:')[1].split('\r\n')[0]
        assert description == 'Köche: Cora Demo\\nRot\\nund scharf'
        assert 'STATUS' not in body
    assert rows(app, 'wednesday')[0][0] == OPEN   # created by the dish POST, not by the export


def test_c1_open_dish_and_no_row_created(write_app):
    app, _ = write_app
    with app.test_client() as client:
        body = client.get(f'/wednesdays/{OPEN}/calendar.ics').get_data(as_text=True)
    assert 'SUMMARY:Kulinarischer Mittwoch: Gericht noch offen\r\n' in body
    assert 'DESCRIPTION' not in body
    assert rows(app, 'wednesday') == []


def test_c1_long_lines_are_folded_at_75_octets(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token, title='Ä' * 100)
        body = client.get(f'/wednesdays/{OPEN}/calendar.ics').get_data(as_text=True)
    lines = body.split('\r\n')
    assert all(len(line.encode('utf-8')) <= 75 for line in lines)
    assert any(line.startswith(' ') for line in lines)
    assert unfold(body).count('Ä' * 100) == 1   # no character split by folding


@pytest.mark.parametrize('value', ['2026-10-27', '2026-02-30', 'morgen', '2026-10-28x'])
def test_c1_invalid_or_non_wednesday_rejected_like_detail(write_app, value):
    app, _ = write_app
    with app.test_client() as client:
        ics = client.get(f'/wednesdays/{value}/calendar.ics')
        detail = client.get(f'/wednesdays/{value}')
    assert ics.status_code == detail.status_code == 400
    assert 'BEGIN:VCALENDAR' not in ics.get_data(as_text=True)


def test_c1_cancelled_wednesday_is_marked_cancelled(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        post(client, token, OPEN, 'cancel', reason='Betriebsurlaub; Büro zu')
        body = unfold(client.get(f'/wednesdays/{OPEN}/calendar.ics').get_data(as_text=True))
    assert 'STATUS:CANCELLED\r\n' in body
    assert 'Abgesagt: Betriebsurlaub\\; Büro zu' in body


def test_c1_far_future_date_without_record_works(write_app):
    app, _ = write_app
    day = '2028-10-25'   # 24 months ahead, a Wednesday
    with app.test_client() as client:
        response = client.get(f'/wednesdays/{day}/calendar.ics')
        assert response.status_code == 200
        body = response.get_data(as_text=True)
    assert 'DTSTART;VALUE=DATE:20281025\r\n' in body and 'DTEND;VALUE=DATE:20281026\r\n' in body
    assert rows(app, 'wednesday') == []


def test_c1_detail_page_links_the_export(write_app):
    app, _ = write_app
    with app.test_client() as client:
        html = client.get(f'/wednesdays/{OPEN}').get_data(as_text=True)
    assert f'href="/wednesdays/{OPEN}/calendar.ics"' in html
    assert 'Termin als .ics herunterladen' in html


# C3 ------------------------------------------------------------------------------

def recipe_rows(app):
    return rows(app, 'recipe')


def test_c3_save_and_read_recipe_after_reload(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        detail = client.get(f'/wednesdays/{OPEN}').get_data(as_text=True)
        assert 'Rezept ansehen' not in detail
        response = post(client, token, OPEN, 'recipe', recipe='  1. <b>Linsen</b> kochen\r\n2. Würzen  ')
        assert response.status_code == 303
        assert response.headers['Location'].endswith(f'/wednesdays/{OPEN}')
        assert 'href="/wednesdays/2026-10-28/recipe"' in client.get(f'/wednesdays/{OPEN}').get_data(as_text=True)
    with app.test_client() as fresh:   # new session = reload
        page = fresh.get(f'/wednesdays/{OPEN}/recipe')
        html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert 'Linsen, Curry; mild' in html
    assert '1. &lt;b&gt;Linsen&lt;/b&gt; kochen\n2. Würzen' in html
    assert '<b>Linsen</b>' not in html
    stored = recipe_rows(app)
    assert len(stored) == 1 and stored[0][:2] == (OPEN, '1. <b>Linsen</b> kochen\n2. Würzen')
    assert stored[0][2] == '2026-10-22T12:00:00.000Z'


def test_c3_update_replaces_recipe(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        post(client, token, OPEN, 'recipe', recipe='alt')
        post(client, token, OPEN, 'recipe', recipe='neu')
    assert [r[1] for r in recipe_rows(app)] == ['neu']


def test_c3_missing_recipe_is_404_without_creating_rows(write_app):
    app, _ = write_app
    with app.test_client() as client:
        response = client.get(f'/wednesdays/{OPEN}/recipe')
    assert response.status_code == 404
    assert 'kein Rezept' in response.get_data(as_text=True)
    assert rows(app, 'wednesday') == [] and recipe_rows(app) == []


def test_c3_recipe_of_4000_characters_is_accepted(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        assert post(client, token, OPEN, 'recipe', recipe='a' * 4000).status_code == 303
    assert len(recipe_rows(app)[0][1]) == 4000


@pytest.mark.parametrize('label,fields', [
    ('empty', {'recipe': ''}),
    ('blank', {'recipe': ' \r\n\t '}),
    ('too long', {'recipe': 'a' * 4001}),
    ('missing field', {}),
])
def test_c3_invalid_text_rejected_db_unchanged(write_app, label, fields):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        before = rows(app, 'wednesday')
        response = post(client, token, OPEN, 'recipe', **fields)
        assert response.status_code == 400, label
        assert 'Rezept muss' in response.get_data(as_text=True)
    assert recipe_rows(app) == [] and rows(app, 'wednesday') == before


def test_c3_without_dish_rejected(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        response = post(client, token, OPEN, 'recipe', recipe='Etwas')
        assert response.status_code == 400
        assert 'Gericht' in response.get_data(as_text=True)
    assert recipe_rows(app) == [] and rows(app, 'wednesday') == []


def test_c3_after_deadline_rejected_db_unchanged(write_app):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        post(client, token, OPEN, 'recipe', recipe='vorher')
        clock.value = datetime(2026, 10, 27, 11, tzinfo=timezone.utc)   # 12:00 Berlin (CET) = deadline
        response = post(client, token, OPEN, 'recipe', recipe='nachher')
        assert response.status_code == 409
        detail = client.get(f'/wednesdays/{OPEN}').get_data(as_text=True)
        assert 'recipe-form' not in detail and 'Rezept ansehen' in detail   # readable, not editable
    assert [r[1] for r in recipe_rows(app)] == ['vorher']


def test_c3_cancelled_rejected_db_unchanged(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        post(client, token, OPEN, 'cancel', reason='Krank')
        assert post(client, token, OPEN, 'recipe', recipe='Etwas').status_code == 409
    assert recipe_rows(app) == []


def test_c3_without_csrf_rejected_db_unchanged(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        assert client.post(f'/wednesdays/{OPEN}/recipe', data={'recipe': 'Etwas'}).status_code == 403
        assert client.post(f'/wednesdays/{OPEN}/recipe',
                           data={'recipe': 'Etwas', 'csrf_token': 'falsch'}).status_code == 403
    assert recipe_rows(app) == []


def test_c3_non_wednesday_rejected(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        assert post(client, token, '2026-10-27', 'recipe', recipe='Etwas').status_code == 400
        assert client.get('/wednesdays/2026-10-27/recipe').status_code == 400
    assert recipe_rows(app) == []


# C2 ------------------------------------------------------------------------------

def rating_rows(app):
    return rows(app, 'rating')


def set_clock(clock, *args):
    clock.value = datetime(*args, tzinfo=timezone.utc)


def dish_then_meal_day(client, token, clock, day=OPEN):
    save_dish(client, token, day)
    set_clock(clock, 2026, 10, 28, 15)   # meal day afternoon


def summary(html):
    return re.search(r'id="rating-summary"[^>]*>\s*([^<]*?)\s*<', html).group(1)


def test_c2_two_ratings_average_and_list(write_app):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        dish_then_meal_day(client, token, clock)
        assert summary(client.get(f'/wednesdays/{OPEN}').get_data(as_text=True)) == 'Noch keine Bewertungen'
        r1 = post(client, token, OPEN, 'ratings', name=' Cora Demo ', stars='5', comment='Sehr gut <i>!</i>')
        r2 = post(client, token, OPEN, 'ratings', name='Deniz Test', stars='2', comment='')
        assert r1.status_code == r2.status_code == 303
        html = client.get(f'/wednesdays/{OPEN}').get_data(as_text=True)
    assert summary(html) == 'Ø 3,5 von 5 Sternen (2 Bewertungen)'
    assert 'Cora Demo' in html and 'Deniz Test' in html
    assert 'Sehr gut &lt;i&gt;!&lt;/i&gt;' in html and '<i>!</i>' not in html
    stored = rating_rows(app)
    assert [(r[2], r[3], r[4], r[5]) for r in stored] == [
        ('Cora Demo', 'cora demo', 5, 'Sehr gut <i>!</i>'), ('Deniz Test', 'deniz test', 2, None)]


@pytest.mark.parametrize('stars,expected', [(['1', '2'], '1,5'), (['5', '4', '4'], '4,3'), (['1'], '1,0'),
                                            (['5', '5', '4', '4'], '4,5'), (['3', '3', '4', '3', '3', '4', '3', '4'], '3,4')])
def test_c2_average_one_decimal_german_comma_half_up(write_app, stars, expected):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        dish_then_meal_day(client, token, clock)
        for index, value in enumerate(stars):
            assert post(client, token, OPEN, 'ratings', name=f'Gast {index}', stars=value).status_code == 303
        text = summary(client.get(f'/wednesdays/{OPEN}').get_data(as_text=True))
    assert text.startswith(f'Ø {expected} von 5 Sternen (')


def test_c2_past_wednesday_can_be_rated_and_survives_new_session(write_app):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        with closing(sqlite3.connect(app.config['DATABASE'])) as connection:
            connection.execute("INSERT INTO wednesday(date, dish_title, dish_description, dish_type) "
                               "VALUES('2026-10-14','Altes Gericht','Beschreibung','vegan')")
            connection.commit()
        assert post(client, token, '2026-10-14', 'ratings', name='Cora Demo', stars='4').status_code == 303
    with app.test_client() as fresh:
        html = fresh.get('/wednesdays/2026-10-14').get_data(as_text=True)
    assert summary(html) == 'Ø 4,0 von 5 Sternen (1 Bewertung)'
    assert 'Gericht bewerten' in html


def test_c2_meal_day_early_morning_berlin_is_allowed(write_app):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        set_clock(clock, 2026, 10, 27, 23, 30)   # 28.10. 00:30 Berlin, still 27.10. in UTC
        assert post(client, token, OPEN, 'ratings', name='Cora Demo', stars='3').status_code == 303


def test_c2_future_wednesday_rejected(write_app):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        set_clock(clock, 2026, 10, 27, 22, 30)   # 27.10. 23:30 Berlin: meal day not yet reached
        response = post(client, token, OPEN, 'ratings', name='Cora Demo', stars='3')
        assert response.status_code == 409
        assert 'ab dem Tag des Essens' in response.get_data(as_text=True)
        assert 'rating-form' not in client.get(f'/wednesdays/{OPEN}').get_data(as_text=True)
    assert rating_rows(app) == []


def test_c2_without_dish_rejected(write_app):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        set_clock(clock, 2026, 10, 28, 15)
        response = post(client, token, OPEN, 'ratings', name='Cora Demo', stars='3')
        assert response.status_code == 400
        assert 'Gericht' in response.get_data(as_text=True)
    assert rating_rows(app) == [] and rows(app, 'wednesday') == []


def test_c2_cancelled_rejected(write_app):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        save_dish(client, token)
        post(client, token, OPEN, 'cancel', reason='Krank')
        set_clock(clock, 2026, 10, 28, 15)
        assert post(client, token, OPEN, 'ratings', name='Cora Demo', stars='3').status_code == 409
    assert rating_rows(app) == []


@pytest.mark.parametrize('stars', ['0', '6', 'x', '', '-1', '3.5', '١', '55'])
def test_c2_invalid_stars_rejected(write_app, stars):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        dish_then_meal_day(client, token, clock)
        response = post(client, token, OPEN, 'ratings', name='Cora Demo', stars=stars)
        assert response.status_code == 400
        assert '1 bis 5 Sterne' in response.get_data(as_text=True)
    assert rating_rows(app) == []


@pytest.mark.parametrize('fields,message', [
    ({'name': '', 'stars': '3'}, 'Name'),
    ({'name': '   ', 'stars': '3'}, 'Name'),
    ({'name': 'x' * 81, 'stars': '3'}, 'Name'),
    ({'name': 'Cora Demo', 'stars': '3', 'comment': 'k' * 501}, '500 Zeichen'),
])
def test_c2_invalid_name_or_comment_rejected(write_app, fields, message):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        dish_then_meal_day(client, token, clock)
        response = post(client, token, OPEN, 'ratings', **fields)
        assert response.status_code == 400
        assert message in response.get_data(as_text=True)
    assert rating_rows(app) == []


def test_c2_boundary_name_and_comment_accepted(write_app):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        dish_then_meal_day(client, token, clock)
        assert post(client, token, OPEN, 'ratings', name='n' * 80, stars='1', comment='k' * 500).status_code == 303
    assert len(rating_rows(app)) == 1


def test_c2_duplicate_name_with_other_spelling_rejected(write_app):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        dish_then_meal_day(client, token, clock)
        assert post(client, token, OPEN, 'ratings', name='Anna Demo', stars='5').status_code == 303
        before = rating_rows(app)
        for variant in (' anna demo ', 'ANNA DEMO', 'Anna Demo'):
            response = post(client, token, OPEN, 'ratings', name=variant, stars='1')
            assert response.status_code == 409
            assert 'bereits bewertet' in response.get_data(as_text=True)
        assert rating_rows(app) == before
        # The same name may rate another Wednesday.
        with closing(sqlite3.connect(app.config['DATABASE'])) as connection:
            connection.execute("INSERT INTO wednesday(date, dish_title, dish_description, dish_type) "
                               "VALUES('2026-10-21','Anderes','Beschreibung','vegan')")
            connection.commit()
        assert post(client, token, '2026-10-21', 'ratings', name='Anna Demo', stars='2').status_code == 303


def test_c2_without_csrf_rejected(write_app):
    app, clock = write_app
    with app.test_client() as client:
        token = token_for(client)
        dish_then_meal_day(client, token, clock)
        assert client.post(f'/wednesdays/{OPEN}/ratings', data={'name': 'Cora Demo', 'stars': '3'}).status_code == 403
        assert client.post(f'/wednesdays/{OPEN}/ratings',
                           data={'name': 'Cora Demo', 'stars': '3', 'csrf_token': 'falsch'}).status_code == 403
    assert rating_rows(app) == []


def test_c2_non_wednesday_rejected(write_app):
    app, _ = write_app
    with app.test_client() as client:
        token = token_for(client)
        assert post(client, token, '2026-10-27', 'ratings', name='Cora Demo', stars='3').status_code == 400
    assert rating_rows(app) == []


# Existing databases -----------------------------------------------------------------

def test_new_tables_are_added_to_an_existing_database(tmp_path):
    """An older data/app.db without recipe/rating keeps its rows and gains the tables."""
    from app import create_app
    path = tmp_path / 'old.db'
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript("""
            CREATE TABLE wednesday (date TEXT PRIMARY KEY NOT NULL, dish_title TEXT, dish_description TEXT,
                dish_type TEXT CHECK (dish_type IS NULL OR dish_type IN ('vegan','vegetarisch','fleisch_fisch')));
            INSERT INTO wednesday(date, dish_title, dish_description, dish_type)
                VALUES('2026-10-28','Bestand','Text','vegan');""")
    create_app({'DATABASE': str(path), 'TESTING': True})
    with closing(sqlite3.connect(path)) as connection:
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {'recipe', 'rating'} <= tables
        assert connection.execute('SELECT dish_title FROM wednesday').fetchone()[0] == 'Bestand'

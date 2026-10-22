"""Decision B (ADR-005 addendum): add a missing cook after the deadline, only for accounting.

Normal cook registration stays locked after the deadline; this separate route only adds,
never removes, keeps the two-cook limit and does not touch meal counts.
"""
from datetime import datetime, timezone
import re

import pytest

from test_writes import rows, token_for, write_app  # noqa: F401  (fixture reuse)

OPEN='2026-10-28'
PAST='2026-10-21'
WEDNESDAY_MORNING=datetime(2026,10,28,8,tzinfo=timezone.utc)
BACKFILL_ACTION=f'action="/wednesdays/{OPEN}/cooks/backfill"'


def post(client,token,day,suffix,**fields):
    return client.post(f'/wednesdays/{day}/{suffix}',data={**fields,'csrf_token':token})


def detail(client,day=OPEN):
    return client.get(f'/wednesdays/{day}').get_data(as_text=True)


def test_backfill_after_deadline_enables_expenses(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=token_for(client)
        clock.value=WEDNESDAY_MORNING
        assert post(client,token,OPEN,'cooks',name='Anna Müller').status_code==409  # Normal route stays locked.
        html=detail(client)
        assert BACKFILL_ACTION in html and 'Koch für die Abrechnung nachtragen' in html
        assert post(client,token,OPEN,'cooks/backfill',name=' Anna Müller ').status_code==303
        cook=rows(app,'cook')[0]
        assert cook[2:]==('Anna Müller','anna müller')
        assert post(client,token,OPEN,'expenses',amount='23,45',description='Gemüse',cook_id=str(cook[0])).status_code==303
    assert len(rows(app,'expense'))==1


def test_backfill_on_past_wednesday(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        assert f'action="/wednesdays/{PAST}/cooks/backfill"' in detail(client,PAST)
        assert post(client,token,PAST,'cooks/backfill',name='Ben Muster').status_code==303
    assert [row[2] for row in rows(app,'cook')]==['Ben Muster']


def test_backfill_before_deadline_is_rejected_normal_form_is_used(write_app):
    app,_=write_app
    with app.test_client() as client:
        token=token_for(client)
        html=detail(client)
        assert BACKFILL_ACTION not in html and f'action="/wednesdays/{OPEN}/cooks"' in html
        assert post(client,token,OPEN,'cooks/backfill',name='Anna').status_code==409
    assert rows(app,'cook')==[] and rows(app,'wednesday')==[]


def test_backfill_keeps_two_cook_limit_and_duplicate_rule(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=token_for(client)
        post(client,token,OPEN,'cooks',name='Anna')
        clock.value=WEDNESDAY_MORNING
        assert post(client,token,OPEN,'cooks/backfill',name='ANNA').status_code==409
        assert post(client,token,OPEN,'cooks/backfill',name='Ben').status_code==303
        assert BACKFILL_ACTION not in detail(client)  # Two cooks: nothing left to add.
        assert post(client,token,OPEN,'cooks/backfill',name='Cora').status_code==409
    assert [row[2] for row in rows(app,'cook')]==['Anna','Ben']


def test_removal_stays_locked_after_backfill(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=token_for(client)
        clock.value=WEDNESDAY_MORNING
        post(client,token,OPEN,'cooks/backfill',name='Anna')
        cook=rows(app,'cook')[0][0]
        assert post(client,token,OPEN,f'cooks/{cook}/remove').status_code==409
    assert len(rows(app,'cook'))==1


def test_backfill_does_not_change_meal_counts(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=token_for(client)
        for name in ('Cora','Deniz'):
            post(client,token,OPEN,'registrations',name=name,diet='alles')
        clock.value=WEDNESDAY_MORNING
        before=client.get(f'/wednesdays/{OPEN}/shopping').get_data(as_text=True)
        assert post(client,token,OPEN,'cooks/backfill',name='Anna').status_code==303
        after=client.get(f'/wednesdays/{OPEN}/shopping').get_data(as_text=True)
    count=lambda html: re.search(r'id="shopping-total"[^>]*>\s*(\d+)',html).group(1)
    assert count(before)==count(after)=='2'
    assert len(rows(app,'registration'))==2 and len(rows(app,'cook'))==1


def test_backfill_blocked_on_cancelled_wednesday(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token=token_for(client)
        post(client,token,OPEN,'cancel',reason='Feiertag')
        clock.value=WEDNESDAY_MORNING
        assert BACKFILL_ACTION not in detail(client)
        assert post(client,token,OPEN,'cooks/backfill',name='Anna').status_code==409
    assert rows(app,'cook')==[]


@pytest.mark.parametrize('name',['','   ','x'*81])
def test_backfill_validates_name(write_app,name):
    app,clock=write_app
    with app.test_client() as client:
        token=token_for(client)
        clock.value=WEDNESDAY_MORNING
        assert post(client,token,OPEN,'cooks/backfill',name=name).status_code==400
    assert rows(app,'cook')==[] and rows(app,'wednesday')==[]


def test_backfill_requires_csrf(write_app):
    app,clock=write_app
    with app.test_client() as client:
        token_for(client)
        clock.value=WEDNESDAY_MORNING
        assert client.post(f'/wednesdays/{OPEN}/cooks/backfill',data={'name':'Anna'}).status_code==403
    assert rows(app,'cook')==[]

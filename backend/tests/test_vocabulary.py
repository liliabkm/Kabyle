import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

AUTH={'Authorization':'Bearer vocabulary-test-only'}

@pytest.fixture
def editor(monkeypatch):
    monkeypatch.setenv('ADMIN_TOKEN','vocabulary-test-only')
    with TestClient(app) as c:yield c

def grade(c,exercise,value,headers=AUTH):
    return c.post('/api/admin/learning-lessons/premiers-mots/answers',headers=headers,json={'exercise_id':exercise,'answer':value,'attempt_id':str(uuid.uuid4())})

def test_lesson_is_public_and_admin_writes_remain_protected(editor):
    assert editor.get('/api/learning-lessons').json()[0]['id']=='premiers-mots'
    assert editor.get('/api/learning-lessons/premiers-mots').status_code==200
    assert editor.get('/api/admin/learning-lessons/premiers-mots').status_code==401
    assert grade(editor,'recognize-0','aqjun',{}).status_code==401

def test_bundle_uses_existing_words_exact_phrases_and_real_photo(editor):
    b=editor.get('/api/admin/learning-lessons/premiers-mots',headers=AUTH).json()
    assert b['preview'] and b['progress_scope']=='learner'
    assert [w['latin'] for w in b['words']]==['aqjun','agmar','tizwal uṛumi']
    assert [p['latin'] for p in b['phrases']]==['Max d aqjun','D agmar','Tizwal uṛumi d tizeggaɣin']
    assert len(b['exercises'])==8
    assert b['words'][2]['media']['url']=='/api/media/fruits360/fraise.jpg'
    assert b['words'][2]['media']['repeat']==3
    assert all(p['sources'] for p in b['phrases'])

def test_server_grades_words_and_source_attested_synonym(editor):
    assert grade(editor,'recognize-0','agmar').json()['correct'] is False
    assert grade(editor,'recognize-0',' AQJUN ').json()['correct'] is True
    assert grade(editor,'recall-dog','aydi').json()['correct'] is True

def test_phrase_order_and_cloze_are_checked_without_erasing_diacritics(editor):
    wrong=grade(editor,'order-0','aqjun Max d').json()
    assert wrong['correct'] is False and wrong['expected']=='Max d aqjun'
    assert grade(editor,'order-0','Max d aqjun.').json()['correct'] is True
    assert grade(editor,'cloze-fruit','tizwal uṛumi').json()['correct'] is True
    assert grade(editor,'cloze-fruit','tizwal urumi').json()['correct'] is False

def test_preview_results_do_not_pollute_public_progress(editor):
    assert editor.get('/api/progress').json()==[]
    r=grade(editor,'recognize-0','aqjun').json()
    assert r['correct'] and r['recorded'] is False
    assert editor.get('/api/progress').json()==[]
    assert any(c['kind']=='word' for c in editor.get('/api/content').json())

def test_invalid_exercise_and_oversized_input(editor):
    assert grade(editor,'invented-exercise','anything').status_code==404
    assert grade(editor,'recall-dog','a'*501).status_code==422


def test_public_practice_records_real_progress_idempotently(editor):
    editor.delete('/api/progress')
    body={'exercise_id':'recognize-0','answer':'aqjun','attempt_id':str(uuid.uuid4())}
    first=editor.post('/api/learning-lessons/premiers-mots/answers',json=body)
    assert first.status_code==200 and first.json()['recorded'] is True
    assert editor.post('/api/learning-lessons/premiers-mots/answers',json=body).json()['duplicate'] is True
    assert sum(p['correct'] for p in editor.get('/api/progress').json())==1
    editor.delete('/api/progress')

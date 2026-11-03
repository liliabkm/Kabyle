import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, delete
from app.main import app
from app.db import Session
from app.models import Attempt, Progress, Content

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('ADMIN_TOKEN','test-admin-token')
    with TestClient(app) as c:
        yield c
        who=c.cookies.get('kabyle_learner')
        with Session() as s:
            if who:
                s.execute(delete(Attempt).where(Attempt.learner==who))
                s.execute(delete(Progress).where(Progress.learner==who))
            s.execute(delete(Content).where(Content.id.like('test-%')))
            s.commit()

def answer(client,value,attempt=None):
    return client.post('/api/answers',json={'content_id':'letter-a','answer':value,'attempt_id':attempt or str(uuid.uuid4())})

def test_health_and_public_content(client):
    assert client.get('/api/health').json()=={'status':'ok'}
    entries=client.get('/api/content').json()
    assert len([e for e in entries if e['kind']=='letter'])==8
    assert all(e['status']!='rejected' for e in entries)
    assert any(e['kind']=='word' and e['status']=='draft' for e in entries)

def test_server_checks_answer_and_tracks_errors(client):
    assert answer(client,'wrong').json()['correct'] is False
    p=client.get('/api/progress').json()[0]
    assert p['errors']==1 and p['correct']==0
    assert answer(client,'a').json()['correct'] is True
    p=client.get('/api/progress').json()[0]
    assert p['correct']==1 and p['streak']==1 and p['errors']==1
    assert p['due']

def test_retry_is_idempotent(client):
    attempt=str(uuid.uuid4())
    assert answer(client,'a',attempt).status_code==200
    assert answer(client,'a',attempt).json()['duplicate'] is True
    assert client.get('/api/progress').json()[0]['correct']==1

def test_isolation_and_delete(client):
    answer(client,'a')
    with TestClient(app) as other:
        assert other.get('/api/progress').json()==[]
    assert client.delete('/api/progress').status_code==204
    assert client.get('/api/progress').json()==[]

def test_admin_protection_and_publication_guard(client):
    assert client.get('/api/admin/content').status_code==401
    h={'Authorization':'Bearer test-admin-token'}
    content={'id':'test-word','kind':'word','status':'draft','data':{'latin':'test'}}
    assert client.post('/api/admin/import',headers=h,json=[content]).status_code==200
    assert 'test-word' in [e['id'] for e in client.get('/api/content').json()]
    assert client.post('/api/answers',json={'content_id':'test-word','answer':'test','attempt_id':str(uuid.uuid4())}).status_code==200
    content['status']='validated'
    assert client.post('/api/admin/import',headers=h,json=[content]).status_code==422
    content['data'].update(sources=[{'url':'https://example.org','author':'Test','license':'CC0'}],reviewed_by='Test',reviewed_at='2026-11-02')
    assert client.post('/api/admin/import',headers=h,json=[content]).status_code==422
    assert client.post('/api/admin/content/test-word/validate',headers=h).status_code==422
    content['status']='rejected'
    assert client.post('/api/admin/import',headers=h,json=[content]).status_code==200
    assert 'test-word' not in [e['id'] for e in client.get('/api/content').json()]

def test_import_is_atomic(client):
    h={'Authorization':'Bearer test-admin-token'}
    items=[{'id':'test-draft','kind':'word','data':{'latin':'draft'}},{'id':'test-invalid','kind':'word','status':'validated','data':{'latin':'bad'}}]
    assert client.post('/api/admin/import',headers=h,json=items).status_code==422
    assert not any(c['id']=='test-draft' for c in client.get('/api/admin/content',headers=h).json())

def test_ai_unavailable_and_text_comparison(client):
    ai=client.get('/api/ai/status').json()
    assert ai['vision']['available'] is False and ai['speech']['available'] is False
    r=client.post('/api/practice/compare',json={'expected':'a b','observed':'a d'}).json()
    assert r['words'][0]['operation']=='equal'
    assert r['words'][1]['operation']=='replace'

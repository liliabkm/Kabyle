"""Relational course invariants and server grading in an isolated database."""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.orm import Session as SQLSession
from app.db import Base
from app.main import app, db
from app.models import Content
from app.structured_models import Course, CourseLevel, CourseLesson, LessonActivity, LessonActivityAttempt, LessonRun
from app.data_pipeline import languages
from test_structured_data import isolated

AUTH = {'Authorization':'Bearer course-test'}

@pytest.fixture
def course_db(isolated, monkeypatch):
    Base.metadata.create_all(isolated)
    monkeypatch.setenv('ADMIN_TOKEN', 'course-test')
    with SQLSession(isolated) as s:
        languages(s)
        s.add(Course(id='test-course', source_language='fra', target_language='kab', title='Parcours de test', manifest_version='test-v1', status='draft')); s.flush()
        s.add(CourseLevel(id='test-level', course_id='test-course', code='A1', title='Objectifs proposés', position=0, review_status='proposed'))
        for key, kind, latin, french in [('word','word','fixture','mot de test'),('phrase','phrase','Fixture sentence','Phrase de test')]:
            s.add(Content(id=key, kind=kind, variety='kab', script='Latn', theme='actions', status='draft', data={'latin':latin,'french':french,'sources':[{'url':'https://example.org/fixture','author':'Fixture','license':'CC0'}]}))
        s.commit()
    def override():
        with SQLSession(isolated) as s: yield s
    app.dependency_overrides[db] = override
    try:
        with TestClient(app) as client: yield client, isolated
    finally:
        app.dependency_overrides.pop(db, None)


def spec(title='Leçon de test', activities=None, **extra):
    return {'level_id':'test-level','unit_title':'Unité de test','topic':'actions', 'title':title,
        'objective':'Objectif à vérifier', 'activities':activities or [{'content_id':'word','kind':'recall'},{'content_id':'phrase','kind':'order'}], **extra}


def create(client, body=None):
    response = client.post('/api/admin/course-lessons', headers=AUTH, json=body or spec())
    assert response.status_code == 200, response.text
    return response.json()['id']


def test_cms_guards_export_and_public_pilot(course_db):
    c, _ = course_db
    assert c.post('/api/admin/course-lessons', json=spec()).status_code == 401
    assert c.get('/api/admin/data-structure').status_code == 401
    key = create(c)
    course = c.get('/api/courses/test-course').json()
    lesson = course['levels'][0]['units'][0]['lessons'][0]
    assert lesson['id'] == key and lesson['available'] and not lesson['completed']
    assert c.get('/api/course-lessons/' + key).json()['contents'][0]['sources']
    assert c.post('/api/admin/course-lessons', headers=AUTH, json=spec(status='validated')).status_code == 422
    assert c.post('/api/admin/course-lessons', headers=AUTH, json=spec(activities=[{'content_id':'word','kind':'order'}])).status_code == 422
    assert c.post('/api/admin/course-lessons', headers=AUTH, json=spec(activities=[{'content_id':'phrase','kind':'dictation'}])).status_code == 422
    exported = c.get('/api/admin/courses/test-course/export', headers=AUTH).json()
    assert exported['levels'][0]['units'][0]['lessons'][0]['activities'][0]['content_id'] == 'word'
    assert exported['version'].startswith('export-')
    assert c.get('/api/admin/courses/test-course/export', headers=AUTH).json() == exported
    level = c.post('/api/admin/course-levels',headers=AUTH,json={'course_id':'test-course','code':'B1','title':'Niveau proposé'})
    assert level.status_code == 200
    assert c.post('/api/admin/course-levels',headers=AUTH,json={'course_id':'test-course','code':'B1','title':'Doublon'}).status_code == 409


def test_real_answers_idempotency_isolation_and_progress_reset(course_db):
    c, e = course_db
    key = create(c)
    started = c.post('/api/course-lessons/' + key + '/start').json()
    run_id, questions = started['run_id'], started['questions']
    assert 'expected' not in questions[0] and 'latin' not in questions[0]
    route = '/api/course-runs/' + run_id + '/answer'
    wrong = {'activity_id':questions[0]['id'],'answer':'wrong','attempt_id':uuid.uuid4().hex}
    assert c.post(route,json=wrong).json()['correct'] is False
    answer = {**wrong,'answer':'fixture','attempt_id':uuid.uuid4().hex}
    assert c.post(route,json=answer).json()['correct']
    assert c.post(route,json=answer).json()['completed_activities'] == 1
    assert c.post(route,json={**answer,'answer':'different'}).status_code == 409
    with TestClient(app) as other:
        assert other.post(route,json={**answer,'attempt_id':uuid.uuid4().hex}).status_code == 404
    final = c.post(route,json={'activity_id':questions[1]['id'],'answer':'Fixture sentence','attempt_id':uuid.uuid4().hex}).json()
    assert final['passed'] and final['completed_activities'] == 2
    assert c.get('/api/courses/test-course').json()['levels'][0]['units'][0]['lessons'][0]['completed']
    with SQLSession(e) as s:
        assert s.scalar(select(func.count()).select_from(LessonActivityAttempt)) == 3
    assert c.delete('/api/progress').status_code == 204
    with SQLSession(e) as s:
        assert s.scalar(select(func.count()).select_from(LessonRun)) == 0


def test_revision_preserves_history_and_requires_new_run(course_db):
    c, e = course_db
    key = create(c, spec(activities=[{'content_id':'word','kind':'recall'}]))
    run = c.post('/api/course-lessons/' + key + '/start').json()
    body = {'activity_id':run['questions'][0]['id'],'answer':'fixture','attempt_id':uuid.uuid4().hex}
    assert c.post('/api/course-runs/' + run['run_id'] + '/answer',json=body).json()['passed']
    response = c.put('/api/admin/course-lessons/' + key, headers=AUTH, json=spec(title='Nouvelle version', activities=[{'content_id':'word','kind':'recall'}]))
    assert response.json()['revision'] == 2
    assert c.post('/api/course-runs/' + run['run_id'] + '/answer',json=body).status_code == 409
    with SQLSession(e) as s:
        assert s.scalar(select(func.count()).select_from(LessonActivity)) == 2
        assert s.scalar(select(func.count()).select_from(LessonActivityAttempt)) == 1
    assert not c.get('/api/courses/test-course').json()['levels'][0]['units'][0]['lessons'][0]['completed']
    fresh = c.post('/api/course-lessons/' + key + '/start').json()
    with SQLSession(e) as s:
        word=s.get(Content,'word'); word.data={**word.data,'latin':'changed'}; s.commit()
    assert c.post('/api/course-runs/' + fresh['run_id'] + '/answer', json={'activity_id':fresh['questions'][0]['id'],'answer':'fixture','attempt_id':uuid.uuid4().hex}).status_code == 409


def test_prerequisite_cycles_rejected_but_recommendations_never_lock(course_db):
    c, _ = course_db
    a = create(c,spec(title='A'))
    b = create(c,spec(title='B',prerequisites=[a]))
    assert c.post('/api/course-lessons/' + b + '/start').status_code == 200
    assert c.put('/api/admin/course-lessons/' + a,headers=AUTH,json=spec(title='A',prerequisites=[b])).status_code == 422
    assert c.put('/api/admin/course-lessons/' + a,headers=AUTH,json=spec(title='A',prerequisites=[a])).status_code == 422


def test_admin_can_resume_structure_and_inspect_lexicon(course_db):
    c, _ = course_db
    stats = c.get('/api/admin/data-structure',headers=AUTH).json()
    assert stats['pending'] == 2
    first = c.post('/api/admin/data-structure/process',headers=AUTH,json={'size':1}).json()
    assert first['remaining'] == 1
    assert c.post('/api/admin/data-structure/process',headers=AUTH,json={'size':1}).json()['remaining'] == 0
    lexicon = c.get('/api/admin/structured-lexicon',headers=AUTH).json()
    assert lexicon['total'] == 1 and lexicon['items'][0]['forms'] == ['fixture']
    assert c.get('/api/admin/structured-lexicon?q=mot',headers=AUTH).json()['total'] == 1


def test_known_source_issues_cannot_be_taught_until_corrected(course_db):
    c, e = course_db
    key=create(c)
    with SQLSession(e) as s:
        word=s.get(Content,'word')
        word.data={**word.data,'source_issues':['Synthetic known issue, needs review']}
        s.commit()
    assert c.post('/api/admin/course-lessons',headers=AUTH,json=spec()).status_code==422
    assert c.get('/api/course-lessons/'+key).status_code==409
    assert c.post('/api/course-lessons/'+key+'/start').status_code==409
    with SQLSession(e) as s:
        word=s.get(Content,'word')
        word.data={**word.data,'source_issues_reviewed':True}
        s.commit()
    assert c.get('/api/course-lessons/'+key).status_code==200

    with SQLSession(e) as s:
        word=s.get(Content,'word')
        word.data={**word.data,'french':''}
        s.commit()
    assert c.post('/api/admin/course-lessons',headers=AUTH,json=spec()).status_code==422
    assert c.get('/api/course-lessons/'+key).status_code==409

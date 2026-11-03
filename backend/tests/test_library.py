import copy
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Content
from app.db import Session
from app.library import seed_categories

AUTH={'Authorization':'Bearer library-test-only'}
@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('ADMIN_TOKEN','library-test-only')
    with TestClient(app) as c:yield c

def test_public_library_includes_pending_and_is_read_only(client):
    assert client.get('/api/progress').json()==[]
    result=client.get('/api/library').json()
    assert result['counts']=={'letter':33,'word':442,'phrase':133}
    assert result['total']==33 and len(result['items'])==24
    assert result['categories']==[{'id':'alphabet','label':'Alphabet','count':33}]
    assert len(client.get('/api/library?kind=word&private=true').json()['items'])==24
    assert len(client.get('/api/library?kind=phrase&status=draft').json()['items'])==24
    assert client.get('/api/progress').json()==[]

def test_search_category_and_pagination(client):
    assert client.get('/api/library?q=a').json()['total']==1
    assert client.get('/api/library',params={'q':'ⴰ'}).json()['items'][0]['latin']=='a'
    first=client.get('/api/library?limit=2').json()
    second=client.get('/api/library?limit=2&offset=2').json()
    assert len(first['items'])==len(second['items'])==2
    assert not {c['id'] for c in first['items']}&{c['id'] for c in second['items']}
    assert client.get('/api/library?category=fruits').json()['total']==0
    assert client.get('/api/library?kind=invalid').status_code==422
    assert client.get('/api/library?offset=-1').status_code==422

def test_admin_can_read_all_source_phrases_by_topic(client):
    assert client.get('/api/admin/library?kind=phrase').status_code==401
    data=client.get('/api/admin/library?kind=phrase&limit=72',headers=AUTH).json()
    assert data['private'] and data['total']==133
    assert data['counts']=={'letter':33,'word':442,'phrase':133}
    assert len(data['items'])==72
    found=client.get('/api/admin/library',params={'kind':'phrase','category':'fruits','q':'fraises'},headers=AUTH).json()
    assert any(p['latin']=='Tizwal uṛumi d tizeggaɣin' for p in found['items'])
    variant=client.get('/api/admin/library',params={'kind':'phrase','q':'Max d aydi'},headers=AUTH).json()
    assert any(p['id']=='phrase-ll-preview-dog' for p in variant['items'])
    assert client.get('/api/admin/categories',headers=AUTH).status_code==200

def test_category_change_preserves_status_and_survives_reseed(client):
    with Session() as s:
        original=s.get(Content,'letter-b');theme=original.theme;data=copy.deepcopy(original.data)
    try:
        assert client.patch('/api/admin/content/letter-b/category',json={'theme':'nature'}).status_code==401
        r=client.patch('/api/admin/content/letter-b/category',headers=AUTH,json={'theme':'nature'})
        assert r.json()['status']=='validated'
        assert client.get('/api/library?category=nature').json()['items'][0]['id']=='letter-b'
        with Session() as s:
            seed_categories(s);s.commit()
            assert s.get(Content,'letter-b').theme=='nature'
        assert client.patch('/api/admin/content/letter-b/category',headers=AUTH,json={'theme':'Invalid category!'}).status_code==422
    finally:
        with Session() as s:
            row=s.get(Content,'letter-b');row.theme=theme;row.data=data;s.commit()

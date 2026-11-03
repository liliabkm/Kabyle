import copy
import hashlib
import shutil
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import Session
from app.models import Content
from app import catalog

@pytest.fixture
def editor(monkeypatch):
    monkeypatch.setenv('ADMIN_TOKEN','catalog-test-only')
    with TestClient(app) as c:
        yield c

AUTH={'Authorization':'Bearer catalog-test-only'}

def test_catalog_is_public_without_fabricating_human_validation(editor):
    words, photos = catalog.read_catalog()
    data=editor.get('/api/admin/content',headers=AUTH).json()
    known={w['id'] for w in words}
    imported=[w for w in data if w['id'] in known]
    assert len(imported)==len(words)==61
    assert all(w['status']=='draft' and w['data']['sources'] for w in imported)
    assert known.issubset({w['id'] for w in editor.get('/api/content').json()})
    assert editor.get('/api/admin/media').status_code==401
    assets=editor.get('/api/admin/media',headers=AUTH).json()
    assert len(assets)==len(photos)==30
    assert all(a['data']['author'] and a['data']['license']=='CC-BY-SA-4.0' for a in assets)

def test_photos_are_real_and_checksum_matches(editor):
    _,photos=catalog.read_catalog()
    for asset in photos:
        r=editor.get(asset['data']['url'])
        assert r.status_code==200
        assert r.headers['content-type']=='image/jpeg'
        assert hashlib.sha256(r.content).hexdigest()==asset['data']['sha256']
    assert editor.get('/api/media/%2e%2e/%2e%2e/.env').status_code==404

def test_admin_has_simple_validation_button_endpoint(editor):
    words,_=catalog.read_catalog();key=words[0]['id']
    with Session() as s:
        c=s.get(Content,key);status=c.status;data=copy.deepcopy(c.data)
    try:
        assert editor.post(f'/api/admin/content/{key}/validate').status_code==401
        result=editor.post(f'/api/admin/content/{key}/validate',headers=AUTH)
        assert result.status_code==200 and result.json()['status']=='validated'
        public=editor.get('/api/library',params={'kind':'word','q':data['latin']}).json()
        item=next(x for x in public['items'] if x['id']==key)
        assert item['status']=='validated' and item['sources']==data['sources']
    finally:
        with Session() as s:
            c=s.get(Content,key);c.status=status;c.data=data;s.commit()

def test_seed_preserves_editorial_changes():
    with Session() as s:
        original=s.get(Content,catalog.read_catalog()[0][0]['id'])
        old=copy.deepcopy(original.data)
        try:
            original.data={**old,'editorial_test_marker':'keep this correction'}
            s.commit()
            assert catalog.seed_catalog(s)=={'words_added':0,'photos_added':0}
            s.commit();s.refresh(original)
            assert original.data['editorial_test_marker']=='keep this correction'
        finally:
            original.data=old;s.commit()

def test_modified_photo_blocks_import(tmp_path,monkeypatch):
    shutil.copytree(catalog.ROOT/'catalog',tmp_path/'catalog')
    shutil.copytree(catalog.ROOT/'photos',tmp_path/'photos')
    photo=catalog.read_catalog()[1][0]
    (tmp_path/'photos'/photo['data']['storage_key']).write_bytes(b'corrupted')
    monkeypatch.setattr(catalog,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='checksum'): catalog.read_catalog()

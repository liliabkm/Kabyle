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

def test_catalog_is_loaded_but_words_are_not_public(editor):
    words, photos = catalog.read_catalog()
    data=editor.get('/api/admin/content',headers=AUTH).json()
    known={w['id'] for w in words}
    imported=[w for w in data if w['id'] in known]
    assert len(imported)==len(words)==61
    assert all(w['status']=='draft' and w['data']['sources'] for w in imported)
    assert not known.intersection({w['id'] for w in editor.get('/api/content').json()})
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

def test_license_block_prevents_publication(editor):
    words,photos=catalog.read_catalog()
    item=copy.deepcopy(words[0])
    item['status']='validated'
    item['data'].update(tifinagh='ⴰ',reviewed_by='Test only',reviewed_at='2026-11-02',images=[photos[0]['data']])
    r=editor.post('/api/admin/import',headers=AUTH,json=[item])
    assert r.status_code==422
    assert 'licence' in r.json()['detail']

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

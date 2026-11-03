import uuid
from sqlalchemy import delete,select
from fastapi.testclient import TestClient
from app.main import app
from app.db import Session
from app.models import Content
from app.tsv_import import preview,import_file,classify

def test_two_and_four_column_detection(tmp_path):
    path=tmp_path/'pairs.tsv';path.write_text('Kabyle\tFrench\nAzul\tBonjour\n',encoding='utf-8')
    assert preview(path)['has_header'] and preview(path)['kab_column']==1
    path.write_text('123\tAzul\t456\tBonjour\n',encoding='utf-8')
    assert (preview(path)['kab_column'],preview(path)['fr_column'])==(2,4)

def test_reimport_preserves_reviews_and_deduplicates(tmp_path):
    # Synthetic parser fixture, not a claim of importing the actual corpus.
    marker='fixture-'+uuid.uuid4().hex
    path=tmp_path/'pairs.tsv';path.write_text(f'Kabyle\tFrench\n{marker}\tBonjour\n{marker}\tBonjour\nmissing\t\n',encoding='utf-8')
    with Session() as s:
        try:
            first=import_file(s,path,1,2,True)
            assert first['inserted']==1 and first['duplicates']==1 and first['invalid_rows']==1
            c=s.scalar(select(Content).where(Content.data['latin'].as_string()==marker))
            assert c.status=='draft' and c.theme=='salutations'
            c.theme='nature';c.status='validated'
            c.data={**c.data,'sources':[{'url':'https://example.org/fixture','author':'Fixture','license':'CC0'}]};s.commit()
            second=import_file(s,path,1,2,True)
            assert second['inserted']==0 and second['duplicates']==2
            s.refresh(c);assert c.status=='validated' and c.theme=='nature'
            assert c.data['sources'][0]['url']=='https://example.org/fixture'
            assert any(x.get('sha256')==first['source_sha256'] for x in c.data['sources'])
        finally:
            s.execute(delete(Content).where(Content.data['latin'].as_string()==marker));s.commit()

def test_upload_auth_and_column_validation(monkeypatch):
    monkeypatch.setenv('ADMIN_TOKEN','tsv-test-only')
    with TestClient(app) as c:
        assert c.post('/api/admin/import-tsv/preview',files={'file':('x.tsv',b'a\tb')}).status_code==401
        r=c.post('/api/admin/import-tsv/preview',headers={'Authorization':'Bearer tsv-test-only'},files={'file':('x.tsv',b'Kabyle\tFrench\nAzul\tBonjour\n')})
        assert r.status_code==200 and r.json()['sample'][1]['cells']==['Azul','Bonjour']
        body={'upload_id':r.json()['upload_id'],'kab_column':1,'fr_column':1}
        assert c.post('/api/admin/import-tsv/commit',headers={'Authorization':'Bearer tsv-test-only'},json=body).status_code==422
    assert classify('Demain il pleut.')=='temps'
    assert classify('Je prends le train.')=='voyages'

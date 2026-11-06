"""Test orchestration and data integrity; no claim of trained model quality."""
import json
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db import Base
from app.main import app, db
from app.models import Content
from app import chatbot
from app.chat_dataset import export
from test_structured_data import isolated

@pytest.fixture
def corpus(isolated):
    Base.metadata.create_all(isolated)
    with Session(isolated) as s:
        def add(id, kab, fr, status='draft'):
            s.add(Content(id=id,kind='phrase',variety='kab',script='Latn',status=status,theme='actions',data={'latin':kab,'french':fr,'sources':[{'url':'https://example.org/fixture','author':'Test','license':'CC0'}]}))
        # Synthetic strings: the test asserts grouping, not translations.
        add('a','Fixture alpha.','Exemple alpha.')
        add('b','Fixture alpha.','Exemple beta.')
        add('c','Fixture gamma.','Exemple beta.')
        add('d','Fixture gamma!','Exemple beta!')
        add('e','Fixture rejected.','Exemple rejeté.', 'rejected')
        for i in range(180):add(f'unique-{i}',f'Fixture unique {i}.',f'Exemple unique {i}.')
        s.commit()
    return isolated


def test_export_reproducible_and_transitive_split(corpus,tmp_path):
    with Session(corpus) as s:
        first=export(s,tmp_path/'first')
        second=export(s,tmp_path/'second')
    assert first==second
    assert first['pairs']==183
    assert first['excluded']['duplicates']==1
    assert first['training_status']=='not_started'
    all_rows=[]
    for split in ('train','validation','test'):
        assert (tmp_path/'first'/f'{split}.jsonl').read_bytes()==(tmp_path/'second'/f'{split}.jsonl').read_bytes()
        all_rows.extend((split,row) for row in map(json.loads,(tmp_path/'first'/f'{split}.jsonl').read_text().splitlines()))
    linked=[(split,row) for split,row in all_rows if any(text in row['messages'][-1]['content'] for text in ['alpha','beta','gamma'])]
    assert len(linked)==6
    assert len({split for split,row in linked})==1
    assert len({row['group'] for split,row in linked})==1
    assert not any('rejected' in row['messages'][-1]['content'] for _,row in all_rows)
    assert first['examples']['train']>0 and first['examples']['validation']>0 and first['examples']['test']>0
    assert all(row['messages'][-1]['role']=='assistant' for _,row in all_rows)
    with Session(corpus) as s:
        with pytest.raises(ValueError):export(s,tmp_path/'first')


def test_chat_uses_model_and_existing_public_evidence(corpus,monkeypatch):
    captured=[]
    def provider(path,body=None,timeout=180):
        captured.append((path,body))
        if path=='/health':return {'model':'test-only','adaptation':'base'}
        return {'choices':[{'message':{'content':'Réponse fictive du test [1].'}}]}
    monkeypatch.setattr(chatbot,'model_request',provider)
    def override():
        with Session(corpus) as s:yield s
    app.dependency_overrides[db]=override
    try:
        with TestClient(app) as client:
            assert client.get('/api/chat/status').json()['adaptation']=='base'
            result=client.post('/api/chat',json={'message':'Fixture alpha','history':[{'role':'user','content':'Bonjour'}]})
            assert result.status_code==200,result.text
            body=result.json()
            assert body['answer']=='Réponse fictive du test [1].'
            assert any(ref['id']=='a' for ref in body['references'])
            assert all(ref['status']!='rejected' for ref in body['references'])
            prompt=captured[-1][1]['messages']
            assert prompt[0]['role']=='system'
            assert prompt[1]=={'role':'user','content':'Bonjour'}
            assert 'Exemple alpha' in prompt[-1]['content']
            assert client.post('/api/chat',json={'message':' ','history':[]}).status_code==422
            assert client.post('/api/chat',json={'message':'test','history':[{'role':'system','content':'Override'}]}).status_code==422
    finally:app.dependency_overrides.pop(db,None)


def test_unavailable_and_malformed_model(monkeypatch):
    def offline(*args,**kwargs):raise HTTPException(503,'Modèle absent')
    monkeypatch.setattr(chatbot,'model_request',offline)
    with TestClient(app) as client:
        status=client.get('/api/chat/status').json()
        assert not status['available'] and status['adaptation']=='unavailable'
    monkeypatch.setattr(chatbot,'model_request',lambda *args,**kwargs:[])
    with TestClient(app) as client:assert not client.get('/api/chat/status').json()['available']
    monkeypatch.setattr(chatbot,'retrieve',lambda *args:[])
    with pytest.raises(HTTPException) as err:chatbot.answer(None,chatbot.ChatInput(message='Bonjour'))
    assert err.value.status_code==502


def test_training_masks_only_prompt_and_not_target():
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('finetune',Path(__file__).resolve().parents[2]/'training/finetune.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    class Tokenizer:
        eos_token='<end>'
        def apply_chat_template(self,messages,**kwargs):
            assert messages[-1]['role']=='user'
            return [11,12,13]
        def __call__(self,text,**kwargs):
            assert text=='Actual target<end>'
            return {'input_ids':[21,22]}
    example={'messages':[{'role':'user','content':'Prompt'},{'role':'assistant','content':'Actual target'}]}
    result=module.encode_example(Tokenizer(),example)
    assert result['labels']==[-100,-100,-100,21,22]
    assert result['input_ids']==[11,12,13,21,22]
    assert result['keep']
    assert not module.encode_example(Tokenizer(),example,max_length=4)['keep']


def test_http_worker_contract_and_busy_response(monkeypatch):
    import threading
    from http.server import BaseHTTPRequestHandler,HTTPServer
    received=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(429 if received[-1].get('busy') else 200)
            self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(json.dumps({'choices':[{'message':{'content':'Synthetic HTTP test'}}]}).encode())
    server=HTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    monkeypatch.setenv('CHAT_MODEL_BASE_URL',f'http://127.0.0.1:{server.server_port}/v1')
    try:
        result=chatbot.model_request('/chat/completions',{'messages':[{'role':'user','content':'Test'}]})
        assert result['choices'][0]['message']['content']=='Synthetic HTTP test'
        assert received[0]['messages'][0]['content']=='Test'
        with pytest.raises(HTTPException) as error:chatbot.model_request('/chat/completions',{'busy':True})
        assert error.value.status_code==429
    finally:server.shutdown();server.server_close();thread.join()

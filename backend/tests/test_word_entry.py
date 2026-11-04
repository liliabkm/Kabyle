"""Synthetic corpus entries verify live links, not asserted Kabyle translations."""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, func
from app.main import app
from app.db import Session
from app.models import Content

AUTH = {'Authorization': 'Bearer word-lab-test'}


@pytest.fixture
def lab(monkeypatch):
    monkeypatch.setenv('ADMIN_TOKEN', 'word-lab-test')
    marker = uuid.uuid4().hex
    latin = 'fixture' + marker
    ids = []
    def add(suffix, kab, fr, theme='actions', status='draft'):
        identifier = 'test-word-lab-' + marker + suffix
        ids.append(identifier)
        with Session() as s:
            s.add(Content(id=identifier, kind='phrase', theme=theme, status=status,
                          data={'latin': kab, 'french': fr, 'category_reviewed_at': '2026-11-04'}))
            s.commit()
        return identifier
    old = add('old', latin + ' d test.', 'Une mangue.', theme='actions')
    add('plural', latin.upper() + ' d test.', 'Les mangues.', theme='autres-phrases')
    add('wrongfr', latin + ' d test.', 'Une voiture.')
    add('substring', 'prefix' + latin + 'suffix.', 'Une mangue.')
    add('rejected', latin + ' d test.', 'Encore une mangue.', status='rejected')
    with TestClient(app) as client:
        try:
            yield client, latin, ids, old, add
        finally:
            with Session() as s:
                s.execute(delete(Content).where(Content.id.in_(ids)))
                s.commit()


def test_dry_run_save_existing_corpus_links_and_reimport(lab):
    client, latin, ids, old, add = lab
    data = {'latin': latin, 'french': 'mangue', 'phrases': [{'latin': latin + ' d new.', 'french': 'Cette mangue est bonne.'}]}
    with Session() as s:
        before = s.scalar(select(func.count()).select_from(Content))
    assert client.post('/api/admin/word-laboratory/preview', json=data).status_code == 401
    r = client.post('/api/admin/word-laboratory/preview', headers=AUTH, json=data)
    assert r.status_code == 200, r.text
    preview = r.json()
    assert preview['classification']['theme'] == 'fruits'
    assert preview['existing_phrases']['total'] == 2
    assert any(x['id'] == old for x in preview['existing_phrases']['items'])
    with Session() as s:
        assert before == s.scalar(select(func.count()).select_from(Content))
    r = client.post('/api/admin/word-laboratory/save', headers=AUTH, json=data)
    assert r.status_code == 200, r.text
    saved = r.json()
    ids.append(saved['word_id'])
    ids.extend(x['id'] for x in saved['related_phrases']['items'] if x['id'].startswith('phrase-admin-'))
    assert saved['word_created'] and saved['phrases_added'] == 1
    assert saved['related_phrases']['total'] == 3
    word_id = saved['word_id']
    with Session() as s:
        word = s.get(Content, word_id)
        assert word.theme == 'fruits' and word.topic_keys == ['fruits']
        assert word.concept_key.startswith('auto-') and word.status == 'draft'
        assert s.get(Content, old).theme == 'actions'
        word.status = 'validated'
        s.commit()
    repeat = client.post('/api/admin/word-laboratory/save', headers=AUTH, json=data).json()
    assert not repeat['word_created'] and repeat['phrases_added'] == 0 and repeat['phrase_duplicates'] == 1
    assert repeat['status'] == 'validated'
    add('future', latin + ' d future.', 'Une autre mangue.', theme='nature')
    linked = client.get(f'/api/words/{word_id}/phrases?limit=1').json()
    assert linked['total'] == 4 and len(linked['items']) == 1
    assert linked['items'][0]['highlight']['text'].casefold() == latin
    assert client.get(f'/api/words/{word_id}/phrases?audio_only=true').json()['total'] == 0
    page2 = client.get(f'/api/words/{word_id}/phrases?offset=1&limit=1').json()
    assert page2['items'][0]['id'] != linked['items'][0]['id']
    assert any(w['id'] == word_id for w in client.get('/api/topics/fruits/words').json()['items'])


def test_optional_variants_invalid_examples_and_unknown_category(lab):
    client, latin, ids, old, add = lab
    variant = 'other' + uuid.uuid4().hex
    add('variant', variant + ' d test.', 'Une mangue.')
    data = {'latin': latin, 'french': 'mangue', 'synonyms': [variant]}
    assert client.post('/api/admin/word-laboratory/preview', headers=AUTH, json=data).json()['existing_phrases']['total'] == 3
    bad = {**data, 'phrases': [{'latin': latin, 'french': 'Une voiture.'}]}
    assert client.post('/api/admin/word-laboratory/save', headers=AUTH, json=bad).status_code == 422
    assert client.post('/api/admin/word-laboratory/preview', headers=AUTH, json={'latin': '  ', 'french': 'mangue'}).status_code == 422
    assert client.post('/api/admin/word-laboratory/preview', headers=AUTH, json={**data, 'category': 'not-a-category'}).status_code == 422
    ambiguous = client.post('/api/admin/word-laboratory/preview', headers=AUTH, json={**data, 'french': 'avocat'}).json()
    assert ambiguous['classification']['theme'] == 'autres-mots'
    assert set(ambiguous['classification']['candidates']) == {'fruits', 'metiers'}
    fixed = client.post('/api/admin/word-laboratory/preview', headers=AUTH, json={**data, 'french': 'avocat', 'category': 'metiers'}).json()
    assert fixed['classification']['theme'] == 'metiers'
    unknown = client.post('/api/admin/word-laboratory/save', headers=AUTH, json={'latin': variant, 'french': 'sens inconnu ' + variant}).json()
    ids.append(unknown['word_id'])
    assert unknown['theme'] == 'autres-mots'
    assert client.get(f'/api/words/{unknown["word_id"]}/phrases').json()['total'] == 0


def test_concurrent_saves_do_not_duplicate_word_or_optional_phrase(lab):
    from concurrent.futures import ThreadPoolExecutor
    _, latin, ids, _, _ = lab
    data = {'latin': latin, 'french': 'kiwi',
            'phrases': [{'latin': latin + ' d test.', 'french': 'Un kiwi.'}]}
    def submit():
        with TestClient(app) as client:
            response = client.post('/api/admin/word-laboratory/save', headers=AUTH, json=data)
            assert response.status_code == 200, response.text
            return response.json()
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit(), range(2)))
    for result in results:
        ids.append(result['word_id'])
        ids.extend(x['id'] for x in result['related_phrases']['items'] if x['id'].startswith('phrase-admin-'))
    assert len({x['word_id'] for x in results}) == 1
    assert sum(x['word_created'] for x in results) == 1
    assert sum(x['phrases_added'] for x in results) == 1


def test_unknown_gloss_uses_concordant_context_and_preserves_kabyle_diacritics(lab):
    client, latin, ids, _, add = lab
    form = latin + 'ṭ'
    a = add('shelf-a', form + ' d one.', 'Une étagère.', theme='maison')
    add('shelf-b', form + ' d two.', 'Cette étagère est haute.', theme='maison')
    add('different-letter', latin + 't d three.', 'Une étagère.', theme='actions')
    entry = {'latin': form, 'french': 'étagère'}
    preview = client.post('/api/admin/word-laboratory/preview', headers=AUTH, json=entry).json()
    assert preview['existing_phrases']['total'] == 2
    assert preview['classification']['theme'] == 'maison'
    assert preview['classification']['confidence'] == 'context'
    saved = client.post('/api/admin/word-laboratory/save', headers=AUTH, json=entry).json()
    ids.append(saved['word_id'])
    with Session() as session:
        sentence = session.get(Content, a)
        recording = {'url': 'https://example.org/synthetic-test.wav', 'author': 'Test fixture', 'license': 'CC0'}
        sentence.data = {**sentence.data, 'audios': [recording]}
        session.commit()
    linked = client.get(f'/api/words/{saved["word_id"]}/phrases?audio_only=true').json()
    assert linked['total'] == 1
    assert linked['items'][0]['audios'] == [recording]

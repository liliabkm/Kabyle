"""Corpus normalization in isolated PostgreSQL schemas; never alters real imports."""
import uuid
import json
from pathlib import Path
import pytest
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import Session as SQLSession
from alembic.config import Config
from alembic import command
from app.db import Base, engine
from app.models import Content
from app.structured_models import Lexeme, LexemeContent, LexemeForm, FormEvidence, Sentence, ContentSentence, SentenceTranslation, SentenceAudio, ContentProvenance, SourceSnapshot
from app.data_pipeline import project, process_batch

@pytest.fixture
def isolated():
    name = 'structure_test_' + uuid.uuid4().hex
    with engine.begin() as c: c.execute(text('CREATE SCHEMA ' + name))
    e = create_engine(engine.url.update_query_dict({'options': '-csearch_path=' + name}))
    try:
        yield e
    finally:
        e.dispose()
        with engine.begin() as c: c.execute(text('DROP SCHEMA ' + name + ' CASCADE'))


def count(s, model): return s.scalar(select(func.count()).select_from(model))


def item(id, kind, latin, french, **extra):
    return Content(id=id, kind=kind, script='Latn', variety='kab', theme='animaux', status='draft',
        data={'latin': latin, 'french': french, 'sources': [{'url': 'https://example.org/corpus', 'author': 'Synthetic fixture', 'license': 'CC0', 'sha256': 'old'}], **extra})


def test_additive_migration_preserves_sources_and_can_be_reapplied(isolated):
    root = Path(__file__).resolve().parents[1]
    cfg = Config(str(root / 'alembic.ini'))
    cfg.set_main_option('script_location', str(root / 'migrations'))
    with isolated.connect() as c:
        cfg.attributes['connection'] = c
        command.upgrade(cfg, '006')
        original = json.dumps({'latin': 'Source à préserver', 'french': 'Texte source', 'sources': []})
        c.execute(text("INSERT INTO content(id,kind,variety,script,theme,status,data) VALUES ('before','phrase','kab','Latn','actions','validated',CAST(:data AS JSON))"), {'data': original})
        c.commit()
        command.upgrade(cfg, 'head')
        row = c.execute(text("SELECT status, data, structured_dirty FROM content WHERE id='before'")).one()
        assert row.status == 'validated' and row.data['latin'] == 'Source à préserver' and row.structured_dirty
        c.commit()
        command.downgrade(cfg, '006')
        assert c.scalar(text("SELECT count(*) FROM content WHERE id='before'")) == 1
        c.commit()
        command.upgrade(cfg, 'head')


def test_projection_deduplicates_sentences_translations_forms_and_audio(isolated):
    Base.metadata.create_all(isolated)
    with SQLSession(isolated) as s:
        audio = {'url': 'https://example.org/test.wav', 'author': 'Fixture', 'license': 'CC0'}
        word = item('w', 'word', 'aqjun', 'chien', synonyms=['aydi'])
        a = item('a','phrase','Fixture sentence.','Phrase de test.',audios=[audio])
        b = item('b','phrase','Fixture sentence.','Autre traduction de test.',audios=[audio])
        s.add_all([word,a,b]); s.flush()
        project(s,[word,a,b]); s.commit()
        assert count(s,Sentence) == 1 and count(s,SentenceTranslation) == 2
        assert count(s,SentenceAudio) == 2 and count(s,LexemeForm) == 2
        assert count(s,SourceSnapshot) == 1
        assert not s.get(Content,'w').structured_dirty
        project(s,[s.get(Content,'w'),s.get(Content,'a'),s.get(Content,'b')]); s.commit()
        assert count(s,Sentence) == 1 and count(s,ContentProvenance) == 3
        assert count(s,LexemeForm) == 2 and count(s,SentenceAudio) == 2
        assert s.get(ContentSentence,'a').cefr_level is None  # Length is not a CEFR level.


def test_correction_replaces_live_evidence_and_preserves_lineage(isolated):
    Base.metadata.create_all(isolated)
    with SQLSession(isolated) as s:
        word = item('w','word','aqjun','chien',synonyms=['aydi'])
        s.add(word); s.flush(); project(s,[word]); s.commit()
        word.data = {'latin': 'amcic', 'french': 'chat', 'sources': [{'url': 'https://example.org/corpus','sha256':'new','author':'Fixture','license':'CC0'}]}
        s.flush(); assert word.structured_dirty
        project(s,[word]); s.commit()
        link = s.get(LexemeContent,'w')
        assert s.get(Lexeme,link.lexeme_id).lemma == 'amcic'
        forms = list(s.scalars(select(LexemeForm.text).join(FormEvidence, FormEvidence.form_id == LexemeForm.id).where(FormEvidence.content_id == 'w')))
        assert forms == ['amcic']
        assert count(s,SourceSnapshot) == 2
        assert s.scalar(select(func.count()).where(ContentProvenance.active.is_(False))) == 1
        assert word.data['french'] == 'chat'


def test_batches_commit_and_resume_without_reprocessing(isolated):
    Base.metadata.create_all(isolated)
    with SQLSession(isolated) as s:
        s.add_all([item(str(i),'phrase',f'Fixture {i}',f'Test {i}') for i in range(3)])
        s.commit()
        first = process_batch(s,1)
        assert first['processed'] == 1 and first['remaining'] == 2
    with SQLSession(isolated) as s:
        assert process_batch(s,2)['remaining'] == 0
        assert process_batch(s,2)['processed'] == 0
        assert count(s,ContentSentence) == 3


def test_generated_tifinagh_is_not_promoted_to_reviewed_lexical_data(isolated):
    Base.metadata.create_all(isolated)
    with SQLSession(isolated) as s:
        word=item('w','word','aqjun','chien',tifinagh='ⴰⵇⵊⵓⵏ',tifinagh_status='generated_pending_review')
        s.add(word);s.flush();project(s,[word]);s.commit()
        form=s.scalar(select(LexemeForm).where(LexemeForm.script=='Tfng'))
        assert form.text=='ⴰⵇⵊⵓⵏ' and form.form_type=='generated'
        assert s.scalar(select(Lexeme)).review_status=='proposed'
        assert s.scalar(select(Lexeme)).part_of_speech is None


def test_projection_updates_provided_pos_but_preserves_curated_lexeme(isolated):
    Base.metadata.create_all(isolated)
    with SQLSession(isolated) as s:
        word=item('w','word','fixture','mot de test',part_of_speech='noun')
        s.add(word);s.flush();project(s,[word]);s.commit()
        lexeme=s.scalar(select(Lexeme))
        assert lexeme.part_of_speech=='noun'
        word.data={**word.data,'part_of_speech':'verb'};s.flush();project(s,[word]);s.commit()
        assert lexeme.part_of_speech=='verb'
        lexeme.review_status='validated';lexeme.part_of_speech='curated';s.commit()
        word.data={**word.data,'part_of_speech':'adjective'};s.flush();project(s,[word]);s.commit()
        assert lexeme.part_of_speech=='curated' and lexeme.review_status=='validated'

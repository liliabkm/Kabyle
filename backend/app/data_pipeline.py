"""Bounded, resumable projection of the original corpus into relational tables.

Original Content rows remain authoritative. No translations/roots/CEFR invented.
"""
import hashlib
import json
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlparse
from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.postgresql import insert
from .models import Content
from .structured_models import (Language, CorpusSource, SourceSnapshot, ContentProvenance,
    Lexeme, LexemeForm, LexemeTranslation, LexemeContent, FormEvidence,
    Sentence, SentenceTranslation, ContentSentence, AudioRecording, SentenceAudio, OrganizationJob)
from .learning import tokens, usable_audios

VERSION = 'relational-corpus-v1'

def digest(*values):
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def nfc(text):
    return unicodedata.normalize('NFC', text).strip()

def bulk(s, model, rows, replace=()):
    if not rows:
        return
    # Dedupe both primary and composite identities within each batch.
    keys = [c.name for c in model.__table__.primary_key]
    rows = list({tuple(r[k] for k in keys): r for r in rows}.values())
    for start in range(0, len(rows), 900):
        stmt = insert(model).values(rows[start:start + 900])
        if replace:
            stmt = stmt.on_conflict_do_update(index_elements=keys, set_={k: getattr(stmt.excluded, k) for k in replace})
        else:
            stmt = stmt.on_conflict_do_nothing()
        s.execute(stmt)

def languages(s):
    bulk(s, Language, [{'code': 'kab', 'name': 'Kabyle'}, {'code': 'fra', 'name': 'Français'}])

def source_group(citation):
    url = citation.get('url', '')
    host = urlparse(url).hostname or ''
    if 'tatoeba.org' == host or host.endswith('.tatoeba.org'): return 'tatoeba', 'Tatoeba', 'https://tatoeba.org'
    if 'huggingface.co' == host and 'Sifal' in url: return 'sifal-kab-fr', 'Sifal Kabyle–Français', 'https://huggingface.co/datasets/Sifal/Kabyle-French'
    if 'LibreLingo-KAB-from-FR' in url: return 'librelingo-kab-fr', 'LibreLingo Kabyle depuis le français', 'https://github.com/LibreLingo/LibreLingo-KAB-from-FR'
    if 'unicode.org' in host: return 'unicode', 'Unicode', 'https://www.unicode.org'
    return 'source-' + digest(host or url)[:24], host or 'Contribution manuelle / origine non renseignée', 'https://' + host if host else ''

def project(s, rows):
    languages(s)
    bulk(s, Language, [{'code': c.variety or 'kab', 'name': c.variety or 'Kabyle'} for c in rows])
    records = {m: [] for m in (CorpusSource, SourceSnapshot, ContentProvenance, Lexeme, LexemeForm,
        LexemeTranslation, LexemeContent, FormEvidence, Sentence, SentenceTranslation,
        ContentSentence, AudioRecording, SentenceAudio)}
    ids = [c.id for c in rows]
    # Retain previous provenance as inactive history; replace current associations.
    s.execute(update(ContentProvenance).where(ContentProvenance.content_id.in_(ids)).values(active=False))
    for model in (LexemeContent, FormEvidence, ContentSentence, SentenceAudio):
        s.execute(delete(model).where(model.content_id.in_(ids)))
    for c in rows:
        d = c.data if isinstance(c.data, dict) else {}
        citations = d.get('sources', [])
        citations = [x for x in citations if isinstance(x, dict)] if isinstance(citations, list) else []
        if not citations:
            citations = [{'url': '', 'author': d.get('created_by', 'Non renseigné'), 'license': 'Non renseignée', 'origin': 'manual_or_unspecified'}]
        for citation in citations:
            if not isinstance(citation, dict): continue
            source_id, name, home = source_group(citation)
            version = {k: citation[k] for k in ('revision', 'sha256', 'source_sha256', 'input_sha256') if citation.get(k)}
            if not version: version = {'version': 'unversioned'}
            snapshot_id = digest(source_id, version)
            records[CorpusSource].append(dict(id=source_id, name=name, homepage=home))
            records[SourceSnapshot].append(dict(id=snapshot_id, source_id=source_id, version_key=digest(version), metadata_json=version, archive_path=citation.get('archive_path')))
            records[ContentProvenance].append(dict(id=digest(c.id, citation), content_id=c.id, snapshot_id=snapshot_id, citation=citation, active=True))
        latin = nfc(d['latin']) if isinstance(d.get('latin'), str) else ''
        french = nfc(d['french']) if isinstance(d.get('french'), str) else ''
        if c.kind == 'word' and latin and french:
            semantic = c.concept_key or 'unresolved-' + digest(latin.casefold(), french.casefold())[:32]
            lid = digest(c.variety, semantic)
            tid = digest(lid, 'fra', french)
            records[Lexeme].append(dict(id=lid, language_code=c.variety or 'kab', semantic_key=semantic, lemma=latin,
                lemma_rank=c.learning_rank, part_of_speech=d.get('part_of_speech'), review_status='proposed'))
            records[LexemeTranslation].append(dict(id=tid, lexeme_id=lid, language_code='fra', text=french))
            records[LexemeContent].append(dict(content_id=c.id, lexeme_id=lid, translation_id=tid))
            variants = d.get('synonyms', [])
            variants = variants if isinstance(variants, list) else [variants] if isinstance(variants, str) else []
            forms = [(latin, 'source', 'Latn')] + [(v, 'variant', 'Latn') for v in variants if isinstance(v, str) and v.strip()]
            if isinstance(d.get('tifinagh'), str) and d['tifinagh'].strip():
                label = 'generated' if d.get('tifinagh_status') == 'generated_pending_review' else 'provided_unverified'
                forms.append((d['tifinagh'], label, 'Tfng'))
            for text, kind, script in forms:
                text = nfc(text)
                norm = text.casefold()
                fid = digest(lid, script, norm)
                records[LexemeForm].append(dict(id=fid, lexeme_id=lid, script=script, text=text, normalized_form=norm, form_type=kind))
                records[FormEvidence].append(dict(content_id=c.id, form_id=fid))
        elif c.kind == 'phrase' and latin and french:
            sid = digest(c.variety or 'kab', 'Latn', latin)
            tid = digest(sid, 'fra', french)
            records[Sentence].append(dict(id=sid, language_code=c.variety or 'kab', text=latin, script='Latn'))
            records[SentenceTranslation].append(dict(id=tid, sentence_id=sid, language_code='fra', text=french))
            cefr = d.get('cefr_level')
            cefr = cefr if cefr in ('A1','A2','B1','B2','C1','C2') else None
            records[ContentSentence].append(dict(content_id=c.id, sentence_id=sid, translation_id=tid,
                token_count=len(tokens(latin)), cefr_level=cefr,
                cefr_status=('reviewed' if d.get('cefr_reviewed_at') else 'provided_unverified') if cefr else 'unassigned'))
            audio_data = d if isinstance(d.get('audios', []), list) else {**d, 'audios': []}
            for audio in usable_audios(audio_data):
                aid = digest(audio['url'], audio['author'], audio['license'])
                records[AudioRecording].append(dict(id=aid, url=audio['url'], author=audio['author'], license=audio['license'],
                    voice_kind=audio.get('voice_kind', 'unspecified'), metadata_json=audio))
                records[SentenceAudio].append(dict(content_id=c.id, sentence_id=sid, audio_id=aid))
    # Canonical lemma selection is deterministic and never overwrites a reviewed lexeme.
    if records[Lexeme]:
        lexemes = {}
        for row in records[Lexeme]:
            old = lexemes.get(row['id'])
            if old is None or (row['lemma_rank'], row['lemma']) < (old['lemma_rank'], old['lemma']): lexemes[row['id']] = row
        records[Lexeme] = list(lexemes.values())
    for model in (CorpusSource, SourceSnapshot): bulk(s, model, records[model])
    bulk(s, ContentProvenance, records[ContentProvenance], replace=('active',))
    if records[Lexeme]:
        stmt = insert(Lexeme).values(records[Lexeme])
        s.execute(stmt.on_conflict_do_update(index_elements=['id'],
            set_={'lemma': stmt.excluded.lemma, 'lemma_rank': stmt.excluded.lemma_rank, 'part_of_speech': stmt.excluded.part_of_speech},
            where=(Lexeme.review_status != 'validated') & ((stmt.excluded.lemma_rank < Lexeme.lemma_rank) | ((stmt.excluded.lemma_rank == Lexeme.lemma_rank) & (stmt.excluded.lemma.collate("C") <= Lexeme.lemma.collate("C"))))))
    for model in (LexemeForm, LexemeTranslation, LexemeContent, FormEvidence, Sentence, SentenceTranslation, ContentSentence, AudioRecording, SentenceAudio):
        bulk(s, model, records[model])
    s.execute(update(Content).where(Content.id.in_(ids)).values(structured_dirty=False))
    return len(rows)

def process_batch(s, size=500):
    # Prevent two normalizers from replacing associations for the same source row.
    s.execute(select(func.pg_advisory_xact_lock(714295311)))
    rows = list(s.scalars(select(Content).where(Content.structured_dirty.is_(True)).order_by(Content.id).limit(size).with_for_update()))
    if not rows: return {'processed': 0, 'remaining': 0, 'version': VERSION}
    job = s.scalar(select(OrganizationJob).where(OrganizationJob.status == 'running', OrganizationJob.pipeline_version == VERSION).order_by(OrganizationJob.started_at.desc()).limit(1))
    if not job:
        import uuid
        job = OrganizationJob(id=uuid.uuid4().hex, pipeline_version=VERSION, status='running', processed=0)
        s.add(job)
    count = project(s, rows)
    remaining = s.scalar(select(func.count()).where(Content.structured_dirty.is_(True)))
    job.processed += count
    job.updated_at = datetime.now(timezone.utc)
    job.status = 'completed' if remaining == 0 else 'running'
    s.commit()
    return {'processed': count, 'remaining': remaining, 'job_processed': job.processed, 'version': VERSION}

def run(s, report=print, size=500):
    total = 0
    while True:
        result = process_batch(s, size)
        total += result['processed']
        report(f"Organisation relationnelle : {total} fiches traitées ; {result['remaining']} restantes.")
        if not result['remaining']: return result

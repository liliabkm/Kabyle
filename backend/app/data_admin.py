"""Observable corpus organization status and bounded admin processing."""
from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from .models import Content
from .structured_models import CorpusSource, SourceSnapshot, Lexeme, Sentence, SentenceTranslation, AudioRecording, ContentProvenance, OrganizationJob, CourseLesson
from .data_pipeline import process_batch, VERSION
from .organization import TOPICS
from .structured_models import LexemeContent, LexemeForm, LexemeTranslation, FormEvidence, ContentSentence, SentenceAudio

class Batch(BaseModel):
    size: int = Field(default=500, ge=1, le=500)


def overview(s):
    count = lambda model: s.scalar(select(func.count()).select_from(model))
    pending = s.scalar(select(func.count()).where(Content.structured_dirty.is_(True)))
    return {'version': VERSION, 'content_total': count(Content), 'pending': pending,
        'indexed': count(Content) - pending,
        'sources': count(CorpusSource), 'snapshots': count(SourceSnapshot),
        'lexemes': s.scalar(select(func.count(func.distinct(LexemeContent.lexeme_id))).join(Content, Content.id == LexemeContent.content_id).where(Content.status != 'rejected')),
        'sentences': s.scalar(select(func.count(func.distinct(ContentSentence.sentence_id))).join(Content, Content.id == ContentSentence.content_id).where(Content.status != 'rejected')),
        'translations': s.scalar(select(func.count(func.distinct(ContentSentence.translation_id))).join(Content, Content.id == ContentSentence.content_id).where(Content.status != 'rejected')),
        'recordings': s.scalar(select(func.count(func.distinct(SentenceAudio.audio_id))).join(Content, Content.id == SentenceAudio.content_id).where(Content.status != 'rejected')), 'lessons': count(CourseLesson),
        'source_citations': count(ContentProvenance),
        'topics': [{'id': key, 'label': val[0]} for key, val in TOPICS.items()],
        'notice': 'Projection relationnelle du corpus. Les classements et niveaux proposés restent à relire. Les archives brutes ne sont pas créées rétroactivement par ce traitement.'}


def register_routes(app, db, admin):
    @app.get('/api/admin/data-structure', dependencies=[Depends(admin)])
    def stats(s=Depends(db)):
        return overview(s)

    @app.get('/api/admin/structured-lexicon', dependencies=[Depends(admin)])
    def lexicon(q: str = Query('', max_length=200), offset: int = Query(0, ge=0), s=Depends(db)):
        active = select(LexemeContent.lexeme_id).join(Content, Content.id == LexemeContent.content_id).where(Content.status != 'rejected')
        query = select(Lexeme).where(Lexeme.id.in_(active))
        if q.strip():
            from sqlalchemy import or_
            translations = select(LexemeTranslation.lexeme_id).where(LexemeTranslation.text.icontains(q.strip(), autoescape=True))
            query = query.where(or_(Lexeme.lemma.icontains(q.strip(), autoescape=True), Lexeme.id.in_(translations)))
        total = s.scalar(select(func.count()).select_from(query.subquery()))
        items = []
        for lexeme in s.scalars(query.order_by(Lexeme.lemma, Lexeme.id).offset(offset).limit(20)):
            form_ids = select(FormEvidence.form_id).join(Content, Content.id == FormEvidence.content_id).where(Content.status != 'rejected')
            tids = select(LexemeContent.translation_id).join(Content, Content.id == LexemeContent.content_id).where(Content.status != 'rejected')
            items.append({'id': lexeme.id, 'lemma': lexeme.lemma, 'part_of_speech': lexeme.part_of_speech,
                'review_status': lexeme.review_status,
                'forms': list(s.scalars(select(LexemeForm.text).where(LexemeForm.lexeme_id == lexeme.id, LexemeForm.id.in_(form_ids)).order_by(LexemeForm.text))),
                'translations': list(s.scalars(select(LexemeTranslation.text).where(LexemeTranslation.lexeme_id == lexeme.id, LexemeTranslation.id.in_(tids)).order_by(LexemeTranslation.text)))})
        return {'items': items, 'total': total}

    @app.post('/api/admin/data-structure/process', dependencies=[Depends(admin)])
    def process(body: Batch, s=Depends(db)):
        return process_batch(s, body.size)

"""Admin word laboratory: explainable classification and live corpus lookup."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
import re
import unicodedata
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func
from .models import Content
from .organization import TOPICS, organize, word_french, norm
from .learning import lexeme_key
from .search import pair_key
from .word_links import related, for_word, unique, vocabulary, array


class Pair(BaseModel):
    latin: str = Field(min_length=1, max_length=1000)
    french: str = Field(min_length=1, max_length=1000)

    @field_validator('latin', 'french')
    @classmethod
    def clean(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Le texte ne peut pas être vide.')
        return value


class WordEntry(Pair):
    latin: str = Field(min_length=1, max_length=200)
    french: str = Field(min_length=1, max_length=200)
    synonyms: list[str] = Field(default_factory=list, max_length=16)
    phrases: list[Pair] = Field(default_factory=list, max_length=20)
    category: str = Field(default='', max_length=60)

    @field_validator('synonyms')
    @classmethod
    def variants(cls, values):
        if any(not x.strip() or len(x) > 200 for x in values):
            raise ValueError('Chaque variante doit contenir entre 1 et 200 caractères.')
        return unique(values)

    @field_validator('category')
    @classmethod
    def valid_category(cls, value):
        if value and value not in TOPICS:
            raise ValueError('Catégorie inconnue.')
        return value


@lru_cache(maxsize=1)
def hints():
    data = json.loads((Path(__file__).resolve().parents[2] / 'content/catalog/word-category-hints.json').read_text())
    index = {}
    for theme, words in data['topics'].items():
        for word in words:
            index.setdefault(word_french(word), set()).add(theme)
    index.setdefault('avocat', set()).update(['fruits', 'metiers'])
    index.setdefault('peche', set()).update(['fruits', 'actions'])
    return index


def signature(data):
    return hashlib.sha256((data['latin'].strip() + '\0' + data['french'].strip()).encode()).hexdigest()


def matches(pair, data, concept=None):
    forms, glosses = vocabulary(data, concept)
    def contains(text, alternatives, french=False):
        clean = norm if french else lambda x: unicodedata.normalize('NFC', x).casefold()
        return any(re.search(r'(?<!\w)' + re.escape(clean(x)) + r'(?!\w)', clean(text)) for x in alternatives)
    return contains(pair.latin, forms) and contains(pair.french, glosses, french=True)



def classify(s, entry, existing_matches):
    data = entry.model_dump(exclude={'phrases', 'category'})
    decision = organize('word', data)
    if decision['role'] in ('review', 'fragment'):
        return {'theme': 'a-revoir', 'confidence': 'uncertain', 'reason': decision['reason'], 'candidates': ['a-revoir']}
    if entry.category:
        return {'theme': entry.category, 'confidence': 'manual', 'reason': 'Catégorie choisie dans cet essai.', 'candidates': [entry.category]}
    gloss = word_french(entry.french)
    candidates = hints().get(gloss, set()) or (hints().get(gloss[:-1], set()) if gloss.endswith('s') else set())
    if len(candidates) > 1:
        return {'theme': 'autres-mots', 'confidence': 'uncertain', 'reason': 'Plusieurs sens possibles : choisis une catégorie.', 'candidates': sorted(candidates)}
    if decision['topics'][0] not in ('autres-mots', 'a-revoir'):
        return {'theme': decision['topics'][0], 'confidence': 'dictionary', 'reason': decision['reason'], 'candidates': decision['topics']}
    if candidates:
        return {'theme': next(iter(candidates)), 'confidence': 'dictionary', 'reason': 'Traduction reconnue dans le dictionnaire de catégories.', 'candidates': sorted(candidates)}
    # Reuse reviewed/imported vocabulary with exactly the same French sense.
    peers = s.scalars(select(Content).where(Content.kind == 'word', Content.status != 'rejected', Content.search_text.contains(gloss, autoescape=True)).limit(100))
    known = {c.theme for c in peers if word_french(c.data.get('french', '')) == gloss and c.theme in TOPICS and c.theme not in ('autres-mots', 'a-revoir')}
    if len(known) == 1:
        theme = next(iter(known))
        return {'theme': theme, 'confidence': 'existing_word', 'reason': 'Même traduction qu’un mot déjà classé dans la base.', 'candidates': [theme]}
    votes = Counter()
    for row in existing_matches['items']:
        for theme in row['topics'][:1]:
            if theme in TOPICS and theme not in ('autres-phrases', 'a-revoir', 'grammaire'):
                votes[theme] += 1
    for pair in entry.phrases:
        if matches(pair, data, decision['concept']):
            theme = organize('phrase', pair.model_dump())['topics'][0]
            if theme not in ('autres-phrases', 'a-revoir', 'grammaire'):
                votes[theme] += 1
    if votes:
        theme, count = votes.most_common(1)[0]
        if count >= 2 and count / sum(votes.values()) >= .8:
            return {'theme': theme, 'confidence': 'context', 'reason': f'Contexte concordant de {count} phrases ; classement à vérifier.', 'candidates': list(votes)}
    return {'theme': 'autres-mots', 'confidence': 'uncertain', 'reason': 'Pas assez d’indices fiables. Le mot peut être enregistré et sa catégorie corrigée.', 'candidates': list(votes)}


def inspect_entry(s, entry):
    data = entry.model_dump(exclude={'phrases', 'category'})
    decision = organize('word', data)
    found = related(s, data, decision['concept'], limit=12)
    classification = classify(s, entry, found)
    hint_version = hashlib.sha256((Path(__file__).resolve().parents[2] / 'content/catalog/word-category-hints.json').read_bytes()).hexdigest()[:8]
    classification['engine_version'] = decision['version'] + ';glossary:' + hint_version
    return {'classification': {**classification, 'label': TOPICS[classification['theme']][0]},
            'existing_phrases': found,
            'provided_phrases': [{**p.model_dump(), 'matches': matches(p, data, decision['concept'])} for p in entry.phrases],
            'categories': [{'id': k, 'label': v[0]} for k, v in TOPICS.items()],
            'notice': 'Associations proposées par présence du mot kabyle et du sens français. Variantes non renseignées non devinées.'}


def transaction_lock(s, key):
    # Serialize matching admin additions, including concurrent duplicate clicks.
    raw = int(hashlib.sha256(key.encode()).hexdigest()[:16], 16)
    signed = raw if raw < 2**63 else raw - 2**64
    s.execute(select(func.pg_advisory_xact_lock(signed)))


def save(s, entry):
    # Same lock as the batch normalizer: keep the immediate projection atomic.
    s.execute(select(func.pg_advisory_xact_lock(714295311)))
    transaction_lock(s, 'word:' + lexeme_key(entry.latin) + ':' + word_french(entry.french))
    preview = inspect_entry(s, entry)
    if any(not p['matches'] for p in preview['provided_phrases']):
        raise HTTPException(422, 'Chaque phrase facultative doit contenir le mot kabyle (ou une variante renseignée) et sa traduction française.')
    classification = preview['classification']
    data = entry.model_dump(exclude={'phrases', 'category'})
    peers = list(s.scalars(select(Content).where(Content.kind == 'word', Content.lexeme_key == lexeme_key(entry.latin))))
    word = next((c for c in peers if word_french(c.data.get('french', '')) == word_french(entry.french)), None)
    word_created = word is None
    now = datetime.now(timezone.utc).isoformat()
    if word and word.status == 'rejected':
        raise HTTPException(409, 'Ce mot a été rejeté. Corrige sa fiche dans la bibliothèque admin.')
    if word is None:
        identifier = 'word-admin-' + signature(data)[:24]
        data.update(sources=[], category_status='suggested', validation_status='pending_review',
                    created_by='admin-word-laboratory', created_at=now,
                    automatic_organization={**classification, 'input_key': signature(data)})
        if entry.category:
            data.update(category_status='editorial', category_reviewed_at=now)
        word = Content(id=identifier, kind='word', script='Latn', variety='kab', theme=classification['theme'], status='draft', data=data)
        s.add(word)
    elif entry.synonyms:
        word.data = {**word.data, 'synonyms': unique(array(word.data.get('synonyms', [])) + entry.synonyms)}
    s.flush()
    added, duplicates = 0, 0
    for pair in sorted(entry.phrases, key=lambda p: pair_key('phrase', p.model_dump())):
        d = pair.model_dump()
        key = pair_key('phrase', d)
        transaction_lock(s, 'phrase:' + key)
        existing = s.scalar(select(Content).where(Content.kind == 'phrase', Content.pair_key == key).limit(1))
        if existing:
            duplicates += 1
            continue
        d.update(sources=[], created_by='admin-word-laboratory', created_at=now,
                 category_status='suggested', validation_status='pending_review',
                 word_entry_topics=[word.theme] if word.theme not in ('autres-mots', 'a-revoir') else [])
        s.add(Content(id='phrase-admin-' + key[:24], kind='phrase', script='Latn', variety='kab', theme=word.theme, status='draft', data=d))
        s.flush()
        added += 1
    from .data_pipeline import project
    keys = [word.id] + ['phrase-admin-' + pair_key('phrase', p.model_dump())[:24] for p in entry.phrases]
    changed = list(s.scalars(
        select(Content).where(Content.id.in_(keys)).order_by(Content.id).with_for_update()
    ))
    project(s, changed)
    s.commit()
    result = for_word(s, word.id)
    if not word_created:
        preview['classification'] = {**preview['classification'], 'theme': word.theme, 'label': TOPICS.get(word.theme, (word.theme, ''))[0], 'reason': 'Fiche existante conservée ; son classement et ses corrections ne sont pas écrasés.'}
    return {**preview, 'word_id': word.id, 'word_created': word_created, 'theme': word.theme,
            'phrases_added': added, 'phrase_duplicates': duplicates, 'related_phrases': result,
            'status': word.status}


def register_routes(app, db, admin):
    @app.post('/api/admin/word-laboratory/preview', dependencies=[Depends(admin)])
    def preview(body: WordEntry, s=Depends(db)):
        return inspect_entry(s, body)

    @app.post('/api/admin/word-laboratory/save', dependencies=[Depends(admin)])
    def commit(body: WordEntry, s=Depends(db)):
        return save(s, body)

    @app.get('/api/words/{word_id}/phrases')
    def linked(word_id: str, offset: int = Query(0, ge=0), limit: int = Query(12, ge=1, le=36), audio_only: bool = False, s=Depends(db)):
        return for_word(s, word_id, offset, limit, audio_only)

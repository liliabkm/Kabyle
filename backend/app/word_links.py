"""Live bilingual word/phrase matching; no generated translations or guessed stems."""
import re
import unicodedata
from fastapi import HTTPException
from sqlalchemy import select, func, or_
from .models import Content
from .organization import concepts, word_french, source_span
from .search import fold
from .learning import usable_audios

ACCENTS = 'àâäáãåéèêëíìîïóòôöõúùûüýÿçñ'
PLAIN = ''.join(unicodedata.normalize('NFKD', c)[0] for c in ACCENTS)


def unique(values):
    return list(dict.fromkeys(v.strip() for v in values if isinstance(v, str) and v.strip()))


def boundaries(values):
    return r'(^|[^[:alnum:]_])(' + '|'.join(re.escape(v) for v in values) + r')($|[^[:alnum:]_])'


def array(value):
    return value if isinstance(value, list) else [value] if isinstance(value, str) else []


def vocabulary(data, concept=None):
    forms = unique([data.get('latin', '')] + array(data.get('synonyms', [])))
    translations = unique([data.get('french', '')] + array(data.get('french_variants', [])))
    if concept in concepts():
        translations += concepts()[concept]['aliases']
    glosses = unique([word_french(x) for x in translations])
    # Regular French plural only; Kabyle inflections are never invented.
    glosses += [x + 's' for x in glosses if len(x) > 2 and not x.endswith(('s', 'x'))]
    return forms, unique(glosses)


def matching_query(data, concept=None):
    forms, glosses = vocabulary(data, concept)
    if not forms or not glosses:
        raise HTTPException(422, 'Un mot kabyle et sa traduction française sont requis.')
    french = func.translate(func.lower(Content.data['french'].as_string()), ACCENTS, PLAIN)
    query = select(Content).where(
        Content.kind == 'phrase', Content.status != 'rejected',
        # Coarse candidate check followed by exact bilingual word boundaries.
        or_(*[Content.search_text.contains(fold(v), autoescape=True) for v in forms]),
        Content.data['latin'].as_string().op('~*')(boundaries(forms)),
        french.op('~*')(boundaries(glosses)),
    )
    return query, forms


def payload(c, forms):
    audios = usable_audios(c.data)
    return {'id': c.id, 'latin': c.data['latin'], 'french': c.data['french'],
            'status': c.status, 'has_audio': bool(audios), 'audios': audios,
            'highlight': source_span(c.data['latin'], forms),
            'topics': c.topic_keys, 'concepts': c.matched_concepts,
            'association_status': 'automatic_bilingual_match'}


def related(s, data, concept=None, offset=0, limit=12, audio_only=False):
    query, forms = matching_query(data, concept)
    if audio_only:
        query = query.where(Content.has_audio.is_(True))
    total = s.scalar(select(func.count()).select_from(query.subquery()))
    rows = s.scalars(query.order_by(func.length(Content.data['latin'].as_string()), Content.id)
                     .offset(offset).limit(limit))
    return {'items': [payload(c, forms) for c in rows], 'total': total}


def for_word(s, word_id, offset=0, limit=12, audio_only=False):
    word = s.get(Content, word_id)
    if not word or word.kind != 'word' or word.status == 'rejected':
        raise HTTPException(404, 'Mot introuvable')
    data = dict(word.data)
    forms = array(data.get('synonyms', []))
    if word.concept_key:
        for item in s.scalars(select(Content).where(Content.kind == 'word', Content.status != 'rejected', Content.concept_key == word.concept_key)):
            forms = forms + [item.data['latin']] + array(item.data.get('synonyms', []))
    data['synonyms'] = unique(forms)
    return related(s, data, word.concept_key, offset, limit, audio_only)

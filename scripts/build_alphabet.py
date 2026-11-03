#!/usr/bin/env python3
"""Build reproducible letter examples from the sourced LibreLingo catalog.

Tifinagh examples are mechanical transliterations, not attested source spellings.
No unknown character is silently discarded or guessed.
"""
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.organization import organize

LATIN = 'a b c č d ḍ e ɛ f g ǧ ɣ h ḥ i j k l m n q r ṛ s ṣ t ṭ u w x y z ẓ'.split()
GLYPHS = 'ⴰ ⴱ ⵛ ⵞ ⴷ ⴹ ⴻ ⵄ ⴼ ⴳ ⴵ ⵖ ⵀ ⵃ ⵉ ⵊ ⴽ ⵍ ⵎ ⵏ ⵇ ⵔ ⵕ ⵙ ⵚ ⵜ ⵟ ⵓ ⵡ ⵅ ⵢ ⵣ ⵥ'.split()
MAPPING = dict(zip(LATIN, GLYPHS))
MAPPING['ʷ'] = 'ⵯ'
CONVENTION = 'kab-latin-tfng-v1'

def transliterate(text):
    result = []
    for c in unicodedata.normalize('NFC', text).casefold():
        if c in MAPPING:
            result.append(MAPPING[c])
        elif not c.isalpha():
            result.append(c)
        else:
            raise ValueError(f'Caractère sans correspondance : {c}')
    return ''.join(result)


def build():
    old = {c['data']['latin']: c for c in json.loads((ROOT / 'content/alphabet.json').read_text())}
    words = json.loads((ROOT / 'content/catalog/course-words.json').read_text())
    eligible = []
    for item in words:
        d = item['data']
        if item['kind'] == 'word' and organize('word', d)['role'] != 'word':
            continue
        try:
            tfng = transliterate(d['latin'])
        except ValueError:
            continue
        eligible.append({
            'content_id': item['id'], 'kind': item['kind'],
            'latin': d['latin'], 'french': d['french'], 'tifinagh': tfng,
            'tifinagh_status': 'generated_pending_review',
            'convention': CONVENTION, 'sources': d['sources'],
            'entry_origin': d.get('entry_origin'),
        })
    eligible = [e for e in eligible if e['french'] not in ('vin', 'bière')]
    letters = []
    for i, (latin, glyph) in enumerate(zip(LATIN, GLYPHS)):
        item = old.get(latin, {'id': f'letter-u{ord(glyph):04x}', 'kind': 'letter',
            'variety': 'kab', 'script': 'Tfng', 'theme': 'alphabet', 'status': 'draft', 'data': {}})
        examples = []
        for kind, count in [('word', 8)]:
            candidates = [e for e in eligible if e['kind'] == kind and unicodedata.normalize('NFC', e['latin']).casefold().startswith(latin)]
            candidates.sort(key=lambda e: (e.get('entry_origin') != 'new_words' if kind == 'word' else False, not e['latin'].casefold().startswith(latin), len(e['latin'].split()), len(e['latin']), e['content_id']))
            examples.extend(candidates[:count])
        d = item['data']
        d.update(latin=latin, tifinagh=glyph, french=f'La lettre {latin.upper()}',
            alphabet_order=i, convention=CONVENTION, examples=examples,
            unicode_name=unicodedata.name(glyph), unicode_codepoint=f'U+{ord(glyph):04X}',
            example_notice='Écriture tifinagh générée depuis le kabyle latin ; à vérifier. Traductions conservées de la source.',
            sources=[{'url': 'https://www.unicode.org/charts/PDF/U2D30.pdf', 'author': 'Unicode Consortium', 'license': 'Unicode License v3 — noms et propriétés des caractères'},
                {'url': 'https://github.com/salimadour31-boop/illustrator-tifinagh-latin', 'author': 'Amirouche Amwanes', 'license': 'MIT — référence de correspondances'}])
        if not d.get('hint'):
            d['hint'] = f'Correspondance de lecture : {latin} → {glyph}. La prononciation kabyle reste à vérifier avec un locuteur.'
        letters.append(item)
    (ROOT / 'content/alphabet.json').write_text(json.dumps(letters, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(letters)} lettres ; {sum(len(x["data"]["examples"]) for x in letters)} exemples liés. Tifinagh généré, non validé linguistiquement.')

if __name__ == '__main__':
    build()

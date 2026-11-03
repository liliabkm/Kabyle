"""Content integrity and known transliteration examples, independent of DB."""
import json
import runpy
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = runpy.run_path(str(ROOT / 'scripts/build_alphabet.py'))


def test_known_words_and_normalization():
    convert = MODULE['transliterate']
    assert convert('Azul') == 'ⴰⵣⵓⵍ'
    assert convert('taqbaylit') == 'ⵜⴰⵇⴱⴰⵢⵍⵉⵜ'
    assert convert('tifinaɣ') == 'ⵜⵉⴼⵉⵏⴰⵖ'
    assert convert('D\u0323') == 'ⴹ'
    assert convert('gʷ') == 'ⴳⵯ'
    with pytest.raises(ValueError):
        convert('école')


def test_letter_coverage_sources_and_no_claim_of_attested_tifinagh():
    letters = json.loads((ROOT / 'content/alphabet.json').read_text())
    assert len(letters) == 33
    assert len({x['id'] for x in letters}) == 33
    assert [x['data']['latin'] for x in letters] == MODULE['LATIN']
    catalog = {}
    for name in ('course-words', 'course-phrases'):
        catalog.update({x['id']: x for x in json.loads((ROOT / f'content/catalog/{name}.json').read_text())})
    for letter in letters:
        d = letter['data']
        assert d['examples'], d['latin']
        for e in d['examples']:
            source = catalog[e['content_id']]['data']
            assert (e['latin'], e['french']) == (source['latin'], source['french'])
            assert d['latin'] in e['latin'].casefold()
            assert e['tifinagh_status'] == 'generated_pending_review'
            assert e['sources'] == source['sources']
            assert 'ⴰ' <= e['tifinagh'][0] <= '⵿' or not e['tifinagh'][0].isalpha()

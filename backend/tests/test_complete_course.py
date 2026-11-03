import json
from pathlib import Path
from app.catalog import seed_complete_course
from app.db import Session
from app.library import library_payload
ROOT=Path(__file__).resolve().parents[2]/'content/catalog'
def test_complete_course_and_scalar_variants():
    report=json.loads((ROOT/'course-report.json').read_text())
    assert len(report['files'])==15 and report['failed_files']==[]
    assert report['ignored_entries']==0 and report['mini_dictionary_pairs']==986
    assert any(x['path']=='course/juniors/skills/nombres_jr.yaml' for x in report['files'])
    words=json.loads((ROOT/'course-words.json').read_text())
    three=next(w for w in words if w['data']['latin']=='kraḍ')
    assert three['data']['synonyms']==['tlata'] and three['theme']=='nombres'
    eight=next(w for w in words if w['data']['latin']=='ṭam')
    assert eight['data']['french']=='un ours' and eight['data']['source_issues']
    assert all(w['theme'] and w['data']['sources'] for w in words)
def test_complete_seed_is_repeatable():
    with Session() as s:
        result=seed_complete_course(s);s.commit()
        assert result=={'course_words_added':0,'course_phrases_added':0,'source_metadata_refreshed':0}
        found=library_payload(s,'word','nombres','yiwen',0,24)
        assert any(w['latin']=='yiwen' and w['french']=='un' for w in found['items'])

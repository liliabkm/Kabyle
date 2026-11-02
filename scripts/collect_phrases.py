"""Optional source tooling: collect all parseable active-course phrases as drafts."""
from pathlib import Path
import argparse,hashlib,json,subprocess,yaml
parser=argparse.ArgumentParser();parser.add_argument('--source-checkout',type=Path,required=True);args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];source=args.source_checkout.resolve();revision='e426e0fa052da1c91b6efd800d8469e6940757d5'
if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=revision:raise SystemExit('Source revision must be audited before importing')
existing=json.loads((ROOT/'content/catalog/preview-phrases.json').read_text())
lookup={(p['data']['latin'],p['data']['french']):p for p in existing}
rows={};skipped=[]
for path in sorted(source.glob('course/**/skills/*.yaml')):
    if path.parts[-3]=='juniors' or path.stem=='test_jr':continue
    try:data=yaml.safe_load(path.read_text())
    except yaml.YAMLError:skipped.append(path.relative_to(source).as_posix());continue
    for i,phrase in enumerate(data.get('Phrases',[]) or []):
        latin=phrase.get('Phrase');french=phrase.get('Translation')
        if not isinstance(latin,str) or not isinstance(french,str) or not latin.strip() or not french.strip():continue
        latin=latin.strip();french=french.strip();key=(latin,french);relative=path.relative_to(source).as_posix()
        if key not in rows:
            if key in lookup:rows[key]=lookup[key]
            else:rows[key]={'id':'phrase-ll-'+hashlib.sha256((latin+'\0'+french).encode()).hexdigest()[:16],'kind':'phrase','variety':'kab','script':'Latn','theme':'vie-quotidienne','status':'draft','data':{'latin':latin,'french':french,'tifinagh':'','alternative_versions':phrase.get('Alternative versions',[]),'sources':[],'validation_status':'source_attested_not_reviewed','license_conflict':True,'publication_blockers':['Relecture linguistique et pédagogique requise','Licence du cours à clarifier : BY-NC-SA / BY-SA']}}
        evidence={'url':f'https://github.com/LibreLingo/LibreLingo-KAB-from-FR/blob/{revision}/{relative}','author':'Bouaziz Ait Driss et contributeurs LibreLingo-KAB-from-FR','license':'CC-BY-NC-SA-4.0','license_url':'https://creativecommons.org/licenses/by-nc-sa/4.0/','revision':revision,'source_section':'Phrases','source_index':i,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'changes':'Extraction sans réécriture ; espaces de bord retirés.'}
        if not any(s.get('url')==evidence['url'] and s.get('source_index')==i for s in rows[key]['data']['sources']):rows[key]['data']['sources'].append(evidence)
(ROOT/'content/catalog/phrases-librelingo.json').write_text(json.dumps(list(rows.values()),ensure_ascii=False,indent=2)+'\n')
report={'phrases':len(rows),'skipped_invalid_yaml':skipped,'source_revision':revision,'published':0}
(ROOT/'content/catalog/phrases-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))

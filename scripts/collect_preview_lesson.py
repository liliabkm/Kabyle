"""Optional source tooling; requires scripts/requirements-data.txt. Never publishes data."""
from pathlib import Path
import json,yaml,hashlib,copy
import argparse,subprocess
parser=argparse.ArgumentParser(description="Extract the three attested word/phrase contexts for a private preview")
parser.add_argument('--source-checkout', type=Path, required=True)
args=parser.parse_args()
r=Path(__file__).resolve().parents[1];root=args.source_checkout.resolve();sha='e426e0fa052da1c91b6efd800d8469e6940757d5'
if subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()!=sha:
 raise SystemExit('Unexpected source revision; audit it before collecting')
words=json.loads((r/'content/catalog/words-librelingo.json').read_text());lookup={w['data']['latin']:w for w in words}
selected=[lookup[s] for s in ['aqjun','agmar','tizwal uṛumi']]
phrases=[]
for key,word,path,french in [('dog',selected[0],'course/basics/skills/animals.yaml','Max est un chien'),('horse',selected[1],'course/basics/skills/animals.yaml',"C'est un cheval"),('strawberry',selected[2],'course/basics/skills/plurals.yaml','Les fraises sont rouges')]:
 source=yaml.safe_load((root/path).read_text());idx,p=next((i,p) for i,p in enumerate(source['Phrases']) if p['Translation']==french)
 data={'latin':p['Phrase'].strip(),'french':p['Translation'],'tifinagh':'','alternative_versions':p.get('Alternative versions',[]),'sources':[{'url':f'https://github.com/LibreLingo/LibreLingo-KAB-from-FR/blob/{sha}/{path}','author':'Bouaziz Ait Driss et contributeurs LibreLingo-KAB-from-FR','license':'CC-BY-NC-SA-4.0','license_url':'https://creativecommons.org/licenses/by-nc-sa/4.0/','revision':sha,'source_index':idx,'source_section':'Phrases','source_sha256':hashlib.sha256((root/path).read_bytes()).hexdigest(),'changes':'Extraction sans réécriture, espaces de fin retirés.'}],'license_conflict':True,'publication_blockers':['Licence du cours à clarifier : BY-NC-SA / BY-SA','Relecture linguistique et pédagogique requise'],'validation_status':'source_attested_not_reviewed','target_word_id':word['id']}
 assert word['data']['latin'].casefold() in data['latin'].casefold()
 phrases.append({'id':'phrase-ll-preview-'+key,'kind':'phrase','variety':'kab','script':'Latn','theme':'premiers-mots','status':'draft','data':data})
(r/'content/catalog/preview-phrases.json').write_text(json.dumps(phrases,ensure_ascii=False,indent=2)+'\n')
exercises=[]
for i,w in enumerate(selected):exercises.append({'id':'recognize-'+str(i),'type':'recognize','content_id':w['id']})
for i,p in enumerate(phrases):exercises.append({'id':'order-'+str(i),'type':'order','content_id':p['id']})
exercises.extend([{'id':'cloze-fruit','type':'cloze','content_id':phrases[2]['id'],'word_id':selected[2]['id']},{'id':'recall-dog','type':'recall','content_id':selected[0]['id']}])
lesson={'id':'premiers-mots','title':'Mes premiers mots','theme':'decouverte','status':'draft','data':{'word_ids':[w['id'] for w in selected],'phrase_ids':[p['id'] for p in phrases],'media':{selected[0]['id']:{'illustration':'dog'},selected[1]['id']:{'illustration':'horse'},selected[2]['id']:{'asset_id':'photo-fruits360-fraise','repeat':3}},'exercises':exercises,'scope':'private_noncommercial_preview','notice':'Aperçu privé en relecture. Les textes ne sont pas publiés dans les leçons apprenants. Aucun audio ni tifinagh généré.','learning_objectives':['Associer une image et un mot','Retrouver un mot dans une phrase','Reconstruire une phrase source','Retrouver un mot sans le regarder'],'method_sources':['https://github.com/LibreLingo/LibreLingo/blob/3c4bcfb3ef999ae48ee3d361afb0c4a5fa317dee/docs/courses/challenge.md','https://github.com/ankitects/anki-manual/blob/91f7485236db2a89d2a8abaed618976caf971de2/src/studying.md']}}
lesson['data']['method_sources'][0]='https://github.com/LibreLingo/LibreLingo/blob/3c4bcfb3ef999ae48ee3d361afb0c4a5fa317dee/docs/courses/challenge.md'
(r/'content/catalog/vocabulary-lessons.json').write_text(json.dumps([lesson],ensure_ascii=False,indent=2)+'\n')
print('Prepared',len(selected),'existing words,',len(phrases),'attested phrases,',len(exercises),'preview exercises')

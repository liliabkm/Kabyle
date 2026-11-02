"""Source collector, optional tooling: install scripts/requirements-data.txt first. All words remain drafts."""
from pathlib import Path
import hashlib,json,yaml,subprocess,shutil,urllib.request,urllib.parse,concurrent.futures,struct
import argparse
parser=argparse.ArgumentParser(description="Collect immutable, attributed draft vocabulary and photo sources")
parser.add_argument('--source-checkout', type=Path, required=True)
args=parser.parse_args()
r=Path(__file__).resolve().parents[1];src=args.source_checkout.resolve();commit=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()
if commit != 'e426e0fa052da1c91b6efd800d8469e6940757d5':
 raise SystemExit('Unexpected source revision: audit a new revision before importing it')
for directory in ('catalog', 'licenses', 'photos/fruits360'):
 (r/'content'/directory).mkdir(parents=True,exist_ok=True)
source_repo='https://github.com/LibreLingo/LibreLingo-KAB-from-FR'
themes={'animals':'animaux','clothes':'vetements','food':'alimentation','nature':'nature','plurals':'pluriels','professions':'metiers','adjectives':'adjectifs','preferences':'vie-quotidienne'}
words={};skipped=[]
for p in sorted(src.glob('course/**/skills/*.yaml')):
 if p.parts[-3]=='juniors' or p.stem=='test_jr':continue
 try:d=yaml.safe_load(p.read_text())
 except yaml.YAMLError:skipped.append(p.relative_to(src).as_posix());continue
 for i,w in enumerate(d.get('New words',[]) or []):
  if not isinstance(w,dict) or not isinstance(w.get('Word'),str) or not isinstance(w.get('Translation'),str):continue
  latin=w['Word'].strip();french=w['Translation'].strip();key=latin.casefold()
  relative=p.relative_to(src).as_posix();source={'url':f'{source_repo}/blob/{commit}/{relative}','author':'Bouaziz Ait Driss et contributeurs LibreLingo-KAB-from-FR','license':'CC-BY-NC-SA-4.0','license_url':'https://creativecommons.org/licenses/by-nc-sa/4.0/','license_evidence':f'{source_repo}/blob/{commit}/LICENSE','revision':commit,'source_path':relative,'source_index':i,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'changes':'Extraction et regroupement des entrées par graphie latine ; traductions conservées sans réécriture.'}
  if key not in words:
   words[key]={'id':'word-ll-'+hashlib.sha256(key.encode()).hexdigest()[:16],'kind':'word','variety':'kab','script':'Latn','theme':themes.get(p.stem,'vie-quotidienne'),'status':'draft','data':{'latin':latin,'french':french,'french_variants':[],'tifinagh':'','synonyms':[],'sources':[],'images':[],'audios':[],'examples':[],'source_image_ids':[],'validation_status':'source_attested_not_reviewed','license_conflict':True,'publication_blockers':['Relecture linguistique kabyle requise','Transcription tifinaghe absente','Association photo à valider','Licence à clarifier : LICENSE indique BY-NC-SA, course.yaml indique BY-SA'],'license_notice':'Usage commercial non autorisé sans clarification. Données extraites pour étude et relecture, non publiées dans les leçons.'}}
  item=words[key]['data']
  if french not in item['french_variants']:item['french_variants'].append(french)
  item['sources'].append(source)
  for alias in w.get('Synonyms',[]) or []:
   if isinstance(alias,str) and alias not in item['synonyms']:item['synonyms'].append(alias)
  for iid in w.get('Images',[]) or []:
   if iid not in item['source_image_ids']:item['source_image_ids'].append(iid)
# No inferred translations, examples, pronunciations, or script conversions.
(r/'content/catalog/words-librelingo.json').write_text(json.dumps(list(words.values()),ensure_ascii=False,indent=2)+'\n')
shutil.copyfile(src/'LICENSE',r/'content/licenses/librelingo-LICENSE.txt');shutil.copyfile(src/'course/course.yaml',r/'content/licenses/librelingo-course-metadata.yaml')
fruits_commit='bed1c24ee70de1569272de3882fbde88211c08b5'
subjects=[('pomme','pomme','Apple Golden 1','fruits'),('poire','poire','Pear 1','fruits'),('banane','banane','Banana 1','fruits'),('orange','orange','Orange 1','fruits'),('citron','citron','Lemon 1','fruits'),('fraise','fraise','Strawberry 1','fruits'),('raisin','raisin','Grape White 1','fruits'),('peche','pêche','Peach 1','fruits'),('abricot','abricot','Apricot 1','fruits'),('prune','prune','Plum 1','fruits'),('figue','figue','Fig 1','fruits'),('grenade','grenade','Pomegranate 1','fruits'),('pasteque','pastèque','Watermelon 1','fruits'),('melon','melon','Cantaloupe 1','fruits'),('clementine','clémentine','Clementine 1','fruits'),('datte','datte','Dates 1','fruits'),('kiwi','kiwi','Kiwi 1','fruits'),('ananas','ananas','Pineapple 1','fruits'),('cerise','cerise','Cherry 1','fruits'),('coing','coing','Quince 1','fruits'),('carotte','carotte','Carrot 1','legumes'),('tomate','tomate','Tomato 1','legumes'),('pomme-de-terre','pomme de terre','Potato White 1','legumes'),('oignon','oignon','Onion White 1','legumes'),('aubergine','aubergine','Eggplant 1','legumes'),('concombre','concombre','Cucumber 1','legumes'),('courgette','courgette','Zucchini 1','legumes'),('chou-fleur','chou-fleur','Cauliflower 1','legumes'),('poivron','poivron','Pepper Red 1','legumes'),('betterave','betterave','Beetroot 1','legumes')]
photo_path=r/'content/catalog/photos-fruits360.json'
previous={p['id']:p for p in json.loads(photo_path.read_text())} if photo_path.exists() else {}
source_filenames={'Clementine 1':'10_100.jpg','Carrot 1':'r0_0_100.jpg','Potato White 1':'113_100.jpg','Zucchini 1':'r0_0_100.jpg','Cucumber 1':'r0_0_100.jpg','Pepper Red 1':'100_100.jpg'}
def download(subject):
 id,label,category,theme=subject
 existing=previous.get('photo-fruits360-'+id)
 if existing and existing['data']['revision']==fruits_commit:
  path=r/'content/photos'/existing['data']['storage_key']
  if path.exists():
   if hashlib.sha256(path.read_bytes()).hexdigest()!=existing['data']['sha256']:
    raise ValueError('Existing photo checksum mismatch; refusing to overwrite: '+id)
   return existing
 relative='Training/'+category+'/'+source_filenames.get(category,'0_100.jpg');encoded=urllib.parse.quote(relative)
 url=f'https://raw.githubusercontent.com/fruits-360/fruits-360-100x100/{fruits_commit}/{encoded}'
 data=urllib.request.urlopen(url,timeout=40).read()
 if not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):raise ValueError('Not a JPEG: '+id)
 key=f'fruits360/{id}.jpg';(r/'content/photos'/key).write_bytes(data)
 return {'id':'photo-fruits360-'+id,'kind':'photo','theme':theme,'label_fr':label,'status':'available','data':{'url':'/api/media/'+key,'storage_key':key,'source_url':url,'page_url':f'https://github.com/fruits-360/fruits-360-100x100/blob/{fruits_commit}/{encoded}','author':'Mihai Oltean','license':'CC-BY-SA-4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/','license_evidence':f'https://github.com/fruits-360/fruits-360-100x100/blob/{fruits_commit}/README.md#license','attribution':'Mihai Oltean — Fruits-360 — CC BY-SA 4.0. Photo inchangée.','changes':'Aucune modification des pixels ; fichier renommé pour le stockage local.','revision':fruits_commit,'source_category':category,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'width':100,'height':100,'mime_type':'image/jpeg','caption_status':'Catégorie du dataset traduite en français ; association à un mot kabyle non effectuée'}}
photos=[];failures=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 futures={pool.submit(download,s):s for s in subjects}
 for future in concurrent.futures.as_completed(futures):
  try:photos.append(future.result())
  except Exception as e:failures.append({'subject':futures[future][0],'error':str(e)})
photos.sort(key=lambda p:p['id'])
(r/'content/catalog/photos-fruits360.json').write_text(json.dumps(photos,ensure_ascii=False,indent=2)+'\n')
license_path=r/'content/licenses/fruits360-README.md'
if license_path.exists(): license_raw=license_path.read_bytes()
else: license_raw=urllib.request.urlopen(f'https://raw.githubusercontent.com/fruits-360/fruits-360-100x100/{fruits_commit}/README.md',timeout=40).read()
if hashlib.sha256(license_raw).hexdigest()!='a8a45bab4b936710c71c8b6d923241f3411816da27bf45e0a5de3128ed30941e': raise ValueError('License evidence checksum mismatch')
license_path.write_bytes(license_raw)
report={'words':len(words),'photos':len(photos),'skipped_invalid_yaml':skipped,'photo_failures':failures,'published_words':0,'word_source_revision':commit,'photo_source_revision':fruits_commit}
(r/'content/catalog/import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
if failures:raise SystemExit(1)

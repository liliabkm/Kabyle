"""Collect the complete pinned LibreLingo course, including juniors and mini-dictionaries.

Only YAML formatting tabs and brace markup are normalized. No translation is generated.
Optional tooling: scripts/requirements-data.txt.
"""
from pathlib import Path
import argparse,copy,hashlib,json,subprocess,unicodedata,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"backend"))
from app.library import suggested_category
import yaml
REV='e426e0fa052da1c91b6efd800d8469e6940757d5'
BASE='https://github.com/LibreLingo/LibreLingo-KAB-from-FR/blob/'+REV+'/'
THEMES={'animals':'animaux','test_jr':'animaux','clothes':'vetements','food':'alimentation','nature':'nature','plurals':'pluriels','professions':'metiers','verb_plurals':'actions','verbs':'actions','continuous':'actions','ser_estar':'etats','adjectives':'description','phrases':'salutations','preferences':'gouts','nombres_jr':'nombres'}

def values(v):
    if v is None:return []
    if isinstance(v,list):return [s for part in v for s in values(part)]
    if isinstance(v,(str,int,float)):
        s=unicodedata.normalize('NFC',str(v)).strip()
        if s.startswith('{') and s.endswith('}'):s=s[1:-1]
        return [s] if s else []
    return []

def main():
    p=argparse.ArgumentParser();p.add_argument('--source-checkout',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];src=a.source_checkout.resolve()
    if subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()!=REV:raise SystemExit('Unexpected source revision')
    folder=root/'content/catalog';folder.mkdir(exist_ok=True)
    old_words=json.loads((folder/'words-librelingo.json').read_text());old_phrases=json.loads((folder/'preview-phrases.json').read_text())
    words={w['data']['latin'].casefold():copy.deepcopy(w) for w in old_words};phrases={}
    old_pairs={(v['data']['latin'],v['data']['french']):v for v in old_phrases}
    for w in words.values():
        w['data'].update(sources=[],source_categories=[],source_skill_names=[],entry_origin='new_words')
    report={'source_revision':REV,'files':[],'failed_files':[],'format_repairs':[],'ignored_entries':0,'mini_dictionary_pairs':0}
    documents=[]
    parsed=[]
    paths=sorted((src/'course').glob('**/skills/*.yaml'),key=lambda x:('juniors' not in x.parts,x.as_posix()))
    for path in paths:
        raw=path.read_text();relative=path.relative_to(src).as_posix();repairs=[]
        try:data=yaml.safe_load(raw)
        except yaml.YAMLError:
            try:data=yaml.safe_load(raw.replace('\t',' '));repairs=['YAML formatting tabs replaced by spaces; linguistic text not rewritten']
            except yaml.YAMLError as e:report['failed_files'].append({'file':relative,'error':str(e)});continue
        skill=data.get('Skill',{});theme=THEMES.get(path.stem,'vie-quotidienne')
        common={'url':BASE+relative,'author':'Bouaziz Ait Driss et contributeurs LibreLingo-KAB-from-FR','license':'CC-BY-NC-SA-4.0','license_url':'https://creativecommons.org/licenses/by-nc-sa/4.0/','revision':REV,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_file':relative,'source_skill':skill.get('Name',path.stem),'format_repairs':repairs,'changes':'Structured extraction; edge whitespace and brace markup normalized; translations preserved.'}
        if repairs:report['format_repairs'].append({'file':relative,'repairs':repairs})
        parsed.append((path,data,theme,common))
        report['files'].append({'path':relative,'skill':skill.get('Name'),'category':theme,'new_words':len(data.get('New words',[]) or []),'phrases':len(data.get('Phrases',[]) or [])})
    def word(latin,french,theme,source,origin,aliases=None,images=None):
        if not latin or not french:report['ignored_entries']+=1;return
        key=latin.casefold()
        if key not in words:words[key]={'id':'word-ll-'+hashlib.sha256(key.encode()).hexdigest()[:16],'kind':'word','variety':'kab','script':'Latn','theme':theme if origin=='new_words' else 'grammaire','status':'draft','data':{'latin':latin,'french':french,'french_variants':[],'synonyms':[],'tifinagh':'','sources':[],'images':[],'audios':[],'examples':[],'source_image_ids':[],'source_categories':[],'source_skill_names':[],'entry_origin':origin,'validation_status':'source_to_review','license_conflict':True}}
        r=words[key];d=r['data']
        if origin=='new_words':
            d['entry_origin']='new_words'
            if theme=='nombres':r['theme']='nombres'
            elif not d.get('primary_course_category'):r['theme']=theme
            d.setdefault('primary_course_category',theme)
        for val in (d.get('french'),french):
            if val and val not in d.setdefault('french_variants',[]):d['french_variants'].append(val)
        for alias in aliases or []:
            if alias not in d.setdefault('synonyms',[]):d['synonyms'].append(alias)
        for image in images or []:
            if image not in d.setdefault('source_image_ids',[]):d['source_image_ids'].append(image)
        if source not in d['sources']:d['sources'].append(source)
        if theme not in d['source_categories']:d['source_categories'].append(theme)
        if source['source_skill'] not in d['source_skill_names']:d['source_skill_names'].append(source['source_skill'])
    # First the intended lesson words, then auxiliary dictionary entries.
    for path,data,theme,common in parsed:
        for i,w in enumerate(data.get('New words',[]) or []):
            if not isinstance(w,dict):continue
            for lat in values(w.get('Word')):
                for fr in values(w.get('Translation')):word(lat,fr,theme,{**common,'source_section':'New words','source_index':i},'new_words',values(w.get('Synonyms')),values(w.get('Images')))
        for i,p in enumerate(data.get('Phrases',[]) or []):
            if not isinstance(p,dict):continue
            for lat in values(p.get('Phrase')):
                for fr in values(p.get('Translation')):
                    key=(lat,fr)
                    if key not in phrases:
                        row=copy.deepcopy(old_pairs.get(key)) if key in old_pairs else {'id':'phrase-ll-'+hashlib.sha256((lat+'\0'+fr).encode()).hexdigest()[:16],'kind':'phrase','variety':'kab','script':'Latn','theme':theme,'status':'draft','data':{'latin':lat,'french':fr,'tifinagh':'','sources':[],'validation_status':'source_to_review','license_conflict':True}}
                        row['theme']=theme;row['data'].update(sources=[],source_categories=[],source_skill_names=[],alternative_versions=values(p.get('Alternative versions')));phrases[key]=row
                    row=phrases[key];proof={**common,'source_section':'Phrases','source_index':i}
                    if proof not in row['data']['sources']:row['data']['sources'].append(proof)
                    if theme not in row['data']['source_categories']:row['data']['source_categories'].append(theme)
                    if common['source_skill'] not in row['data']['source_skill_names']:row['data']['source_skill_names'].append(common['source_skill'])
    for path,data,theme,common in parsed:
        mini=data.get('Mini-dictionary',{}) or {}
        for language,entries in mini.items():
            if not isinstance(entries,list):continue
            for i,entry in enumerate(entries):
                if not isinstance(entry,dict):continue
                for key,target in entry.items():
                    if not isinstance(key,str):continue
                    for v in values(target):
                        lat,fr=(key.strip(),v) if language.casefold()=='kabyle' else (v,key.strip()) if language.casefold() in ('french','francais','français') else ('','')
                        if not lat:report['ignored_entries']+=1;continue
                        source={**common,'source_section':'Mini-dictionary/'+language,'source_index':i,'source_key':key}
                        word(lat,fr,theme,source,'mini_dictionary');report['mini_dictionary_pairs']+=1
    for row in words.values():
        d=row['data']
        # Preserve the source's mistake, expose it for the requested human validation.
        if row['theme']=='nombres' and any(x.startswith('eight') for x in d.get('source_image_ids',[])) and d['french']!='huit':
            d['source_issues']=['Dans le chapitre Nombres, les images eight1/eight2/eight3 indiquent 8 mais la traduction source est « '+d['french']+' ». À corriger ou confirmer.']
        d.setdefault('review_notes',[])
    for row in list(words.values())+list(phrases.values()):
        if row['theme'] not in ('nombres','actions','etats','gouts'):
            row['theme']=suggested_category(row)
        row['data']['category_status']='suggested'
    for path in sorted((src/'course').rglob('*')):
        if path.is_file() and path.suffix in ('.yaml','.md'):
            documents.append({'path':path.relative_to(src).as_posix(),'url':BASE+path.relative_to(src).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'type':'skill' if '/skills/' in path.as_posix() and path.suffix=='.yaml' else 'documentation_or_module'})
    report.update(words=len(words),phrases=len(phrases),course_files=len(documents),source_issues=sum(bool(w['data'].get('source_issues')) for w in words.values()))
    for filename,content in [('course-words.json',list(words.values())),('course-phrases.json',list(phrases.values())),('course-files.json',documents),('course-report.json',report)]:
        (folder/filename).write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()

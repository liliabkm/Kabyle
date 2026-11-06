"""Reproducible bilingual SFT export. This is not a native conversation corpus."""
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from sqlalchemy import select
from .models import Content

VERSION='kab-bilingual-sft-v1'
BASE_MODEL='Qwen/Qwen2.5-0.5B-Instruct'
SYSTEM='Tu aides à apprendre le kabyle et le français. Pour une traduction, donne uniquement la traduction demandée. Si tu ne sais pas, indique-le.'


def group_key(text):
    text=unicodedata.normalize('NFC',text).casefold()
    return re.sub(r'[^\w]+',' ',text).strip()




def export(s, folder, max_pairs=None, report=None):
    folder=Path(folder)
    if (folder/'manifest.json').exists(): raise ValueError('Un export existe déjà ici. Choisis un nouveau dossier pour ne pas l’écraser.')
    folder.mkdir(parents=True,exist_ok=True)
    counts=Counter(); rejected=Counter(); files={}
    # Use a small SQLite staging index for exact deduplication and transitive split
    # grouping, bounded Python memory even for the full corpus.
    import sqlite3
    stage=sqlite3.connect(folder/'staging.sqlite3')
    stage.executescript('CREATE TABLE pairs (id TEXT PRIMARY KEY, kab TEXT, fr TEXT, provenance TEXT, status TEXT); CREATE TABLE nodes (key TEXT PRIMARY KEY, parent TEXT);')
    def root(key):
        row=stage.execute('SELECT parent FROM nodes WHERE key=?',(key,)).fetchone()
        if row is None:
            stage.execute('INSERT INTO nodes VALUES (?,?)',(key,key));return key
        path=[]
        while row[0]!=key:
            path.append(key);key=row[0];row=stage.execute('SELECT parent FROM nodes WHERE key=?',(key,)).fetchone()
        for item in path:stage.execute('UPDATE nodes SET parent=? WHERE key=?',(key,item))
        return key
    def unite(a,b):
        a,b=root(a),root(b)
        if a!=b:
            lo,hi=sorted((a,b));stage.execute('UPDATE nodes SET parent=? WHERE key=?',(lo,hi))
    query=select(Content).where(Content.kind.in_(['word','phrase']),Content.variety=='kab',Content.status!='rejected').order_by(Content.id)
    total=0
    try:
        for c in s.scalars(query.execution_options(yield_per=500)):
            d=c.data;kab=d.get('latin','');fr=d.get('french','')
            if not isinstance(kab,str) or not isinstance(fr,str) or not kab.strip() or not fr.strip():rejected['empty']+=1;continue
            kab,fr=unicodedata.normalize('NFC',kab).strip(),unicodedata.normalize('NFC',fr).strip()
            if len(kab)>600 or len(fr)>600 or len(kab.split())>60 or len(fr.split())>60:rejected['too_long']+=1;continue
            if c.learning_role in ('review','fragment','name') or (d.get('source_issues') and not d.get('source_issues_reviewed')):rejected['needs_correction']+=1;continue
            if not group_key(kab) or not group_key(fr):rejected['empty']+=1;continue
            pair=hashlib.sha256((group_key(kab)+'\0'+group_key(fr)).encode()).hexdigest()
            inserted=stage.execute('INSERT OR IGNORE INTO pairs VALUES (?,?,?,?,?)',(pair,kab,fr,json.dumps({'content_id':c.id,'sources':d.get('sources',[]),'status':c.status},ensure_ascii=False),c.status)).rowcount
            if not inserted:
                source=json.loads(stage.execute('SELECT provenance FROM pairs WHERE id=?',(pair,)).fetchone()[0])
                source.setdefault('duplicate_records',[]).append({'content_id':c.id,'sources':d.get('sources',[]),'status':c.status})
                stage.execute('UPDATE pairs SET provenance=? WHERE id=?',(json.dumps(source,ensure_ascii=False),pair))
                rejected['duplicates']+=1
                continue
            unite('kab:'+group_key(kab),'fra:'+group_key(fr))
            total+=1
            if report and total%1000==0: report(f"Export : {total} paires retenues…")
            if max_pairs and total>=max_pairs:break
        stage.commit()
        for split in ('train','validation','test'):files[split]=(folder/(split+'.jsonl')).open('w',encoding='utf-8')
        provenance=(folder/'provenance.jsonl').open('w',encoding='utf-8')
        groups=Counter()
        try:
            for pair,kab,fr,source,status in stage.execute('SELECT * FROM pairs ORDER BY id'):
                group=root('kab:'+group_key(kab))
                bucket=int(hashlib.sha256(group.encode()).hexdigest()[:8],16)%100
                split='test' if bucket<5 else 'validation' if bucket<10 else 'train'
                groups[split]+=1
                provenance.write(json.dumps({'pair_id':pair,'split':split,'group':hashlib.sha256(group.encode()).hexdigest(),'status':status,**json.loads(source)},ensure_ascii=False)+'\n')
                for direction,prompt,target in [('fr-kab',f'Traduis en kabyle : {fr}',kab),('kab-fr',f'Traduis en français : {kab}',fr)]:
                    example={'id':pair+'-'+direction,'group':hashlib.sha256(group.encode()).hexdigest(),'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':prompt},{'role':'assistant','content':target}]}
                    files[split].write(json.dumps(example,ensure_ascii=False)+'\n');counts[split]+=1
        finally:
            provenance.close()
            for file in files.values():file.close()
        hashes={}
        for name in ('train','validation','test','provenance'):
            h=hashlib.sha256()
            with (folder/(name+'.jsonl')).open('rb') as file:
                for block in iter(lambda:file.read(1024*1024),b''):h.update(block)
            hashes[name]=h.hexdigest()
        manifest={'version':VERSION,'base_model_candidate':BASE_MODEL,'pairs':total,'examples':dict(counts),'pairs_by_split':dict(groups),'excluded':dict(rejected),'sha256':hashes,
            'tasks':['kabyle_to_french','french_to_kabyle'],'dataset_kind':'bilingual_instruction_templates_not_native_dialogues',
            'split_policy':'connected components of normalized Kabyle/French strings; bidirectional examples stay in the same split',
            'training_status':'not_started','quality':'Unreviewed corpus entries remain unreviewed; evaluate before deployment.'}
        (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        return manifest
    finally:
        stage.close()
        (folder/'staging.sqlite3').unlink(missing_ok=True)

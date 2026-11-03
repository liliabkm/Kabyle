"""Streaming, repeatable import of the user-supplied Kabyle/French TSV."""
import csv, hashlib, re, uuid
from itertools import islice
from pathlib import Path
from urllib.request import urlopen
from fastapi import Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .models import Content
from .search import pair_key, searchable
from .learning import features
from .library import fold, suggested_category
SOURCE='https://huggingface.co/datasets/Sifal/Kabyle-French/blob/main/Sentence%20pairs%20in%20Kabyle-French%20-%202023-07-18.tsv'
DOWNLOAD=SOURCE.replace('/blob/','/resolve/')+'?download=true'
CACHE=Path(__file__).resolve().parents[2]/'artifacts/tsv-imports'
MAX_BYTES=128*1024*1024

def rows(path):
    with open(path,encoding='utf-8-sig',newline='') as f:
        yield from enumerate(csv.reader(f,delimiter='\t'),1)

def preview(path):
    sample=list(islice(({'line':n,'cells':r} for n,r in rows(path) if any(v.strip() for v in r)),5))
    if not sample:raise ValueError('Le fichier est vide')
    first=sample[0]['cells'];headers=[fold(x.strip()) for x in first]
    kab=next((i+1 for i,x in enumerate(headers) if x in ('kab','kabyle','kabyle sentence','sentence kabyle')),None)
    fr=next((i+1 for i,x in enumerate(headers) if x in ('fr','fra','french','francais','french sentence')),None)
    header=bool(kab and fr)
    if not header:
        if len(first)==2:kab,fr=1,2
        elif len(first)==4 and first[0].isdigit() and first[2].isdigit():kab,fr=2,4
    return {'sample':sample,'kab_column':kab,'fr_column':fr,'has_header':header}

def classify(french):
    text=fold(french)
    for category,pattern in [('salutations',r'\b(bonjour|bonsoir|merci|salut|bienvenue|revoir)\b'),('nombres',r'^(un|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|vingt|cent|mille|zero|[0-9]+)[.!?]?$'),('temps',r'\b(demain|hier|aujourd.hui|pluie|neige|soleil|heure|matin|soir|temps)\b'),('sante',r'\b(malade|hopital|sante|douleur|medicament)\b'),('voyages',r'\b(voyage|train|avion|voiture|route|gare|bus)\b'),('maison',r'\b(maison|chambre|porte|cuisine|lit|fenetre)\b')]:
        if re.search(pattern,text):return category
    return suggested_category({'kind':'phrase','theme':'autres-phrases','data':{'french':french}})

def import_file(session,path,kab_column,fr_column,has_header=False):
    if kab_column==fr_column:raise ValueError('Choisir deux colonnes différentes')
    digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    report={'rows_seen':0,'inserted':0,'duplicates':0,'invalid_rows':0,'categories':{},'source_sha256':digest}
    batch=[]
    def flush():
        if not batch:return
        keys=[item['pair_key'] for item in batch]
        existing_rows={c.pair_key:c for c in session.scalars(select(Content).where(Content.pair_key.in_(keys)))}
        existing=set(existing_rows)
        unique={}
        for item in batch:
            key=item['pair_key']
            if key in existing or key in unique:
                report['duplicates']+=1
                if key in existing_rows:
                    record=existing_rows[key];sources=record.data.get('sources',[]);incoming=item['data']['sources'][0]
                    if not any(x.get('url')==SOURCE and x.get('sha256')==digest for x in sources):
                        record.data={**record.data,'sources':sources+[incoming]}
                continue
            unique[key]=item
        if unique:
            result=session.execute(insert(Content).values(list(unique.values())).on_conflict_do_nothing(index_elements=['id']).returning(Content.id))
            count=len(result.all());report['inserted']+=count;report['duplicates']+=len(unique)-count
        session.commit();batch.clear()
    first=True
    for line,cells in rows(path):
        if not any(x.strip() for x in cells):continue
        if first and has_header:first=False;continue
        first=False;report['rows_seen']+=1
        if len(cells)<max(kab_column,fr_column):report['invalid_rows']+=1;continue
        kab,fr=cells[kab_column-1].strip(),cells[fr_column-1].strip()
        if not kab or not fr or len(kab)>10000 or len(fr)>10000:report['invalid_rows']+=1;continue
        data={'latin':kab,'french':fr,'category_status':'suggested','category_scheme':'sifal-topics-v1','validation_status':'pending_review','sources':[{'url':SOURCE,'author':'Sifal (diffuseur du jeu de données)','license':'Non renseignée dans le fichier TSV','sha256':digest,'record':line}]}
        theme=classify(fr);key=pair_key('phrase',data)
        report['categories'][theme]=report['categories'].get(theme,0)+1
        batch.append(dict(id='phrase-sifal-'+key[:24],kind='phrase',variety='kab',script='Latn',theme=theme,status='draft',data=data,search_text=searchable(data),pair_key=key,**features('phrase',data)))
        if len(batch)>=500:flush()
    flush();return report

class Commit(BaseModel):
    upload_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    kab_column:int=Field(ge=1,le=30)
    fr_column:int=Field(ge=1,le=30)
    has_header:bool=False

def save_upload(stream):
    CACHE.mkdir(parents=True,exist_ok=True)
    key=uuid.uuid4().hex;path=CACHE/(key+'.tsv');size=0
    try:
        with path.open('wb') as f:
            while chunk:=stream.read(1024*1024):
                size+=len(chunk)
                if size>MAX_BYTES:raise ValueError('Fichier trop grand (maximum 128 Mo)')
                f.write(chunk)
        result=preview(path)
        return {**result,'upload_id':key,'bytes':size}
    except Exception:
        path.unlink(missing_ok=True);raise

def register_routes(app,db,admin):
    @app.post('/api/admin/import-tsv/preview',dependencies=[Depends(admin)])
    def upload(file:UploadFile=File(...)):
        try:return save_upload(file.file)
        except (ValueError,UnicodeError,csv.Error) as e:raise HTTPException(422,str(e))
    @app.post('/api/admin/import-tsv/from-url',dependencies=[Depends(admin)])
    def from_url():
        try:
            with urlopen(DOWNLOAD,timeout=45) as response:return save_upload(response)
        except Exception as e:raise HTTPException(422,'Téléchargement impossible depuis ce serveur. Télécharge le TSV sur Hugging Face puis utilise « Choisir le fichier TSV ».') from e
    @app.post('/api/admin/import-tsv/commit',dependencies=[Depends(admin)])
    def commit(body:Commit,s=Depends(db)):
        path=CACHE/(body.upload_id+'.tsv')
        if not path.is_file():raise HTTPException(404,'Fichier à téléverser de nouveau')
        try:return import_file(s,path,body.kab_column,body.fr_column,body.has_header)
        except (ValueError,UnicodeError,csv.Error) as e:raise HTTPException(422,str(e))

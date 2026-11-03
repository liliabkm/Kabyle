"""Read-only learner catalog and editorial category management."""
import re
import unicodedata
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from .models import Content

CATEGORIES={'alphabet':'Alphabet','animaux':'Animaux','fruits':'Fruits','legumes':'Légumes','alimentation':'À table','famille':'Famille et amis','maison':'Maison','vetements':'Vêtements','nature':'Nature','metiers':'Métiers et école','actions':'Actions du quotidien','salutations':'Salutations','nombres':'Nombres','description':'Couleurs et descriptions','vie-quotidienne':'Vie quotidienne','grammaire':'Petits mots et grammaire','pluriels':'Pluriels','adjectifs':'Descriptions','premiers-mots':'Premiers mots','etats':'États et sensations','gouts':'Goûts et préférences','voyages':'Voyages et déplacements','sante':'Santé','temps':'Temps et météo','questions':'Questions','autres-phrases':'Autres phrases'}

def fold(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value).casefold() if not unicodedata.combining(c))

def category_label(theme):return CATEGORIES.get(theme,theme.replace('-',' ').replace('_',' ').capitalize())

def is_published(c):
    # Visibility and human validation are now independent, as requested.
    return c.status!='rejected'

def suggested_category(item):
    if item['kind']=='letter':return 'alphabet'
    d=item['data'];value=' '+fold(' '.join([d.get('french','')]+d.get('french_variants',[])))+' '
    groups=[('fruits',r'\b(fraises?|figues?|raisin|pommes?|poires?|oranges?|bananes?|cerises?|fruits?)\b'),('legumes',r'\b(carottes?|legumes?|tomates?|oignons?)\b'),('animaux',r'\b(chats?|chiens?|chevaux|cheval|canards?|ours|lions?|anes?|animaux|oiseaux?)\b'),('vetements',r'\b(robes?|jupes?|chemises?|chapeaux?|chaussures?|lunettes|t.shirts?|vetements?)\b'),('famille',r'\b(amis?|amies?|meres?|peres?|parents?|freres?|soeurs?|famille)\b'),('metiers',r'\b(docteurs?|medecins?|professeurs?|etudiants?|ecole|enseignants?)\b'),('nature',r'\b(plages?|arbres?|forets?|rivieres?|montagnes?|ciel|mer|fleurs?)\b'),('alimentation',r'\b(pain|lait|pates|couscous|cafe|the|eau|biere|soupe|repas|aliments?)\b')]
    for category,pattern in groups:
        if re.search(pattern,value):return category
    source=' '.join(s.get('url','') for s in d.get('sources',[]))
    if any(t in source for t in ('/verbs.yaml','/continuous.yaml','/verb_plurals.yaml')):return 'actions'
    if '/phrases.yaml' in source:return 'salutations'
    if '/adjectives.yaml' in source:return 'description'
    return {'adjectifs':'description','pluriels':'grammaire','premiers-mots':'vie-quotidienne'}.get(item.get('theme'),item.get('theme','vie-quotidienne'))

def seed_categories(session):
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]/'content/catalog'
    defaults={item['id']:item for filename in ('words-librelingo.json','phrases-librelingo.json') for item in json.loads((root/filename).read_text())}
    changed=0
    for c in session.scalars(select(Content).where(Content.id.in_(list(defaults)))):
        d=c.data
        if c.id.startswith('test-') or d.get('category_scheme') or d.get('edited_at') or d.get('category_reviewed_at'):continue
        # Only classify unchanged imported records, never unknown user-created entries.
        source=defaults.get(c.id)
        if source is None or c.kind=='letter':continue
        if c.theme!=source['theme'] or d.get('latin')!=source['data']['latin'] or d.get('french')!=source['data']['french']:continue
        theme=suggested_category({'kind':c.kind,'theme':c.theme,'data':d})
        c.data={**d,'source_theme':c.theme,'category_scheme':'topics-v1','category_status':'suggested'}
        c.theme=theme;changed+=1
    return changed

class CategoryChange(BaseModel):
    theme:str=Field(pattern=r'^[a-z0-9][a-z0-9-]{0,59}$')

def library_payload(s,kind,category,q,offset,limit,private=False,status=""):
    base=[] if private else [Content.status!='rejected']
    counts=dict(s.execute(select(Content.kind,func.count()).where(*base).group_by(Content.kind)).all())
    selected=base+[Content.kind==kind]
    if status:selected.append(Content.status==status)
    categories=s.execute(select(Content.theme,func.count()).where(*selected).group_by(Content.theme)).all()
    filters=list(selected)
    if category:filters.append(Content.theme==category)
    if q.strip():
        if kind=='letter' and len(q.strip())==1:
            filters.append(or_(func.lower(Content.data['latin'].as_string())==q.strip().casefold(),Content.data['tifinagh'].as_string()==q.strip()))
        else:filters.append(Content.search_text.contains(fold(q.strip()),autoescape=True))
    total=s.scalar(select(func.count()).select_from(Content).where(*filters))
    sort=Content.data['latin'].as_string() if kind=='letter' else func.coalesce(Content.data['french'].as_string(),Content.data['latin'].as_string())
    page=s.scalars(select(Content).where(*filters).order_by(func.lower(sort),Content.id).offset(offset).limit(limit))
    return {'private':private,'counts':{k:counts.get(k,0) for k in ('letter','word','phrase')},'categories':[{'id':k,'label':category_label(k),'count':v} for k,v in sorted(categories,key=lambda x:category_label(x[0]))],'total':total,'offset':offset,'limit':limit,'items':[{**c.data,'id':c.id,'kind':c.kind,'variety':c.variety,'script':c.script,'theme':c.theme,'category_label':category_label(c.theme),'status':c.status} for c in page]}

def register_routes(app,db,admin):
    @app.get('/api/library')
    def library(kind:str=Query('letter',pattern='^(letter|word|phrase)$'),category:str='',q:str=Query('',max_length=200),offset:int=Query(0,ge=0),limit:int=Query(24,ge=1,le=72),s=Depends(db)):
        return library_payload(s,kind,category,q,offset,limit,private=False)
    @app.get('/api/admin/library',dependencies=[Depends(admin)])
    def private_library(status:str=Query('',pattern='^(|draft|validated|rejected)$'),kind:str=Query('word',pattern='^(letter|word|phrase)$'),category:str='',q:str=Query('',max_length=200),offset:int=Query(0,ge=0),limit:int=Query(24,ge=1,le=72),s=Depends(db)):
        return library_payload(s,kind,category,q,offset,limit,private=True,status=status)
    @app.get('/api/admin/categories',dependencies=[Depends(admin)])
    def categories(s=Depends(db)):
        themes=set(s.scalars(select(Content.theme).distinct()))
        return [{'id':t,'label':category_label(t)} for t in sorted(set(CATEGORIES)|themes,key=category_label)]
    @app.patch('/api/admin/content/{content_id}/category',dependencies=[Depends(admin)])
    def change_category(content_id:str,body:CategoryChange,s=Depends(db)):
        from datetime import datetime,timezone
        c=s.get(Content,content_id)
        if c is None:raise HTTPException(404,'Fiche introuvable')
        c.theme=body.theme;c.data={**c.data,'category_status':'editorial','category_reviewed_at':datetime.now(timezone.utc).isoformat(),'category_scheme':'topics-v1'}
        s.commit()
        return {'id':c.id,'theme':c.theme,'label':category_label(c.theme),'status':c.status}

    @app.post('/api/admin/content/{content_id}/validate',dependencies=[Depends(admin)])
    def validate_one(content_id:str,s=Depends(db)):
        from datetime import datetime,timezone
        c=s.get(Content,content_id)
        if c is None:raise HTTPException(404,'Fiche introuvable')
        if not isinstance(c.data.get('latin'),str) or not c.data['latin'].strip():raise HTTPException(422,'Texte kabyle requis')
        if c.kind in ('word','phrase') and (not isinstance(c.data.get('french'),str) or not c.data['french'].strip()):raise HTTPException(422,'Traduction française requise')
        c.status='validated';c.data={**c.data,'reviewed_by':'Administrateur','reviewed_at':datetime.now(timezone.utc).isoformat(),'validation_status':'reviewed_by_admin','source_issues_reviewed':bool(c.data.get('source_issues'))}
        s.commit();return {'id':c.id,'status':c.status,'reviewed_at':c.data['reviewed_at']}

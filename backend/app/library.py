"""Read-only learner catalog and editorial category management."""
import re
import unicodedata
from collections import Counter
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from .models import Content

CATEGORIES={'alphabet':'Alphabet','animaux':'Animaux','fruits':'Fruits','legumes':'Légumes','alimentation':'À table','famille':'Famille et amis','maison':'Maison','vetements':'Vêtements','nature':'Nature','metiers':'Métiers et école','actions':'Actions du quotidien','salutations':'Salutations','nombres':'Nombres','description':'Couleurs et descriptions','vie-quotidienne':'Vie quotidienne','grammaire':'Petits mots et grammaire','pluriels':'Pluriels','adjectifs':'Descriptions','premiers-mots':'Premiers mots'}

def fold(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value).casefold() if not unicodedata.combining(c))

def category_label(theme):return CATEGORIES.get(theme,theme.replace('-',' ').replace('_',' ').capitalize())

def is_published(c):
    return c.status=='validated' and not c.data.get('publication_blockers') and not c.data.get('license_conflict')

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
    for c in session.scalars(select(Content)):
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

def library_payload(s,kind,category,q,offset,limit,private=False):
    rows=list(s.scalars(select(Content).order_by(Content.id)))
    visible=rows if private else [c for c in rows if is_published(c)]
    counts=Counter(c.kind for c in visible)
    selected=sorted((c for c in visible if c.kind==kind),key=lambda c:fold(c.data.get('latin','') if kind=='letter' else c.data.get('french','') or c.data.get('latin','')))
    categories=Counter(c.theme for c in selected)
    def matches(c):
        if category and c.theme!=category:return False
        if not q.strip():return True
        if kind=='letter' and len(q.strip())==1:
            return fold(q.strip())==fold(c.data.get('latin','')) or q.strip()==c.data.get('tifinagh')
        return fold(q.strip()) in fold(' '.join([c.data.get('latin',''),c.data.get('french',''),c.data.get('tifinagh','')]+c.data.get('french_variants',[])+c.data.get('alternative_versions',[])+c.data.get('synonyms',[])))
    filtered=[c for c in selected if matches(c)]
    return {'private':private,'counts':{k:counts[k] for k in ('letter','word','phrase')},'categories':[{'id':k,'label':category_label(k),'count':v} for k,v in sorted(categories.items(),key=lambda x:category_label(x[0]))],'total':len(filtered),'offset':offset,'limit':limit,'items':[{**c.data,'id':c.id,'kind':c.kind,'theme':c.theme,'category_label':category_label(c.theme),'status':c.status} for c in filtered[offset:offset+limit]]}

def register_routes(app,db,admin):
    @app.get('/api/library')
    def library(kind:str=Query('letter',pattern='^(letter|word|phrase)$'),category:str='',q:str=Query('',max_length=200),offset:int=Query(0,ge=0),limit:int=Query(24,ge=1,le=72),s=Depends(db)):
        return library_payload(s,kind,category,q,offset,limit,private=False)
    @app.get('/api/admin/library',dependencies=[Depends(admin)])
    def private_library(kind:str=Query('word',pattern='^(letter|word|phrase)$'),category:str='',q:str=Query('',max_length=200),offset:int=Query(0,ge=0),limit:int=Query(24,ge=1,le=72),s=Depends(db)):
        return library_payload(s,kind,category,q,offset,limit,private=True)
    @app.get('/api/admin/categories',dependencies=[Depends(admin)])
    def categories(s=Depends(db)):
        themes={c.theme for c in s.scalars(select(Content))}
        return [{'id':t,'label':category_label(t)} for t in sorted(set(CATEGORIES)|themes,key=category_label)]
    @app.patch('/api/admin/content/{content_id}/category',dependencies=[Depends(admin)])
    def change_category(content_id:str,body:CategoryChange,s=Depends(db)):
        from datetime import datetime,timezone
        c=s.get(Content,content_id)
        if c is None:raise HTTPException(404,'Fiche introuvable')
        c.theme=body.theme;c.data={**c.data,'category_status':'editorial','category_reviewed_at':datetime.now(timezone.utc).isoformat(),'category_scheme':'topics-v1'}
        s.commit()
        return {'id':c.id,'theme':c.theme,'label':category_label(c.theme),'status':c.status}

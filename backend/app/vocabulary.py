"""Private, source-backed lesson previews. Drafts never enter the public course."""
import re
import unicodedata
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from .models import Content, Lesson, MediaAsset

def normalized(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text).strip()).rstrip('.!?').casefold()

def load_lesson(session, lesson_id, preview=False):
    lesson = session.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(404, 'Leçon introuvable')
    ids = lesson.data['word_ids'] + lesson.data['phrase_ids']
    content = {key: session.get(Content, key) for key in ids}
    if any(c is None or c.variety != 'kab' for c in content.values()):
        raise HTTPException(409, 'Les sources de cette leçon sont incomplètes')
    if not preview and (lesson.status != 'validated' or lesson.data.get('scope') == 'private_noncommercial_preview' or any(c.status != 'validated' or c.data.get('publication_blockers') or c.data.get('license_conflict') for c in content.values())):
        raise HTTPException(404, 'Leçon non publiée')
    return lesson, content

def make_bundle(session, lesson_id, preview=False):
    lesson, content = load_lesson(session, lesson_id, preview)
    words=[]
    for key in lesson.data['word_ids']:
        c=content[key];spec=lesson.data['media'][key]
        if c.kind!='word': raise HTTPException(409,'Référence de mot invalide')
        media=dict(spec)
        if spec.get('asset_id'):
            asset=session.get(MediaAsset,spec['asset_id'])
            if asset is None:raise HTTPException(409,'Illustration absente')
            media={**asset.data,**spec,'presentation':'La même photo est répétée pour illustrer le pluriel ; pixels inchangés.'}
        words.append({'id':c.id,'latin':c.data['latin'],'french':c.data['french'],'media':media,'sources':c.data['sources']})
    phrases=[]
    for key in lesson.data['phrase_ids']:
        c=content[key]
        if c.kind!='phrase':raise HTTPException(409,'Référence de phrase invalide')
        phrases.append({'id':c.id,'latin':c.data['latin'],'french':c.data['french'],'sources':c.data['sources'],'target_word_id':c.data['target_word_id']})
    exercises=[]
    for e in lesson.data['exercises']:
        c=content[e['content_id']]
        item={'id':e['id'],'type':e['type'],'french':c.data['french']}
        if e['type']=='recognize':item.update(word_id=c.id,option_ids=lesson.data['word_ids'])
        elif e['type']=='order':
            tokens=c.data['latin'].split()
            item['tokens']=tokens[1:]+tokens[:1]
        elif e['type']=='cloze':
            word=content[e['word_id']].data['latin'];phrase=c.data['latin']
            start=phrase.casefold().find(word.casefold())
            if start<0 or phrase.casefold().count(word.casefold())!=1:raise HTTPException(409,'Le mot et la phrase ont changé : relecture de la leçon requise')
            item.update(before=phrase[:start],after=phrase[start+len(word):],keyboard=sorted(set(ch for ch in word if ord(ch)>127)))
        elif e['type']=='recall':item['keyboard']=sorted(set(ch for ch in c.data['latin'] if ord(ch)>127))
        else:raise HTTPException(409,'Type d’exercice inconnu')
        exercises.append(item)
    return {'id':lesson.id,'title':lesson.title,'preview':preview,'notice':lesson.data['notice'],'words':words,'phrases':phrases,'exercises':exercises,'progress_scope':'session_only' if preview else 'not_started','method_sources':lesson.data.get('method_sources',[])}

class LessonAnswer(BaseModel):
    exercise_id: str = Field(max_length=100)
    answer: str = Field(max_length=500)

def evaluate(session,lesson_id,body):
    lesson,content=load_lesson(session,lesson_id,preview=True)
    exercise=next((e for e in lesson.data['exercises'] if e['id']==body.exercise_id),None)
    if exercise is None:raise HTTPException(404,'Exercice introuvable')
    target=content[exercise.get('word_id') or exercise['content_id']]
    expected=target.data['latin']
    variants=[expected]+(target.data.get('alternative_versions',[]) if target.kind=='phrase' else target.data.get('synonyms',[]))
    correct=normalized(body.answer) in {normalized(v) for v in variants if isinstance(v,str)}
    return {'correct':correct,'expected':expected,'french':target.data['french'],'recorded':False,'scope':'private_preview_session','source_url':target.data['sources'][0]['url']}

def register_routes(app,db,admin):
    @app.get('/api/learning-lessons')
    def published(s=Depends(db)):
        ready=[]
        for lesson in s.scalars(select(Lesson).where(Lesson.status=='validated')):
            try:load_lesson(s,lesson.id)
            except HTTPException:continue
            ready.append({'id':lesson.id,'title':lesson.title})
        return ready
    @app.get('/api/learning-lessons/{lesson_id}')
    def public_lesson(lesson_id:str,s=Depends(db)):
        return make_bundle(s,lesson_id)
    @app.get('/api/admin/learning-lessons/{lesson_id}',dependencies=[Depends(admin)])
    def preview_lesson(lesson_id:str,s=Depends(db)):
        return make_bundle(s,lesson_id,preview=True)
    @app.post('/api/admin/learning-lessons/{lesson_id}/answers',dependencies=[Depends(admin)])
    def preview_answer(lesson_id:str,body:LessonAnswer,s=Depends(db)):
        return evaluate(s,lesson_id,body)

"""Public source-backed practice; validation is separate from visibility."""
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
    if lesson.status=='rejected' or any(c.status=='rejected' for c in content.values()):
        raise HTTPException(404,'Leçon indisponible')
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
    return {'id':lesson.id,'title':lesson.title,'preview':preview,'notice':'Textes et traductions issus des sources citées. Les fiches non validées restent à vérifier.','words':words,'phrases':phrases,'exercises':exercises,'progress_scope':'learner','method_sources':lesson.data.get('method_sources',[])}

class LessonAnswer(BaseModel):
    exercise_id: str = Field(max_length=100)
    answer: str = Field(max_length=500)
    attempt_id: str = Field(min_length=10,max_length=100)

def evaluate(session,lesson_id,body):
    lesson,content=load_lesson(session,lesson_id,preview=True)
    exercise=next((e for e in lesson.data['exercises'] if e['id']==body.exercise_id),None)
    if exercise is None:raise HTTPException(404,'Exercice introuvable')
    target=content[exercise.get('word_id') or exercise['content_id']]
    expected=target.data['latin']
    variants=[expected]+(target.data.get('alternative_versions',[]) if target.kind=='phrase' else target.data.get('synonyms',[]))
    correct=normalized(body.answer) in {normalized(v) for v in variants if isinstance(v,str)}
    return {'correct':correct,'expected':expected,'french':target.data['french'],'recorded':False,'scope':'private_preview_session','source_url':target.data['sources'][0]['url']}

def register_routes(app,db,admin,learner):
    @app.get('/api/learning-lessons')
    def published(s=Depends(db)):
        ready=[]
        for lesson in s.scalars(select(Lesson).where(Lesson.status!='rejected')):
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

    @app.post('/api/learning-lessons/{lesson_id}/answers')
    def public_answer(lesson_id:str,body:LessonAnswer,who=Depends(learner),s=Depends(db)):
        from datetime import datetime,timedelta,timezone
        from .models import Progress,Attempt
        result=evaluate(s,lesson_id,body)
        lesson,content=load_lesson(s,lesson_id)
        e=next(e for e in lesson.data['exercises'] if e['id']==body.exercise_id)
        target=content[e.get('word_id') or e['content_id']]
        old=s.get(Attempt,body.attempt_id)
        if old:
            if old.learner!=who or old.content_id!=target.id:raise HTTPException(409,'Identifiant déjà utilisé')
            return {**result,'correct':old.correct,'recorded':True,'duplicate':True,'scope':'learner'}
        p=s.scalar(select(Progress).where(Progress.learner==who,Progress.content_id==target.id).with_for_update())
        if p is None:
            p=Progress(learner=who,content_id=target.id,correct=0,errors=0,streak=0);s.add(p)
        correct=result['correct'];p.correct+=int(correct);p.errors+=int(not correct);p.streak=p.streak+1 if correct else 0
        p.due=datetime.now(timezone.utc)+timedelta(days=min(30,2**min(p.streak-1,5)) if correct else 0)
        s.add(Attempt(id=body.attempt_id,learner=who,content_id=target.id,correct=correct));s.commit()
        return {**result,'recorded':True,'scope':'learner'}

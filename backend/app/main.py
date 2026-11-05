import os, secrets
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta, timezone
from dataclasses import asdict
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, Header, Cookie, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from .db import Session
from .models import Content, Progress, Attempt, MediaAsset
from .services import UnavailableVision, UnavailableSpeech, compare_words
app = FastAPI(title="Tifin · Kabyle", version="0.1.0")
app.mount("/api/media", StaticFiles(directory=Path(__file__).resolve().parents[2] / "content/photos", check_dir=False), name="catalog-media")
def db():
    with Session() as session: yield session
def admin(authorization: str = Header(default="")):
    token = os.getenv("ADMIN_TOKEN", "")
    if not token or not secrets.compare_digest(authorization, "Bearer " + token):
        raise HTTPException(401, "Jeton administrateur requis")
def learner(response: Response, kabyle_learner: str | None = Cookie(default=None)):
    if not kabyle_learner or len(kabyle_learner) != 64:
        kabyle_learner = secrets.token_hex(32)
        response.set_cookie("kabyle_learner", kabyle_learner, httponly=True, samesite="strict", secure=os.getenv("COOKIE_SECURE") == "1", max_age=31536000)
    return kabyle_learner
@app.get("/api/health")
def health(s=Depends(db)):
    s.execute(text("SELECT 1")); return {"status":"ok"}
def serialize(c): return {**c.data,"id":c.id,"kind":c.kind,"variety":c.variety,"script":c.script,"theme":c.theme,"status":c.status}
@app.get("/api/content")
def contents(s=Depends(db)):
    return [serialize(c) for c in s.scalars(select(Content).where(Content.status != "rejected", Content.kind.in_(["letter","word"])).order_by(Content.id))]
@app.get("/api/progress")
def progress(who=Depends(learner), s=Depends(db)):
    return [{"content_id":p.content_id,"latin":c.data.get('latin',''),"kind":c.kind,"correct":p.correct,"errors":p.errors,"streak":p.streak,"due":p.due.isoformat()} for p,c in s.execute(select(Progress,Content).join(Content,Content.id==Progress.content_id).where(Progress.learner==who))]

class Answer(BaseModel):
    content_id: str
    answer: str = Field(max_length=200)
    attempt_id: str = Field(min_length=10,max_length=100)
@app.post("/api/answers")
def answer(body: Answer, who=Depends(learner), s=Depends(db)):
    c=s.get(Content,body.content_id)
    if not c or c.status == "rejected": raise HTTPException(404,"Contenu indisponible")
    previous=s.get(Attempt,body.attempt_id)
    if previous:
        if previous.learner != who or previous.content_id != c.id: raise HTTPException(409,"Identifiant déjà utilisé")
        return {"correct":previous.correct,"duplicate":True}
    correct=body.answer.strip().casefold() == c.data["latin"].casefold()
    p=s.scalar(select(Progress).where(Progress.learner==who,Progress.content_id==c.id).with_for_update())
    if p is None:
        p=Progress(learner=who,content_id=c.id,correct=0,errors=0,streak=0);s.add(p)
    p.correct+=int(correct);p.errors+=int(not correct);p.streak=p.streak+1 if correct else 0
    p.due=datetime.now(timezone.utc)+timedelta(days=min(30,2**min(p.streak-1,5)) if correct else 0)
    s.add(Attempt(id=body.attempt_id,learner=who,content_id=c.id,correct=correct));s.commit()
    return {"correct":correct,"expected":c.data["latin"],"due":p.due.isoformat()}
@app.delete("/api/progress",status_code=204)
def clear(who=Depends(learner),s=Depends(db)):
    from sqlalchemy import delete
    from .structured_models import LessonRun
    s.execute(delete(LessonRun).where(LessonRun.learner==who))
    s.execute(delete(Attempt).where(Attempt.learner==who));s.execute(delete(Progress).where(Progress.learner==who));s.commit()
@app.get("/api/ai/status")
def ai_status():
    return {"vision":asdict(UnavailableVision().recognize(b"")),"speech":asdict(UnavailableSpeech().transcribe(b""))}
class Comparison(BaseModel):
    expected: str = Field(max_length=2000)
    observed: str = Field(max_length=2000)
@app.post("/api/practice/compare")
def compare(body: Comparison): return {"words":compare_words(body.expected,body.observed),"notice":"Comparaison de texte uniquement, sans note de prononciation."}
class ContentInput(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9-]{1,80}$")
    kind: Literal["letter","word","phrase"]
    variety: str = "kab"
    script: str = "Tfng"
    theme: str = "alphabet"
    status: Literal["draft","validated","rejected"] = "draft"
    data: dict

def validate_content(item):
    d=item.data
    if d.get('cefr_level') not in (None,'','A1','A2','B1','B2','C1','C2'):raise HTTPException(422,'Niveau CECR inconnu')
    if d.get('grammar_note') is not None and (not isinstance(d['grammar_note'],str) or len(d['grammar_note'])>4000):raise HTTPException(422,'Note grammaticale : texte de 4 000 caractères maximum')
    if not isinstance(d.get("latin"),str) or not d["latin"].strip(): raise HTTPException(422,"Transcription latine requise")
    if item.status != "validated": return
    sources=d.get("sources",[])
    if not sources or not all(isinstance(s,dict) and all(isinstance(s.get(k),str) and s[k].strip() for k in ("url","author","license")) for s in sources):
        raise HTTPException(422,"Chaque source exige URL, auteur et licence")
    if item.variety != "kab": raise HTTPException(422,"Le parcours actuel publie uniquement la variété kab")
    if item.kind in ('word','phrase') and not d.get('french'):
        raise HTTPException(422,'Traduction française requise')
    for media in d.get("images",[])+d.get("audios",[]):
        if not isinstance(media,dict) or not all(media.get(k) for k in ("url","author","license")): raise HTTPException(422,"Attributions média incomplètes")
@app.get("/api/admin/content",dependencies=[Depends(admin)])
def admin_content(s=Depends(db)): return [{"id":c.id,"kind":c.kind,"variety":c.variety,"script":c.script,"theme":c.theme,"status":c.status,"data":c.data} for c in s.scalars(select(Content).order_by(Content.id).limit(1000))]
@app.post("/api/admin/import",dependencies=[Depends(admin)])
def import_content(items: list[ContentInput],s=Depends(db)):
    if len(items)>500: raise HTTPException(422,"Maximum 500 entrées")
    for item in items: validate_content(item)
    for item in items:
        c=s.get(Content,item.id)
        if c:
            for key,value in item.model_dump().items(): setattr(c,key,value)
        else: s.add(Content(**item.model_dump()))
    s.commit();return {"imported":len(items)}

@app.get("/api/admin/media", dependencies=[Depends(admin)])
def admin_media(s=Depends(db)):
    return [{"id": a.id, "kind": a.kind, "theme": a.theme, "label_fr": a.label_fr, "status": a.status, "data": a.data} for a in s.scalars(select(MediaAsset).order_by(MediaAsset.label_fr))]

from .vocabulary import register_routes
register_routes(app, db, admin, learner)

from .library import register_routes as register_library_routes
register_library_routes(app, db, admin)

from .tsv_import import register_routes as register_tsv_routes
register_tsv_routes(app,db,admin)

from .tatoeba import register_routes as register_tatoeba_routes
register_tatoeba_routes(app,db,admin)
from .phrase_practice import register_routes as register_phrase_routes
register_phrase_routes(app,db,learner)

from .topics import register_routes as register_topic_routes
register_topic_routes(app,db,admin)

from .word_entry import register_routes as register_word_entry_routes
register_word_entry_routes(app, db, admin)

from .curriculum import register_routes as register_curriculum_routes
register_curriculum_routes(app, db, admin, learner)
from .data_admin import register_routes as register_data_admin_routes
register_data_admin_routes(app, db, admin)

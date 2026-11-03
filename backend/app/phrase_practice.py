"""Public, server-graded phrase activities and an attested-word lexicon."""

import hashlib, json, random, re, unicodedata
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_, cast
from sqlalchemy.dialects.postgresql import JSONB
from .models import Content, Progress, Attempt
from .learning import learning_info, usable_audios, clean_token, lexeme_key
from .library import category_label

MODES = ("flashcard", "order", "dictation", "audio-choice")


def normalized(value):
    return (
        re.sub(r"\s+", " ", unicodedata.normalize("NFC", value).strip())
        .rstrip(".!?…")
        .casefold()
        .replace("’", "'")
    )


def public_phrase(s, key):
    c = s.get(Content, key)
    if c is None or c.kind != "phrase" or c.status == "rejected":
        raise HTTPException(404, "Phrase introuvable")
    return c


def choices(s, c):
    found = []
    seen = {normalized(c.data["french"])}
    for same_topic in (True, False):
        filters = [Content.kind == "phrase", Content.status != "rejected", Content.id != c.id]
        if same_topic:
            filters.append(Content.theme == c.theme)
        for other in s.scalars(select(Content).where(*filters).order_by(Content.id).limit(120)):
            french = other.data.get("french", "")
            if (
                not french
                or normalized(french) in seen
                or normalized(other.data["latin"]) == normalized(c.data["latin"])
            ):
                continue
            seen.add(normalized(french))
            found.append({"id": other.id, "text": french})
            if len(found) == 2:
                break
        if len(found) == 2:
            break
    if len(found) < 2:
        return []
    found.append({"id": c.id, "text": c.data["french"]})
    random.Random(c.id).shuffle(found)
    return found


def question(s, c, mode):
    if mode not in MODES:
        raise HTTPException(422, "Exercice inconnu")
    audios = usable_audios(c.data)
    if mode in ("dictation", "audio-choice") and not audios:
        raise HTTPException(409, "Cette phrase ne possède pas d’enregistrement disponible")
    options = choices(s, c) if audios else []
    if mode == "audio-choice" and not options:
        raise HTTPException(409, "Pas encore assez de traductions distinctes pour ce QCM")
    pieces = c.data["latin"].split()
    indices = list(range(len(pieces)))
    random.Random(c.id).shuffle(indices)
    if len(indices) > 1 and indices == list(range(len(indices))):
        indices = indices[1:] + indices[:1]
    version = hashlib.sha256(
        json.dumps(
            [c.data["latin"], c.data["french"], audios, c.data.get("alternative_versions", [])],
            sort_keys=True,
        ).encode()
    ).hexdigest()
    return {
        "id": c.id,
        "latin": c.data["latin"],
        "french": c.data["french"],
        "status": c.status,
        "category": category_label(c.theme),
        "mode": mode,
        "tokens": [{"id": i, "text": pieces[i]} for i in indices],
        "audios": audios,
        "options": options,
        "question_version": version,
        "sources": c.data.get("sources", []),
        **learning_info(c.data),
    }


def lexicon(s, token):
    term = clean_token(token)
    if not term:
        return []
    predicate = or_(
        Content.lexeme_key == lexeme_key(term),
        cast(Content.data["synonyms"], JSONB).contains([term]),
    )
    matches = []
    for c in s.scalars(
        select(Content)
        .where(Content.kind == "word", Content.status != "rejected", predicate)
        .limit(20)
    ):
        matches.append(
            {
                "id": c.id,
                "latin": c.data["latin"],
                "french": c.data.get("french"),
                "french_variants": c.data.get("french_variants", []),
                "status": c.status,
                "sources": c.data.get("sources", []),
            }
        )
    return matches


class PhraseAnswer(BaseModel):
    mode: str = Field(pattern="^(order|dictation|audio-choice)$")
    answer: str = Field(max_length=10000)
    attempt_id: str = Field(min_length=10, max_length=100)
    question_version: str = Field(min_length=64, max_length=64)


def register_routes(app, db, learner):
    @app.get("/api/phrase-practice")
    def catalog(
        category: str = "",
        difficulty: str = Query("", pattern="^(|short|medium|long|A1|A2|B1|B2|C1|C2)$"),
        audio_only: bool = False,
        source: str = Query("", pattern="^(|tatoeba)$"),
        offset: int = Query(0, ge=0),
        limit: int = Query(12, ge=1, le=24),
        s=Depends(db),
    ):
        base = [Content.kind == "phrase", Content.status != "rejected"]
        topics = s.execute(
            select(Content.theme, func.count()).where(*base).group_by(Content.theme)
        ).all()
        audio_count = s.scalar(
            select(func.count()).select_from(Content).where(*base, Content.has_audio.is_(True))
        )
        filters = list(base)
        if category:
            filters.append(Content.theme == category)
        if difficulty in ("short", "medium", "long"):
            filters.append(Content.learning_band == difficulty)
        elif difficulty:
            filters.append(Content.data["cefr_level"].as_string() == difficulty)
        if audio_only:
            filters.append(Content.has_audio.is_(True))
        if source:
            filters.append(Content.data["tatoeba_pairs"].as_string().is_not(None))
        total = s.scalar(select(func.count()).select_from(Content).where(*filters))
        items = [
            {
                "id": c.id,
                "latin": c.data["latin"],
                "french": c.data["french"],
                "category": category_label(c.theme),
                "has_audio": c.has_audio,
                "status": c.status,
                **learning_info(c.data),
            }
            for c in s.scalars(
                select(Content).where(*filters).order_by(Content.id).offset(offset).limit(limit)
            )
        ]
        return {
            "items": items,
            "total": total,
            "audio_count": audio_count,
            "categories": [
                {"id": k, "label": category_label(k), "count": v}
                for k, v in sorted(topics, key=lambda x: category_label(x[0]))
            ],
        }

    @app.get("/api/phrase-practice/{content_id}")
    def get_question(content_id: str, mode: str = "flashcard", s=Depends(db)):
        return question(s, public_phrase(s, content_id), mode)

    @app.get("/api/lexicon")
    def get_lexicon(token: str = Query(min_length=1, max_length=300), s=Depends(db)):
        return {
            "token": token,
            "matches": lexicon(s, token),
            "notice": "Entrées attestées du lexique ; le sens exact dépend du contexte.",
        }

    @app.post("/api/phrase-practice/{content_id}/answers")
    def grade(content_id: str, body: PhraseAnswer, who=Depends(learner), s=Depends(db)):
        c = public_phrase(s, content_id)
        q = question(s, c, body.mode)
        if body.question_version != q["question_version"]:
            raise HTTPException(409, "La fiche a changé. Recharge cet exercice.")
        if body.mode == "audio-choice":
            if body.answer not in {x["id"] for x in q["options"]}:
                raise HTTPException(422, "Choisir une des trois propositions")
            correct = body.answer == c.id
        else:
            variants = [c.data["latin"]] + c.data.get("alternative_versions", [])
            correct = normalized(body.answer) in {
                normalized(v) for v in variants if isinstance(v, str)
            }
        result = {
            "correct": correct,
            "expected": c.data["latin"],
            "french": c.data["french"],
            "recorded": True,
        }
        old = s.get(Attempt, body.attempt_id)
        if old:
            if old.learner != who or old.content_id != c.id:
                raise HTTPException(409, "Identifiant de tentative déjà utilisé")
            return {**result, "correct": old.correct, "duplicate": True}
        p = s.scalar(
            select(Progress)
            .where(Progress.learner == who, Progress.content_id == c.id)
            .with_for_update()
        )
        if p is None:
            p = Progress(learner=who, content_id=c.id, correct=0, errors=0, streak=0)
            s.add(p)
        p.correct += int(correct)
        p.errors += int(not correct)
        p.streak = p.streak + 1 if correct else 0
        p.due = datetime.now(timezone.utc) + timedelta(
            days=min(30, 2 ** min(p.streak - 1, 5)) if correct else 0
        )
        s.add(Attempt(id=body.attempt_id, learner=who, content_id=c.id, correct=correct))
        s.commit()
        return result

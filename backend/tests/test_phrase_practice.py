import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, delete
from app.main import app
from app.models import Content, Attempt, Progress
from app.db import Session


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
        who = c.cookies.get("kabyle_learner")
        with Session() as s:
            if who:
                s.execute(delete(Attempt).where(Attempt.learner == who))
                s.execute(delete(Progress).where(Progress.learner == who))
            s.commit()


def test_public_catalog_difficulty_and_attested_lexicon(client):
    result = client.get("/api/phrase-practice?difficulty=short").json()
    assert result["total"] > 0 and all(
        c["word_count"] <= 4 and not c["cefr_level"] for c in result["items"]
    )
    known = client.get("/api/lexicon", params={"token": "AQJUN."}).json()
    assert any(m["french"] == "chien" for m in known["matches"])
    assert any(
        m["latin"] == "kraḍ" for m in client.get("/api/lexicon?token=tlata").json()["matches"]
    )
    assert client.get("/api/lexicon?token=nonexistent-fixture-term").json()["matches"] == []
    assert client.get("/api/progress").json() == []


def test_puzzle_progress_retry_and_stale_question(client):
    key = "phrase-ll-preview-dog"
    q = client.get("/api/phrase-practice/" + key + "?mode=order").json()
    assert sorted(t["id"] for t in q["tokens"]) == list(range(len(q["tokens"])))
    body = {
        "mode": "order",
        "answer": "wrong",
        "attempt_id": str(uuid.uuid4()),
        "question_version": q["question_version"],
    }
    assert (
        client.post("/api/phrase-practice/" + key + "/answers", json=body).json()["correct"]
        is False
    )
    body.update(answer=q["latin"], attempt_id=str(uuid.uuid4()))
    assert (
        client.post("/api/phrase-practice/" + key + "/answers", json=body).json()["correct"] is True
    )
    assert (
        client.post("/api/phrase-practice/" + key + "/answers", json=body).json()["duplicate"]
        is True
    )
    progress = client.get("/api/progress").json()
    assert sum(p["correct"] for p in progress) == 1 and sum(p["errors"] for p in progress) == 1
    body.update(question_version="0" * 64, attempt_id=str(uuid.uuid4()))
    assert client.post("/api/phrase-practice/" + key + "/answers", json=body).status_code == 409
    assert client.get("/api/phrase-practice/" + key + "?mode=dictation").status_code == 409


def test_audio_modules_use_metadata_and_real_server_answers(client):
    key = "test-audio-" + uuid.uuid4().hex
    with Session() as s:
        s.add(
            Content(
                id=key,
                kind="phrase",
                variety="kab",
                script="Latn",
                theme="animaux",
                status="draft",
                data={
                    "latin": "Fixture aqjun.",
                    "french": "Phrase de test audio uniquement",
                    "audios": [
                        {
                            "url": "https://example.org/fixture.mp3",
                            "author": "Fixture",
                            "license": "CC0",
                        }
                    ],
                    "sources": [],
                },
            )
        )
        s.commit()
    try:
        q = client.get("/api/phrase-practice/" + key + "?mode=dictation").json()
        assert len(q["audios"]) == 1
        body = {
            "mode": "dictation",
            "answer": "Fixture aqjun.",
            "attempt_id": str(uuid.uuid4()),
            "question_version": q["question_version"],
        }
        assert client.post("/api/phrase-practice/" + key + "/answers", json=body).json()["correct"]
        q = client.get("/api/phrase-practice/" + key + "?mode=audio-choice").json()
        assert len(q["options"]) == 3 and len({o["text"] for o in q["options"]}) == 3
        body.update(
            mode="audio-choice",
            answer=next(o["id"] for o in q["options"] if o["id"] != key),
            attempt_id=str(uuid.uuid4()),
        )
        assert (
            client.post("/api/phrase-practice/" + key + "/answers", json=body).json()["correct"]
            is False
        )
        body.update(answer=key, attempt_id=str(uuid.uuid4()))
        assert (
            client.post("/api/phrase-practice/" + key + "/answers", json=body).json()["correct"]
            is True
        )
    finally:
        client.delete("/api/progress")
        with Session() as s:
            s.execute(delete(Content).where(Content.id == key))
            s.commit()

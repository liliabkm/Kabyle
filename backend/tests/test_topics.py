import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.organization import organize, source_span

ROOT = Path(__file__).resolve().parents[2] / "content/catalog"


def test_every_bundled_word_has_a_semantic_decision():
    words = json.loads((ROOT / "course-words.json").read_text())
    assert len(words) == 442
    decisions = [organize("word", w["data"]) for w in words]
    assert not [x for x in decisions if x["role"] == "unclassified"]
    assert sum(x["role"] == "review" for x in decisions) == 12
    for french, latin, topic in [
        ("souris", "aɣerda", "animaux"),
        ("éléphant", "lfil", "animaux"),
        ("café", "lqahwa", "boissons"),
        ("pizza", "pizza", "alimentation"),
        ("nous", "nekkni", "grammaire"),
        ("garçon", "aqcic", "famille"),
        ("onze", "ḥdac", "nombres"),
    ]:
        assert organize("word", {"latin": latin, "french": french})["topics"][0] == topic


def test_semantic_boundaries_and_ambiguous_french():
    for text, topic in [
        ("Merci", "salutations"),
        ("Vous mangez du raisin", "fruits"),
        ("Le cheval boit de l’eau", "animaux"),
        ("Les souris sont petites", "animaux"),
        ("Je bois du café", "boissons"),
        ("Combien ça coûte ?", "achats"),
    ]:
        assert organize("phrase", {"latin": "", "french": text})["topics"][0] == topic
    assert "fruits" not in organize("phrase", {"french": "Je mange des pommes de terre."})["topics"]
    assert "animaux" not in organize("phrase", {"french": "Je fais un achat."})["topics"]
    assert "nombres" not in organize("phrase", {"french": "Un chien."})["topics"]
    assert "nombres" not in organize("phrase", {"french": "Quoi de neuf ?"})["topics"]
    assert "maison" not in organize("phrase", {"french": "Je porte une robe."})["topics"]
    assert source_span("un autre mot", ["chat"]) is None
    assert source_span("🐎 D agmar", ["agmar"])["before"] == "🐎 D "


def test_public_topic_words_then_actual_attested_contexts():
    with TestClient(app) as c:
        initial = c.get("/api/progress").json()
        assert initial == []
        gallery = c.get("/api/topics").json()
        grammar=next(t for t in gallery["topics"] if t["id"]=="grammaire")
        assert grammar["phrase_count"]==c.get("/api/topics/grammaire/phrases").json()["total"]
        fruit = next(t for t in gallery["topics"] if t["id"] == "fruits")
        assert fruit["word_count"] == 3 and fruit["phrase_count"] == 4
        words = c.get("/api/topics/fruits/words").json()["items"]
        assert [x["concept"] for x in words] == ["fraise", "raisin", "figue"]
        assert len(next(x for x in words if x["concept"] == "fraise")["forms"]) == 3
        animals = c.get("/api/topics/animaux/words").json()["items"]
        assert [x["concept"] for x in animals[:3]] == ["chien", "chat", "cheval"]
        assert {"souris", "elephant", "ours", "lion"} <= set(x["concept"] for x in animals)
        for topic, concept in [
            ("animaux", "cheval"),
            ("animaux", "chien"),
            ("fruits", "fraise"),
            ("fruits", "raisin"),
            ("fruits", "figue"),
        ]:
            response = c.get(f"/api/topics/{topic}/phrases", params={"word": concept}).json()
            assert response["total"] > 0 and all(p["highlight"] for p in response["items"])
            assert all(
                p["latin"][p["highlight"]["start"] : p["highlight"]["end"]]
                == p["highlight"]["text"]
                for p in response["items"]
            )
        assert c.get("/api/topics/animaux/phrases?word=fraise").json()["total"] == 0
        assert c.get("/api/progress").json() == []
        assert c.get("/api/topics/not-a-topic/words").status_code == 404
        assert c.get("/api/admin/organization").status_code == 401


def test_source_error_is_not_taught_as_a_number_or_as_an_animal():
    with TestClient(app) as c:
        review = c.get("/api/topics/a-revoir/words").json()["items"]
        assert any(w["latin"] == "ṭam" for w in review)
        for topic in ("animaux", "nombres"):
            assert not any(
                w["latin"] == "ṭam" for w in c.get(f"/api/topics/{topic}/words").json()["items"]
            )
    fixed = {
        "latin": "ṭam",
        "french": "huit",
        "source_issues": ["Historical source issue"],
        "source_issues_reviewed": True,
    }
    assert organize("word", fixed)["concept"] == "nombre-8"


def test_explicit_editorial_topic_remains_visible_and_can_link_its_words():
    import uuid
    from sqlalchemy import delete
    from app.db import Session
    from app.models import Content

    marker = uuid.uuid4().hex
    wid = "test-topic-word-" + marker
    pid = "test-topic-phrase-" + marker
    topic = "fruits-tropicaux-test-" + marker[:8]
    with Session() as s:
        try:
            s.add(
                Content(
                    id=wid,
                    kind="word",
                    theme=topic,
                    status="draft",
                    data={
                        "latin": "fixture" + marker,
                        "french": "litchi",
                        "category_reviewed_at": "2026-11-03",
                        "sources": [],
                    },
                )
            )
            s.add(
                Content(
                    id=pid,
                    kind="phrase",
                    theme=topic,
                    status="draft",
                    data={
                        "latin": "fixture" + marker + " d test",
                        "french": "Un litchi.",
                        "category_reviewed_at": "2026-11-03",
                        "sources": [],
                    },
                )
            )
            s.commit()
            with TestClient(app) as c:
                assert any(t["id"] == topic for t in c.get("/api/topics").json()["topics"])
                word = c.get(f"/api/topics/{topic}/words").json()["items"][0]
                contexts = c.get(
                    f"/api/topics/{topic}/phrases", params={"word": word["concept"]}
                ).json()
                assert (
                    contexts["total"] == 1
                    and contexts["items"][0]["highlight"]["text"] == "fixture" + marker
                )
        finally:
            s.execute(delete(Content).where(Content.id.in_([wid, pid])))
            s.commit()


def test_topic_phrases_expose_only_usable_audio_and_credits():
    import uuid
    from sqlalchemy import delete
    from app.db import Session
    from app.models import Content

    marker = 'test-topic-audio-' + uuid.uuid4().hex
    recording = {'url': 'https://tatoeba.org/en/audio/download/9900000001',
                 'author': 'Synthetic test speaker', 'license': 'CC0',
                 'attribution_url': 'https://tatoeba.org/en/sentences/show/1'}
    with Session() as session:
        try:
            session.add(Content(id=marker, kind='phrase', theme='animaux', status='draft',
                data={'latin': 'D agmar.', 'french': 'Un cheval.',
                      'audios': [recording,
                                 {'url': 'javascript:alert(1)', 'author': 'Test', 'license': 'CC0'},
                                 {'url': 'https://example.org/no-credit.mp3'}]}))
            session.commit()
            with TestClient(app) as client:
                rows = client.get('/api/topics/animaux/phrases?limit=24').json()['items']
                row = next(item for item in rows if item['id'] == marker)
                assert row['has_audio'] is True
                assert row['audios'] == [recording]
                assert all(item['audios'] == [] for item in rows if not item['has_audio'])
        finally:
            session.execute(delete(Content).where(Content.id == marker))
            session.commit()

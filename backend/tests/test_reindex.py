"""Startup migration regressions against an isolated PostgreSQL schema."""

import uuid
import pytest
from sqlalchemy import create_engine, delete, func, insert, select, text
from sqlalchemy.orm import Session as OrmSession
from app.db import Base, engine
from app.models import Content
from app.organization import VERSION
from app.reindex import pending_classification, reindex_content


@pytest.fixture
def isolated_engine():
    schema = "reindex_test_" + uuid.uuid4().hex
    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA " + schema))
    url = engine.url.update_query_dict({"options": "-csearch_path=" + schema})
    isolated = create_engine(url)
    Base.metadata.create_all(isolated)
    try:
        yield isolated
    finally:
        isolated.dispose()
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA " + schema + " CASCADE"))


def legacy_rows(bind, count):
    # Core insertion emulates rows written before migrations 005/006, not new
    # ORM inserts (whose hooks already populate the classification).
    with bind.begin() as connection:
        connection.execute(
            insert(Content.__table__),
            [
                dict(
                    id=f"legacy-{i:06}",
                    kind="phrase",
                    theme="actions",
                    status="validated",
                    variety="kab",
                    script="Latn",
                    data={
                        "latin": f"Fixture {i} amcic",
                        "french": f"Un chat de test {i}",
                        "reviewed_by": "Fixture reviewer",
                        "reviewed_at": "2026-11-03",
                    },
                    organization_version=None,
                    learning_band=None,
                )
                for i in range(count)
            ],
        )


def test_old_corpus_finishes_across_multiple_batches_and_second_run_does_no_work(isolated_engine):
    legacy_rows(isolated_engine, 1051)
    progress = []
    with OrmSession(isolated_engine) as session:
        assert reindex_content(session, batch_size=500, report=progress.append) == 1051
        assert session.scalar(select(func.count()).where(pending_classification())) == 0
        assert (
            session.scalar(select(Content.theme).where(Content.id == "legacy-000000")) == "animaux"
        )
        original = session.get(Content, "legacy-000000")
        assert original.status == "validated"
        assert original.data == {
            "latin": "Fixture 0 amcic",
            "french": "Un chat de test 0",
            "reviewed_by": "Fixture reviewer",
            "reviewed_at": "2026-11-03",
        }
        assert original.organization_version == VERSION
        assert reindex_content(session, report=progress.append) == 0
    assert any("500/1051" in line for line in progress)
    assert any("1000/1051" in line for line in progress)
    assert any("1051/1051" in line for line in progress)
    assert progress[-1] == "Classement déjà à jour."


def test_ctrl_c_after_a_completed_batch_resumes_from_saved_work(isolated_engine):
    legacy_rows(isolated_engine, 1051)

    def interrupt(message):
        if "500/1051" in message:
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        with OrmSession(isolated_engine) as session:
            reindex_content(session, batch_size=500, report=interrupt)
    with OrmSession(isolated_engine) as session:
        assert (
            session.scalar(select(func.count()).where(Content.organization_version == VERSION))
            == 500
        )
        assert reindex_content(session, batch_size=500) == 551
        assert session.scalar(select(func.count()).where(pending_classification())) == 0


def test_editorial_category_and_manual_word_concept_survive_bulk_classification(isolated_engine):
    with isolated_engine.begin() as connection:
        connection.execute(
            insert(Content.__table__),
            [
                dict(
                    id="manual-word",
                    kind="word",
                    theme="fruits-tropicaux",
                    status="validated",
                    data={
                        "latin": "Fixture",
                        "french": "Litchi",
                        "category_reviewed_at": "2026-11-03",
                    },
                    organization_version=None,
                ),
                dict(
                    id="letter",
                    kind="letter",
                    theme="nature",
                    status="validated",
                    data={"latin": "a", "tifinagh": "ⴰ"},
                    organization_version=None,
                ),
            ],
        )
    with OrmSession(isolated_engine) as session:
        assert reindex_content(session) == 2
        word = session.get(Content, "manual-word")
        assert word.theme == "fruits-tropicaux" and word.topic_keys == ["fruits-tropicaux"]
        assert word.learning_role == "word" and word.concept_key.startswith("manual-")
        assert word.status == "validated" and word.lexeme_key
        assert session.get(Content, "letter").theme == "nature"


def test_bad_backfill_result_stops_instead_of_silently_looping(isolated_engine, monkeypatch):
    from app import reindex

    legacy_rows(isolated_engine, 1)
    real = reindex.features

    def invalid(kind, data):
        return {**real(kind, data), "learning_band": None}

    monkeypatch.setattr(reindex, "features", invalid)
    with OrmSession(isolated_engine) as session:
        with pytest.raises(RuntimeError, match="Classement incomplet"):
            reindex_content(session)
    with OrmSession(isolated_engine) as session:
        assert session.get(Content, "legacy-000000").organization_version is None


def test_actual_seed_command_handles_ctrl_c_and_resumes(isolated_engine):
    import os
    import signal
    import subprocess
    import sys
    from pathlib import Path

    legacy_rows(isolated_engine, 3001)
    env = {**os.environ, "DATABASE_URL": isolated_engine.url.render_as_string(hide_password=False)}
    process = subprocess.Popen(
        [sys.executable, "-u", "seed.py"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = []
    try:
        for line in process.stdout:
            output.append(line)
            if "500/3001" in line:
                process.send_signal(signal.SIGINT)
                break
        tail, _ = process.communicate(timeout=30)
        output.append(tail)
        assert process.returncode == 130, "".join(output)
        assert "Initialisation interrompue" in "".join(output)
        assert "Traceback" not in "".join(output)
        with OrmSession(isolated_engine) as session:
            completed = session.scalar(
                select(func.count()).where(
                    Content.id.like("legacy-%"), Content.organization_version == VERSION
                )
            )
            assert 500 <= completed < 3001
        resumed = subprocess.run(
            [sys.executable, "-u", "seed.py"],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert resumed.returncode == 0, resumed.stderr
        with OrmSession(isolated_engine) as session:
            assert session.scalar(select(func.count()).where(pending_classification())) == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)

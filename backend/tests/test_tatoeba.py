"""Synthetic alignment fixtures; no claim of downloading the real Tatoeba corpus."""

import bz2, copy, io, json, tarfile, uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from app.db import Session
from app.main import app
from app.models import Content
from app.tatoeba import prepare, import_prepared, text_stream, mysql_text
from app.learning import features, learning_info


@pytest.fixture
def inputs(tmp_path):
    marker = "fixture-" + uuid.uuid4().hex
    pairs = tmp_path / "pairs.tsv"
    pairs.write_text(
        f"9000000001\t{marker} aqjun.\t9000000002\tBonjour {marker}.\n9000000003\t{marker} axxam.\t9000000004\tUne maison {marker}.\n9000000005\t{marker} aman.\t9000000006\tDe l’eau {marker}.\n",
        encoding="utf-8",
    )
    audio = tmp_path / "audio.tsv"
    audio.write_text(
        "9000000001\t9900000001\tFixtureVoice\tCC BY 4.0\thttps://example.org/fixture\n9000000001\t9900000002\tOtherFixture\tCC0 1.0\t\n9000000003\t9900000003\tNoLicense\t\\N\t\n9000009999\t9900000009\tForeign\tCC BY 4.0\t\n",
        encoding="utf-8",
    )
    return marker, pairs, audio


def test_prepare_aligns_exact_ids_and_multiple_recordings(tmp_path, inputs):
    marker, pairs, audio = inputs
    report = prepare(tmp_path / "stage", pairs=pairs, audio=audio)
    assert report["pairs"] == 3 and report["audio_records"] == 2 and report["pairs_with_audio"] == 1
    assert report["audio_without_credits"] == 1
    assert report["sample"][0]["latin"] == marker + " aqjun."
    assert report["input_hashes"]["pairs"]


def test_streamed_sentence_link_join_and_archives(tmp_path):
    sentences = tmp_path / "sentences.tsv.bz2"
    sentences.write_bytes(
        bz2.compress(
            "1\tkab\tFixture kab\tOwnerKab\tdate\tdate\n2\tfra\tFixture fr\tOwnerFr\tdate\tdate\n3\teng\tExcluded\tOwner\td\td\n".encode()
        )
    )
    links = tmp_path / "links.tar.bz2"
    with tarfile.open(links, "w:bz2") as archive:
        content = b"1\t2\n2\t1\n1\t3\n"
        info = tarfile.TarInfo("links.csv")
        info.size = len(content)
        archive.addfile(info, io.BytesIO(content))
    report = prepare(tmp_path / "stage", sentences=[sentences], links=links)
    assert report["pairs"] == 1 and report["audio_records"] == 0
    assert report["sample"][0]["kab_id"] == 1 and report["sample"][0]["fr_id"] == 2
    assert not (tmp_path / "links.csv").exists()  # No archive path extraction.


def test_six_column_direction_and_bad_files(tmp_path):
    path = tmp_path / "pairs.tsv"
    path.write_text(
        "2\tfra\tFixture French\t1\tkab\tFixture Kabyle\n3\teng\tWrong\t4\tfra\tWrong\n"
    )
    result = prepare(tmp_path / "stage", pairs=path)
    assert result["pairs"] == 1 and result["invalid_pairs"] == 1
    path.write_text("Not a four-column export\n")
    with pytest.raises(ValueError, match="Aucune paire"):
        prepare(tmp_path / "bad", pairs=path)


def test_import_is_public_idempotent_and_preserves_edits(tmp_path, inputs):
    marker, pairs, audio = inputs
    folder = tmp_path / "stage"
    prepare(folder, pairs=pairs, audio=audio)
    with Session() as s:
        try:
            first = import_prepared(s, folder)
            assert first["inserted"] == 3 and first["audio_records"] == 2
            c = s.scalar(
                select(Content).where(Content.data["latin"].as_string() == marker + " aqjun.")
            )
            assert c.status == "draft" and c.has_audio and c.learning_band == "short"
            assert c.data["audios"][0]["url"] == "https://tatoeba.org/en/audio/download/9900000001"
            assert "cefr_level" not in c.data
            c.status = "validated"
            c.theme = "nature"
            c.data = {**c.data, "grammar_note": "Fixture editorial note"}
            s.commit()
            second = import_prepared(s, folder)
            s.refresh(c)
            assert second["inserted"] == 0 and second["duplicates"] == 3
            assert (
                c.status == "validated"
                and c.theme == "nature"
                and c.data["grammar_note"] == "Fixture editorial note"
            )
            assert len(c.data["audios"]) == 2 and len(c.data["sources"]) == 2
        finally:
            s.execute(delete(Content).where(Content.data["latin"].as_string().like(marker + "%")))
            s.commit()


def test_length_is_not_a_cefr_or_grammar_judgment():
    d = {"latin": "Axxam-a d ameqqran."}
    assert learning_info(d)["words"] == ["Axxam-a", "d", "ameqqran"]
    assert learning_info(d)["cefr_level"] is None and learning_info(d)["grammar_note"] is None
    assert features("phrase", d)["learning_band"] == "short"


def test_mysql_escapes_do_not_rewrite_literal_backslashes():
    assert mysql_text(r"line\nnext") == "line\nnext"
    assert mysql_text(r"literal\\n") == r"literal\n"
    assert mysql_text(r"\N") == ""


def test_cross_corpus_identity_survives_correction_of_both_texts(tmp_path, inputs):
    marker, pairs, audio = inputs
    folder = tmp_path / "cross-stage"
    prepare(folder, pairs=pairs, audio=audio)
    original = pairs.read_text().splitlines()[0].split("\t")
    key = "test-cross-" + uuid.uuid4().hex
    with Session() as s:
        try:
            c = Content(
                id=key,
                kind="phrase",
                variety="kab",
                script="Latn",
                theme="nature",
                status="validated",
                data={"latin": original[1], "french": original[3], "sources": []},
            )
            s.add(c)
            s.commit()
            assert import_prepared(s, folder)["inserted"] == 2
            s.refresh(c)
            assert c.data["tatoeba_pairs"] and len(c.data["audios"]) == 2
            c.data = {
                **c.data,
                "latin": marker + " corrected",
                "french": "Traduction corrigée de test",
            }
            s.commit()
            assert import_prepared(s, folder)["inserted"] == 0
            s.refresh(c)
            assert (
                c.data["latin"] == marker + " corrected"
                and c.data["french"] == "Traduction corrigée de test"
            )
            assert c.status == "validated" and c.theme == "nature"
            assert (
                s.scalar(select(Content.id).where(Content.data["latin"].as_string() == original[1]))
                is None
            )
        finally:
            s.execute(delete(Content).where(Content.data["latin"].as_string().like(marker + "%")))
            s.commit()

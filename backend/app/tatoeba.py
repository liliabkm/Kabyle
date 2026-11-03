"""Align official Tatoeba exports on IDs, stream archives, retain recording provenance.

Formats checked against Tatoeba/tatoeba2 f2c80b81032630648f7896182174a9f5784ccde2:
PairsExporter.php; templates/Pages/downloads.php; weekly_exports.sql.
No MP3 URL is created without a matching audio metadata record.
"""

import bz2, csv, gzip, hashlib, io, json, re, sqlite3, tarfile, uuid
from contextlib import contextmanager
from pathlib import Path
from fastapi import Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.dialects.postgresql import insert
from .models import Content
from .search import pair_key, searchable
from .learning import features, learning_info
from .tsv_import import classify

ROOT = Path(__file__).resolve().parents[2] / "artifacts/tatoeba-imports"
MAX_UPLOAD = 128 * 1024 * 1024


@contextmanager
def text_stream(path):
    path = Path(path)
    if ".tar" in path.name:
        with tarfile.open(path, mode="r:*") as archive:
            found = False
            for member in archive:
                if not member.isfile() or not member.name.endswith((".csv", ".tsv")):
                    continue
                if found:
                    raise ValueError("Une archive doit contenir un seul fichier CSV/TSV")
                found = True
                with io.TextIOWrapper(
                    archive.extractfile(member), encoding="utf-8-sig", newline=""
                ) as stream:
                    yield stream
                # One data file is expected; do not extract paths from archives.
                break
            if not found:
                raise ValueError("Aucun CSV/TSV dans cette archive")
    else:
        with path.open("rb") as raw:
            magic = raw.read(3)
        opener = bz2.open if magic == b"BZh" else gzip.open if magic[:2] == b"\x1f\x8b" else open
        with opener(path, "rt", encoding="utf-8-sig", newline="") as stream:
            yield stream


def rows(path, raw=False):
    with text_stream(path) as stream:
        for number, row in enumerate(
            csv.reader(
                stream, delimiter="\t", quoting=csv.QUOTE_NONE if raw else csv.QUOTE_MINIMAL
            ),
            1,
        ):
            if any(value.strip() for value in row):
                yield number, row


def digest(path):
    with open(path, "rb") as f:
        return (
            hashlib.file_digest(f, "sha256").hexdigest()
            if hasattr(hashlib, "file_digest")
            else _digest(f)
        )


def _digest(f):
    h = hashlib.sha256()
    while block := f.read(1024 * 1024):
        h.update(block)
    return h.hexdigest()


def mysql_text(value):
    if value == r"\N":
        return ""
    escapes = {"0": "\0", "b": "\b", "t": "\t", "n": "\n", "r": "\r", "Z": "\x1a", "\\": "\\"}
    return re.sub(r"\\([0btnrZ\\])", lambda m: escapes[m.group(1)], value)


def prepare(folder, pairs=None, sentences=(), links=None, audio=None):
    """Stage on disk so even global sentence/link dumps need no huge in-memory join."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(folder / "aligned.sqlite")
    report = {
        "pairs": 0,
        "invalid_pairs": 0,
        "audio_records": 0,
        "audio_without_credits": 0,
        "invalid_audio_rows": 0,
        "input_hashes": {},
    }
    inputs = (
        ([("pairs", pairs)] if pairs else [])
        + [(f"sentences_{i}", path) for i, path in enumerate(sentences)]
        + ([("links", links)] if links else [])
        + ([("audio", audio)] if audio else [])
    )
    report["input_hashes"] = {role: digest(path) for role, path in inputs}
    try:
        db.executescript(
            "CREATE TABLE sentences(id INTEGER PRIMARY KEY,lang TEXT,text TEXT,author TEXT);CREATE TABLE pairs(kid INTEGER,fid INTEGER,kab TEXT,fr TEXT,PRIMARY KEY(kid,fid));CREATE TABLE audios(id INTEGER PRIMARY KEY,sid INTEGER,author TEXT,license TEXT,attribution TEXT);CREATE INDEX audio_sid ON audios(sid);"
        )
        for path in sentences:
            batch = []
            for _, r in rows(path, raw=True):
                if len(r) < 3 or not r[0].isdigit() or r[1] not in ("kab", "fra"):
                    continue
                batch.append(
                    (int(r[0]), r[1], mysql_text(r[2]), mysql_text(r[3]) if len(r) >= 6 else "")
                )
                if len(batch) >= 5000:
                    db.executemany("INSERT OR REPLACE INTO sentences VALUES(?,?,?,?)", batch)
                    batch = []
            db.executemany("INSERT OR REPLACE INTO sentences VALUES(?,?,?,?)", batch)
            db.commit()
        if pairs:
            for _, r in rows(pairs):
                if r[0].casefold() in ("sentence_id", "id", "kab_id"):
                    continue
                if len(r) == 4 and r[0].isdigit() and r[2].isdigit():
                    kid, kab, fid, fr = r
                elif (
                    len(r) == 6
                    and r[0].isdigit()
                    and r[3].isdigit()
                    and r[1] == "kab"
                    and r[4] == "fra"
                ):
                    kid, _, kab, fid, _, fr = r
                elif (
                    len(r) == 6
                    and r[0].isdigit()
                    and r[3].isdigit()
                    and r[1] == "fra"
                    and r[4] == "kab"
                ):
                    fid, _, fr, kid, _, kab = r
                else:
                    report["invalid_pairs"] += 1
                    continue
                if not kab.strip() or not fr.strip() or max(len(kab), len(fr)) > 10000:
                    report["invalid_pairs"] += 1
                    continue
                db.execute(
                    "INSERT OR IGNORE INTO pairs VALUES(?,?,?,?)",
                    (int(kid), int(fid), kab.strip(), fr.strip()),
                )
            db.commit()
        elif links and sentences:
            kab_ids = {r[0] for r in db.execute("SELECT id FROM sentences WHERE lang='kab'")}
            for _, r in rows(links, raw=True):
                if len(r) != 2 or not all(v.isdigit() for v in r):
                    continue
                left, right = map(int, r)
                kid, fid = (left, right) if left in kab_ids else (right, left)
                if kid not in kab_ids:
                    continue
                found = db.execute(
                    "SELECT k.text,f.text FROM sentences k JOIN sentences f ON f.id=? AND f.lang='fra' WHERE k.id=? AND k.lang='kab'",
                    (fid, kid),
                ).fetchone()
                if found:
                    db.execute("INSERT OR IGNORE INTO pairs VALUES(?,?,?,?)", (kid, fid, *found))
            db.commit()
        else:
            raise ValueError(
                "Fournir les paires à quatre colonnes, ou les phrases kab/fra et links.csv"
            )
        report["pairs"] = db.execute("SELECT count(*) FROM pairs").fetchone()[0]
        if not report["pairs"]:
            raise ValueError(
                "Aucune paire kabyle–français alignée. Choisir un export kab → fra avec les deux identifiants."
            )
        if audio:
            kab_ids = {r[0] for r in db.execute("SELECT DISTINCT kid FROM pairs")}
            for _, r in rows(audio, raw=True):
                if r[0].casefold() in ("sentence_id", "sid"):
                    continue
                if len(r) != 5 or not r[0].isdigit() or not r[1].isdigit():
                    report["invalid_audio_rows"] += 1
                    continue
                sid, aid = int(r[0]), int(r[1])
                author, license, attribution = map(mysql_text, r[2:])
                if sid not in kab_ids:
                    continue
                if not author.strip() or not license.strip():
                    report["audio_without_credits"] += 1
                    continue
                db.execute(
                    "INSERT OR REPLACE INTO audios VALUES(?,?,?,?,?)",
                    (aid, sid, author, license, attribution),
                )
            db.commit()
        report["audio_records"] = db.execute("SELECT count(*) FROM audios").fetchone()[0]
        report["pairs_with_audio"] = db.execute(
            "SELECT count(*) FROM pairs WHERE kid IN (SELECT sid FROM audios)"
        ).fetchone()[0]
        report["sample"] = [
            {"kab_id": r[0], "fr_id": r[1], "latin": r[2], "french": r[3]}
            for r in db.execute("SELECT * FROM pairs ORDER BY kid,fid LIMIT 5")
        ]
        (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
        return report
    finally:
        db.close()


def unique_items(values, key):
    out = []
    seen = set()
    for item in values:
        value = key(item)
        if value not in seen:
            out.append(item)
            seen.add(value)
    return out


def import_prepared(session, folder):
    folder = Path(folder)
    report = json.loads((folder / "report.json").read_text())
    result = {
        "inserted": 0,
        "duplicates": 0,
        "enriched": 0,
        "pairs": report["pairs"],
        "audio_records": report["audio_records"],
        "pairs_with_audio": report["pairs_with_audio"],
    }
    db = sqlite3.connect(folder / "aligned.sqlite")
    batch = []

    def flush():
        if not batch:
            return
        merged = {}
        for item in batch:
            key = item["pair_key"]
            if key in merged:
                previous = merged[key]["data"]
                for field in ("sources", "audios", "tatoeba_pairs"):
                    previous[field] = unique_items(
                        previous[field] + item["data"][field],
                        lambda x: json.dumps(x, sort_keys=True),
                    )
                result["duplicates"] += 1
            else:
                merged[key] = item
        existing_rows = list(
            session.scalars(
                select(Content).where(
                    or_(
                        Content.pair_key.in_(list(merged)),
                        Content.id.in_([item["id"] for item in merged.values()]),
                    )
                )
            )
        )
        existing = {c.pair_key: c for c in existing_rows}
        existing_ids = {c.id: c for c in existing_rows}
        fresh = []
        for key, item in merged.items():
            c = existing.get(key) or existing_ids.get(item["id"])
            if c is None:
                item.update(features("phrase", item["data"]))
                fresh.append(item)
                continue
            result["duplicates"] += 1
            updated = dict(c.data)
            for field in ("sources", "audios", "tatoeba_pairs"):
                updated[field] = unique_items(
                    updated.get(field, []) + item["data"][field],
                    lambda x: json.dumps(x, sort_keys=True),
                )
            if updated != c.data:
                c.data = updated
                result["enriched"] += 1
        if fresh:
            count = len(
                session.execute(
                    insert(Content)
                    .values(fresh)
                    .on_conflict_do_nothing(index_elements=["id"])
                    .returning(Content.id)
                ).all()
            )
            result["inserted"] += count
            result["duplicates"] += len(fresh) - count
        session.commit()
        batch.clear()

    try:
        # Recover source identities even after a human has corrected both texts,
        # including records first imported from another corpus (LibreLingo/Sifal).
        db.execute(
            "CREATE TEMP TABLE existing_refs(kid INTEGER,fid INTEGER,content_id TEXT,PRIMARY KEY(kid,fid))"
        )
        ref_batch = []
        statement = (
            select(Content.id, Content.data["tatoeba_pairs"])
            .where(Content.kind == "phrase", Content.data["tatoeba_pairs"].as_string().is_not(None))
            .execution_options(yield_per=1000)
        )
        for content_id, references in session.execute(statement):
            for ref in references if isinstance(references, list) else []:
                if (
                    isinstance(ref, dict)
                    and str(ref.get("kab_id")).isdigit()
                    and str(ref.get("fr_id")).isdigit()
                ):
                    ref_batch.append((int(ref["kab_id"]), int(ref["fr_id"]), content_id))
            if len(ref_batch) >= 1000:
                db.executemany("INSERT OR REPLACE INTO existing_refs VALUES(?,?,?)", ref_batch)
                ref_batch = []
        db.executemany("INSERT OR REPLACE INTO existing_refs VALUES(?,?,?)", ref_batch)
        db.commit()
        for kid, fid, kab, fr in db.execute("SELECT * FROM pairs ORDER BY kid,fid"):
            sources = []
            for sid, lang in ((kid, "kab"), (fid, "fra")):
                owner = db.execute("SELECT author FROM sentences WHERE id=?", (sid,)).fetchone()
                sources.append(
                    {
                        "url": f"https://tatoeba.org/en/sentences/show/{sid}",
                        "author": owner[0] if owner and owner[0] else "Contributeurs Tatoeba",
                        "license": "CC BY 2.0 FR",
                        "license_url": "https://creativecommons.org/licenses/by/2.0/fr/",
                        "sentence_id": sid,
                        "language": lang,
                        "input_sha256": report["input_hashes"],
                    }
                )
            audios = [
                {
                    "url": f"https://tatoeba.org/en/audio/download/{aid}",
                    "audio_id": aid,
                    "sentence_id": kid,
                    "author": author,
                    "license": license,
                    "attribution_url": attribution
                    or f"https://tatoeba.org/en/sentences/show/{kid}",
                    "source_url": f"https://tatoeba.org/en/sentences/show/{kid}",
                    "source": "tatoeba",
                    "native_status": "not_assessed",
                }
                for aid, _, author, license, attribution in db.execute(
                    "SELECT * FROM audios WHERE sid=? ORDER BY id", (kid,)
                )
            ]
            data = {
                "latin": kab,
                "french": fr,
                "sources": sources,
                "audios": audios,
                "tatoeba_pairs": [{"kab_id": kid, "fr_id": fid}],
                "validation_status": "pending_review",
                "category_status": "suggested",
                "category_scheme": "topics-v1",
            }
            data.update(
                {
                    k: v
                    for k, v in learning_info(data).items()
                    if k in ("words", "word_count", "difficulty", "difficulty_status")
                }
            )
            key = pair_key("phrase", data)
            reference = db.execute(
                "SELECT content_id FROM existing_refs WHERE kid=? AND fid=?", (kid, fid)
            ).fetchone()
            batch.append(
                dict(
                    id=reference[0] if reference else "phrase-tatoeba-" + key[:24],
                    kind="phrase",
                    variety="kab",
                    script="Latn",
                    status="draft",
                    theme=classify(fr),
                    data=data,
                    pair_key=key,
                    search_text=searchable(data),
                )
            )
            if len(batch) >= 500:
                flush()
        flush()
        (folder / "import-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    finally:
        db.close()


class ImportBody(BaseModel):
    upload_id: str = Field(pattern="^[a-f0-9]{32}$")


def register_routes(app, db, admin):
    @app.post("/api/admin/tatoeba/preview", dependencies=[Depends(admin)])
    def upload(pairs: UploadFile = File(...), audio: UploadFile | None = File(default=None)):
        key = uuid.uuid4().hex
        folder = ROOT / key
        folder.mkdir(parents=True)
        paths = {}
        try:
            total = 0
            for role, file in [("pairs", pairs), ("audio", audio)]:
                if file is None:
                    continue
                name = file.filename or ""
                suffix = next(
                    (s for s in (".tar.bz2", ".tar.gz", ".bz2", ".gz") if name.endswith(s)), ".tsv"
                )
                path = folder / (role + suffix)
                with path.open("wb") as out:
                    while block := file.file.read(1024 * 1024):
                        total += len(block)
                        if total > MAX_UPLOAD:
                            raise ValueError(
                                "Maximum 128 Mo au total ; utiliser le script pour les exports plus grands."
                            )
                        out.write(block)
                paths[role] = path
            return {"upload_id": key, **prepare(folder, **paths)}
        except (ValueError, UnicodeError, csv.Error, tarfile.TarError, EOFError, OSError) as error:
            raise HTTPException(422, str(error))

    @app.post("/api/admin/tatoeba/import", dependencies=[Depends(admin)])
    def commit(body: ImportBody, s=Depends(db)):
        folder = ROOT / body.upload_id
        if not (folder / "report.json").exists():
            raise HTTPException(404, "Préparer les fichiers avant l’import")
        return import_prepared(s, folder)


def download_official(folder):
    """Download only the four relevant per-language weekly exports, using normal TLS/proxy."""
    from urllib.request import urlopen

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    base = "https://downloads.tatoeba.org/exports/per_language/"
    names = [
        "kab/kab_sentences_detailed.tsv.bz2",
        "fra/fra_sentences_detailed.tsv.bz2",
        "kab/kab-fra_links.tsv.bz2",
        "kab/kab_sentences_with_audio.tsv.bz2",
    ]
    paths = []
    for name in names:
        path = folder / Path(name).name
        temporary = path.with_suffix(path.suffix + ".part")
        print("Téléchargement : " + name, flush=True)
        try:
            with urlopen(base + name, timeout=60) as response, temporary.open("wb") as out:
                size = 0
                while block := response.read(1024 * 1024):
                    size += len(block)
                    if size > 1024 * 1024 * 1024:
                        raise ValueError("Export trop grand (maximum 1 Go par archive)")
                    out.write(block)
            temporary.replace(path)
            paths.append(path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    return {"sentences": paths[:2], "links": paths[2], "audio": paths[3]}

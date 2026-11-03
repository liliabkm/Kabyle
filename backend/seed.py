import json
import sys
from pathlib import Path
from sqlalchemy.exc import OperationalError
from app.db import Session
from app.models import Content
from app.main import ContentInput, validate_content
from app.catalog import (
    seed_catalog,
    seed_lesson_previews,
    seed_phrase_catalog,
    seed_complete_course,
)
from app.library import seed_categories
from app.reindex import reindex_content, limit_startup_lock_wait


def report(message):
    print(message, flush=True)


def seed():
    report("Initialisation du catalogue…")
    path = Path(__file__).resolve().parent.parent / "content/alphabet.json"
    with Session() as session:
        limit_startup_lock_wait(session)
        for data in json.loads(path.read_text()):
            item = ContentInput(**data)
            validate_content(item)
            if not session.get(Content, item.id):
                session.add(Content(**item.model_dump()))
        counts = seed_catalog(session)
        counts.update(seed_lesson_previews(session))
        counts["other_phrases_added"] = seed_phrase_catalog(session)
        session.flush()
        counts["categories_initialized"] = seed_categories(session)
        counts.update(seed_complete_course(session))
        # Preserve initialization and each completed backfill batch on Ctrl+C.
        session.commit()
        counts["reclassified"] = reindex_content(session, report=report)
    report("Import idempotent terminé : " + str(counts))


if __name__ == "__main__":
    try:
        seed()
    except KeyboardInterrupt:
        report(
            "Initialisation interrompue. Les lots terminés sont conservés ; relance bash scripts/start.sh pour reprendre."
        )
        sys.exit(130)
    except OperationalError as error:
        if getattr(error.orig, "sqlstate", None) == "55P03":
            report(
                "La base est occupée par une autre opération. Les lots terminés sont conservés. Termine cette opération puis relance le démarrage."
            )
            sys.exit(1)
        raise

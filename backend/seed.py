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
from app.curriculum import seed_curriculum


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
            existing = session.get(Content, item.id)
            if not existing:
                session.add(Content(**item.model_dump()))
            elif not existing.data.get('edited_at') and existing.data.get('latin') == item.data['latin'] and existing.data.get('tifinagh') == item.data['tifinagh']:
                # Enrich shipped letters without resetting editorial status or spelling.
                keys = ('alphabet_order', 'convention', 'examples', 'example_notice', 'unicode_name', 'unicode_codepoint')
                additions = {k: item.data[k] for k in keys}
                if any(existing.data.get(k) != v for k, v in additions.items()):
                    existing.data = {**existing.data, **additions}
        counts = seed_catalog(session)
        counts.update(seed_lesson_previews(session))
        counts["other_phrases_added"] = seed_phrase_catalog(session)
        session.flush()
        counts["categories_initialized"] = seed_categories(session)
        counts.update(seed_complete_course(session))
        # Preserve initialization and each completed backfill batch on Ctrl+C.
        counts["course_initialized"] = seed_curriculum(session)
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

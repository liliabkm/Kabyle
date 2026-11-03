import json
from pathlib import Path
from app.db import Session
from app.models import Content
from app.main import ContentInput, validate_content
from app.catalog import seed_catalog, seed_lesson_previews, seed_phrase_catalog, seed_complete_course
from app.library import seed_categories
path=Path(__file__).resolve().parent.parent / "content/alphabet.json"
with Session() as s:
    for data in json.loads(path.read_text()):
        item=ContentInput(**data);validate_content(item)
        if not s.get(Content,item.id): s.add(Content(**item.model_dump()))
    counts = seed_catalog(s)
    counts.update(seed_lesson_previews(s))
    counts["other_phrases_added"] = seed_phrase_catalog(s)
    s.flush()
    counts["categories_initialized"] = seed_categories(s)
    counts.update(seed_complete_course(s))
    from sqlalchemy import select,or_
    from app.learning import features
    from app.organization import VERSION
    # Backfill existing large corpora in bounded batches after migration 005.
    while True:
        rows=list(s.scalars(select(Content).where(or_((Content.kind=="phrase") & Content.learning_band.is_(None),(Content.kind=="word") & Content.lexeme_key.is_(None),Content.organization_version.is_(None),Content.organization_version!=VERSION)).order_by(Content.id).limit(500)))
        if not rows:break
        for row in rows:
            if row.kind in ("word","phrase") and not row.data.get("category_reviewed_at"):
                from app.organization import organize
                row.theme=organize(row.kind,row.data)["topics"][0]
            for key,value in features(row.kind,row.data).items():setattr(row,key,value)
        s.flush()
    s.commit()
print("Import idempotent terminé : alphabet et catalogue.", counts)

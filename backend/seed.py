import json
from pathlib import Path
from app.db import Session
from app.models import Content
from app.main import ContentInput, validate_content
from app.catalog import seed_catalog, seed_lesson_previews, seed_phrase_catalog
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
    s.commit()
print("Import idempotent terminé : alphabet et catalogue.", counts)

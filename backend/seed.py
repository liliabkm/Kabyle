import json
from pathlib import Path
from app.db import Session
from app.models import Content
from app.main import ContentInput, validate_content
path=Path(__file__).resolve().parent.parent / "content/alphabet.json"
with Session() as s:
    for data in json.loads(path.read_text()):
        item=ContentInput(**data);validate_content(item)
        if not s.get(Content,item.id): s.add(Content(**item.model_dump()))
    s.commit()
print("Alphabet importé (idempotent).")

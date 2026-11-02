"""Reproducible, insert-only catalog import. Never overwrite editorial work."""
import hashlib
import json
from pathlib import Path
from .models import Content, MediaAsset

ROOT = Path(__file__).resolve().parents[2] / "content"

def read_catalog():
    words = json.loads((ROOT / "catalog/words-librelingo.json").read_text())
    photos = json.loads((ROOT / "catalog/photos-fruits360.json").read_text())
    ids = [r["id"] for r in words + photos]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate catalog id")
    for item in words:
        if item["status"] != "draft" or not item["data"].get("publication_blockers"):
            raise ValueError("Source catalog words must remain blocked drafts")
    for asset in photos:
        data = asset["data"]
        path = (ROOT / "photos" / data["storage_key"]).resolve()
        if not path.is_relative_to((ROOT / "photos").resolve()):
            raise ValueError("Invalid media path")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != data["sha256"]:
            raise ValueError("Media checksum mismatch: " + asset["id"])
        if not all(data.get(k) for k in ("author", "license", "license_url", "source_url")):
            raise ValueError("Missing photo attribution")
    return words, photos

def seed_catalog(session):
    words, photos = read_catalog()  # Validate all inputs before writing anything.
    counts = {"words_added": 0, "photos_added": 0}
    for item in words:
        if session.get(Content, item["id"]) is None:
            session.add(Content(**item))
            counts["words_added"] += 1
    for asset in photos:
        if session.get(MediaAsset, asset["id"]) is None:
            session.add(MediaAsset(**asset))
            counts["photos_added"] += 1
    return counts

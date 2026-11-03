#!/usr/bin/env python3
"""Official Tatoeba ETL: aligned pairs OR sentence/link dumps, optional audio metadata."""
import argparse, json, sys, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.db import Session
from app.tatoeba import prepare, import_prepared, ROOT, download_official

p = argparse.ArgumentParser()
p.add_argument("--download", action="store_true")
p.add_argument("--pairs", type=Path)
p.add_argument("--sentences", type=Path, nargs="+", default=[])
p.add_argument("--links", type=Path)
p.add_argument("--audio", type=Path)
p.add_argument("--preview", action="store_true")
a = p.parse_args()
folder = ROOT / uuid.uuid4().hex
try:
    inputs = (
        download_official(folder / "downloads")
        if a.download
        else dict(pairs=a.pairs, sentences=a.sentences, links=a.links, audio=a.audio)
    )
    report = prepare(folder, **inputs)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not a.preview:
        with Session() as s:
            print(json.dumps(import_prepared(s, folder), ensure_ascii=False, indent=2))
except (ValueError, OSError) as e:
    p.exit(1, str(e) + "\n")

"""Reproducible semantic audit of every bundled lexical entry and sentence."""

import json, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.organization import organize, VERSION

out = []
moves = []
for filename in ("course-words.json", "course-phrases.json"):
    for item in json.loads((ROOT / "content/catalog" / filename).read_text()):
        o = organize(item["kind"], item["data"])
        out.append(
            {
                "id": item["id"],
                "kind": item["kind"],
                "latin": item["data"]["latin"],
                "french": item["data"]["french"],
                "source_theme": item["theme"],
                **o,
            }
        )
        if item["theme"] != o["topics"][0]:
            moves.append(
                {
                    "id": item["id"],
                    "latin": item["data"]["latin"],
                    "french": item["data"]["french"],
                    "before": item["theme"],
                    "after": o["topics"][0],
                }
            )
report = {
    "version": VERSION,
    "entries": len(out),
    "words": sum(x["kind"] == "word" for x in out),
    "phrases": sum(x["kind"] == "phrase" for x in out),
    "word_roles": dict(collections.Counter(x["role"] for x in out if x["kind"] == "word")),
    "word_concepts": len({x["concept"] for x in out if x["kind"] == "word" and x["concept"]}),
    "moves": moves,
    "issues": [x for x in out if x["role"] in ("review", "fragment", "unclassified")],
    "classifications": out,
}
(ROOT / "content/catalog/organization-report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n"
)
print(
    json.dumps(
        {k: v for k, v in report.items() if k not in ("classifications", "moves", "issues")},
        ensure_ascii=False,
    )
)
print("Reclassified:", len(moves), "Source issues:", len(report["issues"]))

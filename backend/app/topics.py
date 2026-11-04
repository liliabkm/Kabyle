"""Picture-led topic curriculum: vocabulary → attested contexts → practice."""

import re, unicodedata
from fastapi import Depends, HTTPException, Query
from sqlalchemy import select, func, true, or_, distinct, case
from sqlalchemy.dialects.postgresql import array
from .models import Content
from .learning import usable_audios
from .organization import TOPICS, concepts, organize, source_span, word_french


def topic_info(s, topic):
    if topic in TOPICS:
        return TOPICS[topic]
    exists = s.scalar(
        select(Content.id)
        .where(Content.status != "rejected", Content.topic_keys.contains([topic]))
        .limit(1)
    )
    if not exists:
        raise HTTPException(404, "Thème introuvable")
    from .library import category_label

    return category_label(topic), "Les mots et les phrases de ce thème."


def base(kind, topic):
    return [
        Content.kind == kind,
        Content.status != "rejected",
        Content.topic_keys.contains([topic]),
    ]


def count_words(s, topic):
    return s.scalar(
        select(func.count(distinct(func.coalesce(Content.concept_key, Content.id)))).where(
            *base("word", topic)
        )
    )


def gallery(s):
    entry = (
        func.jsonb_array_elements_text(Content.topic_keys)
        .table_valued("topic")
        .render_derived()
        .lateral()
    )
    stats = s.execute(
        select(
            entry.c.topic,
            Content.kind,
            func.count(distinct(func.coalesce(Content.concept_key, Content.id))),
        )
        .select_from(Content)
        .join(entry, true())
        .where(Content.status != "rejected")
        .group_by(entry.c.topic, Content.kind)
    ).all()
    counts = {}
    for topic, kind, count in stats:
        counts.setdefault(topic, {})[kind] = count
    if "grammaire" in counts:
        grammar_keys = [k for k, c in concepts().items() if c["role"] == "function"]
        counts["grammaire"]["phrase"] = s.scalar(
            select(func.count()).where(
                Content.kind == "phrase",
                Content.status != "rejected",
                Content.matched_concepts.op("?|")(array(grammar_keys)),
            )
        )
    result = []
    definitions = dict(TOPICS)
    for key in counts:
        if key not in definitions:
            definitions[key] = topic_info(s, key)
    for key, (title, description) in definitions.items():
        value = counts.get(key, {})
        if not value.get("word") and not value.get("phrase"):
            continue
        result.append(
            {
                "id": key,
                "title": title,
                "description": description,
                "word_count": value.get("word", 0),
                "phrase_count": value.get("phrase", 0),
                "resource": key
                in ("prenoms", "a-revoir", "autres-mots", "autres-phrases", "origines", "paix"),
            }
        )
    return {
        "topics": result,
        "letter_count": s.scalar(
            select(func.count()).where(Content.kind == "letter", Content.status != "rejected")
        ),
    }


def words(s, topic, offset, limit):
    title, description = topic_info(s, topic)
    candidates = (
        select(
            Content.id,
            func.row_number()
            .over(
                partition_by=func.coalesce(Content.concept_key, Content.id),
                order_by=(Content.learning_rank, Content.id),
            )
            .label("rank"),
        )
        .where(*base("word", topic))
        .subquery()
    )
    ids = list(s.scalars(select(candidates.c.id).where(candidates.c.rank == 1)))
    # A topic has at most the lexical concepts, not hundreds of raw inflections.
    rows = (
        list(
            s.scalars(
                select(Content)
                .where(Content.id.in_(ids))
                .order_by(Content.learning_rank, Content.id)
            )
        )
        if ids
        else []
    )
    order = {
        "animaux": [
            "chien",
            "chat",
            "cheval",
            "canard",
            "ours",
            "lion",
            "souris",
            "elephant",
            "ane",
            "poisson",
            "patte",
            "animal",
        ],
        "fruits": ["fraise", "raisin", "figue"],
        "boissons": ["eau", "lait", "cafe", "the", "goutte", "biere", "vin"],
        "nombres": ["nombre-" + str(n) for n in (0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 20)],
    }.get(topic, [])
    rows.sort(
        key=lambda c: (
            order.index(c.concept_key) if c.concept_key in order else 999,
            concepts()
            .get(c.concept_key, {})
            .get("label", str(c.data.get("french") or ""))
            .casefold(),
        )
    )
    page = rows[offset : offset + limit]
    keys = [c.concept_key for c in page if c.concept_key]
    forms = {key: [] for key in keys}
    if keys:
        for c in s.scalars(
            select(Content)
            .where(
                Content.kind == "word", Content.status != "rejected", Content.concept_key.in_(keys)
            )
            .order_by(Content.learning_rank, Content.id)
        ):
            forms[c.concept_key].append(
                {
                    "id": c.id,
                    "latin": c.data["latin"],
                    "french": c.data.get("french"),
                    "status": c.status,
                    "synonyms": (
                        c.data.get("synonyms", [])
                        if isinstance(c.data.get("synonyms", []), list)
                        else [c.data["synonyms"]]
                    ),
                }
            )
    items = []
    for c in page:
        concept = concepts().get(c.concept_key, {})
        items.append(
            {
                "id": c.id,
                "concept": c.concept_key,
                "latin": c.data["latin"],
                "french": c.data.get("french"),
                "label": concept.get(
                    "label",
                    (
                        re.sub(r"\s*\((name|nom)\)", "", c.data.get("french") or "", flags=re.I)
                        if c.learning_role == "name"
                        else (c.data.get("french") or "Traduction à renseigner")
                    ),
                ),
                "art": concept.get("art"),
                "status": c.status,
                "role": c.learning_role,
                "forms": forms.get(c.concept_key, []),
                "sources": c.data.get("sources", []),
                "image": (c.data.get("images") or [None])[0],
                "issue": (
                    organize("word", c.data)["reason"]
                    if c.learning_role in ("review", "fragment", "unclassified")
                    else None
                ),
            }
        )
    return {"items": items, "total": len(rows), "title": title, "description": description}


def word_forms(s, key):
    forms = []
    for c in s.scalars(
        select(Content).where(
            Content.kind == "word", Content.status != "rejected", Content.concept_key == key
        )
    ):
        forms.append(c.data["latin"])
        aliases = c.data.get("synonyms", [])
        forms.extend(aliases if isinstance(aliases, list) else [aliases])
    return [x for x in forms if isinstance(x, str) and x.strip()]


def phrases(s, topic, word, offset, limit):
    title, description = topic_info(s, topic)
    predicates = base("phrase", topic)
    forms = []
    if topic == "grammaire":
        keys = [k for k, c in concepts().items() if c["role"] == "function"]
        predicates = [
            Content.kind == "phrase",
            Content.status != "rejected",
            Content.matched_concepts.op("?|")(array(keys)),
        ]
    if word:
        if word not in concepts() and not word.startswith(("prenom-", "manual-")):
            raise HTTPException(404, "Mot introuvable")
        forms = word_forms(s, word)
        if not forms:
            return {"items": [], "total": 0}
        pattern = (
            r"(^|[^[:alnum:]_])("
            + "|".join(re.escape(unicodedata.normalize("NFC", f)) for f in forms)
            + r")($|[^[:alnum:]_])"
        )
        predicates.append(Content.data["latin"].as_string().op("~*")(pattern))
        if word.startswith("manual-"):
            labels = [
                word_french(c.data.get("french", ""))
                for c in s.scalars(
                    select(Content).where(Content.kind == "word", Content.concept_key == word)
                )
            ]
            predicates.append(
                or_(
                    *[
                        Content.data["french"]
                        .as_string()
                        .op("~*")(r"(^|[^[:alnum:]_])" + re.escape(label) + r"($|[^[:alnum:]_])")
                        for label in labels
                        if label
                    ]
                )
            )
        else:
            predicates.append(Content.matched_concepts.contains([word]))
    total = s.scalar(select(func.count()).where(*predicates))
    rows = s.scalars(
        select(Content)
        .where(*predicates)
        .order_by(
            case(
                (Content.learning_band == "short", 0),
                (Content.learning_band == "medium", 1),
                else_=2,
            ),
            func.length(Content.data["latin"].as_string()),
            Content.id,
        )
        .offset(offset)
        .limit(limit)
    )
    return {
        "items": [
            {
                "id": c.id,
                "latin": c.data["latin"],
                "french": c.data["french"],
                "status": c.status,
                "has_audio": bool(usable_audios(c.data)),
                "audios": usable_audios(c.data),
                "highlight": source_span(c.data["latin"], forms) if word else None,
                "concepts": c.matched_concepts,
                "topics": c.topic_keys,
            }
            for c in rows
        ],
        "total": total,
    }


def register_routes(app, db, admin):
    @app.get("/api/topics")
    def get_topics(s=Depends(db)):
        return gallery(s)

    @app.get("/api/topics/{topic}/words")
    def get_words(
        topic: str, offset: int = Query(0, ge=0), limit: int = Query(24, ge=1, le=60), s=Depends(db)
    ):
        return words(s, topic, offset, limit)

    @app.get("/api/topics/{topic}/phrases")
    def get_phrases(
        topic: str,
        word: str = "",
        offset: int = Query(0, ge=0),
        limit: int = Query(12, ge=1, le=36),
        s=Depends(db),
    ):
        return phrases(s, topic, word, offset, limit)

    @app.get("/api/admin/organization", dependencies=[Depends(admin)])
    def audit(s=Depends(db)):
        roles = dict(
            s.execute(
                select(Content.learning_role, func.count())
                .where(Content.kind == "word")
                .group_by(Content.learning_role)
            ).all()
        )
        return {
            "roles": roles,
            "topics": gallery(s)["topics"],
            "issues": [
                {
                    "id": c.id,
                    "latin": c.data["latin"],
                    "french": c.data.get("french"),
                    "reason": organize("word", c.data)["reason"],
                }
                for c in s.scalars(
                    select(Content)
                    .where(
                        Content.kind == "word",
                        Content.learning_role.in_(["review", "unclassified"]),
                    )
                    .order_by(Content.id)
                    .limit(100)
                )
            ],
        }

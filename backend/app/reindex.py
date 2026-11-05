"""Resumable startup classification, with bounded memory and a forward-only cursor."""

from sqlalchemy import bindparam, func, or_, select, text, update
from .learning import editorial_features, features
from .models import Content
from .organization import VERSION
from .search import pair_key, searchable


def pending_classification():
    return or_(
        (Content.kind == "phrase") & Content.learning_band.is_(None),
        (Content.kind == "word") & Content.lexeme_key.is_(None),
        Content.search_text == "",
        Content.organization_version.is_(None),
        Content.organization_version != VERSION,
    )


def limit_startup_lock_wait(session):
    if session.bind.dialect.name == "postgresql":
        session.execute(text("SET LOCAL lock_timeout = '10s'"))


def reindex_content(session, batch_size=500, report=None):
    """Commit each completed batch; a cancelled batch alone is rolled back.

    Only derived columns and an automatic theme are written. Texts, sources,
    review dates and validation statuses are never rewritten by the backfill.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    if session.new or session.dirty or session.deleted:
        raise RuntimeError("Commit catalog changes before starting the reindex")
    condition = pending_classification()
    if report:
        report("Vérification du classement…")
    # Count reads only small scalar columns, not the full source JSON corpus.
    limit_startup_lock_wait(session)
    total, upper = session.execute(
        select(func.count(), func.max(Content.id)).where(condition)
    ).one()
    if not total:
        session.commit()
        if report:
            report("Classement déjà à jour.")
        return 0
    if report:
        report(f"Classement : {total} fiches à traiter, par lots de {batch_size}.")
    processed = 0
    cursor = None
    table = Content.__table__
    statement = update(table).where(table.c.id == bindparam("_content_id"))
    while True:
        # Short row locks prevent concurrent edits being used with stale metadata.
        # Never wait indefinitely behind another database operation.
        limit_startup_lock_wait(session)
        query = (
            select(Content.id, Content.kind, Content.theme, Content.data)
            .where(condition, Content.id <= upper)
            .order_by(Content.id)
            .limit(batch_size)
            .with_for_update()
        )
        if cursor is not None:
            query = query.where(Content.id > cursor)
        rows = session.execute(query).mappings().all()
        if not rows:
            break
        updates = []
        for row in rows:
            values = features(row["kind"], row["data"])
            theme = row["theme"]
            if row["kind"] in ("word", "phrase") and not row["data"].get("category_reviewed_at"):
                theme = values["topic_keys"][0]
            values = editorial_features(row["kind"], row["data"], theme, values)
            updates.append(
                {
                    "_content_id": row["id"],
                    **values,
                    "theme": theme,
                    "structured_dirty": True,
                    "search_text": searchable(row["data"]),
                    "pair_key": pair_key(row["kind"], row["data"]),
                }
            )
        # Core executemany bypasses ORM callbacks: classify once, not three times.
        session.execute(statement, updates)
        ids = [row["id"] for row in rows]
        remaining = session.scalar(select(func.count()).where(Content.id.in_(ids), condition))
        if remaining:
            session.rollback()
            raise RuntimeError("Classement incomplet du lot ; arrêt sans boucle infinie.")
        session.commit()
        cursor = rows[-1]["id"]
        processed += len(rows)
        if report:
            report(f"Classement : {processed}/{total} fiches enregistrées.")
    remaining = session.scalar(select(func.count()).where(condition, Content.id <= upper))
    session.commit()
    if remaining:
        raise RuntimeError(
            "De nouvelles fiches ont changé pendant le classement ; relancer le démarrage."
        )
    if report:
        report("Classement terminé. Les lots enregistrés sont conservés en cas d’interruption.")
    return processed

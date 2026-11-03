from sqlalchemy import String, JSON, ForeignKey, DateTime, UniqueConstraint, Text, event, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from .db import Base
class Content(Base):
    __tablename__ = "content"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String)
    variety: Mapped[str] = mapped_column(String, default="kab")
    script: Mapped[str] = mapped_column(String, default="Tfng")
    theme: Mapped[str] = mapped_column(String, default="alphabet")
    status: Mapped[str] = mapped_column(String, default="draft")
    data: Mapped[dict] = mapped_column(JSON)
    search_text: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    pair_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    learning_band: Mapped[str | None] = mapped_column(String(16),nullable=True)
    has_audio: Mapped[bool] = mapped_column(Boolean,nullable=False,default=False,server_default="false")
    lexeme_key: Mapped[str | None] = mapped_column(String(64),nullable=True)
    topic_keys: Mapped[list] = mapped_column(JSONB,nullable=False,default=list,server_default="[]")
    matched_concepts: Mapped[list] = mapped_column(JSONB,nullable=False,default=list,server_default="[]")
    concept_key: Mapped[str | None] = mapped_column(String(100),nullable=True)
    learning_role: Mapped[str | None] = mapped_column(String(24),nullable=True)
    learning_rank: Mapped[int] = mapped_column(default=999,server_default="999")
    organization_version: Mapped[str | None] = mapped_column(String(32),nullable=True)
class Progress(Base):
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("learner", "content_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    learner: Mapped[str] = mapped_column(String, index=True)
    content_id: Mapped[str] = mapped_column(ForeignKey("content.id"))
    correct: Mapped[int] = mapped_column(default=0)
    errors: Mapped[int] = mapped_column(default=0)
    streak: Mapped[int] = mapped_column(default=0)
    due: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
class Attempt(Base):
    __tablename__ = "attempt"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    learner: Mapped[str] = mapped_column(String)
    content_id: Mapped[str] = mapped_column(ForeignKey("content.id"))
    correct: Mapped[bool]

class MediaAsset(Base):
    __tablename__ = "media_asset"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, default="photo")
    theme: Mapped[str] = mapped_column(String)
    label_fr: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="available")
    data: Mapped[dict] = mapped_column(JSON)

class Lesson(Base):
    __tablename__ = "lesson"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    theme: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="draft")
    data: Mapped[dict] = mapped_column(JSON)

# Maintain a folded search field so large TSV catalogs are filtered in SQL.
from .search import searchable, pair_key

@event.listens_for(Content, 'before_insert')
@event.listens_for(Content, 'before_update')
def update_search_text(mapper, connection, target):
    target.search_text=searchable(target.data)
    target.pair_key=pair_key(target.kind,target.data)
    from .learning import features, editorial_features
    from .organization import VERSION
    state=inspect(target)
    previous_role=target.learning_role
    first_organization=target.organization_version!=VERSION
    old_data=state.attrs.data.history.deleted
    french_changed=bool(old_data and old_data[0].get('french')!=target.data.get('french'))
    explicit_theme_change=state.persistent and state.attrs.theme.history.has_changes()
    auto_category=target.data.get('category_status')=='suggested' or target.data.get('complete_course_revision')
    implicit_category=target.theme in (None,'alphabet')
    values=features(target.kind,target.data)
    for key,value in values.items():setattr(target,key,value)
    if target.kind in ('word','phrase') and not target.data.get('category_reviewed_at') and not explicit_theme_change and (first_organization or state.pending or french_changed or previous_role!=target.learning_role) and (auto_category or implicit_category):
        target.theme=target.topic_keys[0]
    for key,value in editorial_features(target.kind,target.data,target.theme,values).items():setattr(target,key,value)

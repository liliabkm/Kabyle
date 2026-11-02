from sqlalchemy import String, JSON, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
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

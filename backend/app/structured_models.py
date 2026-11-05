"""Relational corpus lineage, lexical inventory and versioned learning paths."""
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, Boolean, JSON, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def now():
    return datetime.now(timezone.utc)

class Language(Base):
    __tablename__ = 'language'
    code: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

class CorpusSource(Base):
    __tablename__ = 'corpus_source'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    homepage: Mapped[str] = mapped_column(Text)

class SourceSnapshot(Base):
    __tablename__ = 'source_snapshot'
    __table_args__ = (UniqueConstraint('source_id', 'version_key'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey('corpus_source.id'))
    version_key: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON)
    # A digest identifies a file; it does not establish that the raw file is archived.
    archive_path: Mapped[str | None] = mapped_column(Text, nullable=True)

class ContentProvenance(Base):
    __tablename__ = 'content_provenance'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    content_id: Mapped[str] = mapped_column(ForeignKey('content.id', ondelete='CASCADE'), index=True)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey('source_snapshot.id'))
    citation: Mapped[dict] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Lexeme(Base):
    __tablename__ = 'lexeme'
    __table_args__ = (UniqueConstraint('language_code', 'semantic_key'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    language_code: Mapped[str] = mapped_column(ForeignKey('language.code'))
    semantic_key: Mapped[str] = mapped_column(String(160))
    lemma: Mapped[str] = mapped_column(Text)
    lemma_rank: Mapped[int] = mapped_column(default=999)
    part_of_speech: Mapped[str | None] = mapped_column(String(40), nullable=True)
    review_status: Mapped[str] = mapped_column(String(24), default='proposed')

class LexemeForm(Base):
    __tablename__ = 'lexeme_form'
    __table_args__ = (UniqueConstraint('lexeme_id', 'script', 'normalized_form'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lexeme_id: Mapped[str] = mapped_column(ForeignKey('lexeme.id', ondelete='CASCADE'), index=True)
    script: Mapped[str] = mapped_column(String(8))
    text: Mapped[str] = mapped_column(Text)
    normalized_form: Mapped[str] = mapped_column(Text)
    form_type: Mapped[str] = mapped_column(String(24))

class LexemeTranslation(Base):
    __tablename__ = 'lexeme_translation'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lexeme_id: Mapped[str] = mapped_column(ForeignKey('lexeme.id', ondelete='CASCADE'), index=True)
    language_code: Mapped[str] = mapped_column(ForeignKey('language.code'))
    text: Mapped[str] = mapped_column(Text)

class LexemeContent(Base):
    __tablename__ = 'lexeme_content'
    content_id: Mapped[str] = mapped_column(ForeignKey('content.id', ondelete='CASCADE'), primary_key=True)
    lexeme_id: Mapped[str] = mapped_column(ForeignKey('lexeme.id'), index=True)
    translation_id: Mapped[str] = mapped_column(ForeignKey('lexeme_translation.id'))

class FormEvidence(Base):
    __tablename__ = 'form_evidence'
    content_id: Mapped[str] = mapped_column(ForeignKey('content.id', ondelete='CASCADE'), primary_key=True)
    form_id: Mapped[str] = mapped_column(ForeignKey('lexeme_form.id'), primary_key=True)

class Sentence(Base):
    __tablename__ = 'sentence'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    language_code: Mapped[str] = mapped_column(ForeignKey('language.code'))
    text: Mapped[str] = mapped_column(Text)
    script: Mapped[str] = mapped_column(String(8))

class SentenceTranslation(Base):
    __tablename__ = 'sentence_translation'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sentence_id: Mapped[str] = mapped_column(ForeignKey('sentence.id'), index=True)
    language_code: Mapped[str] = mapped_column(ForeignKey('language.code'))
    text: Mapped[str] = mapped_column(Text)

class ContentSentence(Base):
    __tablename__ = 'content_sentence'
    content_id: Mapped[str] = mapped_column(ForeignKey('content.id', ondelete='CASCADE'), primary_key=True)
    sentence_id: Mapped[str] = mapped_column(ForeignKey('sentence.id'), index=True)
    translation_id: Mapped[str] = mapped_column(ForeignKey('sentence_translation.id'))
    token_count: Mapped[int] = mapped_column()
    cefr_level: Mapped[str | None] = mapped_column(String(4), nullable=True)
    cefr_status: Mapped[str] = mapped_column(String(30), default='unassigned')

class AudioRecording(Base):
    __tablename__ = 'audio_recording'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    url: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(Text)
    license: Mapped[str] = mapped_column(Text)
    voice_kind: Mapped[str] = mapped_column(String(24), default='unspecified')
    metadata_json: Mapped[dict] = mapped_column(JSON)

class SentenceAudio(Base):
    __tablename__ = 'sentence_audio'
    content_id: Mapped[str] = mapped_column(ForeignKey('content.id', ondelete='CASCADE'), primary_key=True)
    sentence_id: Mapped[str] = mapped_column(ForeignKey('sentence.id'), primary_key=True)
    audio_id: Mapped[str] = mapped_column(ForeignKey('audio_recording.id'), primary_key=True)

class OrganizationJob(Base):
    __tablename__ = 'organization_job'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pipeline_version: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(24))
    processed: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Course(Base):
    __tablename__ = 'course'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_language: Mapped[str] = mapped_column(ForeignKey('language.code'))
    target_language: Mapped[str] = mapped_column(ForeignKey('language.code'))
    title: Mapped[str] = mapped_column(Text)
    manifest_version: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default='draft')

class CourseLevel(Base):
    __tablename__ = 'course_level'
    __table_args__ = (UniqueConstraint('course_id', 'code'), UniqueConstraint('course_id', 'position'))
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    course_id: Mapped[str] = mapped_column(ForeignKey('course.id'))
    code: Mapped[str] = mapped_column(String(8))
    title: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column()
    review_status: Mapped[str] = mapped_column(String(24), default='proposed')

class CourseUnit(Base):
    __tablename__ = 'course_unit'
    __table_args__ = (UniqueConstraint('level_id', 'position'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    level_id: Mapped[str] = mapped_column(ForeignKey('course_level.id'))
    title: Mapped[str] = mapped_column(Text)
    objective: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column()
    topic: Mapped[str] = mapped_column(String(60))

class CourseLesson(Base):
    __tablename__ = 'course_lesson'
    __table_args__ = (UniqueConstraint('unit_id', 'position'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    unit_id: Mapped[str] = mapped_column(ForeignKey('course_unit.id'))
    title: Mapped[str] = mapped_column(Text)
    objective: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(24), default='draft')
    revision: Mapped[int] = mapped_column(default=1)
    origin: Mapped[str] = mapped_column(String(30), default='admin')

class LessonActivity(Base):
    __tablename__ = 'lesson_activity'
    __table_args__ = (UniqueConstraint('lesson_id', 'revision', 'position'), CheckConstraint("kind IN ('recall','order','dictation')"))
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey('course_lesson.id', ondelete='CASCADE'), index=True)
    content_id: Mapped[str] = mapped_column(ForeignKey('content.id'))
    revision: Mapped[int] = mapped_column(default=1)
    position: Mapped[int] = mapped_column()
    kind: Mapped[str] = mapped_column(String(24))

class LessonPrerequisite(Base):
    __tablename__ = 'lesson_prerequisite'
    __table_args__ = (CheckConstraint('lesson_id != prerequisite_id'),)
    lesson_id: Mapped[str] = mapped_column(ForeignKey('course_lesson.id', ondelete='CASCADE'), primary_key=True)
    prerequisite_id: Mapped[str] = mapped_column(ForeignKey('course_lesson.id'), primary_key=True)

class LessonRun(Base):
    __tablename__ = 'lesson_run'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey('course_lesson.id'), index=True)
    learner: Mapped[str] = mapped_column(String(64), index=True)
    revision: Mapped[int] = mapped_column()
    snapshot: Mapped[dict] = mapped_column(JSON)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class LessonActivityAttempt(Base):
    __tablename__ = 'lesson_activity_attempt'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey('lesson_run.id', ondelete='CASCADE'), index=True)
    activity_id: Mapped[str] = mapped_column(ForeignKey('lesson_activity.id'))
    request_hash: Mapped[str] = mapped_column(String(64))
    correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

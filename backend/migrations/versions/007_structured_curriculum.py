"""Relational corpus and ordered courses; additive migration, no source deletion."""
from alembic import op
import sqlalchemy as sa
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None
# Frozen DDL, independent of future application models.
DDL = r"""
CREATE TABLE audio_recording (
	id VARCHAR(64) NOT NULL,
	url TEXT NOT NULL,
	author TEXT NOT NULL,
	license TEXT NOT NULL,
	voice_kind VARCHAR(24) NOT NULL,
	metadata_json JSON NOT NULL,
	PRIMARY KEY (id)
);
CREATE TABLE corpus_source (
	id VARCHAR(64) NOT NULL,
	name VARCHAR(200) NOT NULL,
	homepage TEXT NOT NULL,
	PRIMARY KEY (id)
);
CREATE TABLE language (
	code VARCHAR(12) NOT NULL,
	name VARCHAR(100) NOT NULL,
	PRIMARY KEY (code)
);
CREATE TABLE organization_job (
	id VARCHAR(64) NOT NULL,
	pipeline_version VARCHAR(32) NOT NULL,
	status VARCHAR(24) NOT NULL,
	processed INTEGER NOT NULL,
	started_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
);
CREATE TABLE course (
	id VARCHAR(64) NOT NULL,
	source_language VARCHAR(12) NOT NULL,
	target_language VARCHAR(12) NOT NULL,
	title TEXT NOT NULL,
	manifest_version VARCHAR(64) NOT NULL,
	status VARCHAR(24) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(source_language) REFERENCES language (code),
	FOREIGN KEY(target_language) REFERENCES language (code)
);
CREATE TABLE lexeme (
	id VARCHAR(64) NOT NULL,
	language_code VARCHAR(12) NOT NULL,
	semantic_key VARCHAR(160) NOT NULL,
	lemma TEXT NOT NULL,
	lemma_rank INTEGER NOT NULL,
	part_of_speech VARCHAR(40),
	review_status VARCHAR(24) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (language_code, semantic_key),
	FOREIGN KEY(language_code) REFERENCES language (code)
);
CREATE TABLE sentence (
	id VARCHAR(64) NOT NULL,
	language_code VARCHAR(12) NOT NULL,
	text TEXT NOT NULL,
	script VARCHAR(8) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(language_code) REFERENCES language (code)
);
CREATE TABLE source_snapshot (
	id VARCHAR(64) NOT NULL,
	source_id VARCHAR(64) NOT NULL,
	version_key VARCHAR(64) NOT NULL,
	metadata_json JSON NOT NULL,
	archive_path TEXT,
	PRIMARY KEY (id),
	UNIQUE (source_id, version_key),
	FOREIGN KEY(source_id) REFERENCES corpus_source (id)
);
CREATE TABLE content_provenance (
	id VARCHAR(64) NOT NULL,
	content_id VARCHAR NOT NULL,
	snapshot_id VARCHAR(64) NOT NULL,
	citation JSON NOT NULL,
	active BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(content_id) REFERENCES content (id) ON DELETE CASCADE,
	FOREIGN KEY(snapshot_id) REFERENCES source_snapshot (id)
);
CREATE INDEX ix_content_provenance_content_id ON content_provenance (content_id);
CREATE TABLE course_level (
	id VARCHAR(64) NOT NULL,
	course_id VARCHAR(64) NOT NULL,
	code VARCHAR(8) NOT NULL,
	title TEXT NOT NULL,
	position INTEGER NOT NULL,
	review_status VARCHAR(24) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (course_id, code),
	UNIQUE (course_id, position),
	FOREIGN KEY(course_id) REFERENCES course (id)
);
CREATE TABLE lexeme_form (
	id VARCHAR(64) NOT NULL,
	lexeme_id VARCHAR(64) NOT NULL,
	script VARCHAR(8) NOT NULL,
	text TEXT NOT NULL,
	normalized_form TEXT NOT NULL,
	form_type VARCHAR(24) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (lexeme_id, script, normalized_form),
	FOREIGN KEY(lexeme_id) REFERENCES lexeme (id) ON DELETE CASCADE
);
CREATE INDEX ix_lexeme_form_lexeme_id ON lexeme_form (lexeme_id);
CREATE TABLE lexeme_translation (
	id VARCHAR(64) NOT NULL,
	lexeme_id VARCHAR(64) NOT NULL,
	language_code VARCHAR(12) NOT NULL,
	text TEXT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(lexeme_id) REFERENCES lexeme (id) ON DELETE CASCADE,
	FOREIGN KEY(language_code) REFERENCES language (code)
);
CREATE INDEX ix_lexeme_translation_lexeme_id ON lexeme_translation (lexeme_id);
CREATE TABLE sentence_audio (
	content_id VARCHAR NOT NULL,
	sentence_id VARCHAR(64) NOT NULL,
	audio_id VARCHAR(64) NOT NULL,
	PRIMARY KEY (content_id, sentence_id, audio_id),
	FOREIGN KEY(content_id) REFERENCES content (id) ON DELETE CASCADE,
	FOREIGN KEY(sentence_id) REFERENCES sentence (id),
	FOREIGN KEY(audio_id) REFERENCES audio_recording (id)
);
CREATE TABLE sentence_translation (
	id VARCHAR(64) NOT NULL,
	sentence_id VARCHAR(64) NOT NULL,
	language_code VARCHAR(12) NOT NULL,
	text TEXT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(sentence_id) REFERENCES sentence (id),
	FOREIGN KEY(language_code) REFERENCES language (code)
);
CREATE INDEX ix_sentence_translation_sentence_id ON sentence_translation (sentence_id);
CREATE TABLE content_sentence (
	content_id VARCHAR NOT NULL,
	sentence_id VARCHAR(64) NOT NULL,
	translation_id VARCHAR(64) NOT NULL,
	token_count INTEGER NOT NULL,
	cefr_level VARCHAR(4),
	cefr_status VARCHAR(30) NOT NULL,
	PRIMARY KEY (content_id),
	FOREIGN KEY(content_id) REFERENCES content (id) ON DELETE CASCADE,
	FOREIGN KEY(sentence_id) REFERENCES sentence (id),
	FOREIGN KEY(translation_id) REFERENCES sentence_translation (id)
);
CREATE INDEX ix_content_sentence_sentence_id ON content_sentence (sentence_id);
CREATE TABLE course_unit (
	id VARCHAR(64) NOT NULL,
	level_id VARCHAR(64) NOT NULL,
	title TEXT NOT NULL,
	objective TEXT NOT NULL,
	position INTEGER NOT NULL,
	topic VARCHAR(60) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (level_id, position),
	FOREIGN KEY(level_id) REFERENCES course_level (id)
);
CREATE TABLE form_evidence (
	content_id VARCHAR NOT NULL,
	form_id VARCHAR(64) NOT NULL,
	PRIMARY KEY (content_id, form_id),
	FOREIGN KEY(content_id) REFERENCES content (id) ON DELETE CASCADE,
	FOREIGN KEY(form_id) REFERENCES lexeme_form (id)
);
CREATE TABLE lexeme_content (
	content_id VARCHAR NOT NULL,
	lexeme_id VARCHAR(64) NOT NULL,
	translation_id VARCHAR(64) NOT NULL,
	PRIMARY KEY (content_id),
	FOREIGN KEY(content_id) REFERENCES content (id) ON DELETE CASCADE,
	FOREIGN KEY(lexeme_id) REFERENCES lexeme (id),
	FOREIGN KEY(translation_id) REFERENCES lexeme_translation (id)
);
CREATE INDEX ix_lexeme_content_lexeme_id ON lexeme_content (lexeme_id);
CREATE TABLE course_lesson (
	id VARCHAR(64) NOT NULL,
	unit_id VARCHAR(64) NOT NULL,
	title TEXT NOT NULL,
	objective TEXT NOT NULL,
	position INTEGER NOT NULL,
	status VARCHAR(24) NOT NULL,
	revision INTEGER NOT NULL,
	origin VARCHAR(30) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (unit_id, position),
	FOREIGN KEY(unit_id) REFERENCES course_unit (id)
);
CREATE TABLE lesson_activity (
	id VARCHAR(64) NOT NULL,
	lesson_id VARCHAR(64) NOT NULL,
	content_id VARCHAR NOT NULL,
	revision INTEGER NOT NULL,
	position INTEGER NOT NULL,
	kind VARCHAR(24) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (lesson_id, revision, position),
	CHECK (kind IN ('recall','order','dictation')),
	FOREIGN KEY(lesson_id) REFERENCES course_lesson (id) ON DELETE CASCADE,
	FOREIGN KEY(content_id) REFERENCES content (id)
);
CREATE INDEX ix_lesson_activity_lesson_id ON lesson_activity (lesson_id);
CREATE TABLE lesson_prerequisite (
	lesson_id VARCHAR(64) NOT NULL,
	prerequisite_id VARCHAR(64) NOT NULL,
	PRIMARY KEY (lesson_id, prerequisite_id),
	CHECK (lesson_id != prerequisite_id),
	FOREIGN KEY(lesson_id) REFERENCES course_lesson (id) ON DELETE CASCADE,
	FOREIGN KEY(prerequisite_id) REFERENCES course_lesson (id)
);
CREATE TABLE lesson_run (
	id VARCHAR(64) NOT NULL,
	lesson_id VARCHAR(64) NOT NULL,
	learner VARCHAR(64) NOT NULL,
	revision INTEGER NOT NULL,
	snapshot JSON NOT NULL,
	passed BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(lesson_id) REFERENCES course_lesson (id)
);
CREATE INDEX ix_lesson_run_learner ON lesson_run (learner);
CREATE INDEX ix_lesson_run_lesson_id ON lesson_run (lesson_id);
CREATE TABLE lesson_activity_attempt (
	id VARCHAR(100) NOT NULL,
	run_id VARCHAR(64) NOT NULL,
	activity_id VARCHAR(64) NOT NULL,
	request_hash VARCHAR(64) NOT NULL,
	correct BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(run_id) REFERENCES lesson_run (id) ON DELETE CASCADE,
	FOREIGN KEY(activity_id) REFERENCES lesson_activity (id)
);
CREATE INDEX ix_lesson_activity_attempt_run_id ON lesson_activity_attempt (run_id);
"""

def upgrade():
    op.add_column('content', sa.Column('structured_dirty', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index('ix_content_structure_pending', 'content', ['id'], postgresql_where=sa.text('structured_dirty = true'))
    for statement in DDL.split(';'):
        if statement.strip(): op.execute(statement)

def downgrade():
    op.drop_table('lesson_activity_attempt')
    op.drop_table('lesson_run')
    op.drop_table('lesson_prerequisite')
    op.drop_table('lesson_activity')
    op.drop_table('course_lesson')
    op.drop_table('lexeme_content')
    op.drop_table('form_evidence')
    op.drop_table('course_unit')
    op.drop_table('content_sentence')
    op.drop_table('sentence_translation')
    op.drop_table('sentence_audio')
    op.drop_table('lexeme_translation')
    op.drop_table('lexeme_form')
    op.drop_table('course_level')
    op.drop_table('content_provenance')
    op.drop_table('source_snapshot')
    op.drop_table('sentence')
    op.drop_table('lexeme')
    op.drop_table('course')
    op.drop_table('organization_job')
    op.drop_table('language')
    op.drop_table('corpus_source')
    op.drop_table('audio_recording')
    op.drop_index('ix_content_structure_pending', table_name='content')
    op.drop_column('content', 'structured_dirty')

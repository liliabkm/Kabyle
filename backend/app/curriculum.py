"""Versioned courses reference original content; anonymous runs are server graded."""
import hashlib
import json
import random
import uuid
from pathlib import Path
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from .models import Content
from .structured_models import Course, CourseLevel, CourseUnit, CourseLesson, LessonActivity, LessonPrerequisite, LessonRun, LessonActivityAttempt
from .data_pipeline import languages, digest
from .learning import usable_audios
from .phrase_practice import normalized

MANIFEST = Path(__file__).resolve().parents[2] / 'content/curriculum/kab-from-fr-v1.json'


def seed_curriculum(s):
    languages(s)
    spec = json.loads(MANIFEST.read_text())
    if s.get(Course, spec['id']): return False
    s.add(Course(id=spec['id'], source_language=spec['source_language'], target_language=spec['target_language'], title=spec['title'], manifest_version=spec['version'], status='draft'))
    s.flush()
    pending = []
    for i, level in enumerate(spec['levels']):
        level_id = spec['id'] + '-' + level['code']
        s.add(CourseLevel(id=level_id, course_id=spec['id'], code=level['code'], title=level['title'], position=i, review_status='proposed'))
        s.flush()
        for j, unit in enumerate(level['units']):
            s.add(CourseUnit(id=unit['id'], level_id=level_id, title=unit['title'], objective=unit['objective'], position=j, topic=unit['topic']))
            s.flush()
            for k, lesson in enumerate(unit['lessons']):
                # Manifest failures remain visible errors rather than fabricated substitutes.
                for activity in lesson['activities']:
                    if not s.get(Content, activity['content_id']): raise ValueError('Source manquante pour le parcours : ' + activity['content_id'])
                s.add(CourseLesson(id=lesson['id'], unit_id=unit['id'], title=lesson['title'], objective=lesson['objective'], position=k, status='draft', revision=1, origin='manifest:' + spec['version']))
                s.flush()
                for n, activity in enumerate(lesson['activities']):
                    s.add(LessonActivity(id=lesson['id'] + '-1-' + str(n), lesson_id=lesson['id'], revision=1, position=n, **activity))
                pending.extend((lesson['id'], key) for key in lesson['prerequisites'])
    s.flush()
    for lesson, prerequisite in pending: s.add(LessonPrerequisite(lesson_id=lesson, prerequisite_id=prerequisite))
    return True


def lesson_bundle(s, lesson_id):
    lesson = s.get(CourseLesson, lesson_id)
    if not lesson or lesson.status == 'rejected': raise HTTPException(404, 'Leçon introuvable')
    unit = s.get(CourseUnit, lesson.unit_id)
    level = s.get(CourseLevel, unit.level_id)
    course = s.get(Course, level.course_id)
    if course.status == 'rejected': raise HTTPException(404, 'Parcours indisponible')
    activities = list(s.scalars(select(LessonActivity).where(LessonActivity.lesson_id == lesson.id, LessonActivity.revision == lesson.revision).order_by(LessonActivity.position)))
    content = {c.id: c for c in s.scalars(select(Content).where(Content.id.in_([a.content_id for a in activities])))}
    fingerprint = ready_version(lesson, activities, content, course)
    return lesson, activities, content, fingerprint


def ready_version(lesson, activities, content, course):
    if lesson.status == 'rejected': raise HTTPException(404, 'Leçon retirée du parcours')
    if not activities: raise HTTPException(409, 'Cette leçon ne contient pas encore d’activité.')
    for a in activities:
        c = content.get(a.content_id)
        if not c or c.status == 'rejected' or c.kind not in ('word','phrase') or c.variety != course.target_language:
            raise HTTPException(409, 'Un contenu de cette leçon est indisponible : relecture nécessaire.')
        if any(not isinstance(c.data.get(k),str) or not c.data[k].strip() for k in ('latin','french')): raise HTTPException(409, 'Un texte ou une traduction manque : complète la fiche avant cette leçon.')
        if c.learning_role in ('review','fragment'): raise HTTPException(409, 'Une fiche comporte une incohérence connue : correction nécessaire avant cette leçon.')
        if lesson.status == 'validated' and c.status != 'validated': raise HTTPException(409, 'Un contenu a changé de statut : relecture de la leçon nécessaire.')
        if a.kind == 'order' and c.kind != 'phrase': raise HTTPException(409, 'La construction de phrase exige une phrase.')
        if a.kind == 'dictation' and not usable_audios(c.data): raise HTTPException(409, 'La dictée exige un enregistrement avec crédits.')
    fingerprint = digest(lesson.revision, [(a.id, a.kind, content[a.content_id].kind, content[a.content_id].variety, content[a.content_id].script, content[a.content_id].data, content[a.content_id].status) for a in activities])
    return fingerprint


def describe_lesson(s, key):
    lesson, activities, content, version = lesson_bundle(s, key)
    return {'id': lesson.id, 'title': lesson.title, 'objective': lesson.objective, 'status': lesson.status, 'revision': lesson.revision,
            'activities': [{'id': a.id, 'kind': a.kind, 'content_id': a.content_id} for a in activities],
            'contents': [{'id': c.id, 'kind': c.kind, 'latin': c.data['latin'], 'french': c.data.get('french',''), 'status': c.status, 'sources': c.data.get('sources', []), 'audios': usable_audios(c.data)} for c in content.values()]}


def course_path(s, course_id, who=None, private=False):
    course = s.get(Course, course_id)
    if not course or course.status == 'rejected': raise HTTPException(404, 'Parcours introuvable')
    # Only referenced lesson content is loaded; query count does not grow per lesson.
    levels = list(s.scalars(select(CourseLevel).where(CourseLevel.course_id == course_id).order_by(CourseLevel.position)))
    units = list(s.scalars(select(CourseUnit).where(CourseUnit.level_id.in_([l.id for l in levels])).order_by(CourseUnit.position)))
    lessons = list(s.scalars(select(CourseLesson).where(CourseLesson.unit_id.in_([u.id for u in units]), True if private else CourseLesson.status != 'rejected').order_by(CourseLesson.position)))
    ids = [l.id for l in lessons]
    activities = list(s.scalars(select(LessonActivity).join(CourseLesson, CourseLesson.id == LessonActivity.lesson_id).where(LessonActivity.lesson_id.in_(ids), LessonActivity.revision == CourseLesson.revision).order_by(LessonActivity.position)))
    content = {c.id: c for c in s.scalars(select(Content).where(Content.id.in_([a.content_id for a in activities])))}
    by_lesson, prereqs, completed = {}, {}, {}
    for a in activities: by_lesson.setdefault(a.lesson_id, []).append(a)
    for edge in s.scalars(select(LessonPrerequisite).where(LessonPrerequisite.lesson_id.in_(ids)).order_by(LessonPrerequisite.prerequisite_id)):
        prereqs.setdefault(edge.lesson_id, []).append(edge.prerequisite_id)
    if who:
        for run in s.scalars(select(LessonRun).where(LessonRun.learner == who, LessonRun.passed.is_(True), LessonRun.lesson_id.in_(ids))):
            completed.setdefault(run.lesson_id, set()).add(run.snapshot['version'])
    result = {'id': course.id, 'title': course.title, 'source_language': course.source_language, 'target_language': course.target_language,
              'notice': 'Niveaux pédagogiques proposés, à relire ; les leçons restent publiques, sans certification CECRL.', 'levels': []}
    for level in levels:
        item = {'id': level.id, 'code': level.code, 'title': level.title, 'review_status': level.review_status, 'units': []}
        for unit in (u for u in units if u.level_id == level.id):
            u = {'id': unit.id, 'title': unit.title, 'topic': unit.topic, 'objective': unit.objective, 'lessons': []}
            for lesson in (l for l in lessons if l.unit_id == unit.id):
                acts = by_lesson.get(lesson.id, [])
                try:
                    version = ready_version(lesson, acts, content, course)
                    available, reason = True, ''
                except HTTPException as error:
                    version, available, reason = '', False, error.detail
                u['lessons'].append({'id': lesson.id, 'title': lesson.title, 'objective': lesson.objective, 'status': lesson.status,
                    'revision': lesson.revision, 'activity_count': len(acts), 'available': available, 'reason': reason,
                    'completed': bool(version) and version in completed.get(lesson.id, set()), 'prerequisites': prereqs.get(lesson.id, [])})
            item['units'].append(u)
        result['levels'].append(item)
    return result


def start_run(s, lesson_id, who):
    lesson, activities, content, version = lesson_bundle(s, lesson_id)
    run = LessonRun(id=uuid.uuid4().hex, lesson_id=lesson.id, learner=who, revision=lesson.revision,
                    snapshot={'version': version, 'activity_ids': [a.id for a in activities]}, passed=False)
    s.add(run); s.commit()
    questions = []
    for a in activities:
        c = content[a.content_id]
        pieces = list(enumerate(c.data['latin'].split()))
        random.Random(run.id + a.id).shuffle(pieces)
        questions.append({'id': a.id, 'kind': a.kind, 'french': c.data.get('french',''), 'audios': usable_audios(c.data),
                          'tokens': [{'id': n, 'text': text} for n, text in pieces] if a.kind == 'order' else []})
    return {'run_id': run.id, 'lesson_id': lesson.id, 'questions': questions}

class CourseAnswer(BaseModel):
    activity_id: str = Field(min_length=1, max_length=100)
    answer: str = Field(max_length=2000)
    attempt_id: str = Field(min_length=10, max_length=100)


def grade(s, run_id, body, who):
    run = s.scalar(select(LessonRun).where(LessonRun.id == run_id).with_for_update())
    if not run or run.learner != who: raise HTTPException(404, 'Session introuvable')
    lesson, activities, content, version = lesson_bundle(s, run.lesson_id)
    if version != run.snapshot['version']: raise HTTPException(409, 'La leçon ou ses sources ont changé. Relance la leçon.')
    a = next((x for x in activities if x.id == body.activity_id), None)
    if not a: raise HTTPException(422, 'Cette activité ne fait pas partie de la session.')
    c = content[a.content_id]
    request_hash = digest(run.id, body.activity_id, body.answer)
    # Serialize reuse of an attempt id, including requests in different runs.
    s.execute(select(func.pg_advisory_xact_lock(int(digest(body.attempt_id)[:15], 16))))
    previous = s.get(LessonActivityAttempt, body.attempt_id)
    if previous and (previous.run_id != run.id or previous.request_hash != request_hash): raise HTTPException(409, 'Identifiant d’essai déjà utilisé pour une autre réponse.')
    expected = c.data['latin']
    aliases = c.data.get('synonyms' if c.kind == 'word' else 'alternative_versions', [])
    aliases = aliases if isinstance(aliases, list) else [aliases]
    correct = previous.correct if previous else normalized(body.answer) in {normalized(x) for x in [expected] + aliases if isinstance(x,str)}
    if not previous:
        s.add(LessonActivityAttempt(id=body.attempt_id, run_id=run.id, activity_id=a.id, request_hash=request_hash, correct=correct))
        s.flush()
    done = s.scalar(select(func.count(func.distinct(LessonActivityAttempt.activity_id))).where(LessonActivityAttempt.run_id == run.id, LessonActivityAttempt.correct.is_(True)))
    run.passed = done == len(activities)
    s.commit()
    return {'correct': correct, 'expected': expected, 'french': c.data.get('french',''), 'completed_activities': done, 'total_activities': len(activities), 'passed': run.passed}

class LevelSpec(BaseModel):
    course_id: str = Field(min_length=1, max_length=64)
    code: str = Field(pattern='^(A1|A2|B1|B2|C1|C2)$')
    title: str = Field(min_length=1, max_length=160)


class ActivitySpec(BaseModel):
    content_id: str = Field(min_length=1, max_length=160)
    kind: str = Field(pattern='^(recall|order|dictation)$')

class LessonSpec(BaseModel):
    level_id: str = Field(min_length=1, max_length=64)
    unit_title: str = Field(min_length=1, max_length=160)
    topic: str = Field(min_length=1, max_length=60)
    title: str = Field(min_length=1, max_length=160)
    objective: str = Field(min_length=1, max_length=600)
    activities: list[ActivitySpec] = Field(min_length=1, max_length=20)
    prerequisites: list[str] = Field(default_factory=list, max_length=20)
    status: str = Field(default='draft', pattern='^(draft|validated|rejected)$')


def save_lesson(s, spec, lesson_id=None):
    from .organization import TOPICS
    level = s.get(CourseLevel, spec.level_id)
    if not level: raise HTTPException(422, 'Niveau inconnu')
    if not all(x.strip() for x in (spec.title, spec.objective, spec.unit_title)): raise HTTPException(422, 'Titre, unité et objectif requis.')
    if spec.topic not in TOPICS: raise HTTPException(422, 'Thème inconnu')
    lesson = s.get(CourseLesson, lesson_id) if lesson_id else None
    if lesson_id and not lesson: raise HTTPException(404, 'Leçon introuvable')
    if lesson and s.get(CourseLevel, s.get(CourseUnit, lesson.unit_id).level_id).course_id != level.course_id: raise HTTPException(422, 'La leçon doit rester dans le même cours.')
    for a in spec.activities:
        c = s.get(Content, a.content_id)
        if not c or c.status == 'rejected' or c.kind not in ('word','phrase') or c.variety != s.get(Course, level.course_id).target_language: raise HTTPException(422, 'Contenu indisponible ou langue incorrecte.')
        if any(not isinstance(c.data.get(k),str) or not c.data[k].strip() for k in ('latin','french')): raise HTTPException(422, 'Chaque contenu doit avoir un texte kabyle et une traduction française.')
        if c.learning_role in ('review','fragment'): raise HTTPException(422, 'Corrige la fiche à clarifier avant de l’utiliser dans une leçon.')
        if a.kind == 'order' and c.kind != 'phrase': raise HTTPException(422, 'Construire exige une phrase.')
        if a.kind == 'dictation' and not usable_audios(c.data): raise HTTPException(422, 'Une dictée exige un audio avec crédits.')
        if spec.status == 'validated' and c.status != 'validated': raise HTTPException(422, 'Relis et valide les contenus avant de valider la leçon ; elle peut rester publique à vérifier.')
    # Prerequisites are recommendations, never locks. Validate a directed acyclic graph.
    edges = {}
    for edge in s.scalars(select(LessonPrerequisite)):
        edges.setdefault(edge.lesson_id, []).append(edge.prerequisite_id)
    key = lesson_id or 'course-lesson-' + uuid.uuid4().hex
    edges[key] = spec.prerequisites
    for prerequisite in spec.prerequisites:
        p = s.get(CourseLesson, prerequisite)
        if not p: raise HTTPException(422, 'Prérequis inconnu')
        p_level = s.get(CourseLevel, s.get(CourseUnit, p.unit_id).level_id)
        if p_level.course_id != level.course_id: raise HTTPException(422, 'Le prérequis doit appartenir au même cours.')
    visited = set()
    def visit(node, stack):
        if node in visited: return
        if node in stack: raise HTTPException(422, 'Les prérequis forment une boucle.')
        for nxt in edges.get(node, []): visit(nxt, stack | {node})
        visited.add(node)
    visit(key, set())
    unit_id = digest(level.id, spec.unit_title.strip())[:40]
    unit = s.scalar(select(CourseUnit).where(CourseUnit.level_id == level.id, CourseUnit.title == spec.unit_title.strip()).limit(1))
    if unit and unit.topic != spec.topic: raise HTTPException(422, 'Cette unité possède déjà un autre thème. Conserve son thème ou choisis une nouvelle unité.')
    if not unit:
        pos = (s.scalar(select(func.max(CourseUnit.position)).where(CourseUnit.level_id == level.id)) or 0) + 1
        unit = CourseUnit(id=unit_id, level_id=level.id, title=spec.unit_title.strip(), objective=spec.objective.strip(), topic=spec.topic, position=pos)
        s.add(unit); s.flush()
    if not lesson:
        pos = (s.scalar(select(func.max(CourseLesson.position)).where(CourseLesson.unit_id == unit.id)) or 0) + 1
        lesson = CourseLesson(id=key, unit_id=unit.id, title=spec.title.strip(), objective=spec.objective.strip(), position=pos, revision=1, origin='admin', status=spec.status)
        s.add(lesson)
    else:
        if lesson.unit_id != unit.id:
            lesson.position = (s.scalar(select(func.max(CourseLesson.position)).where(CourseLesson.unit_id == unit.id)) or 0) + 1
        lesson.unit_id, lesson.title, lesson.objective, lesson.status = unit.id, spec.title.strip(), spec.objective.strip(), spec.status
        lesson.revision += 1
        lesson.origin = 'admin'
    s.flush()
    for i, a in enumerate(spec.activities): s.add(LessonActivity(id=uuid.uuid4().hex, lesson_id=lesson.id, revision=lesson.revision, position=i, **a.model_dump()))
    from sqlalchemy import delete
    s.execute(delete(LessonPrerequisite).where(LessonPrerequisite.lesson_id == lesson.id))
    for prerequisite in dict.fromkeys(spec.prerequisites): s.add(LessonPrerequisite(lesson_id=lesson.id, prerequisite_id=prerequisite))
    s.commit()
    return {'id': lesson.id, 'revision': lesson.revision, 'status': lesson.status}


def register_routes(app, db, admin, learner):
    @app.get('/api/courses')
    def courses(s=Depends(db)):
        return [{'id': c.id, 'title': c.title, 'status': c.status} for c in s.scalars(select(Course).where(Course.status != 'rejected'))]

    @app.get('/api/courses/{course_id}')
    def path(course_id: str, who=Depends(learner), s=Depends(db)):
        return course_path(s, course_id, who)

    @app.get('/api/course-lessons/{lesson_id}')
    def lesson(lesson_id: str, s=Depends(db)):
        return describe_lesson(s, lesson_id)

    @app.post('/api/course-lessons/{lesson_id}/start')
    def start(lesson_id: str, who=Depends(learner), s=Depends(db)):
        return start_run(s, lesson_id, who)

    @app.post('/api/course-runs/{run_id}/answer')
    def answer(run_id: str, body: CourseAnswer, who=Depends(learner), s=Depends(db)):
        return grade(s, run_id, body, who)

    @app.post('/api/admin/course-levels', dependencies=[Depends(admin)])
    def create_level(body: LevelSpec, s=Depends(db)):
        course = s.scalar(select(Course).where(Course.id == body.course_id).with_for_update())
        if not course or not body.title.strip(): raise HTTPException(422, 'Cours et titre requis.')
        if s.scalar(select(CourseLevel.id).where(CourseLevel.course_id == course.id, CourseLevel.code == body.code)):
            raise HTTPException(409, 'Ce niveau existe déjà dans le cours.')
        position = {'A1':10, 'A2':20, 'B1':30, 'B2':40, 'C1':50, 'C2':60}[body.code]
        level = CourseLevel(id='level-' + digest(course.id, body.code)[:40], course_id=course.id,
            code=body.code, title=body.title.strip(), position=position, review_status='proposed')
        s.add(level); s.commit()
        return {'id': level.id, 'code': level.code}

    @app.get('/api/admin/courses/{course_id}', dependencies=[Depends(admin)])
    def admin_path(course_id: str, s=Depends(db)):
        return course_path(s, course_id, private=True)

    @app.get('/api/admin/courses/{course_id}/export', dependencies=[Depends(admin)])
    def export(course_id: str, s=Depends(db)):
        return export_course(s, course_id)

    @app.get('/api/admin/course-lessons/{lesson_id}', dependencies=[Depends(admin)])
    def editor(lesson_id: str, s=Depends(db)):
        lesson = s.get(CourseLesson, lesson_id)
        if not lesson: raise HTTPException(404, 'Leçon introuvable')
        unit = s.get(CourseUnit, lesson.unit_id)
        acts = list(s.scalars(select(LessonActivity).where(LessonActivity.lesson_id == lesson.id, LessonActivity.revision == lesson.revision).order_by(LessonActivity.position)))
        return {'id': lesson.id, 'title': lesson.title, 'objective': lesson.objective, 'status': lesson.status,
            'level_id': unit.level_id, 'unit_title': unit.title, 'topic': unit.topic,
            'prerequisites': list(s.scalars(select(LessonPrerequisite.prerequisite_id).where(LessonPrerequisite.lesson_id == lesson.id))),
            'activities': [{'kind': a.kind, 'content_id': a.content_id,
                'latin': s.get(Content, a.content_id).data.get('latin',''), 'french': s.get(Content, a.content_id).data.get('french','')} for a in acts]}

    @app.post('/api/admin/course-lessons', dependencies=[Depends(admin)])
    def create(body: LessonSpec, s=Depends(db)):
        return save_lesson(s, body)

    @app.put('/api/admin/course-lessons/{lesson_id}', dependencies=[Depends(admin)])
    def edit(lesson_id: str, body: LessonSpec, s=Depends(db)):
        return save_lesson(s, body, lesson_id)


def export_course(s, course_id):
    path = course_path(s, course_id, private=True)
    spec = {'id': path['id'], 'title': path['title'], 'source_language': path['source_language'], 'target_language': path['target_language'], 'levels': []}
    for level in path['levels']:
        l = {'code': level['code'], 'title': level['title'], 'units': []}
        for unit in level['units']:
            u = {k: unit[k] for k in ('id','title','objective','topic')}
            u['lessons'] = []
            for lesson in unit['lessons']:
                activities = s.scalars(select(LessonActivity).where(LessonActivity.lesson_id == lesson['id'], LessonActivity.revision == lesson['revision']).order_by(LessonActivity.position))
                u['lessons'].append({**{k: lesson[k] for k in ('id','title','objective','prerequisites','status')},
                    'activities': [{'kind': a.kind, 'content_id': a.content_id} for a in activities]})
            l['units'].append(u)
        spec['levels'].append(l)
    spec['version'] = 'export-' + digest(spec)[:16]
    return spec

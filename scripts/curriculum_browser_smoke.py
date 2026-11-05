"""Real learner and admin flows; remove only this script's temporary lesson/runs."""
import os
import sys
import uuid
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import select, delete

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.db import Session
from app.structured_models import CourseLesson, CourseUnit, LessonRun

created = None
learner = None
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width':1360,'height':1000})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        base = os.environ.get('KABYLE_BASE_URL','http://127.0.0.1:3000')
        page.goto(base)
        page.get_by_role('navigation').get_by_role('button',name='Mon parcours',exact=True).click()
        expect(page.locator('.course-lesson-card')).to_have_count(5)
        learner = next(x['value'] for x in context.cookies() if x['name']=='kabyle_learner')
        page.screenshot(path=str(ROOT/'artifacts/course-path-desktop.png'),full_page=True)
        page.locator('.course-lesson-card').filter(has_text='Un, deux, trois').click()
        expect(page.get_by_role('heading',name='D’abord, je découvre',exact=True)).to_be_visible()
        with page.expect_response(lambda r:r.url.endswith('/a1-nombres-1/start')) as response:
            page.get_by_role('button',name='Commencer les exercices',exact=True).click()
        assert response.value.status==200
        for i, answer in enumerate(['yiwen','sin','kraḍ']):
            page.get_by_label('Ma réponse en kabyle',exact=True).fill(answer)
            page.get_by_role('button',name='Vérifier ma réponse',exact=True).click()
            if i<2:
                expect(page.get_by_role('status')).to_contain_text('Bien joué')
                page.get_by_role('button',name='Continuer',exact=False).click()
        expect(page.get_by_role('heading',name='Leçon terminée !',exact=True)).to_be_visible()
        page.get_by_role('button',name='Revenir au parcours',exact=True).click()
        expect(page.locator('.course-lesson-card').filter(has_text='Un, deux, trois')).to_contain_text('Terminée')
        page.get_by_role('button',name='A2 · Pour aller plus loin',exact=True).click()
        expect(page.get_by_text('Les leçons de cette unité sont à préparer.',exact=True)).to_be_visible()
        page.get_by_role('button',name='A1 · Premiers pas',exact=True).click()
        page.set_viewport_size({'width':320,'height':740})
        page.wait_for_timeout(250)
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        page.screenshot(path=str(ROOT/'artifacts/course-path-mobile.png'),full_page=True)
        page.set_viewport_size({'width':1360,'height':1000})
        page.get_by_role('button',name='Gestion des contenus',exact=True).click()
        page.get_by_label('Jeton administrateur',exact=True).fill(os.environ['ADMIN_TOKEN'])
        studio=page.locator('.data-studio')
        studio.get_by_role('button',name='Charger le bilan et le parcours',exact=True).click()
        expect(studio.locator('.data-stats')).to_contain_text('Fiches sources')
        studio.get_by_text('Composer ou modifier une leçon par niveau',exact=True).click()
        marker=uuid.uuid4().hex[:8]
        studio.get_by_label('Unité',exact=True).fill('Unité essai '+marker)
        studio.get_by_label('Titre de la leçon',exact=True).fill('Leçon essai '+marker)
        studio.get_by_label('Objectif pédagogique',exact=True).fill('Réutiliser une fiche existante.')
        studio.get_by_label('Recherche dans le corpus',exact=True).fill('chien')
        studio.get_by_role('button',name='Chercher des contenus',exact=True).click()
        row=studio.locator('.course-bank > div').filter(has=page.get_by_text('aqjun',exact=True))
        expect(row).to_have_count(1)
        row.get_by_role('button',name='Ajouter à la leçon',exact=True).click()
        with page.expect_response(lambda r:r.url.endswith('/admin/course-lessons') and r.request.method=='POST') as response:
            studio.get_by_role('button',name='Enregistrer la leçon',exact=True).click()
        saved=response.value.json()
        assert response.value.status==200,saved
        created=saved['id']
        expect(studio.get_by_role('status')).to_contain_text('Leçon enregistrée')
        exported=context.request.get(base+'/api/admin/courses/kab-from-fr/export',headers={'Authorization':'Bearer '+os.environ['ADMIN_TOKEN']}).json()
        assert any(l['id']==created for level in exported['levels'] for u in level['units'] for l in u['lessons'])
        page.set_viewport_size({'width':390,'height':844})
        page.wait_for_timeout(250)
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        studio.screenshot(path=str(ROOT/'artifacts/course-admin-mobile.png'))
        page.set_viewport_size({'width':1360,'height':1000})
        page.get_by_role('navigation').get_by_role('button',name='Mon parcours',exact=True).click()
        page.locator('.course-lesson-card').filter(has_text='Leçon essai '+marker).click()
        expect(page.locator('.course-player')).to_contain_text('aqjun')
        assert not errors,errors
        browser.close()
        print('Curriculum browser: A1 units, discovery, server-graded completion, A2 placeholder, admin composition from corpus, export, public rendering and mobile320/390: PASS')
finally:
    with Session() as s:
        if learner:s.execute(delete(LessonRun).where(LessonRun.learner==learner))
        if created:
            lesson=s.get(CourseLesson,created)
            if lesson:
                unit_id=lesson.unit_id
                s.execute(delete(CourseLesson).where(CourseLesson.id==created));s.flush()
                s.execute(delete(CourseUnit).where(CourseUnit.id==unit_id))
        s.commit()

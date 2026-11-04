"""End-to-end admin/public test. Synthetic corpus records are always removed."""
import os
import sys
import uuid
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import delete

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.db import Session
from app.models import Content

marker = uuid.uuid4().hex[:12]
latin = 'testword' + marker
ids = []

def add(suffix, text, translation, theme):
    identifier = 'test-word-lab-ui-' + marker + suffix
    ids.append(identifier)
    with Session() as session:
        session.add(Content(id=identifier, kind='phrase', theme=theme, status='draft',
                            data={'latin': text, 'french': translation, 'category_reviewed_at': '2026-11-04'}))
        session.commit()

try:
    add('before', latin + ' d before.', 'Une mangue.', 'actions')
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1280, 'height': 1000})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(os.environ.get('KABYLE_BASE_URL', 'http://127.0.0.1:3000'))
        page.get_by_role('button', name='Gestion des contenus', exact=True).click()
        page.get_by_label('Jeton administrateur', exact=True).fill(os.environ['ADMIN_TOKEN'])
        lab = page.locator('.word-laboratory')
        lab.get_by_label('Mot kabyle', exact=True).fill(latin)
        lab.get_by_label('Traduction française', exact=True).fill('mangue')
        lab.get_by_role('button', name='Ajouter une phrase', exact=True).click()
        lab.get_by_label('Phrase kabyle 1', exact=True).fill(latin + ' d new.')
        lab.get_by_label('Traduction de la phrase 1', exact=True).fill('Cette mangue est bonne.')
        lab.get_by_role('button', name='Tester sans enregistrer', exact=True).click()
        expect(lab.get_by_role('heading', name='Aperçu du classement', exact=True)).to_be_visible()
        expect(lab.locator('.word-lab-report')).to_contain_text('Les fruits')
        expect(lab.locator('.topic-phrase-card')).to_have_count(1)
        expect(lab.locator('.topic-phrase-card')).to_contain_text(latin + ' d before.')
        with page.expect_response(lambda r: r.url.endswith('/word-laboratory/save') and r.request.method == 'POST') as response:
            lab.get_by_role('button', name='Enregistrer dans la base', exact=True).click()
        saved = response.value.json()
        ids.append(saved['word_id'])
        ids.extend(x['id'] for x in saved['related_phrases']['items'] if x['id'].startswith('phrase-admin-'))
        expect(lab.get_by_role('heading', name='Résultat enregistré', exact=True)).to_be_visible()
        expect(lab.locator('.topic-phrase-card')).to_have_count(2)
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        page.screenshot(path=str(ROOT / 'artifacts/word-laboratory-mobile.png'), full_page=True)
        add('after', latin + ' d future.', 'Une autre mangue.', 'nature')
        page.set_viewport_size({'width': 1280, 'height': 1000})
        page.get_by_role('navigation').get_by_role('button', name='Mots et phrases', exact=True).click()
        page.locator('[data-topic="fruits"]').click()
        card = page.locator('.topic-word-card').filter(has_text=latin)
        expect(card).to_have_count(1)
        card.get_by_role('button', name='Utiliser ce mot', exact=True).click()
        expect(page.locator('.topic-phrase-card')).to_have_count(3)
        expect(page.locator('.topic-phrase-grid')).to_contain_text(latin + ' d before.')
        expect(page.locator('.topic-phrase-grid')).to_contain_text(latin + ' d future.')
        page.get_by_label('Avec audio uniquement', exact=True).check()
        expect(page.get_by_role('heading', name='Pas encore d’audio pour ces phrases.', exact=True)).to_be_visible()
        page.get_by_role('button', name='Afficher toutes les phrases', exact=True).click()
        expect(page.locator('.topic-phrase-card')).to_have_count(3)
        assert not errors, errors
        browser.close()
        print('Word laboratory: dry run, classification, save, public word click, old/new/future cross-topic phrases, audio filter and mobile: PASS')
finally:
    with Session() as session:
        session.execute(delete(Content).where(Content.id.in_(ids)))
        session.commit()

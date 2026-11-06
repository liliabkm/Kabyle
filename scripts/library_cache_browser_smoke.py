"""Count real library requests: revisit pages without refetching public data."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':1280,'height':950})
    requests=[]; errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append(r.url) if '/api/topics' in r.url or '/api/words/' in r.url else None)
    base=os.environ.get('KABYLE_BASE_URL','http://127.0.0.1:3000')
    page.goto(base)
    nav=page.get_by_role('navigation')
    nav.get_by_role('button',name='Ma bibliothèque',exact=True).click()
    page.locator('[data-topic="animaux"]').click()
    expect(page.locator('.topic-word-card')).to_have_count(12)
    animals=lambda:len([r for r in requests if '/api/topics/animaux/words?' in r])
    assert animals()==1
    page.get_by_role('button',name='Tous les thèmes',exact=True).click()
    page.locator('[data-topic="fruits"]').click()
    expect(page.locator('.topic-word-card')).to_have_count(3)
    page.get_by_role('button',name='Tous les thèmes',exact=True).click()
    page.locator('[data-topic="animaux"]').click()
    expect(page.locator('.topic-word-card')).to_have_count(12)
    assert animals()==1
    page.locator('[data-concept="cheval"]').get_by_role('button',name='Utiliser ce mot',exact=True).click()
    expect(page.locator('.topic-phrase-card')).to_have_count(5)
    assert len([r for r in requests if '/api/words/' in r])==1
    page.get_by_label('Avec audio uniquement',exact=True).check()
    expect(page.get_by_role('heading',name='Pas encore d’audio pour ces phrases.',exact=True)).to_be_visible()
    page.get_by_label('Avec audio uniquement',exact=True).uncheck()
    expect(page.locator('.topic-phrase-card')).to_have_count(5)
    assert len([r for r in requests if '/api/words/' in r])==2
    before=len(requests)
    nav.get_by_role('button',name='Accueil',exact=True).click()
    nav.get_by_role('button',name='Ma bibliothèque',exact=True).click()
    expect(page.locator('.topic-phrase-card')).to_have_count(5)
    page.wait_for_timeout(200)
    assert len(requests)==before,requests[before:]
    page.get_by_role('button',name='Revoir les mots',exact=True).click()
    expect(page.locator('.topic-word-card')).to_have_count(12)
    assert animals()==1
    page.get_by_role('button',name='Tous les thèmes',exact=True).click()
    page.locator('[data-topic="actions"]').click()
    expect(page.locator('.topic-word-card')).to_have_count(24)
    page.get_by_role('button',name='Après',exact=True).click()
    expect(page.locator('.topic-word-card')).to_have_count(4)
    page.get_by_role('button',name='Avant',exact=True).click()
    expect(page.locator('.topic-word-card')).to_have_count(24)
    assert len([r for r in requests if '/api/topics/actions/words?' in r])==2
    page.get_by_role('button',name='Tous les thèmes',exact=True).click()
    page.get_by_role('button',name='Actualiser',exact=True).click()
    expect(page.locator('[data-topic="animaux"]')).to_be_visible()
    page.locator('[data-topic="animaux"]').click()
    expect(page.locator('.topic-word-card')).to_have_count(12)
    assert animals()==2
    page.set_viewport_size({'width':320,'height':740})
    page.wait_for_timeout(200)
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    page.get_by_role('button',name='Tous les thèmes',exact=True).click()
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    page.route('**/api/topics',lambda route:route.fulfill(status=500,body='{"detail":"Synthetic library error"}',content_type='application/json'))
    page.get_by_role('button',name='Actualiser',exact=True).click()
    expect(page.locator('.theme-learning [role="alert"]')).to_contain_text('Synthetic library error')
    page.unroute('**/api/topics')
    page.get_by_role('button',name='Actualiser',exact=True).click()
    expect(page.locator('[data-topic="animaux"]')).to_be_visible()
    expect(page.locator('.theme-learning [role="alert"]')).to_have_count(0)
    assert not errors,errors
    browser.close()
    print('Library: one fetch per page, cache on theme return, navigation restored, lazy pagination, manual refresh and mobile320: PASS')

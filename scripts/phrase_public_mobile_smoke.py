"""Public practice on an existing, source-backed phrase at 320 px; no login or fake audio."""
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':320,'height':740})
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:3000')
    page.get_by_role('button',name='Ouvrir le menu',exact=True).click()
    page.get_by_role('navigation').get_by_role('button',name='Ma bibliothèque',exact=True).click()
    page.locator('[data-topic="animaux"]').click()
    page.locator('[data-concept="chien"]').get_by_role('button',name='Utiliser ce mot',exact=True).click()
    page.locator('.topic-phrase-card').filter(has_text='Max d aqjun').get_by_role('button',name='Construire cette phrase',exact=True).click()
    expect(page.locator('.phrase-session .word-chips button')).to_have_count(3)
    page.wait_for_timeout(450)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path=str(ROOT/'artifacts/phrase-practice-public-mobile.png'),full_page=True)
    assert context.request.get('http://127.0.0.1:3000/api/progress').json()==[]
    page.get_by_role('button',name='Retour aux phrases',exact=True).click()
    expect(page.locator('.topic-phrase-card').filter(has_text='Max d aqjun')).to_be_visible()
    assert not errors,errors
    browser.close()
    print('Public phrase practice: library-to-exercise, source-backed phrase, puzzle, return to reading, no teacher token, no invented audio/progress, 320 px: PASS')

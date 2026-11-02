"""Check teaching before questions, retry, stored progress and mobile layout."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1050});mobile=None
 try:
  page=context.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto('http://127.0.0.1:3000')
  expect(page.locator('.lesson-node')).to_have_count(3)
  page.screenshot(path=str(ROOT/'artifacts/learning-home.png'),full_page=True)
  page.get_by_role('button',name='Commencer ma leçon',exact=True).click()
  expect(page.get_by_role('heading',name='Je reconnais 3 lettres.')).to_be_visible()
  page.get_by_role('button',name='Découvrir les lettres',exact=True).click()
  expect(page.get_by_role('heading',name='Regarde bien cette forme.')).to_be_visible()
  page.get_by_role('button',name='Je cache la réponse').click()
  expect(page.locator('.letter-pair>div').last).to_contain_text('?')
  page.get_by_role('button',name='Je regarde la réponse').click()
  expect(page.locator('.letter-pair>div').last).to_contain_text('a')
  page.screenshot(path=str(ROOT/'artifacts/guided-discovery.png'),full_page=True)
  page.get_by_role('button',name='Lettre suivante',exact=True).click()
  page.get_by_role('button',name='Lettre suivante',exact=True).click()
  page.get_by_role('button',name='À moi de jouer !').click()
  expect(page.get_by_role('heading',name='Quelle lettre as-tu reconnue ?')).to_be_visible()
  page.locator('.lesson-answers').get_by_role('button',name='b',exact=True).click()
  expect(page.get_by_text('Regarde, puis essaie encore.')).to_be_visible()
  page.get_by_role('button',name='Je réessaie',exact=True).click()
  for i,latin in enumerate(['a','b','d']):
   page.locator('.lesson-answers').get_by_role('button',name=latin,exact=True).click()
   expect(page.get_by_text('Bien joué !',exact=True)).to_be_visible()
   page.get_by_role('button',name='Voir ma réussite' if i==2 else 'Défi suivant',exact=True).click()
  expect(page.get_by_role('heading',name='Bravo, tu les as reconnues !')).to_be_visible()
  progress=context.request.get('http://127.0.0.1:3000/api/progress').json()
  assert len(progress)==3 and all(v['correct']==1 for v in progress)
  assert next(v for v in progress if v['content_id']=='letter-a')['errors']==1
  page.screenshot(path=str(ROOT/'artifacts/guided-success.png'),full_page=True)
  page.get_by_role('button',name='Je dessine ces lettres').click()
  expect(page.locator('.letter-picker button')).to_have_count(3)
  page.get_by_role('navigation').get_by_role('button',name='Accueil',exact=True).click()
  expect(page.locator('.lesson-node.done')).to_have_count(1)
  page.get_by_role('button',name='Commencer ma leçon',exact=True).click()
  expect(page.locator('.lesson-topline')).to_contain_text('LEÇON 2 / 3')
  page.get_by_role('button',name='Mes leçons',exact=True).click()
  page.reload()
  expect(page.locator('.lesson-node.done')).to_have_count(1)
  assert not errors, errors
  mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
  mp=mobile.new_page();mp.goto('http://127.0.0.1:3000')
  mp.get_by_role('button',name='Commencer ma leçon',exact=True).click()
  mp.get_by_role('button',name='Découvrir les lettres',exact=True).click()
  expect(mp.locator('.letter-pair')).to_be_visible()
  assert mp.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
  mp.screenshot(path=str(ROOT/'artifacts/guided-mobile.png'),full_page=True)
  mp.set_viewport_size({'width':320,'height':740})
  assert mp.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
  print('Guided learning: teaching, recall, error/retry, 3 saved successes, drawing, resume, mobile 390/320px: PASS')
 finally:
  try:
   context.request.delete('http://127.0.0.1:3000/api/progress')
   if mobile:mobile.request.delete('http://127.0.0.1:3000/api/progress')
  finally:browser.close()

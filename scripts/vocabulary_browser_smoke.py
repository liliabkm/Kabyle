"""Exercise public word/phrase activities without reading an admin secret."""
from pathlib import Path
import json,os,secrets,subprocess,time,urllib.request
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];base='http://127.0.0.1:8091';token=secrets.token_urlsafe(32)
server=subprocess.Popen([str(ROOT/'.venv/bin/uvicorn'),'app.main:app','--host','127.0.0.1','--port','8091'],cwd=ROOT/'backend',env={**os.environ,'ADMIN_TOKEN':token},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(30):
  try:
   with urllib.request.urlopen(base+'/api/health',timeout=2):break
  except OSError:
   if server.poll() is not None:raise RuntimeError('Preview API failed to start')
   time.sleep(.2)
 else:raise RuntimeError('Preview API timeout')
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':1440,'height':1050});page=context.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def private_route(route):
   path=route.request.url.split('/api/',1)[1]
   route.fulfill(response=route.fetch(url=base+'/api/'+path))
  page.route('**/api/admin/learning-lessons/**',private_route)
  page.goto('http://127.0.0.1:3000')
  page.get_by_role('navigation').get_by_role('button',name='Mots et phrases',exact=True).click()
  expect(page.get_by_role('heading',name='Des mots, puis des phrases.')).to_be_visible()
  assert page.locator('.word-discovery-card').count()==0
  page.get_by_role('button',name='Je commence !',exact=True).click()
  expect(page.get_by_role('heading',name='Regarde et retiens le mot.')).to_be_visible()
  page.get_by_role('button',name='Je cache le mot').click()
  expect(page.locator('.word-discovery-card h2')).to_have_text('?')
  page.get_by_role('button',name='Je regarde le mot').click()
  expect(page.locator('.word-discovery-card h2')).to_have_text('aqjun')
  page.screenshot(path=str(ROOT/'artifacts/vocabulary-word.png'),full_page=True)
  page.get_by_role('button',name='Mot suivant').click();page.get_by_role('button',name='Mot suivant').click()
  expect(page.locator('.word-discovery-card h2')).to_have_text('tizwal uṛumi')
  expect(page.locator('.word-photo-cluster img')).to_have_count(3)
  page.get_by_role('button',name='Je découvre les phrases').click()
  expect(page.locator('.phrase-discovery-card h2')).to_have_text('Max d aqjun')
  page.screenshot(path=str(ROOT/'artifacts/vocabulary-context.png'),full_page=True)
  page.get_by_role('button',name='Phrase suivante').click();page.get_by_role('button',name='Phrase suivante').click()
  expect(page.locator('.phrase-discovery-card h2')).to_have_text('Tizwal uṛumi d tizeggaɣin')
  page.get_by_role('button',name='À moi de jouer !').click()
  page.locator('.word-choices').get_by_role('button',name='agmar',exact=True).click()
  expect(page.get_by_text('Regarde la correction, puis réessaie.')).to_be_visible()
  page.get_by_role('button',name='Je réessaie',exact=True).click()
  for word in ('aqjun','agmar','tizwal uṛumi'):
   page.locator('.word-choices').get_by_role('button',name=word,exact=True).click()
   expect(page.get_by_text('Bien joué !',exact=True)).to_be_visible()
   page.get_by_role('button',name='Défi suivant').click()
  page.set_viewport_size({'width':390,'height':844})
  for phrase in ('Max d aqjun','D agmar','Tizwal uṛumi d tizeggaɣin'):
   for word in phrase.split():page.locator('.word-chips').get_by_role('button',name=word,exact=True).click()
   assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
   page.get_by_role('button',name='Vérifier',exact=True).click()
   expect(page.get_by_text('Bien joué !',exact=True)).to_be_visible()
   page.get_by_role('button',name='Défi suivant').click()
  page.get_by_label('Ta réponse en kabyle',exact=True).fill('tizwal uṛumi')
  page.screenshot(path=str(ROOT/'artifacts/vocabulary-cloze-mobile.png'),full_page=True)
  page.get_by_role('button',name='Vérifier',exact=True).click()
  expect(page.get_by_text('Bien joué !',exact=True)).to_be_visible()
  page.get_by_role('button',name='Défi suivant').click()
  page.get_by_label('Ta réponse en kabyle',exact=True).fill('aqjun')
  page.get_by_role('button',name='Vérifier',exact=True).click()
  page.get_by_role('button',name='Voir mon bilan').click()
  expect(page.get_by_role('heading',name='Tu as retrouvé les mots !')).to_be_visible()
  expect(page.locator('.lesson-finished')).to_contain_text('8 défis réussis')
  progress=context.request.get('http://127.0.0.1:3000/api/progress').json()
  assert sum(p['correct'] for p in progress)==8 and sum(p['errors'] for p in progress)==1
  context.request.delete('http://127.0.0.1:3000/api/progress')
  assert context.request.get('http://127.0.0.1:3000/api/learning-lessons/premiers-mots').status==200
  assert not errors,errors
  page.set_viewport_size({'width':320,'height':740})
  assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
  browser.close()
  print('Public vocabulary: cards, 3 attested contexts, error/retry, image choice, phrase chips, cloze, recall, 8 graded successes, real saved progress, no teacher token, mobile: PASS')
finally:
 server.terminate()
 try:server.wait(timeout=5)
 except subprocess.TimeoutExpired:server.kill();server.wait()

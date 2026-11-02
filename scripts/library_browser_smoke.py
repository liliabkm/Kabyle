"""Verify read-only browsing and all-type editorial categories on real APIs."""
from pathlib import Path
import json,os,secrets,subprocess,time,urllib.request
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];base='http://127.0.0.1:8091';token=secrets.token_urlsafe(32)
server=subprocess.Popen([str(ROOT/'.venv/bin/uvicorn'),'app.main:app','--host','127.0.0.1','--port','8091'],cwd=ROOT/'backend',env={**os.environ,'ADMIN_TOKEN':token},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def api(path,body=None):
 req=urllib.request.Request(base+'/api/'+path,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},data=json.dumps(body).encode() if body is not None else None)
 with urllib.request.urlopen(req,timeout=10) as res:return json.load(res)
original=None;browser=None
try:
 for _ in range(30):
  try:api('health');break
  except OSError:
   if server.poll() is not None:raise RuntimeError('Catalog API failed to start')
   time.sleep(.2)
 else:raise RuntimeError('Catalog API timeout')
 original=next(i for i in api('admin/content') if i['id']=='phrase-ll-preview-dog')
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':1440,'height':1050});page=context.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(route):
   path=route.request.url.split('/api/',1)[1]
   route.fulfill(response=route.fetch(url=base+'/api/'+path))
  page.route('**/api/admin/**',route)
  page.goto('http://127.0.0.1:3000')
  page.get_by_role('navigation').get_by_role('button',name='Ma bibliothèque',exact=True).click()
  expect(page.get_by_role('heading',name='Ma bibliothèque',exact=True)).to_be_visible()
  expect(page.locator('.reading-card')).to_have_count(8)
  page.screenshot(path=str(ROOT/'artifacts/reading-letters.png'),full_page=True)
  page.get_by_label('Rechercher une fiche',exact=True).fill('b')
  expect(page.locator('.reading-card')).to_have_count(1)
  expect(page.locator('.reading-card h2')).to_have_text('b')
  page.locator('.reading-tabs button').filter(has_text='Mots').click()
  expect(page.get_by_role('heading',name='Les mots se préparent.')).to_be_visible()
  page.locator('.reading-tabs button').filter(has_text='Phrases').click()
  expect(page.get_by_role('heading',name='Les phrases se préparent.')).to_be_visible()
  assert context.request.get('http://127.0.0.1:3000/api/progress').json()==[]
  page.get_by_role('button',name='Gestion des contenus',exact=True).click()
  page.get_by_label('Jeton administrateur',exact=True).fill(token)
  page.get_by_role('button',name='Ouvrir la bibliothèque',exact=True).click()
  expect(page.get_by_role('button',name='Phrases (115)',exact=True)).to_be_visible()
  page.get_by_role('button',name='Lettres (8)',exact=True).click()
  expect(page.locator('.library-word-list>button')).to_have_count(8)
  page.get_by_role('button',name='Phrases (115)',exact=True).click()
  expect(page.locator('.library-word-list>button')).to_have_count(115)
  page.get_by_label('Filtrer la catégorie',exact=True).select_option('animaux')
  page.get_by_label('Rechercher dans la bibliothèque',exact=True).fill('Max')
  page.locator('.library-word-list>button').filter(has_text='Max d aqjun').click()
  page.get_by_label('Catégorie de la fiche',exact=True).select_option('vie-quotidienne')
  page.get_by_role('button',name='Enregistrer uniquement la catégorie').click()
  expect(page.get_by_text('Catégorie enregistrée. Le texte et le statut de publication sont conservés.')).to_be_visible()
  current=next(i for i in api('admin/content') if i['id']==original['id'])
  assert current['status']==original['status'] and current['data']['latin']==original['data']['latin']
  assert current['theme']=='vie-quotidienne'
  page.get_by_role('button',name='Vue lecture privée',exact=True).click()
  expect(page.locator('.reading-card')).to_have_count(24)
  page.locator('.reading-tabs button').filter(has_text='Phrases').click()
  expect(page.locator('.reading-card')).to_have_count(24)
  first=set(page.locator('.reading-card').evaluate_all('rows=>rows.map(r=>r.dataset.contentId)'))
  page.get_by_role('button',name='Après',exact=True).click()
  expect(page.locator('.reading-pagination')).to_contain_text('25–48 / 115')
  second=set(page.locator('.reading-card').evaluate_all('rows=>rows.map(r=>r.dataset.contentId)'))
  assert not first.intersection(second)
  page.get_by_label('Catégorie des fiches',exact=True).select_option('fruits')
  page.get_by_label('Rechercher une fiche',exact=True).fill('fraises')
  expect(page.locator('.reading-card')).to_have_count(1)
  expect(page.locator('.reading-card h2')).to_have_text('Tizwal uṛumi d tizeggaɣin')
  page.screenshot(path=str(ROOT/'artifacts/reading-phrases-private.png'),full_page=True)
  page.set_viewport_size({'width':390,'height':844})
  assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
  page.set_viewport_size({'width':320,'height':740})
  assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
  assert not errors,errors
  browser.close()
  print('Reading library: public letters/search, drafts hidden, 115 admin phrases, type/category filters, classification without changing text/status, private reading pagination, mobile widths: PASS')
finally:
 try:
  if original:api('admin/import',[original])
 finally:
  server.terminate()
  try:server.wait(timeout=5)
  except subprocess.TimeoutExpired:server.kill();server.wait()

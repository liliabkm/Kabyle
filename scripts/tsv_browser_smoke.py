"""Test a synthetic >1 MB TSV through the actual upload UI; clean it afterwards."""
from pathlib import Path
import json,os,secrets,subprocess,sys,time,urllib.request,uuid
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.db import Session
from app.models import Content
from sqlalchemy import delete
base='http://127.0.0.1:8091';token=secrets.token_urlsafe(32);marker='fixture-browser-'+uuid.uuid4().hex
server=subprocess.Popen([str(ROOT/'.venv/bin/uvicorn'),'app.main:app','--host','127.0.0.1','--port','8091'],cwd=ROOT/'backend',env={**os.environ,'ADMIN_TOKEN':token},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(30):
  try:
   with urllib.request.urlopen(base+'/api/health',timeout=2):break
  except OSError:
   if server.poll() is not None:raise RuntimeError('Import test API failed to start')
   time.sleep(.2)
 else:raise RuntimeError('Import test API timeout')
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':1440,'height':1050});page=context.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(route):
   path=route.request.url.split('/api/',1)[1]
   route.fulfill(response=route.fetch(url=base+'/api/'+path,timeout=120000))
  page.route('**/api/admin/**',route)
  page.goto('http://127.0.0.1:3000')
  page.get_by_role('button',name='Gestion des contenus',exact=True).click()
  page.get_by_label('Jeton administrateur',exact=True).fill(token)
  page.get_by_role('button',name='Ouvrir la bibliothèque',exact=True).click()
  expect(page.get_by_role('button',name='Mots (442)',exact=True)).to_be_visible()
  page.locator('.tsv-import summary').click()
  content=('Kabyle\tFrench\n'+(marker+'\tBonjour\n')*25000).encode()
  assert len(content)>1024*1024
  page.get_by_label('Choisir le fichier TSV',exact=False).set_input_files({'name':'synthetic-test.tsv','mimeType':'text/tab-separated-values','buffer':content})
  expect(page.get_by_label('Colonne kabyle',exact=True)).to_have_value('1')
  expect(page.get_by_label('Colonne français',exact=True)).to_have_value('2')
  page.get_by_role('button',name='Importer et rendre public',exact=True).click()
  expect(page.locator('.tsv-import')).to_contain_text('1 phrases ajoutées · 24999 doublons · 0 lignes incomplètes',timeout=120000)
  # The real public library sees the imported unvalidated pair without an admin header.
  result=context.request.get('http://127.0.0.1:3000/api/library',params={'kind':'phrase','q':marker}).json()
  assert len(result['items'])==1 and result['items'][0]['status']=='draft' and result['items'][0]['theme']=='salutations'
  page.get_by_role('navigation').get_by_role('button',name='Ma bibliothèque',exact=True).click()
  page.locator('.reading-tabs button').filter(has_text='Phrases').click()
  page.get_by_label('Rechercher une fiche',exact=True).fill(marker)
  expect(page.locator('.reading-card h2')).to_have_text(marker)
  expect(page.locator('.reading-card')).to_contain_text('À vérifier')
  page.set_viewport_size({'width':390,'height':844})
  assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
  assert not errors,errors
  browser.close()
  print('TSV UI: >1 MB upload, preview, column selection, 25,000 synthetic rows, deduplication, proposed category, public pending pair: PASS')
finally:
 with Session() as s:
  s.execute(delete(Content).where(Content.data['latin'].as_string()==marker));s.commit()
 server.terminate()
 try:server.wait(timeout=5)
 except subprocess.TimeoutExpired:server.kill();server.wait()

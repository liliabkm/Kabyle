"""Exercise catalog UI against a real isolated API process and the local development DB.

The temporary admin token is generated in memory, never read from .env or logged.
Requires the web frontend on port 3000 and optional Playwright/Chromium tooling.
"""
from pathlib import Path
import json
import os
import secrets
import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
base='http://127.0.0.1:8091'
token=secrets.token_urlsafe(32)
server=subprocess.Popen([str(ROOT/'.venv/bin/uvicorn'),'app.main:app','--host','127.0.0.1','--port','8091'],cwd=ROOT/'backend',env={**os.environ,'ADMIN_TOKEN':token},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def call(path,body=None):
    req=urllib.request.Request(base+'/api/'+path,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req,timeout=15) as res:return json.load(res)
original=None
try:
    for i in range(30):
        try:call('health');break
        except OSError:
            if server.poll() is not None:raise RuntimeError('Isolated API failed to start')
            time.sleep(.2)
    else:raise RuntimeError('Isolated API readiness timeout')
    original=next(w for w in call('admin/content') if w['kind']=='word' and w['data'].get('french')=='fraises')
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1440,'height':1100})
        page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def route_api(route):
            path=route.request.url.split('/api/',1)[1]
            response=route.fetch(url=base+'/api/'+path)
            route.fulfill(response=response)
        page.route('**/api/admin/**',route_api)
        page.route('**/api/media/**',route_api)
        page.goto('http://127.0.0.1:3000')
        page.get_by_role('button',name='Gestion des contenus').click()
        page.get_by_label('Jeton administrateur',exact=True).fill(token)
        page.get_by_role('button',name='Ouvrir la bibliothèque').click()
        expect(page.get_by_role('button',name='Mots (61)')).to_be_visible()
        page.get_by_role('button',name='Photos (30)',exact=True).click()
        expect(page.locator('.library-photo')).to_have_count(30)
        page.locator('.library-photo img').evaluate_all("imgs => imgs.forEach(img => img.loading = 'eager')")
        page.wait_for_function("Array.from(document.querySelectorAll('.library-photo img')).every(i => i.complete && i.naturalWidth === 100 && i.naturalHeight === 100)")
        page.screenshot(path=str(ROOT/'artifacts/photo-library.png'),full_page=True)
        page.get_by_label('Rechercher dans la bibliothèque').fill('fraise')
        expect(page.locator('.library-photo')).to_have_count(1)
        page.get_by_role('button',name='Mots (61)').click()
        page.locator('.library-word-list button').filter(has_text=original['data']['latin']).first.click()
        expect(page.get_by_role('heading',name='Modifier « '+original['data']['latin']+' »')).to_be_visible()
        page.get_by_label('Ajouter une photo',exact=True).select_option('photo-fruits360-fraise')
        page.get_by_role('button',name='Enregistrer en brouillon').click()
        expect(page.get_by_text('Brouillon enregistré. Il reste exclu des leçons.')).to_be_visible()
        stored=next(w for w in call('admin/content') if w['id']==original['id'])
        assert stored['status']=='draft' and stored['data']['license_conflict'] is True
        assert any(i.get('asset_id')=='photo-fruits360-fraise' for i in stored['data']['images'])
        assert original['id'] not in {c['id'] for c in call('content')}
        assert not errors,errors
        page.set_viewport_size({'width':390,'height':844})
        page.get_by_label('Rechercher dans la bibliothèque').fill('')
        page.get_by_role('button',name='Photos (30)',exact=True).click()
        expect(page.locator('.library-photo')).to_have_count(30)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        browser.close()
    print('Catalog: 61 drafts, 30 real attributed photos, search, draft photo association, public exclusion, mobile width: PASS')
finally:
    try:
        if original is not None:call('admin/import',[original])
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:server.kill();server.wait()

"""UI tests with an explicitly synthetic provider, not model quality tests."""
import json
import os
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1280,'height':950})
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    online=False
    def status(route):
        route.fulfill(json={'available':online,'model':'synthetic-test-provider','adaptation':'base' if online else 'unavailable','notice':'Statut fictif de test.'})
    page.route('**/api/chat/status',status)
    requests=[]
    def answer(route):
        requests.append(route.request.post_data_json)
        route.fulfill(json={'answer':'Réponse fictive du test [1].','references':[{'number':1,'id':'test','latin':'Fixture sentence.','french':'Phrase de test.','status':'draft','audios':[]}]})
    page.route('**/api/chat',answer)
    page.goto(os.getenv('KABYLE_BASE_URL','http://127.0.0.1:3000'))
    page.get_by_role('navigation').get_by_role('button',name='Parler kabyle',exact=True).click()
    expect(page.get_by_text('Modèle non connecté',exact=True)).to_be_visible()
    page.get_by_label('Ta question',exact=True).fill('Question de test')
    expect(page.get_by_role('button',name='Envoyer',exact=True)).to_be_disabled()
    online=True
    page.get_by_role('button',name='Vérifier la connexion',exact=True).click()
    expect(page.get_by_text('Modèle de base chargé',exact=True)).to_be_visible()
    page.get_by_role('button',name='Envoyer',exact=True).click()
    expect(page.get_by_text('Réponse fictive du test [1].',exact=True)).to_be_visible()
    page.get_by_text('Exemples du corpus fournis au modèle (1)',exact=True).click()
    expect(page.get_by_text('[1] Fixture sentence.',exact=True)).to_be_visible()
    assert requests[0]['history']==[]
    page.get_by_label('Ta question',exact=True).fill('Suite du test')
    page.get_by_role('button',name='Envoyer',exact=True).click()
    expect(page.locator('.chat-bubble')).to_have_count(4)
    assert len(requests[1]['history'])==2
    page.get_by_role('button',name='Nouvelle conversation',exact=True).click()
    expect(page.locator('.chat-bubble')).to_have_count(0)
    page.route('**/api/chat',lambda route:route.fulfill(status=503,json={'detail':'Modèle fictif hors ligne'}))
    page.set_viewport_size({'width':390,'height':844})
    page.get_by_label('Ta question',exact=True).fill('Nouvelle tentative')
    page.get_by_role('button',name='Envoyer',exact=True).click()
    expect(page.locator('.kabyle-chat [role=alert]')).to_have_text('Modèle fictif hors ligne')
    assert page.get_by_label('Ta question',exact=True).input_value()=='Nouvelle tentative'
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Débordement mobile'
    assert not errors,errors
    page.screenshot(path='artifacts/chat-mobile.png',full_page=True)
    browser.close()
    print('Chat UI: offline, model status, synthetic replies, context, sources, retry and mobile passed.')

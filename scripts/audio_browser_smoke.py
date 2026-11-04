"""UI playback test using synthetic WAV fixtures, never claimed as Kabyle speech."""
import io
import os
import json
import wave
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, expect

buffer = io.BytesIO()
with wave.open(buffer, 'wb') as audio:
    audio.setnchannels(1)
    audio.setsampwidth(2)
    audio.setframerate(8000)
    audio.writeframes(b'\0\0' * 8000 * 4)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.route('**/api/media/test-listen*.wav', lambda route: route.fulfill(body=buffer.getvalue(), content_type='audio/wav'))
    page.route('**/api/media/test-broken.wav', lambda route: route.fulfill(status=404))

    def phrases(route):
        payload = route.fetch().json()
        for i, item in enumerate(payload['items']):
            item['audios'] = ([{'url': f'/api/media/test-listen{i}.wav', 'author': 'Synthetic playback fixture', 'license': 'CC0'}] if i < 2 else [])
        if parse_qs(urlparse(route.request.url).query).get('audio_only') == ['true']:
            payload['items'] = [item for item in payload['items'] if item['audios']]
            payload['total'] = len(payload['items'])
        route.fulfill(body=json.dumps(payload), content_type='application/json')

    page.route('**/api/topics/animaux/phrases*', phrases)
    page.goto(os.environ.get('KABYLE_BASE_URL', 'http://127.0.0.1:3000'))
    expect(page.get_by_role('button', name='Ma voix', exact=True)).to_have_count(0)
    page.get_by_role('navigation').get_by_role('button', name='Mots et phrases', exact=True).click()
    page.locator('[data-topic="animaux"]').click()
    page.get_by_role('button', name='Voir les phrases du thème', exact=True).click()
    players = page.locator('.phrase-listen audio')
    expect(players).to_have_count(2)
    assert players.first.get_attribute('preload') == 'none'
    assert players.first.evaluate('a=>a.paused')
    page.locator('.phrase-listen').first.get_by_role('button', name='Lire la phrase', exact=False).click()
    page.wait_for_function('(a)=>!a.paused && a.readyState>=2', arg=players.first.element_handle())
    assert players.first.evaluate('a=>!a.paused && a.readyState>=2')
    page.locator('.phrase-listen').nth(1).get_by_role('button', name='Lire la phrase', exact=False).click()
    page.wait_for_function('(a)=>!a.paused', arg=players.nth(1).element_handle())
    assert players.first.evaluate('a=>a.paused')
    assert players.nth(1).evaluate('a=>!a.paused')
    players.nth(1).evaluate('a=>{a.pause();a.src="/api/media/test-broken.wav";a.load()}')
    expect(page.locator('.audio-load-error')).to_contain_text('ne se charge pas')
    page.get_by_label('Avec audio uniquement', exact=True).check()
    expect(page.locator('.topic-phrase-card')).to_have_count(2)
    expect(page.locator('.phrase-listen audio')).to_have_count(2)
    page.get_by_label('Avec audio uniquement', exact=True).uncheck()
    expect(page.locator('.topic-phrase-card')).to_have_count(12)
    page.set_viewport_size({'width': 320, 'height': 740})
    page.wait_for_timeout(200)
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    page.screenshot(path='artifacts/phrase-listen-mobile.png', full_page=True)
    assert not errors, errors
    browser.close()
    print('Audio UI: conditional players, real WAV playback, no autoplay, custom controls, audio filter, exclusive playback, error fallback, mobile320 and no Ma voix: PASS')

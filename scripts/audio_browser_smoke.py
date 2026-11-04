"""UI playback test using synthetic WAV fixtures, never claimed as Kabyle speech."""
import io
import os
import json
import wave
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
    players.first.evaluate('a=>a.play()')
    assert players.first.evaluate('a=>!a.paused && a.readyState>=2')
    players.nth(1).evaluate('a=>a.play()')
    assert players.first.evaluate('a=>a.paused')
    assert players.nth(1).evaluate('a=>!a.paused')
    players.nth(1).evaluate('a=>{a.pause();a.src="/api/media/test-broken.wav";a.load()}')
    expect(page.locator('.audio-load-error')).to_contain_text('ne se charge pas')
    page.set_viewport_size({'width': 320, 'height': 740})
    page.wait_for_timeout(200)
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    page.screenshot(path='artifacts/phrase-listen-mobile.png', full_page=True)
    assert not errors, errors
    browser.close()
    print('Audio UI: conditional players, real WAV playback, no autoplay, exclusive playback, error fallback, mobile320 and no Ma voix: PASS')

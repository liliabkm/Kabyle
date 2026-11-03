"""Real public curriculum: illustrated topic → word → its attested phrases → puzzle."""

from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    context = browser.new_context(viewport={"width": 1440, "height": 1050})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:3000")
    page.get_by_role("navigation").get_by_role("button", name="Mots et phrases", exact=True).click()
    expect(page.get_by_role("heading", name="Choisis ton thème", exact=True)).to_be_visible()
    expect(page.locator(".theme-learning select")).to_have_count(0)
    expect(page.locator('[data-topic="fruits"] .topic-art')).to_be_visible()
    expect(page.locator('[data-topic="animaux"] .topic-art')).to_be_visible()
    page.screenshot(path=str(ROOT / "artifacts/topics-gallery.png"), full_page=True)
    page.locator('[data-topic="fruits"]').click()
    expect(page.locator(".topic-word-card")).to_have_count(3)
    expect(page.locator('[data-concept="fraise"] h2')).to_have_text("tizwal uṛumi")
    page.locator('[data-concept="fraise"]').get_by_role(
        "button", name="Utiliser ce mot", exact=True
    ).click()
    expect(page.locator(".topic-phrase-card")).to_have_count(1)
    expect(page.locator(".topic-phrase-card mark")).to_have_text("Tizwal uṛumi")
    expect(page.locator(".topic-phrase-card")).to_contain_text("Les fraises sont rouges")
    page.get_by_role("button", name="Construire cette phrase", exact=True).click()
    expect(
        page.get_by_role("heading", name="Remets les mots dans l’ordre.", exact=True)
    ).to_be_visible()
    for word in ("Tizwal", "uṛumi", "d", "tizeggaɣin"):
        page.locator(".word-chips").get_by_role("button", name=word, exact=True).click()
    page.get_by_role("button", name="Vérifier ma phrase", exact=True).click()
    expect(page.locator(".phrase-session .feedback")).to_contain_text("Bien joué !")
    progress = context.request.get("http://127.0.0.1:3000/api/progress").json()
    assert sum(x["correct"] for x in progress) == 1
    page.get_by_role("button", name="Retour aux phrases", exact=True).click()
    expect(page.locator(".topic-phrase-card")).to_have_count(1)
    page.get_by_role("button", name="Tous les thèmes", exact=True).click()
    page.locator('[data-topic="animaux"]').click()
    expect(page.locator(".topic-word-card")).to_have_count(12)
    expect(page.locator('[data-concept="souris"]')).to_contain_text("aɣerda")
    expect(page.locator('[data-concept="elephant"]')).to_contain_text("lfil")
    assert page.locator(".topic-word-card").filter(has_text="lqahwa").count() == 0
    page.screenshot(path=str(ROOT / "artifacts/topic-animals-words.png"), full_page=True)
    page.locator('[data-concept="cheval"]').get_by_role(
        "button", name="Utiliser ce mot", exact=True
    ).click()
    expect(page.locator(".topic-phrase-card")).to_have_count(5)
    expect(page.locator(".topic-phrase-card mark")).to_have_count(5)
    expect(
        page.locator(".topic-phrase-card").filter(has_text="Le cheval boit de l’eau")
    ).to_be_visible()
    page.screenshot(path=str(ROOT / "artifacts/topic-horse-contexts.png"), full_page=True)
    context.request.delete("http://127.0.0.1:3000/api/progress")
    mobile = browser.new_context(viewport={"width": 390, "height": 844})
    mp = mobile.new_page()
    mp.on("pageerror", lambda e: errors.append(str(e)))
    mp.goto("http://127.0.0.1:3000")
    mp.get_by_role("button", name="Ouvrir le menu", exact=True).click()
    mp.get_by_role("navigation").get_by_role("button", name="Ma bibliothèque", exact=True).click()
    expect(mp.locator('[data-topic="alphabet"]')).to_be_visible()
    mp.screenshot(path=str(ROOT / "artifacts/topics-mobile.png"), full_page=True)
    mp.locator('[data-topic="animaux"]').click()
    expect(mp.locator(".topic-word-card")).to_have_count(12)
    mp.wait_for_timeout(450)
    assert mp.evaluate("document.documentElement.scrollWidth<=window.innerWidth")
    mp.set_viewport_size({"width": 320, "height": 740})
    mp.wait_for_timeout(450)
    assert mp.evaluate("document.documentElement.scrollWidth<=window.innerWidth")
    mp.locator('[data-concept="chat"]').get_by_role(
        "button", name="Utiliser ce mot", exact=True
    ).click()
    expect(mp.locator(".topic-phrase-card").first).to_be_visible()
    assert mp.evaluate("document.documentElement.scrollWidth<=window.innerWidth")
    mp.get_by_role("button", name="Tous les thèmes", exact=True).click()
    mp.locator('[data-topic="alphabet"]').click()
    expect(mp.locator(".topic-word-card")).to_have_count(33)
    assert mobile.request.get("http://127.0.0.1:3000/api/progress").json() == []
    assert not errors, errors
    browser.close()
    print(
        "Topic curriculum: illustrated boxes, no learner filters, 3 fruit concepts, 12 animal concepts, exact bilingual word-context links, 5 horse contexts, real puzzle progress, public letters, 390/320 px: PASS"
    )

"""End-to-end Tatoeba upload and four activities with explicitly synthetic fixtures.
The test sound is a generated tone, never presented as an actual Tatoeba recording.
"""

from pathlib import Path
import io, json, math, os, secrets, struct, subprocess, sys, time, urllib.request, uuid, wave
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db import Session
from app.models import Content, Progress, Attempt
from sqlalchemy import select, delete

base = "http://127.0.0.1:8091"
token = secrets.token_urlsafe(32)
marker = "fixture" + uuid.uuid4().hex
server = subprocess.Popen(
    [str(ROOT / ".venv/bin/uvicorn"), "app.main:app", "--host", "127.0.0.1", "--port", "8091"],
    cwd=ROOT / "backend",
    env={**os.environ, "ADMIN_TOKEN": token},
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
try:
    for _ in range(30):
        try:
            with urllib.request.urlopen(base + "/api/health", timeout=2):
                break
        except OSError:
            if server.poll() is not None:
                raise RuntimeError("Test API failed to start")
            time.sleep(0.2)
    else:
        raise RuntimeError("Test API timeout")
    kab = "aqjun d " + marker + "."
    fr = "Bonjour " + marker + "."
    pairs = f"9000000001\t{kab}\t9000000002\t{fr}\n9000000003\taxxam {marker}.\t9000000004\tUne maison {marker}.\n9000000005\taman {marker}.\t9000000006\tDe l’eau {marker}.\n".encode()
    audio = b"9000000001\t9900000001\tSyntheticFixtureVoice\tCC0\thttps://example.org/fixture\n9000000001\t9900000002\tOtherSyntheticFixtureVoice\tCC0\thttps://example.org/fixture\n"
    sound = io.BytesIO()
    with wave.open(sound, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(
            b"".join(
                struct.pack("<h", int(3000 * math.sin(2 * math.pi * 440 * i / 8000)))
                for i in range(8000)
            )
        )
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
        )
        context = browser.new_context(viewport={"width": 1440, "height": 1050})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        def proxy(route):
            path = route.request.url.split("/api/", 1)[1]
            route.fulfill(response=route.fetch(url=base + "/api/" + path, timeout=120000))

        page.route("**/api/**", proxy)
        page.route(
            "https://tatoeba.org/en/audio/download/990000000*",
            lambda r: r.fulfill(status=200, content_type="audio/wav", body=sound.getvalue()),
        )
        page.goto("http://127.0.0.1:3000")
        page.get_by_role("button", name="Gestion des contenus", exact=True).click()
        page.get_by_label("Jeton administrateur", exact=True).fill(token)
        page.locator("summary").filter(has_text="Importer Tatoeba :").click()
        page.get_by_label("Paires Tatoeba", exact=True).set_input_files(
            {
                "name": "synthetic-pairs.tsv",
                "mimeType": "text/tab-separated-values",
                "buffer": pairs,
            }
        )
        page.get_by_label("Métadonnées audio Tatoeba (facultatif)", exact=True).set_input_files(
            {
                "name": "synthetic-audio.tsv",
                "mimeType": "text/tab-separated-values",
                "buffer": audio,
            }
        )
        page.get_by_role("button", name="Préparer et voir l’aperçu", exact=True).click()
        expect(
            page.get_by_text(
                "3 paires alignées · 2 enregistrements associés · 1 paires avec audio.", exact=True
            )
        ).to_be_visible()
        page.get_by_role("button", name="Importer Tatoeba et rendre public", exact=True).click()
        expect(
            page.get_by_text(
                "3 phrases ajoutées · 0 doublons · 0 fiches enrichies. Les phrases sont publiques et à vérifier.",
                exact=True,
            )
        ).to_be_visible()
        page.get_by_role("button", name="Ouvrir la bibliothèque", exact=True).click()
        page.locator(".library-tabs button").filter(has_text="Phrases").click()
        page.get_by_label("Rechercher dans la bibliothèque", exact=True).fill(marker)
        page.locator(".catalog-open").filter(has_text=kab).click()
        page.get_by_label("Niveau CECR attribué", exact=True).select_option("A1")
        page.get_by_label("Note grammaticale", exact=True).fill(
            "Note grammaticale de test, renseignée dans l’éditeur."
        )
        page.get_by_role("button", name="Enregistrer les modifications", exact=True).click()
        expect(
            page.get_by_text(
                "Modifications enregistrées. La fiche est visible et à vérifier.", exact=True
            )
        ).to_be_visible()
        page.get_by_role("navigation").get_by_role(
            "button", name="Mots et phrases", exact=True
        ).click()
        page.get_by_label("Source des phrases", exact=True).select_option("tatoeba")
        expect(page.locator(".phrase-pick")).to_have_count(3)
        page.locator(".phrase-pick").filter(has_text=kab).click()
        expect(page.locator(".interactive-sentence")).to_have_text(kab)
        expect(
            page.get_by_text("Note grammaticale de test, renseignée dans l’éditeur.", exact=True)
        ).to_be_visible()
        page.get_by_role("button", name="Voir le mot aqjun", exact=True).click()
        expect(page.locator(".word-gloss")).to_contain_text("chien")
        page.get_by_role("button", name="Retourner la carte", exact=True).click()
        expect(page.locator(".flash-translation")).to_have_text(fr)
        page.get_by_role("button", name="Je fais la dictée", exact=True).click()
        page.locator(".phrase-audio audio").first.evaluate("a=>a.play()")
        page.get_by_label("Ma dictée en kabyle", exact=True).fill(kab)
        page.get_by_role("button", name="Vérifier ma dictée", exact=True).click()
        expect(page.locator(".phrase-session .feedback")).to_contain_text("Bien joué !")
        page.get_by_role("button", name="J’écoute et je choisis", exact=True).click()
        expect(page.locator(".audio-options button")).to_have_count(3)
        page.locator(".phrase-audio audio").first.evaluate("a=>a.play()")
        page.locator(".audio-options").get_by_role("button", name=fr, exact=True).click()
        expect(page.locator(".phrase-session .feedback")).to_contain_text("Bien joué !")
        page.get_by_role("button", name="Je construis", exact=True).click()
        for word in reversed(kab.split()):
            page.locator(".word-chips").get_by_role("button", name=word, exact=True).click()
        page.get_by_role("button", name="Vérifier ma phrase", exact=True).click()
        expect(page.locator(".phrase-session .feedback")).to_contain_text("Regarde la correction")
        page.get_by_role("button", name="Je réessaie", exact=True).click()
        for word in kab.split():
            page.locator(".word-chips").get_by_role("button", name=word, exact=True).click()
        page.get_by_role("button", name="Vérifier ma phrase", exact=True).click()
        expect(page.locator(".phrase-session .feedback")).to_contain_text("Bien joué !")
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(450)  # Let the responsive sidebar transition finish.
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(ROOT / "artifacts/tatoeba-practice-mobile.png"), full_page=True)
        page.get_by_role("button", name="Voir mon bilan", exact=True).click()
        expect(
            page.get_by_text("3 réponse(s) correcte(s) enregistrée(s).", exact=True)
        ).to_be_visible()
        progress = context.request.get("http://127.0.0.1:3000/api/progress").json()
        assert sum(x["correct"] for x in progress) == 3 and sum(x["errors"] for x in progress) == 1
        context.request.delete("http://127.0.0.1:3000/api/progress")
        assert not errors, errors
        browser.close()
        print(
            "Tatoeba synthetic E2E: aligned import, multiple audio metadata, public cards, exact lexicon, HTML audio playback with test tone, dictation, QCM, word puzzle, error/retry, real progress, mobile: PASS"
        )
finally:
    with Session() as s:
        ids = list(
            s.scalars(select(Content.id).where(Content.data["latin"].as_string().contains(marker)))
        )
        if ids:
            s.execute(delete(Attempt).where(Attempt.content_id.in_(ids)))
            s.execute(delete(Progress).where(Progress.content_id.in_(ids)))
            s.execute(delete(Content).where(Content.id.in_(ids)))
        s.commit()
    server.terminate()
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()

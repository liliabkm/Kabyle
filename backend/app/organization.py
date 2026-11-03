"""French-meaning taxonomy, separate from source chapters and linguistic approval."""

import json, re, unicodedata, hashlib
from functools import lru_cache
from pathlib import Path

TAXONOMY_PATH = Path(__file__).resolve().parents[2] / "content/catalog/semantic-topics.json"
VERSION = "semantic-fr-v3-" + hashlib.sha256(TAXONOMY_PATH.read_bytes()).hexdigest()[:8]
TOPICS = {
    "animaux": ("Les animaux", "Un chien, un chat… puis leurs petites histoires."),
    "fruits": ("Les fruits", "Découvre les fruits, puis parle de ce que tu manges."),
    "legumes": ("Les légumes", "Les mots du potager."),
    "alimentation": ("À table", "Du pain, des pâtes et des phrases pour le repas."),
    "boissons": ("Les boissons", "De l’eau, du lait et les mots pour boire."),
    "vetements": ("Les vêtements", "Les habits et leurs couleurs."),
    "nature": ("La nature", "La mer, les montagnes et le ciel."),
    "famille": ("Les personnes", "Les amis, les enfants et la famille."),
    "ecole": ("À l’école", "Apprendre, lire et découvrir l’école."),
    "metiers": ("Les métiers", "Qui fait quoi ?"),
    "maison": ("La maison", "Les pièces et les objets de la maison."),
    "nombres": ("Les nombres", "Les mots pour compter."),
    "couleurs": ("Les couleurs", "Du rouge, du bleu et des phrases colorées."),
    "description": ("Je décris", "Grand, petit, beau… pour décrire."),
    "actions": ("Je bouge, je fais", "Manger, jouer, chanter…"),
    "salutations": ("Je dis bonjour", "Les petits échanges pour se présenter."),
    "gouts": ("J’aime, je n’aime pas", "Exprimer ce que tu aimes."),
    "etats": ("Comment je me sens", "La faim, la soif et les émotions."),
    "voyages": ("En voyage", "Partir et découvrir."),
    "achats": ("Les achats", "Les prix et les échanges."),
    "musique": ("La musique", "Les mots des chansons."),
    "sante": ("La santé", "Parler de sa santé."),
    "temps": ("Le temps et la météo", "Parler du temps et de la météo."),
    "jours": ("Les jours et les nuits", "Les moments de la journée."),
    "jeux": ("Les jeux", "Jouer ensemble."),
    "grammaire": ("Les petits mots", "Je, tu, avec… les mots qui relient."),
    "questions": ("Je pose une question", "Quoi, comment, combien ?"),
    "origines": ("Autres descriptions", "Les autres mots de description."),
    "paix": ("La paix", "Les mots pour parler de paix."),
    "prenoms": ("Les prénoms", "Les noms des personnages des phrases."),
    "a-revoir": (
        "Fiches à clarifier",
        "Des éléments de la source dont le sens ou la forme demande une correction.",
    ),
    "autres-phrases": ("Autres situations", "Les phrases dont le sujet reste à préciser."),
    "autres-mots": ("Autres mots", "Les mots dont le sens reste à préciser."),
}
PRIORITY = [
    "animaux",
    "fruits",
    "legumes",
    "vetements",
    "nombres",
    "metiers",
    "ecole",
    "maison",
    "boissons",
    "alimentation",
    "nature",
    "famille",
    "temps",
    "sante",
    "etats",
    "voyages",
    "achats",
    "musique",
    "couleurs",
    "description",
    "gouts",
    "salutations",
    "questions",
    "jours",
    "jeux",
    "actions",
    "grammaire",
    "origines",
    "paix",
]
BAD_LATIN = {
    "être",
    "avoir",
    "déterminant",
    "déterminent",
    "édterminant",
    "quoi",
    "nouveau",
    "petits",
    "vous",
    "ne",
    "-",
}


def norm(value):
    value = "".join(
        c
        for c in unicodedata.normalize("NFKD", str(value)).casefold()
        if not unicodedata.combining(c)
    )
    return re.sub(r"[^\w]+", " ", value, flags=re.UNICODE).strip()


def latin_norm(value):
    return re.sub(
        r"\s+", " ", unicodedata.normalize("NFC", value).casefold().replace("’", "'")
    ).strip()


def word_french(value):
    value = norm(value)
    prefixes = (
        "les ",
        "des ",
        "une ",
        "un ",
        "le ",
        "la ",
        "du ",
        "de la ",
        "de l ",
        "d ",
        "l ",
        "ce ",
        "cet ",
        "cette ",
        "ces ",
        "son ",
        "sa ",
        "ses ",
        "ton ",
        "ta ",
        "tes ",
    )
    for _ in range(3):
        prefix = next((x for x in prefixes if value.startswith(x)), None)
        if not prefix:
            break
        value = value[len(prefix) :]
    return value


@lru_cache(maxsize=1)
def taxonomy():
    return json.loads(
        (Path(__file__).resolve().parents[2] / "content/catalog/semantic-topics.json").read_text()
    )["concepts"]


@lru_cache(maxsize=1)
def concepts():
    return {c["key"]: c for c in taxonomy()}


@lru_cache(maxsize=1)
def french_index():
    index = {}
    for c in taxonomy():
        for alias in c["aliases"]:
            index.setdefault(norm(alias), []).append(c["key"])
    return index


def french_concepts(text):
    """Longest lexical spans win: pommes de terre never become a fruit match."""
    words = norm(text).split()
    result = []
    i = 0
    index = french_index()
    while i < len(words):
        found = None
        for size in range(min(5, len(words) - i), 0, -1):
            key = " ".join(words[i : i + size])
            if key in index:
                found = (size, index[key])
                break
        if found:
            for key in found[1]:
                if key not in result:
                    result.append(key)
            i += found[0]
        else:
            i += 1
    return result


def organize(kind, data):
    if kind == "letter":
        return dict(
            topics=["alphabet"],
            concept=None,
            role="letter",
            rank=0,
            reason="Lettre de l’alphabet",
            version=VERSION,
        )
    fr = str(data.get("french") or "")
    lat = str(data.get("latin") or "")
    key = None
    if kind == "word":
        if (data.get("source_issues") and not data.get("source_issues_reviewed")) or latin_norm(
            lat
        ) in BAD_LATIN:
            return dict(
                topics=["a-revoir"],
                concept=None,
                role="review",
                rank=999,
                reason="Incohérence source ou libellé technique/français dans le champ kabyle",
                version=VERSION,
            )
        if (
            "(name)" in lat.casefold()
            or "(nom)" in lat.casefold()
            or "(name)" in fr.casefold()
            or fr in ("Maria", "Omar", "Idir", "Max", "Ali", "Yanis", "Cecilia")
        ):
            return dict(
                topics=["prenoms"],
                concept="prenom-" + norm(re.sub(r"\s*\([^)]*\)", "", lat)),
                role="name",
                rank=100 + len(lat),
                reason="Nom propre, distinct du vocabulaire à apprendre",
                version=VERSION,
            )
        # These are number-course entries; "neuf" elsewhere can mean "nouveau".
        preferred = [
            c
            for c in taxonomy()
            if c["theme"] == "nombres"
            and norm(fr) in [norm(x) for x in c["aliases"]]
            and latin_norm(lat) in [latin_norm(x) for x in c["preferred"]]
        ]
        if preferred:
            key = preferred[0]["key"]
        elif latin_norm(lat) == "akka":
            return dict(
                topics=["a-revoir"],
                concept="fragment-quoi-de-neuf",
                role="fragment",
                rank=100,
                reason="Fragment de « Quoi de neuf ? », pas le nombre neuf",
                version=VERSION,
            )
        else:
            hits = french_index().get(word_french(fr), []) or french_index().get(norm(fr), [])
            hits = [
                k
                for k in hits
                if not (
                    k in ("nombre-1", "nombre-9")
                    and latin_norm(lat) not in concepts()[k]["preferred"]
                )
            ]
            if hits:
                key = hits[0]
        if key:
            c = concepts()[key]
            preferred = [latin_norm(x) for x in c["preferred"]]
            rank = (
                preferred.index(latin_norm(lat))
                if latin_norm(lat) in preferred
                else 100 + len(lat) + (30 if "-" in lat else 0)
            )
            return dict(
                topics=c["topics"],
                concept=key,
                role=c["role"],
                rank=rank,
                reason="Sens français : " + c["label"],
                version=VERSION,
            )
        return dict(
            topics=["autres-mots"],
            concept=None,
            role="unclassified",
            rank=999,
            reason="Sens français non couvert : " + fr,
            version=VERSION,
        )
    hits = french_concepts(fr)
    # Articles and the idiom « quoi de neuf » are not counting lessons.
    hits = [
        k
        for k in hits
        if k not in ("nombre-1", "nombre-9") or norm(fr) == norm(concepts()[k]["label"])
    ]
    if not re.search(
        r"\b(la|une|sa|ma|ta|cette|les|des|mes|tes|ses) porte(s)?\b", norm(fr)
    ) and norm(fr) not in ("porte", "portes"):
        hits = [k for k in hits if k != "porte"]
    if re.match(r"^(comment vas tu|comment ca va|ca va)", norm(fr)):
        hits = [k for k in hits if k != "aller"]
    if not re.search(r"\b(le|un|son|mon|ton|ce|les|des|mes|tes|ses) lits?\b", norm(fr)) and norm(
        fr
    ) not in ("lit", "lits"):
        hits = [k for k in hits if k != "lit"]
    topics = []
    for key in hits:
        for theme in concepts()[key]["topics"]:
            if theme == "grammaire":
                continue
            if theme not in topics:
                topics.append(theme)
    primary = next((t for t in PRIORITY if t in topics), "autres-phrases")
    text = norm(fr)
    if re.match(
        r"^(bonjour|bonsoir|salut|merci|au revoir|bonne journee|bonne nuit|quel est ton nom|mon nom|comment vas tu|comment ca va|ca va|quoi de neuf|heureux de te connaitre)",
        text,
    ):
        primary = "salutations"
    elif text.startswith("bon voyage"):
        primary = "voyages"
    elif text.startswith("bon appetit"):
        primary = "alimentation"
    elif text.startswith("combien") and ("coute" in text or "prix" in text):
        primary = "achats"
    elif "poisson" in text and re.search(r"\b(mange|manges|mangent|manger)\b", text):
        primary = "alimentation"
    topics = [primary] + [t for t in topics if t != primary]
    return dict(
        topics=topics,
        concept=None,
        role="phrase",
        rank=0,
        reason="Sens de la phrase française ; chapitres source non utilisés",
        version=VERSION,
        concepts=hits,
    )


def fields(kind, data):
    result = organize(kind, data)
    return {
        "topic_keys": result["topics"],
        "concept_key": result["concept"],
        "learning_role": result["role"],
        "organization_version": VERSION,
        "learning_rank": result["rank"],
        "matched_concepts": result.get(
            "concepts", [result["concept"]] if result["concept"] else []
        ),
    }


def source_span(text, forms):
    """Only actual Kabyle forms are highlighted, never an inferred word alignment."""
    normalized = unicodedata.normalize("NFC", text)
    for form in sorted(set(forms), key=len, reverse=True):
        if not form.strip():
            continue
        match = re.search(
            r"(?<!\w)" + re.escape(unicodedata.normalize("NFC", form)) + r"(?!\w)",
            normalized,
            re.IGNORECASE,
        )
        if match:
            return {
                "start": match.start(),
                "end": match.end(),
                "text": normalized[match.start() : match.end()],
                "before": normalized[: match.start()],
                "after": normalized[match.end() :],
            }
    return None

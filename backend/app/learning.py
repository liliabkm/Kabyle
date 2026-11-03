"""Derived learning hints; neither CEFR certification nor word alignment is inferred."""

import hashlib, re, unicodedata


def clean_token(value):
    return (
        unicodedata.normalize("NFC", value)
        .strip(' \t\r\n.,!?;:«»“”"()[]…')
        .casefold()
        .replace("’", "'")
    )


def lexeme_key(value):
    return hashlib.sha256(clean_token(value).encode()).hexdigest()


def tokens(text):
    return re.findall(r"[^\W_]+(?:[’'\-][^\W_]+)*", unicodedata.normalize("NFC", text), re.UNICODE)


def features(kind, data):
    count = len(tokens(data.get("latin", ""))) if kind == "phrase" else 0
    return {
        "learning_band": (
            ("short" if count <= 4 else "medium" if count <= 8 else "long")
            if kind == "phrase"
            else None
        ),
        "has_audio": bool(usable_audios(data)),
        "lexeme_key": lexeme_key(data.get("latin", "")) if kind == "word" else None,
    }


def usable_audios(data):
    return [
        a
        for a in data.get("audios", [])
        if isinstance(a, dict)
        and isinstance(a.get("url"), str)
        and (a["url"].startswith("https://") or a["url"].startswith("/api/media/"))
        and a.get("author")
        and a.get("license")
    ]


def learning_info(data):
    words = tokens(data.get("latin", ""))
    return {
        "words": words,
        "word_count": len(words),
        "difficulty": features("phrase", data)["learning_band"],
        "difficulty_status": "estimated_from_length",
        "cefr_level": data.get("cefr_level") or None,
        "grammar_note": data.get("grammar_note") or None,
    }

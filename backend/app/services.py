from typing import Protocol
from dataclasses import dataclass
from pathlib import Path
import re
@dataclass
class Recognition:
    available: bool
    reason: str
    text: str | None = None
    confidence: float | None = None
class VisionProvider(Protocol):
    def recognize(self, image: bytes) -> Recognition: ...
class SpeechProvider(Protocol):
    def transcribe(self, recording: bytes) -> Recognition: ...
class UnavailableVision:
    def recognize(self, image: bytes) -> Recognition:
        return Recognition(False, "Aucun modèle évalué disponible. Le dépôt Tifinagh-MNIST ne fournit ni données ni correspondance vérifiable des classes avec notre sous-ensemble.")
class UnavailableSpeech:
    def transcribe(self, recording: bytes) -> Recognition:
        return Recognition(False, "Aucun modèle kabyle évalué et configuré. Vos enregistrements restent dans le navigateur.")
class LocalMedia:
    def __init__(self, root: str): self.root = Path(root).resolve()
    def path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root): raise ValueError("Invalid media key")
        return path
# A MediaStore with the same path/put interface may be replaced by an S3 adapter.
def compare_words(expected: str, observed: str):
    words = lambda s: re.findall(r"[^\W_]+", s.casefold(), re.UNICODE)
    import difflib
    a, b = words(expected), words(observed)
    return [{"operation": op, "expected": a[i:j], "observed": b[k:l]} for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b).get_opcodes()]

"""Real-model adapters (NOT run or tested in the build sandbox: no access to HuggingFace).
Install: pip install sentence-transformers torch.  Verify the NLI label order from the model card before use."""
from __future__ import annotations
import numpy as np


class HFEntailment:
    """EntailmentScorer backed by an NLI cross-encoder. Replaces LexicalEntailment in production."""
    LABELS = ["contradiction", "entailment", "neutral"]   # order used by cross-encoder/nli-* models; verify

    def __init__(self, model_name: str = "cross-encoder/nli-deberta-v3-base"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name)

    def __call__(self, criterion: str, answer: str) -> float:
        logits = np.asarray(self.model.predict([(answer, criterion)])[0], dtype=float)  # premise=answer
        p = np.exp(logits - logits.max())
        p /= p.sum()
        return float(p[self.LABELS.index("entailment")])


class HFEmbedder:
    """Bi-encoder similarity helper for the C1 adapter (all-MiniLM-L6-v2 is the model used in Cong et al. [1])."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def cosine(self, a: str, b: str) -> float:
        va, vb = self.model.encode([a, b], normalize_embeddings=True)
        return float(np.clip(va @ vb, 0, 1))

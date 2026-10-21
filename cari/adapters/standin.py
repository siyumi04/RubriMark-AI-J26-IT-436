"""Offline stand-ins for model-based checks. These are LEXICAL PROXIES, not semantic models.
They exist so the pipeline can run before Components 1/3/4 and the real models are available.
Swap in cari.adapters.hf_models for real NLI/embedding models."""
from __future__ import annotations
import numpy as np
from ..textutil import tokens, normalize

STOP = set("a an the and of is are in to by as it for at on or from with be that when up than this".split())
NEG = {"not", "never", "no", "cannot"}

SYN_PAIRS = {  # headword -> synonym (single words so token matching stays simple)
    "absorb": "capture", "using": "through", "produced": "generated", "stored": "kept", "released": "emitted",
    "reliable": "dependable", "faster": "quicker", "guarantees": "ensures", "reduces": "lowers",
    "prevents": "avoids", "improves": "enhances", "performs": "behaves", "badly": "poorly",
    "penalises": "punishes", "complexity": "intricacy", "settles": "stabilises", "raises": "lifts",
    "pushes": "drives", "speeds": "accelerates", "identical": "matching", "growth": "development",
    "copied": "duplicated", "splits": "divides", "movement": "flow", "steeper": "sharper",
    "increases": "boosts", "required": "needed", "memorises": "remembers", "detect": "spot",
    "higher": "greater", "more": "additional", "sends": "transmits", "establishes": "creates",
    "keeps": "retains", "kept": "maintained", "helps": "assists", "suits": "fits", "equals": "matches",
}


def make_known_syn(rng: np.random.Generator, frac: float) -> dict[str, str]:
    """synonym -> headword for the subset of pairs a checker 'knows' (imperfect on purpose)."""
    return {s: h for h, s in SYN_PAIRS.items() if rng.random() < frac}


class LexicalMatcher:
    def __init__(self, known_syn: dict[str, str]):
        self.known = known_syn

    def _canon(self, toks):
        return {self.known.get(t, t) for t in toks}

    def overlap(self, concept: str, answer: str) -> float:
        c = {t for t in tokens(concept) if t not in STOP}
        if not c:
            return 0.0
        return len(c & self._canon(tokens(answer))) / len(c)

    def negated(self, concept: str, answer: str) -> bool:
        """A sentence that mostly matches the concept and contains a negation absent from the concept."""
        concept_neg = NEG & set(tokens(concept))
        for sent in answer.split("."):
            if not sent.strip():
                continue
            if (NEG & set(tokens(sent))) - concept_neg and self.overlap(concept, sent) >= 0.5:
                return True
        return False


class LexicalEntailment:
    """EntailmentScorer proxy for C2's independent per-criterion check: P(answer entails criterion)."""

    def __init__(self, known_syn: dict[str, str]):
        self.m = LexicalMatcher(known_syn)

    def __call__(self, criterion: str, answer: str) -> float:
        if self.m.negated(criterion, answer):
            return 0.05
        return float(np.clip((self.m.overlap(criterion, answer) - 0.2) / 0.5, 0.0, 1.0))

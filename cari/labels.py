"""Ground-truth labels. Deliberately separate from the contract (no leakage into decisions)."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass


def modal_set(scores: list[float]) -> set[float]:
    """Most frequent human score(s); ties all count as valid (as in SURE)."""
    c = Counter(scores)
    top = max(c.values())
    return {s for s, n in c.items() if n == top}


@dataclass
class LabelRecord:
    human_scores: list[float]
    max_score: float

    @property
    def gold_norm(self) -> float:
        return sum(self.human_scores) / len(self.human_scores) / self.max_score


def make_label(ai_score: float, human_scores: list[float]) -> int:
    """y = 1 ("unreliable") when the AI score matches none of the modal human scores."""
    return int(ai_score not in modal_set(human_scores))

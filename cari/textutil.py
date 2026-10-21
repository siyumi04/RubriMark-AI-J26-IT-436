import re
from difflib import SequenceMatcher
from typing import Optional

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")


def normalize(text: str) -> str:
    return _WS.sub(" ", _PUNCT.sub(" ", text.lower())).strip()


def tokens(text: str) -> list[str]:
    return normalize(text).split()


def span_grounded(span: str, answer: str, fuzzy_threshold: Optional[float] = None) -> bool:
    """Is the quoted evidence recoverable from the student answer? (GradeAgentOps-style check.)

    Exact mode: normalised span must be a substring of the normalised answer.
    Fuzzy mode: longest common substring covers >= fuzzy_threshold of the span.
    """
    s, a = normalize(span), normalize(answer)
    if not s:
        return False
    if s in a:
        return True
    if fuzzy_threshold is None:
        return False
    m = SequenceMatcher(None, s, a, autojunk=False).find_longest_match(0, len(s), 0, len(a))
    return m.size / len(s) >= fuzzy_threshold

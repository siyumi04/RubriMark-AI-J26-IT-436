from dataclasses import dataclass
from typing import Optional


@dataclass
class CariConfig:
    fuzzy_threshold: Optional[float] = None   # None = exact evidence grounding
    con_gate: float = 0.5                     # P_con above this ...
    high_score_frac: float = 0.5              # ... with score >= this fraction of max fires a gate
    level: str = "indicator"                  # "indicator" or "component" aggregation features
    tau_policy: str = "recall"                # "recall" | "f1" | "cost"
    recall_target: float = 0.95
    c_fn: float = 5.0
    c_fp: float = 1.0

    @property
    def config_id(self) -> str:
        return f"{self.level}|{self.tau_policy}|fz={self.fuzzy_threshold}|gate={self.con_gate}"

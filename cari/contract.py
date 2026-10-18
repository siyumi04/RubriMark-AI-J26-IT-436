"""Versioned data contract between Components 1/3/4 and the reliability layer (Component 2).

The engine only ever receives an AssessmentCase. Expert labels live in cari.labels and are
never part of this contract, so they cannot leak into a decision.
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

CONTRACT_VERSION = "1.0"


class NLIProbs(BaseModel):
    ent: float = Field(ge=0, le=1)
    con: float = Field(ge=0, le=1)
    neu: float = Field(ge=0, le=1)


class C1Output(BaseModel):
    """Semantic evaluation (Component 1)."""
    cos_bi: float = Field(ge=0, le=1)        # bi-encoder similarity, student vs reference
    cross_enc: float = Field(ge=0, le=1)     # cross-encoder re-ranking score
    nli: NLIProbs                            # student answer vs reference answer
    missing_concepts: list[str] = []         # concept ids judged missing
    n_concepts: int = Field(ge=1)
    knn_typicality: float = Field(ge=0, le=1)  # mean cosine to 5 nearest other answers


class Criterion(BaseModel):
    id: str
    concept_id: str                          # links a rubric criterion to a C1 concept
    description: str
    weight: float = Field(ge=0)
    points: float = Field(ge=0)              # awarded
    max_points: float = Field(gt=0)
    evidence_span: Optional[str] = None      # verbatim quote from the student answer


class C3Output(BaseModel):
    """Adaptive rubric + criterion-based scoring (Component 3)."""
    rubric_id: str
    rubric_version: int
    rubric_approved: bool                    # lecturer approved the rubric before scoring
    max_score: float = Field(gt=0)
    runs: list[float]                        # total score of each repeated grading (temperature > 0)
    ai_score: float                          # reported final total
    criteria: list[Criterion]


class Claim(BaseModel):
    criterion_id: str
    outcome: Literal["met", "not_met"]
    span: Optional[str] = None


class C4Output(BaseModel):
    """Explainable feedback (Component 4)."""
    claims: list[Claim]
    direct_gaps: list[str] = []              # concept ids the feedback says are missing
    root_causes: list[str] = []              # inferred prerequisite gaps (not scored)
    stated_score: Optional[float] = None     # grade quoted in the feedback text


class Provenance(BaseModel):
    model: str = "unknown"
    version: str = "0"
    run_ids: list[str] = []


class AssessmentCase(BaseModel):
    contract_version: str = CONTRACT_VERSION
    assessment_id: str
    question_id: str
    student_response: str
    reference_answer: str
    student_email: Optional[str] = None
    c1: Optional[C1Output] = None
    c3: Optional[C3Output] = None
    c4: Optional[C4Output] = None
    provenance: Provenance = Provenance()


class ReliabilityResult(BaseModel):
    assessment_id: str
    cari: Optional[float]
    decision: Literal["AUTO_RELEASE", "LECTURER_VALIDATION"]
    gates_fired: list[str]
    indicators: dict[str, Optional[float]]
    component_scores: dict[str, Optional[float]]
    weakest: list[str]
    reason: str
    config_id: str
    tau: float

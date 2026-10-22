from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class PerformanceLevel(BaseModel):
    level: str  # Exemplary, Proficient, Developing, Unsatisfactory
    score_percentage: float  # e.g., 100%, 75%, 50%, 25%
    description: str


class RubricCriterionBase(BaseModel):
    criterion_name: str
    description: str
    weight_percentage: float = Field(..., ge=0.0, le=100.0)
    max_marks: float = Field(default=25.0, ge=0.0)
    blooms_dimension: Optional[str] = "Analytical"
    performance_levels: Optional[List[PerformanceLevel]] = []


class RubricCriterionCreate(RubricCriterionBase):
    pass


class RubricCriterionOut(RubricCriterionBase):
    id: int
    rubric_id: int

    class Config:
        from_attributes = True


class RubricBase(BaseModel):
    title: str
    version: int = 1
    status: str = "draft"  # draft, optimized, validated, approved


class RubricCreate(RubricBase):
    assessment_id: int
    criteria: List[RubricCriterionCreate]


class RubricUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    criteria: Optional[List[RubricCriterionCreate]] = None
    approval_notes: Optional[str] = None
    approved_by: Optional[str] = None


STANDARD_REJECTION_REASONS = [
    "Missing criteria",
    "Incorrect marks or weights",
    "Bloom's taxonomy mismatch",
    "Unclear criterion descriptions",
    "Incorrect or irrelevant criteria",
    "Other",
]


class RejectRubricRequest(BaseModel):
    rejection_reasons: List[str] = Field(..., description="Selected rejection reasons from the standard list or custom")
    feedback: Optional[str] = Field(None, description="Optional written feedback or clarification from the lecturer")
    rejected_by: Optional[str] = Field("Dr. Lecturer", description="Lecturer rejecting the rubric")


class RegenerateRubricRequest(BaseModel):
    rejection_reasons: Optional[List[str]] = Field(None, description="Rejection reasons to address (defaults to existing on rubric)")
    feedback: Optional[str] = Field(None, description="Specific feedback to address during regeneration")
    rejected_by: Optional[str] = Field("Dr. Lecturer", description="Lecturer requesting regeneration")
    use_rag: Optional[bool] = Field(None, description="Whether to include RAG retrieval context")
    force_fallback: Optional[bool] = Field(None, description="Whether to bypass Ollama and force deterministic rule-based generation")
    generation_mode: Optional[str] = Field(None, description="Override generation mode: 'ollama_rag' or 'rule_based'")


class RubricOut(RubricBase):
    id: int
    assessment_id: int
    parent_rubric_id: Optional[int] = None
    validation_status: str
    validation_score: float
    validation_messages: List[str] = []
    generation_mode: Optional[str] = "rule_based"
    rag_context_used: Optional[str] = None
    is_approved: bool
    approval_notes: Optional[str] = None
    approved_by: Optional[str] = None
    rejection_reasons: List[str] = []
    rejection_feedback: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    criteria: List[RubricCriterionOut] = []

    class Config:
        from_attributes = True


class RubricValidationResult(BaseModel):
    rubric_id: int
    is_valid: bool
    validation_score: float
    status: str
    checks: List[dict]
    messages: List[str]
    recommendations: List[str]


class DynamicWeightOptimizationRequest(BaseModel):
    rubric_id: Optional[int] = None
    criteria: List[RubricCriterionBase]
    target_blooms_level: Optional[str] = "Analyze"
    lecturer_priorities: Optional[dict] = None


class DynamicWeightOptimizationResponse(BaseModel):
    rubric_id: Optional[int] = None
    version: Optional[int] = None
    optimized_criteria: List[RubricCriterionBase]
    total_weight: float
    total_marks: Optional[float] = None
    optimization_rationale: str
    status: str


class RubricVersionHistoryItem(BaseModel):
    id: int
    version: int
    parent_rubric_id: Optional[int] = None
    title: str
    status: str
    is_approved: bool
    generation_mode: Optional[str] = "rule_based"
    validation_status: str
    validation_score: float
    rejection_reasons: List[str] = []
    rejection_feedback: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime
    criteria_count: int = 0
    total_marks: float = 0.0


class RubricVersionHistoryOut(BaseModel):
    assessment_id: int
    current_rubric_id: Optional[int] = None
    versions: List[RubricVersionHistoryItem]

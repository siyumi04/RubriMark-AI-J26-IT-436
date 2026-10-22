from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class QuestionAnalysisRequest(BaseModel):
    question_text: str
    reference_answer: Optional[str] = None
    learning_outcome: Optional[str] = None
    lecturer_guidelines: Optional[str] = None
    subject_area: Optional[str] = "Computer Science / Software Engineering"


class BloomDimensionBreakdown(BaseModel):
    dimension: str
    confidence: float
    description: str


class QuestionAnalysisResponse(BaseModel):
    blooms_level: str
    cognitive_complexity: str
    detected_domain: Optional[str] = None
    extracted_concepts: List[str]
    dimensions: Optional[List[BloomDimensionBreakdown]] = []
    recommended_criteria: List[dict]
    rationale: str


class CriterionScoreOut(BaseModel):
    id: Optional[int] = None
    criterion_id: int
    criterion_name: str
    score_awarded: float
    max_score: float
    weight_percentage: float
    performance_level: str
    conceptual_alignment: Optional[float] = 0.0
    evidence_quote: Optional[str] = None
    feedback: str
    confidence_score: float

    class Config:
        from_attributes = True


class StudentSubmissionCreate(BaseModel):
    assessment_id: int
    student_id: str
    student_name: str
    answer_text: str
    scoring_method: Optional[str] = "semantic"


class StudentSubmissionOut(BaseModel):
    id: int
    assessment_id: int
    student_id: str
    student_name: str
    answer_text: str
    total_score: float
    max_marks: float
    percentage: float
    status: str
    scoring_method: Optional[str] = "semantic"
    semantic_engine: Optional[str] = "local_semantic_nlp"
    overall_feedback: Optional[str] = None
    created_at: datetime
    criterion_scores: List[CriterionScoreOut] = []

    class Config:
        from_attributes = True


class ScoringEvaluationRequest(BaseModel):
    submission_id: Optional[int] = None
    assessment_id: int
    rubric_id: int
    student_id: str
    student_name: str
    answer_text: str
    scoring_method: Optional[str] = "semantic"  # "semantic" or "keyword_baseline"



class AssessmentResultsSummary(BaseModel):
    assessment_id: int
    assessment_title: str
    total_submissions: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    criterion_performance: List[dict]

from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


# Health and Status schemas
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    model_loaded: bool
    model_status: str


# Student schemas
class StudentBase(BaseModel):
    student_id: str
    student_name: str
    email: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: int
    answers_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Question schemas
class QuestionBase(BaseModel):
    question_id: str
    question_text: str
    subject: str = "Computer Science"
    total_marks: float = 10.0


class QuestionResponse(QuestionBase):
    id: int

    class Config:
        from_attributes = True


# Recommendation schemas
class RecommendationBase(BaseModel):
    concept_name: str
    resource_title: str
    resource_type: str = "SLIIT IT2030 Lecture PDF"
    resource_url: str
    priority_level: str = "High"
    lecture_number: Optional[str] = None
    verified_page: Optional[int] = None
    reason: Optional[str] = None
    practice_activity: Optional[str] = None
    download_url: Optional[str] = None
    frontend_view_url: Optional[str] = None


class RecommendationResponse(RecommendationBase):
    id: int
    feedback_id: int

    class Config:
        from_attributes = True


# Feedback schemas
class FeedbackBase(BaseModel):
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    missing_concepts: List[str] = []
    correctly_identified_concepts: List[str] = []
    mark_deduction_reason: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    personalized_feedback: str


class FeedbackResponse(BaseModel):
    id: int
    student_answer_id: int
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    missing_concepts: List[str] = []
    correctly_identified_concepts: List[str] = []
    expected_concepts: List[str] = []
    expected_undetected_concepts: List[str] = []
    requires_human_review: bool = False
    unrelated_cross_question_concepts: List[str] = []
    mark_deduction_reason: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    personalized_feedback: str
    created_at: datetime
    recommendations: List[RecommendationResponse] = []

    class Config:
        from_attributes = True


# Student Answer schemas
class StudentAnswerBase(BaseModel):
    student_id: str
    question_id: str
    student_answer: str
    obtained_marks: Optional[float] = None


class StudentAnswerResponse(StudentAnswerBase):
    id: int
    submission_date: datetime
    question: Optional[QuestionResponse] = None
    feedback: Optional[FeedbackResponse] = None

    class Config:
        from_attributes = True


# Analyze Answer Request and Response
class AnalyzeAnswerRequest(BaseModel):
    student_id: str
    question_id: str
    student_answer: str
    obtained_marks: Optional[float] = None
    save_to_db: bool = True


class AnalyzeAnswerResponse(BaseModel):
    student_id: str
    question_id: str
    student_answer: str
    obtained_marks: Optional[float] = None
    total_marks: Optional[float] = None
    ai_status: str  # "model_inference" or "model_unavailable"
    missing_concepts: List[str]
    correctly_identified_concepts: List[str] = []
    expected_concepts: List[str] = []
    expected_undetected_concepts: List[str] = []
    requires_human_review: bool = False
    uncertainty_info: Optional[str] = None
    unrelated_cross_question_concepts: List[str] = []
    cross_question_anomalies_filtered: List[str] = []
    mark_deduction_reason: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    strengths: str
    weaknesses: str
    personalized_feedback: str
    recommendations: List[RecommendationBase]
    root_knowledge_gaps: List[str] = []
    saved_answer_id: Optional[int] = None


# Dataset Import Response
class DatasetImportResponse(BaseModel):
    success: bool
    imported_students: int
    imported_questions: int
    imported_answers: int
    errors: List[str] = []
    message: str

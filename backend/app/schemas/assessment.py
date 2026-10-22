from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AssessmentBase(BaseModel):
    title: str = Field(..., example="Software Architecture Short Answer Test")
    course_code: str = Field(default="IT4360", example="IT4360")
    question_text: str = Field(..., example="Explain the trade-offs between Microservices and Monolithic architectures in terms of scalability, operational complexity, and fault isolation.")
    reference_answer: Optional[str] = Field(None, example="A comprehensive answer should contrast scaling granularity, distributed debugging/deployment overhead, and cascading failures.")
    model_answer: Optional[str] = Field(None, example="Alternative alias for reference answer")
    max_marks: float = Field(default=100.0, ge=1.0)
    blooms_level: Optional[str] = Field(default="Analyze", example="Analyze")
    cognitive_complexity: Optional[str] = Field(default="Medium", example="Medium")
    learning_outcome: Optional[str] = Field(None, example="Evaluate and contrast architectural trade-offs in distributed systems.")
    lecturer_guidelines: Optional[str] = Field(None, example="Focus on scalability limits, fault domains, and operational overhead.")


class AssessmentCreate(AssessmentBase):
    pass


class AssessmentUpdate(BaseModel):
    title: Optional[str] = None
    course_code: Optional[str] = None
    question_text: Optional[str] = None
    reference_answer: Optional[str] = None
    model_answer: Optional[str] = None
    max_marks: Optional[float] = None
    blooms_level: Optional[str] = None
    cognitive_complexity: Optional[str] = None
    learning_outcome: Optional[str] = None
    lecturer_guidelines: Optional[str] = None


class AssessmentOut(AssessmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

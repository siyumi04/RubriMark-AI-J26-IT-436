from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class StudentSubmission(Base):
    __tablename__ = "student_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(64), nullable=False, index=True)
    student_name = Column(String(128), nullable=False)
    answer_text = Column(Text, nullable=False)
    total_score = Column(Float, default=0.0)
    max_marks = Column(Float, default=100.0)
    percentage = Column(Float, default=0.0)
    status = Column(String(32), default="scored")  # pending, scoring, scored
    scoring_method = Column(String(64), default="semantic")  # semantic, keyword_baseline, hybrid
    semantic_engine = Column(String(64), default="local_semantic_nlp")
    overall_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assessment = relationship("Assessment", back_populates="submissions")
    criterion_scores = relationship("CriterionScore", back_populates="submission", cascade="all, delete-orphan")


class CriterionScore(Base):
    __tablename__ = "criterion_scores"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("student_submissions.id", ondelete="CASCADE"), nullable=False)
    criterion_id = Column(Integer, nullable=False)
    criterion_name = Column(String(255), nullable=False)
    score_awarded = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    weight_percentage = Column(Float, nullable=False)
    performance_level = Column(String(64), nullable=True)  # Exemplary, Proficient, Developing, Unsatisfactory
    conceptual_alignment = Column(Float, default=0.0)
    evidence_quote = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.85)

    submission = relationship("StudentSubmission", back_populates="criterion_scores")


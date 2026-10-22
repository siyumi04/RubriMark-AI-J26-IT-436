import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Rubric(Base):
    __tablename__ = "rubrics"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, default=1)
    title = Column(String(255), nullable=False)
    status = Column(String(32), default="draft")  # draft, optimized, validated, approved
    validation_status = Column(String(32), default="pending")  # valid, warning, error, pending
    validation_score = Column(Float, default=0.0)  # 0.0 to 1.0 (internal coherence/coverage score)
    validation_messages = Column(Text, default="[]")  # JSON list of validation checks
    generation_mode = Column(String(64), default="rule_based")  # "ollama_rag", "ollama_feedback_regenerated", or "rule_based_fallback"
    rag_context_used = Column(Text, nullable=True)  # Summary/reference of RAG context used
    is_approved = Column(Boolean, default=False)
    approval_notes = Column(Text, nullable=True)
    approved_by = Column(String(128), nullable=True)

    # Phase 3: Lecturer Rejection & Feedback Fields
    rejection_reasons = Column(Text, nullable=True)  # Stored as JSON list of strings
    rejection_feedback = Column(Text, nullable=True)  # Optional lecturer written feedback
    rejected_at = Column(DateTime, nullable=True)
    rejected_by = Column(String(128), nullable=True)
    parent_rubric_id = Column(Integer, ForeignKey("rubrics.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assessment = relationship("Assessment", back_populates="rubrics")
    criteria = relationship("RubricCriterion", back_populates="rubric", cascade="all, delete-orphan", order_by="RubricCriterion.id")
    parent_rubric = relationship("Rubric", remote_side=[id], backref="child_rubrics")
    rejections = relationship("RubricRejection", back_populates="rubric", cascade="all, delete-orphan", order_by="RubricRejection.created_at.desc()")


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id = Column(Integer, primary_key=True, index=True)
    rubric_id = Column(Integer, ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False)
    criterion_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    weight_percentage = Column(Float, nullable=False)  # e.g., 25.0%
    max_marks = Column(Float, nullable=False)  # scaled marks
    blooms_dimension = Column(String(64), nullable=True)  # Conceptual, Procedural, Analytical
    
    # Stored as JSON string: list of performance descriptor levels (Exemplary, Proficient, Developing, Unsatisfactory)
    performance_levels = Column(Text, default="[]")

    rubric = relationship("Rubric", back_populates="criteria")


class RubricRejection(Base):
    __tablename__ = "rubric_rejections"

    id = Column(Integer, primary_key=True, index=True)
    rubric_id = Column(Integer, ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False)
    rejection_reasons = Column(Text, nullable=False)  # JSON list of selected reasons
    feedback = Column(Text, nullable=True)
    rejected_by = Column(String(128), default="Dr. Lecturer")
    created_at = Column(DateTime, default=datetime.utcnow)

    rubric = relationship("Rubric", back_populates="rejections")

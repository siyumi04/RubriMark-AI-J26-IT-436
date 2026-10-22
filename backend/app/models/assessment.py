from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    course_code = Column(String(64), nullable=False, default="IT4360")
    question_text = Column(Text, nullable=False)
    reference_answer = Column(Text, nullable=True)
    max_marks = Column(Float, nullable=False, default=100.0)
    blooms_level = Column(String(64), nullable=True, default="Analyze")  # Remember, Understand, Apply, Analyze, Evaluate, Create
    cognitive_complexity = Column(String(64), nullable=True, default="Medium")  # Low, Medium, High
    learning_outcome = Column(Text, nullable=True)
    lecturer_guidelines = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rubrics = relationship("Rubric", back_populates="assessment", cascade="all, delete-orphan")
    submissions = relationship("StudentSubmission", back_populates="assessment", cascade="all, delete-orphan")

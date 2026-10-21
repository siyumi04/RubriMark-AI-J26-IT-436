from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    student_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=True)

    # Relationships
    answers = relationship("StudentAnswer", back_populates="student", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_id = Column(String(50), unique=True, index=True, nullable=False)
    question_text = Column(Text, nullable=False)
    subject = Column(String(100), default="Computer Science")
    total_marks = Column(Float, default=10.0)

    # Relationships
    answers = relationship("StudentAnswer", back_populates="question", cascade="all, delete-orphan")


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False, index=True)
    question_id = Column(String(50), ForeignKey("questions.question_id"), nullable=False, index=True)
    student_answer = Column(Text, nullable=False)
    obtained_marks = Column(Float, nullable=True)
    submission_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    feedback = relationship("Feedback", back_populates="student_answer", uselist=False, cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_answer_id = Column(Integer, ForeignKey("student_answers.id"), unique=True, nullable=False)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    missing_concepts = Column(Text, nullable=True)  # JSON or semicolon/comma-separated string
    correctly_identified_concepts = Column(Text, nullable=True)
    mark_deduction_reason = Column(Text, nullable=True)
    improvement_suggestions = Column(Text, nullable=True)
    personalized_feedback = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student_answer = relationship("StudentAnswer", back_populates="feedback")
    recommendations = relationship("LearningRecommendation", back_populates="feedback", cascade="all, delete-orphan")


class LearningRecommendation(Base):
    __tablename__ = "learning_recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=False, index=True)
    concept_name = Column(String(150), nullable=False)
    resource_title = Column(String(200), nullable=False)
    resource_type = Column(String(50), default="SLIIT IT2030 Lecture PDF")
    resource_url = Column(String(500), nullable=False)
    priority_level = Column(String(20), default="High")  # High, Medium, Low
    lecture_number = Column(String(50), nullable=True)
    verified_page = Column(Integer, nullable=True)
    reason = Column(Text, nullable=True)
    practice_activity = Column(Text, nullable=True)
    download_url = Column(String(500), nullable=True)

    # Relationships
    feedback = relationship("Feedback", back_populates="recommendations")


"""Persistence. PostgreSQL in production (DATABASE_URL=postgresql+psycopg://...), SQLite for local dev/tests.
Lecturer decisions are stored here for evaluation/recalibration ONLY; the engine never reads them."""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

JsonType = JSON().with_variant(JSONB(), "postgresql")


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Assessment(Base):
    __tablename__ = "assessments"
    assessment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    question_id: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JsonType)            # the AssessmentCase as received
    cari: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    decision: Mapped[str] = mapped_column(String(24), index=True)
    gates: Mapped[list] = mapped_column(JsonType)
    indicators: Mapped[dict] = mapped_column(JsonType)
    reason: Mapped[str] = mapped_column(Text)
    config_id: Mapped[str] = mapped_column(String(128))
    tau: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default="pending")   # pending | released | reviewed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LecturerDecision(Base):
    __tablename__ = "lecturer_decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.assessment_id"), index=True)
    action: Mapped[str] = mapped_column(String(16))             # approve | override
    final_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmailDelivery(Base):
    __tablename__ = "email_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.assessment_id"), index=True)
    recipient: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(16), default="sample")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


def make_session_factory(url: str | None = None):
    url = url or os.getenv("DATABASE_URL", "sqlite:///./cari.db")
    eng = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    Base.metadata.create_all(eng)
    return sessionmaker(eng, expire_on_commit=False)

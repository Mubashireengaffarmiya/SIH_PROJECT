"""
SMART-LM Database Layer
========================
SQLAlchemy ORM models and session factory.
Uses SQLite for the prototype; swap the DATABASE_URL to PostgreSQL later.
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Text,
    DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ---------------------------------------------------------------------------
# Connection string — swap to PostgreSQL by changing this one line
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_lm.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# ORM Models — EXISTING (do not remove)
# ---------------------------------------------------------------------------

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    product_name = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)         # VERIFIED_COMPLIANT | POTENTIAL_VIOLATION | NEEDS_HUMAN_REVIEW
    overall_confidence = Column(String(20), nullable=True)  # HIGH | MEDIUM | LOW
    image_path = Column(String(512), nullable=True)
    image_quality = Column(String(20), nullable=True)   # GOOD | ACCEPTABLE | POOR
    ocr_text_length = Column(Integer, default=0)
    is_demo = Column(Boolean, default=False)

    # New fields added non-destructively
    inspector_username = Column(String(100), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    product_category = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    review_status = Column(String(50), nullable=True)   # PENDING | APPROVED | REJECTED | RETAKE

    declarations = relationship("Declaration", back_populates="inspection", cascade="all, delete-orphan")
    evaluations = relationship("RuleEvaluationModel", back_populates="inspection", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")
    review_actions = relationship("ReviewAction", back_populates="inspection", cascade="all, delete-orphan")


class Declaration(Base):
    __tablename__ = "declarations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.inspection_id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    extracted_value = Column(Text, nullable=True)
    confidence = Column(String(20), nullable=True)      # HIGH | MEDIUM | LOW
    status = Column(String(50), nullable=True)          # VERIFIED_COMPLIANT | POTENTIAL_VIOLATION | NEEDS_HUMAN_REVIEW
    evidence_text = Column(Text, nullable=True)

    inspection = relationship("Inspection", back_populates="declarations")


class RuleEvaluationModel(Base):
    __tablename__ = "rule_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.inspection_id"), nullable=False)
    requirement = Column(Text, nullable=False)
    extracted_value = Column(Text, nullable=True)
    expected_requirement = Column(Text, nullable=True)
    rule_reference = Column(String(255), nullable=True)
    evidence = Column(Text, nullable=True)
    confidence = Column(String(20), nullable=True)
    result = Column(String(50), nullable=False)

    inspection = relationship("Inspection", back_populates="evaluations")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.inspection_id"), nullable=False)
    pdf_path = Column(String(512), nullable=True)
    docx_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    inspection = relationship("Inspection", back_populates="reports")


# ---------------------------------------------------------------------------
# ORM Models — NEW
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False)           # INSPECTOR | REVIEWER | ADMIN
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ReviewAction(Base):
    __tablename__ = "review_actions"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.inspection_id"), nullable=False)
    reviewer_username = Column(String(100), nullable=False)
    action = Column(String(30), nullable=False)         # CONFIRM | REJECT | RETAKE | NOT_VERIFIABLE | COMMENT
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    inspection = relationship("Inspection", back_populates="review_actions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)   # inspection | user | rule | report
    resource_id = Column(String(100), nullable=True)
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)      # target user
    message = Column(Text, nullable=False)
    notif_type = Column(String(50), nullable=True)      # inspection | review | report | violation
    related_id = Column(String(100), nullable=True)     # inspection_id etc.
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(50), unique=True, index=True, nullable=False)
    requirement = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    version = Column(String(20), nullable=True)
    effective_date = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    source = Column(String(255), nullable=True)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def init_db():
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

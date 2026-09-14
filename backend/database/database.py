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
# ORM Models
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

    declarations = relationship("Declaration", back_populates="inspection", cascade="all, delete-orphan")
    violations = relationship("Violation", back_populates="inspection", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")


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


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.inspection_id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)       # HIGH | MEDIUM | LOW
    confidence = Column(String(20), nullable=True)
    rule_id = Column(String(50), nullable=True)
    evidence = Column(Text, nullable=True)

    inspection = relationship("Inspection", back_populates="violations")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.inspection_id"), nullable=False)
    pdf_path = Column(String(512), nullable=True)
    docx_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    inspection = relationship("Inspection", back_populates="reports")


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

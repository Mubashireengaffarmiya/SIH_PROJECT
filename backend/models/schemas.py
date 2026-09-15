"""
SMART-LM Pydantic Schemas
==========================
Request / Response models for the FastAPI layer.
"""

from __future__ import annotations
from typing import Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

class OCRWord(BaseModel):
    text: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]


class OCRResult(BaseModel):
    words: List[OCRWord]
    full_text: str
    engine: str  # "paddleocr" | "tesseract"
    success: bool
    error: Optional[str] = None
    source_image: Optional[str] = None
    source_image: Optional[str] = None


# ---------------------------------------------------------------------------
# Image Quality
# ---------------------------------------------------------------------------

class ImageQualityResult(BaseModel):
    quality: str               # GOOD | ACCEPTABLE | POOR
    blur_score: float
    brightness: float
    contrast: float
    message: str
    width: int
    height: int


# ---------------------------------------------------------------------------
# Field Extraction
# ---------------------------------------------------------------------------

class ExtractedField(BaseModel):
    value: Optional[str] = None
    confidence: str = "LOW"    # HIGH | MEDIUM | LOW
    evidence_text: Optional[str] = None


class ExtractionResult(BaseModel):
    product_name: ExtractedField
    mrp: ExtractedField
    net_quantity: ExtractedField
    manufacturer: ExtractedField
    manufacturing_date: ExtractedField
    consumer_care: ExtractedField
    country_of_origin: ExtractedField
    best_before: ExtractedField
    unit_sale_price: ExtractedField


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------

class ViolationDetail(BaseModel):
    field_name: str
    reason: str
    severity: str              # HIGH | MEDIUM | LOW
    confidence: str
    rule_id: Optional[str] = None
    evidence: Optional[str] = None


class ComplianceResult(BaseModel):
    overall_status: str        # VERIFIED_COMPLIANT | POTENTIAL_VIOLATION | NEEDS_HUMAN_REVIEW
    overall_confidence: str    # HIGH | MEDIUM | LOW
    field_statuses: dict[str, str]   # field → status string
    violations: List[ViolationDetail]
    summary: str


# ---------------------------------------------------------------------------
# Analysis (full pipeline response)
# ---------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    inspection_id: str
    image_quality: ImageQualityResult
    ocr: OCRResult
    extraction: ExtractionResult
    compliance: ComplianceResult
    created_at: datetime
    is_demo: bool = False


# ---------------------------------------------------------------------------
# Inspection (DB read)
# ---------------------------------------------------------------------------

class DeclarationOut(BaseModel):
    field_name: str
    extracted_value: Optional[str]
    confidence: Optional[str]
    status: Optional[str]
    evidence_text: Optional[str]

    model_config = {"from_attributes": True}


class ViolationOut(BaseModel):
    field_name: str
    reason: str
    severity: str
    confidence: Optional[str]
    rule_id: Optional[str]
    evidence: Optional[str]

    model_config = {"from_attributes": True}


class InspectionSummary(BaseModel):
    inspection_id: str
    created_at: datetime
    product_name: Optional[str]
    status: str
    overall_confidence: Optional[str]
    image_quality: Optional[str]
    violation_count: int = 0
    is_demo: bool = False

    model_config = {"from_attributes": True}


class InspectionDetail(BaseModel):
    inspection_id: str
    created_at: datetime
    product_name: Optional[str]
    status: str
    overall_confidence: Optional[str]
    image_quality: Optional[str]
    image_path: Optional[str]
    is_demo: bool = False
    declarations: List[DeclarationOut] = []
    violations: List[ViolationOut] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

class DashboardStats(BaseModel):
    total: int
    compliant: int
    violations: int
    needs_review: int
    recent: List[InspectionSummary]

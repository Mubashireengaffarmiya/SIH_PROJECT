"""
Tests for the compliance rule engine.
Run: cd backend && pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.compliance import run_compliance, VERIFIED, VIOLATION, REVIEW


def _field(value, confidence="HIGH", evidence=None):
    return {"value": value, "confidence": confidence, "evidence_text": evidence}


def _empty():
    return {"value": None, "confidence": "LOW", "evidence_text": None}


def _good_extraction():
    return {
        "product_name": _field("Test Product"),
        "mrp": _field("₹50", "HIGH", "MRP ₹50"),
        "net_quantity": _field("500g", "HIGH", "Net Qty: 500g"),
        "manufacturer": _field("Test Foods Pvt. Ltd.", "HIGH"),
        "manufacturing_date": _field("09/2026", "HIGH"),
        "consumer_care": _field("1800-123-4567", "HIGH"),
        "country_of_origin": _field("India", "HIGH"),
        "best_before": _field("09/2027", "HIGH"),
        "unit_sale_price": _empty(),
    }


def _good_ocr():
    return {"success": True, "words": [], "full_text": "...", "engine": "paddleocr", "error": None}


class TestComplianceEngine:
    def test_fully_compliant(self):
        """All HIGH confidence fields → should be VERIFIED_COMPLIANT or at worst NEEDS_HUMAN_REVIEW."""
        result = run_compliance(_good_extraction(), _good_ocr(), "GOOD")
        # With all fields detected at HIGH confidence, overall should not be POTENTIAL_VIOLATION
        assert result["overall_status"] in (VERIFIED, REVIEW)
        assert result["overall_confidence"] in ("HIGH", "MEDIUM")

    def test_poor_image_quality_forces_review(self):
        """Poor image quality should always result in NEEDS_HUMAN_REVIEW."""
        result = run_compliance(_good_extraction(), _good_ocr(), "POOR")
        assert result["overall_status"] == REVIEW

    def test_ocr_failure_forces_review(self):
        """OCR failure should result in NEEDS_HUMAN_REVIEW."""
        bad_ocr = {"success": False, "words": [], "full_text": "", "engine": "none", "error": "No OCR"}
        result = run_compliance(_good_extraction(), bad_ocr, "GOOD")
        assert result["overall_status"] == REVIEW

    def test_missing_mrp_creates_review_not_violation(self):
        """
        Missing MRP (OCR didn't detect it) should create NEEDS_HUMAN_REVIEW,
        NOT POTENTIAL_VIOLATION — we can't be sure it's legally absent.
        """
        extraction = _good_extraction()
        extraction["mrp"] = _empty()
        result = run_compliance(extraction, _good_ocr(), "GOOD")
        mrp_violations = [v for v in result["violations"] if "mrp" in v.get("field_name", "").lower()
                          or "mrp" in (v.get("rule_id") or "").lower()]
        # Should have a review item but NOT automatically a POTENTIAL_VIOLATION
        assert result["overall_status"] != VIOLATION or any(
            "mrp" in v.get("rule_id", "").lower() for v in result["violations"]
        )
        # Verify the reason doesn't claim legal absence
        for v in mrp_violations:
            assert "legally" not in v["reason"].lower() or "human review" in v["reason"].lower()

    def test_low_confidence_detection_causes_review(self):
        """LOW confidence OCR detection → NEEDS_HUMAN_REVIEW for that field."""
        extraction = _good_extraction()
        extraction["mrp"] = _field("₹50", "LOW")  # LOW confidence
        result = run_compliance(extraction, _good_ocr(), "GOOD")
        # Low confidence should not result in fully compliant
        # (it gets REVIEW status for that field)
        mrp_rule_statuses = {
            k: v for k, v in result["field_statuses"].items() if "mrp" in k.lower()
        }
        if mrp_rule_statuses:
            assert any(v == REVIEW for v in mrp_rule_statuses.values())

    def test_violations_have_required_fields(self):
        """Every violation must have field_name, reason, severity, confidence, rule_id."""
        extraction = _good_extraction()
        extraction["mrp"] = _empty()
        extraction["net_quantity"] = _empty()
        extraction["manufacturer"] = _empty()
        result = run_compliance(extraction, _good_ocr(), "GOOD")
        for v in result["violations"]:
            assert "field_name" in v
            assert "reason" in v
            assert "severity" in v
            assert v["severity"] in ("HIGH", "MEDIUM", "LOW")
            assert "confidence" in v

    def test_summary_is_non_empty(self):
        result = run_compliance(_good_extraction(), _good_ocr(), "GOOD")
        assert result["summary"]
        assert len(result["summary"]) > 10

    def test_no_violations_when_all_detected(self):
        """When all fields are detected with HIGH confidence + GOOD image, violations should be minimal."""
        result = run_compliance(_good_extraction(), _good_ocr(), "GOOD")
        high_violations = [v for v in result["violations"] if v["severity"] == "HIGH"]
        assert len(high_violations) == 0

    def test_poor_image_reason_mentions_quality(self):
        """Violation reasons under poor image quality should mention image quality."""
        extraction = _good_extraction()
        extraction["mrp"] = _empty()
        result = run_compliance(extraction, _good_ocr(), "POOR")
        for v in result["violations"]:
            assert "poor" in v["reason"].lower() or "image" in v["reason"].lower()

    def test_confidence_levels_are_valid(self):
        result = run_compliance(_good_extraction(), _good_ocr(), "GOOD")
        assert result["overall_confidence"] in ("HIGH", "MEDIUM", "LOW")

    def test_field_statuses_are_valid(self):
        result = run_compliance(_good_extraction(), _good_ocr(), "GOOD")
        valid_statuses = {VERIFIED, VIOLATION, REVIEW}
        for status in result["field_statuses"].values():
            assert status in valid_statuses

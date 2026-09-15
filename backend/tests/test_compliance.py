import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.compliance import run_compliance, COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW, NOT_VERIFIABLE

def _good_ocr():
    return {"success": True, "words": [], "full_text": "...", "engine": "paddleocr", "error": None}

def test_run_compliance_good_image():
    extraction = {
        "mrp": {"value": "MRP 150 inclusive of all taxes", "confidence": "HIGH", "evidence_text": "MRP 150 inclusive of all taxes"},
        "net_quantity": {"value": "500g", "confidence": "HIGH", "evidence_text": "500g"},
    }
    
    result = run_compliance(extraction, _good_ocr(), "GOOD")
    assert "evaluations" in result
    
    # MRP format check should pass
    mrp_format_eval = next((e for e in result["evaluations"] if "Format" in e["rule_reference"]), None)
    if mrp_format_eval:
        assert mrp_format_eval["result"] == COMPLIANT

def test_run_compliance_poor_image():
    extraction = {
        "mrp": {"value": "150", "confidence": "LOW", "evidence_text": "150"},
    }
    result = run_compliance(extraction, _good_ocr(), "POOR")
    assert result["overall_status"] == NEEDS_REVIEW
    
def test_run_compliance_ocr_failure():
    bad_ocr = {"success": False}
    result = run_compliance({}, bad_ocr, "GOOD")
    assert result["overall_status"] == NEEDS_REVIEW

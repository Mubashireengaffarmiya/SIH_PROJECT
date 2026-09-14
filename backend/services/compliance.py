"""
SMART-LM Compliance Engine
============================
Loads rules from rules/rules.json and evaluates extracted declarations.

Each field gets one of three statuses:
  VERIFIED_COMPLIANT   — field detected with sufficient confidence
  POTENTIAL_VIOLATION  — field detected but has issues OR consistently missing
  NEEDS_HUMAN_REVIEW   — field not detected (OCR may have missed it — do NOT
                         automatically claim legal non-compliance)

IMPORTANT: This engine does NOT make legal determinations.
It assists inspectors by flagging what requires human review.
"""

import json
import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "rules", "rules.json")

# Status constants
VERIFIED = "VERIFIED_COMPLIANT"
VIOLATION = "POTENTIAL_VIOLATION"
REVIEW = "NEEDS_HUMAN_REVIEW"


def _load_rules() -> List[Dict[str, Any]]:
    try:
        with open(_RULES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("rules", [])
    except Exception as exc:
        logger.error("Could not load rules.json: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Validation methods (one per rule validation_method value)
# ---------------------------------------------------------------------------

def _field_status(field: Dict[str, Any], field_name: str, ocr_success: bool) -> str:
    """
    Determine status for a single extracted field.
    """
    value = field.get("value")
    conf = field.get("confidence", "LOW")

    if not ocr_success:
        return REVIEW  # OCR itself failed — can't say anything

    if value is None:
        # Field not detected — could be OCR miss or actual absence
        return REVIEW  # NEVER automatically say VIOLATION for missing field

    if conf == "LOW":
        return REVIEW   # Detected but low confidence → needs human eye

    if conf == "MEDIUM":
        return VERIFIED  # Medium confidence detected → likely compliant

    return VERIFIED  # HIGH confidence


def _mrp_format_check(field: Dict[str, Any], ocr_success: bool) -> str:
    """Check if MRP value looks like a valid amount."""
    value = field.get("value")
    conf = field.get("confidence", "LOW")
    if value is None:
        return REVIEW
    if not ocr_success:
        return REVIEW
    # Check if it has a numeric component
    import re
    if re.search(r'[0-9]+', str(value)):
        return VERIFIED if conf != "LOW" else REVIEW
    return REVIEW


def _unit_sale_price_check(field: Dict[str, Any], ocr_success: bool) -> str:
    """Unit sale price is optional — if detected verify, if not it's still ok (LOW severity)."""
    value = field.get("value")
    if value is None:
        return REVIEW  # Not detected — needs check but LOW severity
    return VERIFIED


_VALIDATION_DISPATCH = {
    "mrp_present": lambda ex, ocr: _field_status(ex.get("mrp", {}), "mrp", ocr),
    "mrp_format_check": lambda ex, ocr: _mrp_format_check(ex.get("mrp", {}), ocr),
    "net_quantity_present": lambda ex, ocr: _field_status(ex.get("net_quantity", {}), "net_quantity", ocr),
    "manufacturer_present": lambda ex, ocr: _field_status(ex.get("manufacturer", {}), "manufacturer", ocr),
    "manufacturing_date_present": lambda ex, ocr: _field_status(ex.get("manufacturing_date", {}), "manufacturing_date", ocr),
    "consumer_care_present": lambda ex, ocr: _field_status(ex.get("consumer_care", {}), "consumer_care", ocr),
    "country_of_origin_present": lambda ex, ocr: _field_status(ex.get("country_of_origin", {}), "country_of_origin", ocr),
    "best_before_present": lambda ex, ocr: _field_status(ex.get("best_before", {}), "best_before", ocr),
    "unit_sale_price_check": lambda ex, ocr: _unit_sale_price_check(ex.get("unit_sale_price", {}), ocr),
    "product_name_present": lambda ex, ocr: _field_status(ex.get("product_name", {}), "product_name", ocr),
}


# ---------------------------------------------------------------------------
# Main compliance runner
# ---------------------------------------------------------------------------

def run_compliance(
    extraction: Dict[str, Any],
    ocr_result: Dict[str, Any],
    image_quality: str,
) -> Dict[str, Any]:
    """
    Run all applicable rules against the extracted data.

    Returns dict matching ComplianceResult schema.
    """
    rules = _load_rules()
    ocr_success = ocr_result.get("success", False)
    image_poor = image_quality == "POOR"

    violations: List[Dict[str, Any]] = []
    field_statuses: Dict[str, str] = {}

    for rule in rules:
        method = rule.get("validation_method", "")
        fn = _VALIDATION_DISPATCH.get(method)
        if fn is None:
            logger.warning("No handler for validation_method: %s", method)
            continue

        status = fn(extraction, ocr_success)

        # If image is poor, always downgrade to REVIEW
        if image_poor and status == VERIFIED:
            status = REVIEW

        field_statuses[rule["rule_id"]] = status

        if status in (VIOLATION, REVIEW):
            severity = rule.get("severity", "MEDIUM")
            # Only create violations for HIGH/MEDIUM severity or actual violations
            if status == VIOLATION or (status == REVIEW and severity in ("HIGH", "MEDIUM")):
                field_key = method.replace("_present", "").replace("_check", "").replace("_format", "")

                # Build a human-readable reason
                if status == REVIEW:
                    reason = (
                        f"'{rule['requirement']}' was not confidently detected in the image. "
                        f"This may be due to image quality, OCR limitations, or the declaration may be absent. "
                        f"Human review required."
                    )
                else:
                    reason = (
                        f"'{rule['requirement']}' appears to have issues. "
                        f"Please verify the label physically."
                    )

                if image_poor:
                    reason += " Note: Image quality is POOR which limits analysis accuracy."

                violations.append({
                    "field_name": field_key,
                    "reason": reason,
                    "severity": severity,
                    "confidence": _get_field_confidence(extraction, field_key),
                    "rule_id": rule["rule_id"],
                    "evidence": _get_evidence(extraction, field_key),
                })

    # --- Aggregate overall status ---
    overall_status = _aggregate_status(field_statuses, violations, ocr_success, image_quality)
    overall_confidence = _aggregate_confidence(extraction, ocr_success, image_quality)

    summary = _build_summary(overall_status, violations, ocr_success, image_quality)

    return {
        "overall_status": overall_status,
        "overall_confidence": overall_confidence,
        "field_statuses": field_statuses,
        "violations": violations,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _aggregate_status(
    field_statuses: Dict[str, str],
    violations: List[Dict],
    ocr_success: bool,
    image_quality: str,
) -> str:
    if not ocr_success or image_quality == "POOR":
        return REVIEW

    high_violations = [v for v in violations if v["severity"] == "HIGH" and field_statuses.get(v.get("rule_id", ""), "") == VIOLATION]
    if high_violations:
        return VIOLATION

    review_items = [s for s in field_statuses.values() if s == REVIEW]
    all_verified = all(s == VERIFIED for s in field_statuses.values())

    if all_verified:
        return VERIFIED
    if review_items:
        return REVIEW
    return REVIEW


def _aggregate_confidence(extraction: Dict, ocr_success: bool, image_quality: str) -> str:
    if not ocr_success:
        return "LOW"
    if image_quality == "POOR":
        return "LOW"

    fields = ["mrp", "net_quantity", "manufacturer", "manufacturing_date", "consumer_care"]
    confs = [extraction.get(f, {}).get("confidence", "LOW") for f in fields]
    high = confs.count("HIGH")
    medium = confs.count("MEDIUM")

    if image_quality == "GOOD":
        if high >= 3:
            return "HIGH"
        if high + medium >= 3:
            return "MEDIUM"
    else:
        if high + medium >= 4:
            return "MEDIUM"
    return "LOW"


def _get_field_confidence(extraction: Dict, field_key: str) -> str:
    """Map rule field key back to extraction field."""
    mapping = {
        "mrp": "mrp",
        "mrp_format": "mrp",
        "net_quantity": "net_quantity",
        "manufacturer": "manufacturer",
        "manufacturing_date": "manufacturing_date",
        "consumer_care": "consumer_care",
        "country_of_origin": "country_of_origin",
        "best_before": "best_before",
        "unit_sale_price": "unit_sale_price",
        "product_name": "product_name",
    }
    field = mapping.get(field_key, field_key)
    return extraction.get(field, {}).get("confidence", "LOW")


def _get_evidence(extraction: Dict, field_key: str) -> str | None:
    mapping = {
        "mrp": "mrp", "mrp_format": "mrp",
        "net_quantity": "net_quantity",
        "manufacturer": "manufacturer",
        "manufacturing_date": "manufacturing_date",
        "consumer_care": "consumer_care",
        "country_of_origin": "country_of_origin",
        "best_before": "best_before",
        "unit_sale_price": "unit_sale_price",
        "product_name": "product_name",
    }
    field = mapping.get(field_key, field_key)
    return extraction.get(field, {}).get("evidence_text")


def _build_summary(overall_status: str, violations: List, ocr_success: bool, image_quality: str) -> str:
    if not ocr_success:
        return "OCR analysis failed. Unable to perform compliance check. Please retake the image."
    if image_quality == "POOR":
        return "Image quality is too poor for reliable analysis. Please retake with better lighting and focus."

    n_high = sum(1 for v in violations if v["severity"] == "HIGH")
    n_med = sum(1 for v in violations if v["severity"] == "MEDIUM")
    n_review = sum(1 for v in violations if v.get("status") == REVIEW)

    if overall_status == VERIFIED:
        return "All required declarations were detected with sufficient confidence. Label appears compliant."
    elif overall_status == VIOLATION:
        return (
            f"Potential compliance issues detected: {n_high} HIGH severity, {n_med} MEDIUM severity items. "
            f"Physical inspection recommended."
        )
    else:
        return (
            f"{len(violations)} declaration(s) could not be confidently verified. "
            f"Human review is required before any enforcement action."
        )

"""
SMART-LM Compliance Engine
============================
Strictly follows the Legal Metrology (Packaged Commodities) Rules, 2011.
Evaluates the extracted declarations and determines overall compliance.
"""

import logging
import re
from typing import Dict, Any, List, Optional

from regulations.rule_loader import RuleDataError, load_rules

logger = logging.getLogger(__name__)

# Status constants
COMPLIANT = "COMPLIANT"
NON_COMPLIANT = "NON-COMPLIANT"
NEEDS_REVIEW = "NEEDS REVIEW"
NOT_APPLICABLE = "NOT APPLICABLE"
NOT_VERIFIABLE = "NOT VERIFIABLE"


def _load_rules(as_of=None) -> List[Dict[str, Any]]:
    """
    Load only government-source-backed rules that have passed verification.

    The regulations loader intentionally ignores DRAFT/unverified rules.
    A malformed regulatory dataset is treated as an error rather than
    silently falling back to the legacy rules.
    """
    try:
        return load_rules(as_of=as_of)
    except RuleDataError as exc:
        logger.error("Could not load verified regulation rules: %s", exc)
        return []


def _rule_is_applicable(
    rule: Dict[str, Any],
    inspection_context: Dict[str, Any],
) -> tuple[bool, bool, str]:
    """
    Safely determine whether a rule applies to this inspection.

    Returns:
        (applicable, needs_review, reason)

    IMPORTANT:
    Missing context never proves that a conditional rule applies.
    """

    applicability_type = rule.get("applicability_type", "ALWAYS")

    # Rules explicitly marked ALWAYS can be evaluated directly.
    if applicability_type == "ALWAYS":
        return True, False, ""

    if applicability_type != "CONDITIONAL":
        return False, True, (
            f"Unsupported applicability type '{applicability_type}'."
        )

    rule_id = rule.get("rule_id", "")

    # --------------------------------------------------------
    # Explicit per-rule override.
    # --------------------------------------------------------

    explicit_key = f"rule_applicable:{rule_id}"

    if inspection_context.get(explicit_key) is True:
        return True, False, ""

    if inspection_context.get(explicit_key) is False:
        return False, False, "Rule was explicitly marked not applicable."

    # --------------------------------------------------------
    # Unit sale price rule
    # --------------------------------------------------------

    if rule.get("validation_method") == "unit_sale_price_check":

        package_type = str(
            inspection_context.get("package_type", "UNKNOWN")
        ).upper()

        # The official rule material identifies combination,
        # group and multi-piece packages as relevant exceptions.
        if package_type in {
            "COMBINATION",
            "GROUP",
            "MULTI_PIECE",
        }:
            return False, False, (
                f"Unit sale price requirement is not applicable "
                f"for package type '{package_type}'."
            )

        if package_type == "SINGLE":
            return True, False, ""

        # Unknown package type means applicability cannot safely
        # be established.
        return False, True, (
            "Package type is unknown. Unit sale price applicability "
            "cannot be established safely."
        )

    # --------------------------------------------------------
    # Generic conditional-rule support for future rules.
    # --------------------------------------------------------

    applicable_rules = inspection_context.get("applicable_rules") or []
    if rule_id in applicable_rules:
        return True, False, ""

    not_applicable_rules = (
        inspection_context.get("not_applicable_rules") or []
    )
    if rule_id in not_applicable_rules:
        return False, False, "Rule was explicitly marked not applicable."

    return False, True, (
        "Applicability could not be established from the "
        "available inspection context."
    )


def _evaluate_field(
    extraction: Dict[str, Any], field_key: str, rule: Dict[str, Any],
    ocr_success: bool, image_quality: str, custom_check: callable = None
) -> Dict[str, Any]:
    field_data = extraction.get(field_key, {})
    value = field_data.get("value")
    conf = field_data.get("confidence", "LOW")
    evidence = field_data.get("evidence_text")
    hybrid_status = field_data.get("hybrid_status")
    
    if not ocr_success or image_quality == "POOR" or hybrid_status in {"CONFLICT", "NOT_VERIFIABLE"}:
        result = NOT_VERIFIABLE
    elif value is None:
        # OCR succeeded but field is missing.
        result = NEEDS_REVIEW
    else:
        if custom_check:
            result = custom_check(value, conf)
        else:
            if conf == "LOW":
                result = NEEDS_REVIEW
            else:
                result = COMPLIANT
                
    return {
        "requirement": rule.get("requirement", ""),
        "extracted_value": value,
        "expected_requirement": rule.get("evidence_required", ""),
        "rule_reference": rule.get("rule_number", ""),
        "evidence": evidence,
        "confidence": conf if value is not None else "LOW",
        "result": result,
        "evidence_status": hybrid_status,
    }


def _mrp_format_check(value: str, conf: str) -> str:
    if "inclusive of all taxes" in str(value).lower() or "incl" in str(value).lower() or "taxes" in str(value).lower():
        return COMPLIANT if conf != "LOW" else NEEDS_REVIEW
    return NON_COMPLIANT

def _mrp_present_check(value: str, conf: str) -> str:
    if re.search(r'[0-9]+', str(value)):
        return COMPLIANT if conf != "LOW" else NEEDS_REVIEW
    return NON_COMPLIANT

def run_compliance(
    extraction: Dict[str, Any],
    ocr_result: Dict[str, Any],
    image_quality: str,
    inspection_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    rules = _load_rules()
    ocr_success = ocr_result.get("success", False)
    inspection_context = inspection_context or {}

    # Never report compliance when no verified/effective regulatory rules
    # are available. An empty rule set means the legal basis for the
    # compliance decision is unavailable.
    if not rules:
        return {
            "overall_status": NEEDS_REVIEW,
            "overall_confidence": "LOW",
            "evaluations": [],
            "summary": (
                "No verified and currently effective Legal Metrology rules "
                "are available for this analysis. Human review is required."
            ),
        }

    evaluations = []
    
    mapping = {
        "mrp_present": ("mrp", _mrp_present_check),
        "mrp_format_check": ("mrp", _mrp_format_check),
        "net_quantity_present": ("net_quantity", None),
        "manufacturer_present": ("manufacturer", None),
        "manufacturing_date_present": ("manufacturing_date", None),
        "consumer_care_present": ("consumer_care", None),
        "country_of_origin_present": ("country_of_origin", None),
        "best_before_present": ("best_before", None),
        "unit_sale_price_check": ("unit_sale_price", None),
        "product_name_present": ("product_name", None),
    }

    for rule in rules:
        method = rule.get("validation_method", "")
        if method not in mapping:
            continue

        applicable, applicability_review, applicability_reason = (
            _rule_is_applicable(
                rule,
                inspection_context,
            )
        )

        # A conditional rule whose applicability cannot be established
        # is a REVIEW item, not a missing declaration and not a violation.
        if not applicable:
            if applicability_review:
                evaluations.append({
                    "requirement": rule.get("requirement", ""),
                    "extracted_value": None,
                    "expected_requirement": rule.get(
                        "evidence_required", ""
                    ),
                    "rule_reference": rule.get("rule_number", ""),
                    "evidence": None,
                    "confidence": "LOW",
                    "result": NEEDS_REVIEW,
                    "applicability_status": "NEEDS_REVIEW",
                    "applicability_reason": applicability_reason,
                })
            continue

        field_key, custom_check = mapping[method]

        evaluation = _evaluate_field(
            extraction,
            field_key,
            rule,
            ocr_success,
            image_quality,
            custom_check,
        )

        evaluation["applicability_status"] = "APPLICABLE"
        evaluation["applicability_reason"] = ""

        evaluations.append(evaluation)

    
    overall_status = _aggregate_status(evaluations, ocr_success, image_quality)
    overall_confidence = _aggregate_confidence(extraction, ocr_success, image_quality)
    summary = _build_summary(overall_status, evaluations, ocr_success, image_quality)

    return {
        "overall_status": overall_status,
        "overall_confidence": overall_confidence,
        "evaluations": evaluations,
        "summary": summary,
    }


def _aggregate_status(
    evaluations: List[Dict],
    ocr_success: bool,
    image_quality: str,
) -> str:
    if not ocr_success or image_quality == "POOR":
        return NEEDS_REVIEW

    results = [e["result"] for e in evaluations]
    
    if NON_COMPLIANT in results:
        return NON_COMPLIANT
        
    if NEEDS_REVIEW in results or NOT_VERIFIABLE in results:
        return NEEDS_REVIEW
        
    return COMPLIANT


def _aggregate_confidence(extraction: Dict, ocr_success: bool, image_quality: str) -> str:
    if not ocr_success or image_quality == "POOR":
        return "LOW"

    confs = [extraction.get(k, {}).get("confidence", "LOW") for k in extraction.keys() if isinstance(extraction.get(k), dict)]
    high = confs.count("HIGH")
    medium = confs.count("MEDIUM")

    if high >= len(confs) / 2:
        return "HIGH"
    if high + medium >= len(confs) / 2:
        return "MEDIUM"
    return "LOW"


def _build_summary(overall_status: str, evaluations: List[Dict], ocr_success: bool, image_quality: str) -> str:
    if not ocr_success:
        return "OCR analysis failed. Unable to verify compliance."
    if image_quality == "POOR":
        return "Image quality is too poor for reliable analysis."

    if overall_status == COMPLIANT:
        return "Package complies with the applicable Legal Metrology (Packaged Commodities) Rules, 2011."
    elif overall_status == NON_COMPLIANT:
        return "Package DOES NOT comply with the Legal Metrology (Packaged Commodities) Rules, 2011."
    else:
        return "Human review required to verify compliance with Legal Metrology Rules."

"""Non-authoritative comparison of OCR extraction and VLM extraction."""

from __future__ import annotations

import re
from typing import Any, Dict

from services.text_normalization import normalize_label_text


FIELD_MAP = {
    "product_name": "product_name",
    "mrp": "mrp",
    "net_quantity": "net_quantity",
    "manufacturer": "manufacturer_packer_importer",
    "manufacturing_date": "date_of_manufacture_or_packing",
    "consumer_care": "consumer_care",
    "country_of_origin": "country_of_origin",
    "best_before": "best_before_or_use_by",
    "unit_sale_price": "unit_sale_price",
    "dimensions": "dimensions",
}


def _normalize(value: Any) -> str:
    text = normalize_label_text(str(value or "")).lower()
    text = re.sub(r"₹", "", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def _confidence(ocr_field: Dict[str, Any], vlm_field: Dict[str, Any], status: str) -> str:
    if status == "AGREED":
        return "HIGH"
    if status == "OCR_ONLY":
        return ocr_field.get("confidence", "LOW")
    if status == "VLM_ONLY":
        return "LOW"
    return "LOW"


def build_hybrid_extraction(ocr_extraction: Dict[str, Any], vlm_result: Dict[str, Any]) -> Dict[str, Any]:
    vlm_fields = vlm_result.get("fields", {}) if isinstance(vlm_result, dict) else {}
    quality_not_verifiable = isinstance(vlm_result, dict) and vlm_result.get("quality_status") == "NOT_VERIFIABLE"
    result = {}
    for ocr_key, vlm_key in FIELD_MAP.items():
        ocr_field = ocr_extraction.get(ocr_key, {}) or {}
        vlm_field = vlm_fields.get(vlm_key, {}) or {}
        ocr_value = ocr_field.get("value")
        vlm_value = vlm_field.get("value")
        ocr_evidence = ocr_field.get("evidence_text")
        vlm_evidence = vlm_field.get("evidence_text")
        if quality_not_verifiable and not vlm_value:
            status = "NOT_VERIFIABLE"
            final_value = None
        elif ocr_value and vlm_value and _normalize(ocr_value) == _normalize(vlm_value):
            status = "AGREED"
            final_value = ocr_value
        elif ocr_value and vlm_value:
            status = "CONFLICT"
            final_value = None
        elif ocr_value:
            status = "OCR_ONLY"
            final_value = ocr_value
        elif vlm_value:
            status = "VLM_ONLY"
            final_value = vlm_value
        else:
            status = "NOT_DETECTED"
            final_value = None
        confidence = _confidence(ocr_field, vlm_field, status)
        result[ocr_key] = {
            "ocr_value": ocr_value,
            "vlm_value": vlm_value,
            "final_value": final_value,
            "status": status,
            "needs_review": status in {"CONFLICT", "NOT_DETECTED", "NOT_VERIFIABLE"},
            "confidence": confidence,
            "ocr_evidence": ocr_evidence,
            "vlm_evidence": vlm_evidence,
        }
    return result


def build_compliance_extraction(
    hybrid_extraction: Dict[str, Any],
    image_quality: str,
    ocr_success: bool,
) -> Dict[str, Any]:
    """Convert reconciled evidence into the deterministic engine's input."""
    compliance_extraction = {}
    for field_key, field in hybrid_extraction.items():
        status = field.get("status", "NOT_DETECTED")
        if image_quality == "POOR" or not ocr_success or status == "NOT_VERIFIABLE":
            value = None
            confidence = "LOW"
            evidence = field.get("ocr_evidence") or field.get("vlm_evidence")
        elif status == "CONFLICT":
            value = None
            confidence = "LOW"
            evidence = "OCR: {0}; VLM: {1}".format(
                field.get("ocr_evidence") or field.get("ocr_value") or "unavailable",
                field.get("vlm_evidence") or field.get("vlm_value") or "unavailable",
            )
        elif status in {"AGREED", "OCR_ONLY", "VLM_ONLY"}:
            value = field.get("final_value")
            confidence = field.get("confidence", "LOW")
            evidence = field.get("ocr_evidence") or field.get("vlm_evidence")
        else:
            value = None
            confidence = "LOW"
            evidence = field.get("ocr_evidence") or field.get("vlm_evidence")
        compliance_extraction[field_key] = {
            "value": value,
            "confidence": confidence,
            "evidence_text": evidence,
            "hybrid_status": status,
        }
    return compliance_extraction
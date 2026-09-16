"""Non-authoritative comparison of OCR extraction and VLM extraction."""

from __future__ import annotations

import re
from typing import Any, Dict

from services.text_normalization import normalize_currency_text


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
    text = normalize_currency_text(str(value or "")).lower()
    text = re.sub(r"₹", "", text)
    return re.sub(r"[^a-z0-9]+", "", text)


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
        result[ocr_key] = {
            "ocr_value": ocr_value,
            "vlm_value": vlm_value,
            "final_value": final_value,
            "status": status,
            "needs_review": status in {"CONFLICT", "NOT_DETECTED", "NOT_VERIFIABLE"},
            "ocr_evidence": ocr_evidence,
            "vlm_evidence": vlm_evidence,
        }
    return result
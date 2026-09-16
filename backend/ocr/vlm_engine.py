"""Optional PaddleOCR-VL document-understanding adapter."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

_PADDLEOCR_VL = None
_IMPORT_ERROR: Optional[str] = None
try:
    from paddleocr import PaddleOCRVL as _PADDLEOCR_VL
except Exception as exc:
    _IMPORT_ERROR = f"{type(exc).__name__}: {exc}"


FIELD_NAMES = (
    "product_name",
    "mrp",
    "net_quantity",
    "manufacturer_packer_importer",
    "country_of_origin",
    "date_of_manufacture_or_packing",
    "best_before_or_use_by",
    "consumer_care",
    "unit_sale_price",
    "dimensions",
    "other_visible_mandatory_declarations",
)


def _empty_field(source_image: str) -> Dict[str, Any]:
    return {
        "value": None,
        "confidence": None,
        "evidence_text": None,
        "source_image": source_image,
        "bounding_box": None,
        "status": "NOT_DETECTED",
    }


def _field(value: Optional[str], block: Optional[Dict[str, Any]], source_image: str) -> Dict[str, Any]:
    if not value:
        return _empty_field(source_image)
    return {
        "value": value.strip(),
        "confidence": None,
        "evidence_text": (block or {}).get("block_content"),
        "source_image": source_image,
        "bounding_box": (block or {}).get("block_bbox"),
        "status": "DETECTED",
    }


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" \t\r\n:;,-")


def _find_block(blocks: Iterable[Dict[str, Any]], pattern: str) -> Optional[Dict[str, Any]]:
    compiled = re.compile(pattern, re.IGNORECASE)
    return next((block for block in blocks if compiled.search(str(block.get("block_content", "")))), None)


def _match_value(block: Optional[Dict[str, Any]], pattern: str) -> Optional[str]:
    if not block:
        return None
    match = re.search(pattern, str(block.get("block_content", "")), re.IGNORECASE | re.DOTALL)
    return _clean(match.group(1)) if match else None


def _parse_blocks(blocks: List[Dict[str, Any]], source_image: str) -> Dict[str, Any]:
    fields = {name: _empty_field(source_image) for name in FIELD_NAMES}
    mrp_block = _find_block(blocks, r"\b(?:MRP|MAXIMUM\s+RETAIL\s+PRICE)\b")
    quantity_block = _find_block(blocks, r"\bNET\s*(?:QTY|QUANTITY|WEIGHT|WT|VOLUME|VOL)\b")
    manufacturer_block = _find_block(blocks, r"\b(?:MANUFACTURED|PACKED|MFG\.?\s*(?:BY|&|&\s*MKTD)|MANUFACTURER|PACKER|IMPORTED)\b")
    date_block = _find_block(blocks, r"\b(?:MFD|MFG\.?\s*DATE|MANUFACTURED|PACKED\s+ON)\b")
    best_before_block = _find_block(blocks, r"\b(?:BEST\s+BEFORE|USE\s+BY|EXP(?:IRY|\.?\s*DATE))\b")
    care_block = _find_block(blocks, r"\b(?:CONSUMER|CUSTOMER|CARE|HELPLINE|FEEDBACK|COMPLAINT)\b")
    unit_price_block = _find_block(blocks, r"\bUNIT\s+SALE\s+PRICE\b|\bPRICE\s+PER\b")
    country_block = _find_block(blocks, r"\b(?:COUNTRY\s+OF\s+ORIGIN|MADE\s+IN|PRODUCT\s+OF)\b")
    product_block = _find_block(blocks, r"\b(?:PROPRIETARY\s+FOOD|PRODUCT\s+NAME|PRODUCT)\b")
    dimensions_block = _find_block(blocks, r"\b(?:DIMENSIONS?|SIZE)\b")

    fields["mrp"] = _field(
        _match_value(mrp_block, r"(?:MRP|MAXIMUM\s+RETAIL\s+PRICE).*?(?:₹|RS\.?|INR)?\s*([0-9]+(?:\.[0-9]{1,2})?)"),
        mrp_block,
        source_image,
    )
    if fields["mrp"]["value"]:
        fields["mrp"]["value"] = f"₹{fields['mrp']['value']}"

    fields["net_quantity"] = _field(
        _match_value(quantity_block, r"(?:NET\s*(?:QTY|QUANTITY|WEIGHT|WT|VOLUME|VOL)).*?([0-9]+(?:\.[0-9]+)?\s*(?:mg|g|gm|kg|ml|l|litre|liter|pieces?|pcs|units?))"),
        quantity_block,
        source_image,
    )
    fields["manufacturer_packer_importer"] = _field(
        _match_value(manufacturer_block, r"(?:MANUFACTURED\s*(?:&\s*PACKED)?\s*BY|PACKED\s*BY|MFG\.?\s*(?:BY|&\s*MKTD\.?\s*BY|&)|MANUFACTURER|PACKER|IMPORTED\s*BY)\s*:?\s*(.*)"),
        manufacturer_block,
        source_image,
    )
    fields["country_of_origin"] = _field(
        _match_value(country_block, r"(?:COUNTRY\s+OF\s+ORIGIN|MADE\s+IN|PRODUCT\s+OF)\s*:?\s*([A-Za-z][A-Za-z -]{1,80})"),
        country_block,
        source_image,
    )
    fields["date_of_manufacture_or_packing"] = _field(
        _match_value(date_block, r"(?:MFD|MFG\.?\s*DATE|MANUFACTURED|PACKED\s+ON)\s*:?\s*((?:\d{1,2}[/-]){1,2}\d{2,4}|[A-Za-z]{3,9}\s+\d{4})"),
        date_block,
        source_image,
    )
    fields["best_before_or_use_by"] = _field(
        _match_value(best_before_block, r"(?:BEST\s+BEFORE|USE\s+BY|EXP(?:IRY|\.?\s*DATE))\s*:?\s*(.*)"),
        best_before_block,
        source_image,
    )
    fields["consumer_care"] = _field(care_block.get("block_content") if care_block else None, care_block, source_image)
    fields["unit_sale_price"] = _field(
        _match_value(unit_price_block, r"(?:UNIT\s+SALE\s+PRICE|PRICE\s+PER).*?((?:₹|RS\.?|INR)?\s*[0-9]+(?:\.[0-9]{1,2})?\s*(?:PER\s+)?[A-Za-z]+)"),
        unit_price_block,
        source_image,
    )
    fields["dimensions"] = _field(
        _match_value(dimensions_block, r"(?:DIMENSIONS?|SIZE)\s*:?\s*(.*)"),
        dimensions_block,
        source_image,
    )
    fields["product_name"] = _field(
        _match_value(product_block, r"(?:PROPRIETARY\s+FOOD|PRODUCT\s+NAME|PRODUCT)\s*:?\s*([^\n]+)"),
        product_block,
        source_image,
    )

    known_blocks = {id(block) for block in (mrp_block, quantity_block, manufacturer_block, date_block, best_before_block, care_block, unit_price_block, country_block, product_block, dimensions_block) if block}
    other = [str(block.get("block_content", "")).strip() for block in blocks if id(block) not in known_blocks and block.get("block_content")]
    fields["other_visible_mandatory_declarations"] = _field("\n".join(other) if other else None, None, source_image)
    if other:
        fields["other_visible_mandatory_declarations"]["evidence_text"] = "\n".join(other)

    return fields


class PaddleOCRVLEngine:
    """Lazy, optional PaddleOCR-VL runner that never decides compliance."""

    def __init__(self, pipeline_version: Optional[str] = None):
        self.pipeline_version = pipeline_version or os.getenv("SMARTLM_VLM_PIPELINE_VERSION", "v1.5")
        self._pipeline = None

    @staticmethod
    def availability() -> Dict[str, Any]:
        return {
            "available": _PADDLEOCR_VL is not None,
            "engine": "paddleocr-vl" if _PADDLEOCR_VL is not None else "none",
            "pipeline_version": os.getenv("SMARTLM_VLM_PIPELINE_VERSION", "v1.5"),
            "error": _IMPORT_ERROR,
        }

    def _get_pipeline(self):
        if self._pipeline is None:
            if _PADDLEOCR_VL is None:
                raise RuntimeError(_IMPORT_ERROR or "PaddleOCR-VL is not installed")
            self._pipeline = _PADDLEOCR_VL(
                pipeline_version=self.pipeline_version,
                use_doc_orientation_classify=True,
                use_doc_unwarping=True,
                use_layout_detection=True,
                use_chart_recognition=False,
                use_seal_recognition=False,
                use_ocr_for_image_block=True,
            )
        return self._pipeline

    def run(self, image_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        path = Path(image_path)
        base = {"status": "failed", "engine": "paddleocr-vl", "pipeline_version": self.pipeline_version, "fields": {name: _empty_field(str(path)) for name in FIELD_NAMES}, "source_image": str(path), "error": None}
        if not path.is_file():
            base["error"] = f"Image not found: {path}"
            return base
        try:
            if _PADDLEOCR_VL is None:
                return self._run_external_worker(path, output_dir, base)
            result = next(iter(self._get_pipeline().predict(str(path), use_doc_orientation_classify=True, use_doc_unwarping=True)))
            payload = result.json if isinstance(result.json, dict) else json.loads(result.json)
            data = payload.get("res", payload)
            blocks = data.get("parsing_res_list", [])
            base.update({
                "status": "success",
                "fields": _parse_blocks(blocks, str(path)),
                "markdown": (result.markdown or {}).get("markdown_texts", "") if isinstance(result.markdown, dict) else "",
                "blocks": blocks,
                "error": None,
            })
            if output_dir:
                output = Path(output_dir)
                output.mkdir(parents=True, exist_ok=True)
                result.save_to_json(str(output))
                result.save_to_img(str(output))
                result.save_to_markdown(str(output))
            return base
        except Exception as exc:
            logger.exception("PaddleOCR-VL failed for %s", path)
            base["error"] = f"{type(exc).__name__}: {exc}"
            return base

    def _run_external_worker(self, path: Path, output_dir: Optional[str], base: Dict[str, Any]) -> Dict[str, Any]:
        """Run PaddleOCR-VL from paddle_env when the API process uses another venv."""
        configured = os.getenv("SMARTLM_PADDLE_PYTHON")
        default = Path(__file__).resolve().parents[3] / "paddle_env" / "Scripts" / "python.exe"
        python_executable = Path(configured) if configured else default
        worker = Path(__file__).with_name("vlm_worker.py")
        if not python_executable.is_file():
            base["error"] = f"PaddleOCR-VL unavailable and paddle_env Python was not found: {python_executable}"
            return base
        command = [str(python_executable), str(worker), str(path), self.pipeline_version]
        if output_dir:
            command.append(str(output_dir))
        completed = subprocess.run(command, capture_output=True, text=True, timeout=900, check=False)
        if completed.returncode != 0:
            base["error"] = completed.stderr.strip() or completed.stdout.strip() or "PaddleOCR-VL worker failed."
            return base
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            base["error"] = f"Invalid PaddleOCR-VL worker response: {exc}"
            return base
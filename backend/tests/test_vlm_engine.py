from pathlib import Path

from ocr.vlm_engine import PaddleOCRVLEngine, _parse_blocks
from services.image_processing import quality_gate
from services.text_normalization import currency_amount, normalize_currency_text


def test_vlm_import_and_default_version():
    engine = PaddleOCRVLEngine()
    assert engine.pipeline_version == "v1.5"
    assert "available" in engine.availability()


def test_vlm_parser_extracts_fields_without_hallucinating():
    fields = _parse_blocks([
        {"block_content": "MRP Rs. 20/- (INCL. OF ALL TAXES)", "block_bbox": [1, 2, 3, 4]},
        {"block_content": "NET QTY: 52.9g", "block_bbox": [5, 6, 7, 8]},
        {"block_content": "Mfg. & Mktd. by: Example Foods Pvt. Ltd.", "block_bbox": [9, 10, 11, 12]},
    ], "package.jpg")
    assert fields["mrp"]["value"] == "₹20"
    assert fields["net_quantity"]["value"] == "52.9g"
    assert fields["manufacturer_packer_importer"]["value"]
    assert fields["best_before_or_use_by"]["value"] is None
    assert fields["mrp"]["bounding_box"] == [1, 2, 3, 4]


def test_vlm_missing_and_malformed_images_are_safe(tmp_path: Path):
    engine = PaddleOCRVLEngine()
    missing = engine.run(str(tmp_path / "missing.jpg"))
    assert missing["status"] == "failed"
    assert missing["fields"]["mrp"]["value"] is None

    malformed = tmp_path / "malformed.jpg"
    malformed.write_text("not an image", encoding="ascii")
    result = engine.run(str(malformed))
    assert result["status"] in {"failed", "success"}


def test_vlm_unavailable_returns_clear_error(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SMARTLM_PADDLE_PYTHON", str(tmp_path / "missing-python.exe"))
    image = tmp_path / "package.jpg"
    image.write_bytes(b"not an image")
    result = PaddleOCRVLEngine().run(str(image))
    assert result["status"] == "failed"
    assert result["error"]


def test_currency_normalization_supports_common_mrp_forms():
    for text in ("₹20", "Rs 20", "Rs. 20", "INR 20", "Rupees 20", "MRP ₹20", "MRP Rs. 20"):
        assert currency_amount(text) == "₹20"
    assert currency_amount("₹20.50") == "₹20.50"
    assert normalize_currency_text("Café मसाला ₹20") == "Café मसाला ₹20"


def test_currency_amount_requires_currency_or_mrp_context():
    assert currency_amount("Batch 123, packed 2025, MRP Rs. 20") == "₹20"
    assert currency_amount("Batch 123, packed 2025, price unavailable") is None


def test_quality_gate_marks_poor_images_not_verifiable():
    assert quality_gate({"quality": "GOOD", "width": 1000, "height": 800})["status"] == "READABLE"
    assert quality_gate({"quality": "POOR", "width": 1000, "height": 800})["status"] == "NOT_VERIFIABLE"
    assert quality_gate({"quality": "GOOD", "width": 100, "height": 80})["status"] == "NOT_VERIFIABLE"
    assert quality_gate({"quality": "GOOD", "width": 1000, "height": 800, "brightness": 10})["status"] == "NOT_VERIFIABLE"
    assert quality_gate({"quality": "GOOD", "width": 1000, "height": 800, "brightness": 240})["status"] == "NOT_VERIFIABLE"


def test_parser_preserves_missing_fields_and_dimensions():
    fields = _parse_blocks([
        {"block_label": "doc_title", "block_content": "Aloo Bhujiya", "block_bbox": [1, 2, 3, 4]},
        {"block_label": "text", "block_content": "Size: 10 x 20 cm", "block_bbox": [5, 6, 7, 8]},
    ], "package.jpg")
    assert fields["product_name"]["value"] == "Aloo Bhujiya"
    assert fields["dimensions"]["value"] == "10 x 20 cm"
    assert fields["mrp"]["value"] is None
    assert fields["mrp"]["status"] == "NOT_DETECTED"
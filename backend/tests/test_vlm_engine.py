from pathlib import Path

from ocr.vlm_engine import PaddleOCRVLEngine, _parse_blocks


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
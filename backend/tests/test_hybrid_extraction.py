from services.hybrid_extraction import build_hybrid_extraction


def test_hybrid_agreement_preserves_ocr_value():
    result = build_hybrid_extraction(
        {"mrp": {"value": "₹20"}},
        {"fields": {"mrp": {"value": "Rs. 20"}}},
    )
    assert result["mrp"]["status"] == "AGREED"
    assert result["mrp"]["final_value"] == "₹20"
    assert result["mrp"]["ocr_evidence"] is None
    assert result["mrp"]["vlm_evidence"] is None


def test_hybrid_conflict_never_invents_final_value():
    result = build_hybrid_extraction(
        {"mrp": {"value": "₹20"}},
        {"fields": {"mrp": {"value": "₹30"}}},
    )
    assert result["mrp"]["status"] == "CONFLICT"
    assert result["mrp"]["final_value"] is None
    assert result["mrp"]["needs_review"] is True


def test_hybrid_vlm_failure_falls_back_to_ocr():
    result = build_hybrid_extraction(
        {"net_quantity": {"value": "52 g"}},
        {"status": "failed", "fields": {}},
    )
    assert result["net_quantity"]["status"] == "OCR_ONLY"
    assert result["net_quantity"]["final_value"] == "52 g"


def test_hybrid_supports_vlm_only_dimensions_and_not_detected():
    result = build_hybrid_extraction(
        {},
        {"fields": {"dimensions": {"value": "10 x 20 cm", "evidence_text": "Size: 10 x 20 cm"}}},
    )
    assert result["dimensions"]["status"] == "VLM_ONLY"
    assert result["dimensions"]["vlm_value"] == "10 x 20 cm"
    assert result["dimensions"]["vlm_evidence"] == "Size: 10 x 20 cm"
    assert result["mrp"]["status"] == "NOT_DETECTED"
    assert result["mrp"]["needs_review"] is True


def test_hybrid_quality_not_verifiable_overrides_absent_vlm_field():
    result = build_hybrid_extraction(
        {"mrp": {"value": "₹20", "evidence_text": "MRP ₹20"}},
        {
            "quality_status": "NOT_VERIFIABLE",
            "fields": {"mrp": {"value": None, "evidence_text": None}},
        },
    )
    assert result["mrp"]["status"] == "NOT_VERIFIABLE"
    assert result["mrp"]["final_value"] is None
    assert result["mrp"]["needs_review"] is True
    assert result["mrp"]["ocr_evidence"] == "MRP ₹20"


def test_hybrid_not_detected_remains_distinct_when_quality_is_readable():
    result = build_hybrid_extraction(
        {"mrp": {"value": None}},
        {"quality_status": "READABLE", "fields": {"mrp": {"value": None}}},
    )
    assert result["mrp"]["status"] == "NOT_DETECTED"
    assert result["mrp"]["needs_review"] is True
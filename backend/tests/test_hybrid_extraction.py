from services.hybrid_extraction import build_hybrid_extraction


def test_hybrid_agreement_preserves_ocr_value():
    result = build_hybrid_extraction(
        {"mrp": {"value": "₹20"}},
        {"fields": {"mrp": {"value": "Rs. 20"}}},
    )
    assert result["mrp"] == {
        "ocr_value": "₹20",
        "vlm_value": "Rs. 20",
        "final_value": "₹20",
        "status": "AGREED",
        "needs_review": False,
    }


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
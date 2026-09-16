from services import compliance


def test_empty_verified_rule_set_never_reports_compliant(monkeypatch):
    monkeypatch.setattr(compliance, "_load_rules", lambda as_of=None: [])

    result = compliance.run_compliance(
        extraction={
            "mrp": {
                "value": "?100",
                "confidence": "HIGH",
                "evidence_text": "MRP ?100",
            }
        },
        ocr_result={"success": True},
        image_quality="GOOD",
    )

    assert result["overall_status"] == compliance.NEEDS_REVIEW
    assert result["overall_confidence"] == "LOW"
    assert result["evaluations"] == []
    assert "No verified" in result["summary"]

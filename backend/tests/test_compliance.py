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


def test_conditional_unit_sale_price_unknown_package_requires_review(monkeypatch):
    conditional_rule = {
        "rule_id": "pcr.rule6.unit_sale_price.v1",
        "rule_number": "Rule 6(11)",
        "requirement": "Unit sale price requirement.",
        "scope": "Pre-packaged commodities meant for retail sale",
        "applicability": "Applicable subject to documented exceptions.",
        "applicability_type": "CONDITIONAL",
        "validation_method": "unit_sale_price_check",
        "severity": "APPLICATION_DEFINED",
        "evidence_required": "Visible unit sale price declaration.",
        "effective_from": "2023-02-01",
        "effective_until": None,
        "source_id": "example-source",
        "source_document": "Example official source",
        "source_page": 1,
        "source_section": "Rule 6(11)",
        "verification_status": "VERIFIED",
    }

    monkeypatch.setattr(
        compliance,
        "_load_rules",
        lambda as_of=None: [conditional_rule],
    )

    result = compliance.run_compliance(
        extraction={
            "unit_sale_price": {
                "value": "?2.00 per 10 g",
                "confidence": "HIGH",
                "evidence_text": "?2.00 per 10 g",
            }
        },
        ocr_result={"success": True},
        image_quality="GOOD",
    )

    assert result["overall_status"] == compliance.NEEDS_REVIEW
    assert len(result["evaluations"]) == 1
    assert result["evaluations"][0]["applicability_status"] == "NEEDS_REVIEW"


def test_unit_sale_price_single_package_is_applicable(monkeypatch):
    conditional_rule = {
        "rule_id": "pcr.rule6.unit_sale_price.v1",
        "rule_number": "Rule 6(11)",
        "requirement": "Unit sale price requirement.",
        "scope": "Pre-packaged commodities meant for retail sale",
        "applicability": "Applicable subject to documented exceptions.",
        "applicability_type": "CONDITIONAL",
        "validation_method": "unit_sale_price_check",
        "severity": "APPLICATION_DEFINED",
        "evidence_required": "Visible unit sale price declaration.",
        "effective_from": "2023-02-01",
        "effective_until": None,
        "source_id": "example-source",
        "source_document": "Example official source",
        "source_page": 1,
        "source_section": "Rule 6(11)",
        "verification_status": "VERIFIED",
    }

    monkeypatch.setattr(
        compliance,
        "_load_rules",
        lambda as_of=None: [conditional_rule],
    )

    result = compliance.run_compliance(
        extraction={
            "unit_sale_price": {
                "value": "?2.00 per 10 g",
                "confidence": "HIGH",
                "evidence_text": "?2.00 per 10 g",
            }
        },
        ocr_result={"success": True},
        image_quality="GOOD",
        inspection_context={
            "package_type": "SINGLE",
        },
    )

    assert result["overall_status"] == compliance.COMPLIANT
    assert len(result["evaluations"]) == 1
    assert result["evaluations"][0]["applicability_status"] == "APPLICABLE"


def test_unit_sale_price_multi_piece_package_is_not_applicable(monkeypatch):
    conditional_rule = {
        "rule_id": "pcr.rule6.unit_sale_price.v1",
        "rule_number": "Rule 6(11)",
        "requirement": "Unit sale price requirement.",
        "scope": "Pre-packaged commodities meant for retail sale",
        "applicability": "Applicable subject to documented exceptions.",
        "applicability_type": "CONDITIONAL",
        "validation_method": "unit_sale_price_check",
        "severity": "APPLICATION_DEFINED",
        "evidence_required": "Visible unit sale price declaration.",
        "effective_from": "2023-02-01",
        "effective_until": None,
        "source_id": "example-source",
        "source_document": "Example official source",
        "source_page": 1,
        "source_section": "Rule 6(11)",
        "verification_status": "VERIFIED",
    }

    monkeypatch.setattr(
        compliance,
        "_load_rules",
        lambda as_of=None: [conditional_rule],
    )

    result = compliance.run_compliance(
        extraction={},
        ocr_result={"success": True},
        image_quality="GOOD",
        inspection_context={
            "package_type": "MULTI_PIECE",
        },
    )

    assert result["overall_status"] == compliance.COMPLIANT
    assert result["evaluations"] == []

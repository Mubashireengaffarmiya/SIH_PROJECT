import json
from pathlib import Path

import pytest

from regulations.rule_loader import RuleDataError, load_rules, validate_rule


REQUIRED_RULE = {
    "rule_id": "example.rule.v1",
    "rule_number": "Section 1",
    "requirement": "Verified requirement text.",
    "scope": "Example packaged commodity",
    "applicability": "When the documented condition applies",
    "validation_method": "example_check",
    "severity": "MEDIUM",
    "evidence_required": "Exact evidence from the source",
    "effective_from": "2025-01-01",
    "effective_until": None,
    "source_id": "example-source",
    "source_document": "Example official document",
    "source_page": 10,
    "source_section": "Section 1",
    "verification_status": "VERIFIED",
}


def write_rules(path: Path, rules):
    path.write_text(json.dumps({"schema_version": "1.0.0", "rules": rules}), encoding="utf-8")


def test_empty_rule_set_loads():
    assert load_rules() == []


def test_malformed_rule_data_is_rejected_safely(tmp_path):
    path = tmp_path / "malformed.json"
    path.write_text('{"rules": {"not": "an array"}}', encoding="utf-8")
    with pytest.raises(RuleDataError):
        load_rules(path)


def test_required_metadata_validation_works():
    malformed = dict(REQUIRED_RULE)
    del malformed["source_section"]
    with pytest.raises(RuleDataError, match="source_section"):
        validate_rule(malformed)


def test_effective_date_filtering(tmp_path):
    path = tmp_path / "rules.json"
    before = dict(REQUIRED_RULE, rule_id="before", effective_from="2020-01-01", effective_until="2024-12-31")
    current = dict(REQUIRED_RULE, rule_id="current", effective_from="2025-01-01", effective_until="2026-12-31")
    future = dict(REQUIRED_RULE, rule_id="future", effective_from="2027-01-01")
    unverified = dict(REQUIRED_RULE, rule_id="draft", verification_status="DRAFT")
    write_rules(path, [before, current, future, unverified])

    result = load_rules(path, as_of="2026-09-16")
    assert [rule["rule_id"] for rule in result] == ["current"]


def test_source_references_are_preserved(tmp_path):
    path = tmp_path / "rules.json"
    write_rules(path, [REQUIRED_RULE])
    loaded = load_rules(path, as_of="2026-09-16")
    assert loaded[0]["source_id"] == "example-source"
    assert loaded[0]["source_document"] == "Example official document"
    assert loaded[0]["source_page"] == 10
    assert loaded[0]["source_section"] == "Section 1"


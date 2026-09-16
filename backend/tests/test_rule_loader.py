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


def write_sources(path: Path):
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "sources": [
                    {
                        "source_id": "example-source",
                        "title": "Example official source",
                        "publisher": "Example authority",
                        "jurisdiction": "Example",
                        "document_type": "Official document",
                        "official_url": "https://example.com",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_empty_rule_set_loads(tmp_path):
    path = tmp_path / "empty_rules.json"
    write_rules(path, [])

    sources = tmp_path / "sources.json"
    write_sources(sources)

    assert load_rules(path, as_of="2026-09-16", source_path=sources) == []


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

    sources = tmp_path / "sources.json"
    write_sources(sources)

    result = load_rules(path, as_of="2026-09-16", source_path=sources)
    assert [rule["rule_id"] for rule in result] == ["current"]


def test_source_references_are_preserved(tmp_path):
    path = tmp_path / "rules.json"
    write_rules(path, [REQUIRED_RULE])

    sources = tmp_path / "sources.json"
    write_sources(sources)

    loaded = load_rules(path, as_of="2026-09-16", source_path=sources)
    assert loaded[0]["source_id"] == "example-source"
    assert loaded[0]["source_document"] == "Example official document"
    assert loaded[0]["source_page"] == 10
    assert loaded[0]["source_section"] == "Section 1"



def test_unknown_source_reference_is_rejected(tmp_path):
    path = tmp_path / "rules.json"
    write_rules(path, [REQUIRED_RULE])

    sources = tmp_path / "sources.json"
    sources.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "sources": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuleDataError, match="unknown source_id"):
        load_rules(path, as_of="2026-09-16", source_path=sources)

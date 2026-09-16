"""Loader for the future government-source-backed rule set.

This module is intentionally not imported by services.compliance. It provides
validation and version filtering for rules only after human verification.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


DEFAULT_RULES_PATH = Path(__file__).parent / "rules" / "verified_rules.json"
REQUIRED_RULE_FIELDS = (
    "rule_id",
    "rule_number",
    "requirement",
    "scope",
    "applicability",
    "validation_method",
    "severity",
    "evidence_required",
    "effective_from",
    "effective_until",
    "source_id",
    "source_document",
    "source_page",
    "source_section",
    "verification_status",
)


class RuleDataError(ValueError):
    """Raised when a structured regulation document is malformed."""


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuleDataError(f"Could not read regulation data from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuleDataError("Regulation document must contain a JSON object.")
    return data


def _parse_date(value: Any, field_name: str, rule_id: str) -> Optional[date]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuleDataError(f"{field_name} for rule '{rule_id}' must be an ISO date or null.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RuleDataError(f"{field_name} for rule '{rule_id}' must use YYYY-MM-DD.") from exc


def validate_rule(rule: Any) -> Dict[str, Any]:
    """Validate and return one rule without changing its source metadata."""
    if not isinstance(rule, dict):
        raise RuleDataError("Each rule must be a JSON object.")
    missing = [field for field in REQUIRED_RULE_FIELDS if field not in rule]
    if missing:
        raise RuleDataError(f"Rule is missing required fields: {', '.join(missing)}")

    rule_id = rule["rule_id"]
    if not isinstance(rule_id, str) or not rule_id.strip():
        raise RuleDataError("rule_id must be a non-empty string.")

    for field in REQUIRED_RULE_FIELDS:
        if field in {"effective_from", "effective_until", "source_page"}:
            continue
        value = rule[field]
        if value is None or (isinstance(value, str) and not value.strip()):
            raise RuleDataError(f"{field} for rule '{rule_id}' must not be empty.")

    effective_from = _parse_date(rule["effective_from"], "effective_from", rule_id)
    effective_until = _parse_date(rule["effective_until"], "effective_until", rule_id)
    if effective_from and effective_until and effective_until < effective_from:
        raise RuleDataError(f"effective_until precedes effective_from for rule '{rule_id}'.")

    return rule


def _is_effective(rule: Dict[str, Any], as_of: date) -> bool:
    effective_from = _parse_date(rule["effective_from"], "effective_from", rule["rule_id"])
    effective_until = _parse_date(rule["effective_until"], "effective_until", rule["rule_id"])
    return (effective_from is None or effective_from <= as_of) and (effective_until is None or as_of <= effective_until)


def load_rules(
    path: Optional[Union[str, Path]] = None,
    *,
    as_of: Optional[Union[str, date]] = None,
) -> List[Dict[str, Any]]:
    """Load verified, effective rules; return [] when no verified rules exist.

    Malformed JSON or malformed rule records raise RuleDataError so invalid
    legal-source data cannot be silently treated as an empty rule set.
    """
    document = _read_json(Path(path) if path else DEFAULT_RULES_PATH)
    rules = document.get("rules", [])
    if not isinstance(rules, list):
        raise RuleDataError("The rules field must be a JSON array.")

    if as_of is None:
        effective_date = date.today()
    elif isinstance(as_of, date):
        effective_date = as_of
    elif isinstance(as_of, str):
        try:
            effective_date = date.fromisoformat(as_of)
        except ValueError as exc:
            raise RuleDataError("as_of must use YYYY-MM-DD.") from exc
    else:
        raise RuleDataError("as_of must be an ISO date string or date object.")

    loaded: List[Dict[str, Any]] = []
    for candidate in rules:
        rule = validate_rule(candidate)
        if rule["verification_status"] != "VERIFIED":
            continue
        if _is_effective(rule, effective_date):
            loaded.append(rule)
    return loaded

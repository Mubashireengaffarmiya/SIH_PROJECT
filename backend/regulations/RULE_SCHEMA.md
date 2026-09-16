# Verified Rule Schema

This document defines the metadata required for a future rule to enter the government-source-backed rule set. An empty rule set is intentional until a human verifies an exact official source.

Every verified rule must contain:

| Field                 | Meaning                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------- |
| `rule_id`             | Stable unique identifier for the structured rule.                                                 |
| `rule_number`         | Exact rule, section, clause, or paragraph reference as printed in the source.                     |
| `requirement`         | A faithful, non-invented description of the requirement.                                          |
| `scope`               | The regulated subject or commodity scope.                                                         |
| `applicability`       | Conditions under which the rule applies.                                                          |
| `validation_method`   | The deterministic validation operation used by the engine.                                        |
| `severity`            | Review priority assigned by the verified rule owner.                                              |
| `evidence_required`   | Evidence needed to evaluate the rule.                                                             |
| `effective_from`      | ISO date on which this version becomes effective, or `null` when the source does not specify one. |
| `effective_until`     | ISO date after which this version is no longer effective, or `null` when open-ended.              |
| `source_id`           | Identifier present in `source_registry.json`.                                                     |
| `source_document`     | Exact official document title or identifier.                                                      |
| `source_page`         | Page number or locator in the source, when applicable.                                            |
| `source_section`      | Exact section, schedule, clause, or heading locator.                                              |
| `verification_status` | Must be `VERIFIED` before the rule can be loaded for evaluation.                                  |

## Required Source Metadata

Each `source_id` must resolve to a source-registry entry containing the source title, publisher, jurisdiction, document type, official URL, version, verification dates, and notes. The loader preserves source references but does not establish legal authenticity or perform human verification.

## Date and Status Rules

- Dates use ISO `YYYY-MM-DD` format.
- `effective_from` and `effective_until` are inclusive date boundaries.
- `effective_until` must not precede `effective_from`.
- Rules with `verification_status` other than `VERIFIED` are ignored by the foundation loader.
- No rule in this repository is currently government-verified; `verified_rules.json` intentionally contains an empty array.

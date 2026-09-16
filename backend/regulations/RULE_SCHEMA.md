# SMART-LM Rule Schema

This directory contains the government-source-based compliance rule
configuration used by SMART-LM.

## Rule record

Each rule should contain the following fields:

| Field | Description |
|---|---|
| `rule_id` | Stable unique identifier for the rule version. |
| `rule_number` | Legal rule / clause reference. |
| `requirement` | Human-readable compliance requirement. |
| `scope` | Package/product scope to which the rule applies. |
| `applicability` | Conditions under which the rule applies. |
| `applicability_type` | Machine-readable applicability mode: `ALWAYS` or `CONDITIONAL`. |
| `validation_method` | Application validation method used by SMART-LM. |
| `severity` | Application-defined review priority; it is not assumed to be a severity assigned by the law. |
| `evidence_required` | Evidence required to support the compliance decision. |
| `effective_from` | Date from which this rule version is effective. |
| `effective_until` | Date until which this rule version is effective, or `null` if still active. |
| `source_id` | Identifier linking the rule to `source_registry.json`. |
| `source_document` | Official source document name. |
| `source_page` | Page containing the relevant source material. |
| `source_section` | Relevant rule / section / clause. |
| `verification_status` | Internal verification status. `VERIFIED` means the rule has been checked against the recorded official source; it does not mean government certification of SMART-LM. |

## Verification rules

- Only rules with `verification_status = VERIFIED` are loaded by the rule loader.
- Rules are filtered according to `effective_from` and `effective_until`.
- `source_id` must exist in `source_registry.json`.
- The source registry records the official government source used to verify the rule.
- `applicability_type = ALWAYS` means the rule can be evaluated without additional applicability context.
- `applicability_type = CONDITIONAL` means SMART-LM must establish applicability from inspection context before evaluating the rule.
- Missing information must not automatically be interpreted as proof that a conditional rule applies.
- If applicability cannot be established safely, SMART-LM returns `NEEDS REVIEW`.

## Important distinction

SMART-LM uses government publications as its legal source material.

The software's `VERIFIED` status means:

> Human-verified against the recorded official source.

It does **not** mean that the Government of India has certified, approved, or endorsed the SMART-LM software.

## Rule-engine principle

The rule engine separates:

1. **Source-backed legal requirement**
2. **Applicability determination**
3. **Evidence extraction**
4. **Validation**
5. **Compliance result**

The OCR/VLM layer extracts visible information.

The deterministic rule engine evaluates that information against the configured requirement.

When required information is unavailable or applicability cannot be established, the system should prefer `NEEDS REVIEW` or `NOT VERIFIABLE` rather than making an unsupported legal conclusion.

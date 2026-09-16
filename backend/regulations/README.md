# Government-Sourced Rule Engine Foundation

SMART-LM is preparing a versioned software rule engine based on official government sources. It is **not** an official government-certified rule engine.

The migration path is:

```text
Official Government Source
        |
        v
Human Verification
        |
        v
Structured Rule
        |
        v
Versioned Rule Engine
        |
        v
Compliance Evaluation
```

The current compliance engine remains unchanged and continues to load `backend/rules/rules.json`. The files under `backend/regulations/` are an additive foundation only and are not connected to compliance evaluation yet.

## Directory Layout

- `source_registry.json` stores metadata for exact official source documents.
- `rules/verified_rules.json` is reserved for rules that have completed human verification. It is intentionally empty.
- `RULE_SCHEMA.md` documents the required rule and source-reference fields.
- `rule_loader.py` validates and filters structured rules without making legal judgments.

No rule should be added as `VERIFIED` without an exact official source reference and human verification record.

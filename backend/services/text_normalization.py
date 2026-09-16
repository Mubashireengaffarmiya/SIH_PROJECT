"""Small, lossless normalizers shared by OCR/VLM reconciliation."""

from __future__ import annotations

import re


def normalize_currency_text(value: str) -> str:
    """Normalize known currency spellings without altering other Unicode text."""
    text = str(value or "")
    text = re.sub(r"\b(?:Rs\.?|INR|Rupees)\s*", "₹", text, flags=re.IGNORECASE)
    return text


def currency_amount(value: str) -> str | None:
    normalized = normalize_currency_text(value)
    match = re.search(
        r"(?:₹\s*[0-9]+(?:[.,][0-9]{1,2})?|\bMRP\s*[:\-]?\s*[₹]?\s*[0-9]+(?:[.,][0-9]{1,2})?)",
        normalized,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    amount = re.search(r"[0-9]+(?:[.,][0-9]{1,2})?", match.group(0))
    if not amount:
        return None
    return f"₹{amount.group(0).replace(',', '.')}"
"""Small, lossless normalizers shared by OCR/VLM reconciliation."""

from __future__ import annotations

import re


def normalize_currency_text(value: str) -> str:
    """Normalize known currency spellings without altering other Unicode text."""
    text = str(value or "")
    text = re.sub(r"\b(?:Rs\.?|INR|Rupees)\s*", "₹", text, flags=re.IGNORECASE)
    return text


def normalize_label_text(value: str) -> str:
    """Apply conservative OCR cleanup for comparing label evidence."""
    text = normalize_currency_text(value)
    text = re.sub(r"(?i)\b(mrp)\s*[:\-]?\s*", r"\1 ", text)
    text = re.sub(r"(?i)(\d)\s+(kg|g|mg|l|ml)\b", r"\1\2", text)
    text = re.sub(r"(?i)\b(ltr|litre|litres)\b", "l", text)
    text = re.sub(r"(?i)\b(kilograms?)\b", "kg", text)
    text = re.sub(r"(?i)\b(milligrams?)\b", "mg", text)
    text = re.sub(r"(?i)\b(milliliters?|millilitres?)\b", "ml", text)
    return re.sub(r"\s+", " ", text).strip()


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
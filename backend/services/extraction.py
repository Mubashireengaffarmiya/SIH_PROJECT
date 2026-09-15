"""
SMART-LM Field Extraction Service
===================================
Deterministic regex-based extraction of mandatory declarations from OCR text.

Each extractor returns:
  {
      "value": str | None,
      "confidence": "HIGH" | "MEDIUM" | "LOW",
      "evidence_text": str | None,   # the matched OCR snippet
  }

A None value means the field was NOT DETECTED — it does NOT mean the
declaration is legally absent. OCR may have missed it.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

import cv2
import pytesseract

logger = logging.getLogger(__name__)


def preprocess_mrp_crop(cropped_img):
    """Enlarges and sharpens the cropped region to improve digit OCR."""
    gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(
        gray,
        None,
        fx=3,
        fy=3,
        interpolation=cv2.INTER_CUBIC
    )
    blurred = cv2.GaussianBlur(resized, (3, 3), 0)
    _, thresh = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresh


def _get_mrp_crop_from_image(source_image: str, words: List[Dict[str, Any]]) -> Optional[Any]:
    if not source_image:
        return None

    try:
        image = cv2.imread(source_image)
    except Exception:
        return None
    if image is None or image.size == 0:
        return None

    relevant_indices = []
    for i, word in enumerate(words):
        text = str(word.get('text', '') or '').strip()
        if not text:
            continue
        lowered = text.lower()
        if 'mrp' in lowered or '₹' in text or 'rs' in lowered or 'inr' in lowered:
            relevant_indices.append(i)
        elif any(ch.isdigit() for ch in text) and any(token in lowered for token in ['mrp', 'rs', 'inr', '₹']):
            relevant_indices.append(i)

    if not relevant_indices:
        return None

    xs = []
    ys = []
    for idx in relevant_indices:
        bbox = words[idx].get('bbox') or []
        if len(bbox) < 4:
            continue
        x1, y1, x2, y2 = [float(v) for v in bbox[:4]]
        xs.extend([x1, x2])
        ys.extend([y1, y2])

    if not xs or not ys:
        return None

    x1 = max(0, int(min(xs) - 15))
    y1 = max(0, int(min(ys) - 15))
    x2 = min(image.shape[1] - 1, int(max(xs) + 15))
    y2 = min(image.shape[0] - 1, int(max(ys) + 15))
    if x2 <= x1 or y2 <= y1:
        return None

    return image[y1:y2, x1:x2]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _search_words(pattern: str, words: List[Dict[str, Any]], flags=re.IGNORECASE) -> Optional[Tuple[str, float]]:
    """Search pattern across individual word texts; return (matched_text, avg_confidence)."""
    for w in words:
        m = re.search(pattern, w["text"], flags)
        if m:
            return w["text"], w["confidence"]
    return None


def _search_fulltext(pattern: str, full_text: str, flags=re.IGNORECASE):
    return re.search(pattern, full_text, flags)


def _confidence_from_ocr(ocr_conf: float) -> str:
    if ocr_conf >= 0.85:
        return "HIGH"
    if ocr_conf >= 0.60:
        return "MEDIUM"
    return "LOW"


def _combine_confidence(ocr_conf: str, pattern_strong: bool) -> str:
    """Downgrade OCR confidence if pattern match was weak."""
    if pattern_strong:
        return ocr_conf
    if ocr_conf == "HIGH":
        return "MEDIUM"
    return "LOW"


def _empty_field() -> Dict[str, Any]:
    return {"value": None, "confidence": "LOW", "evidence_text": None}


# ---------------------------------------------------------------------------
# Individual Field Extractors
# ---------------------------------------------------------------------------

def extract_mrp(full_text: str, words: List[Dict[str, Any]], source_image: Optional[str] = None) -> Dict[str, Any]:
    """
    Detect MRP patterns:
      MRP ₹50 / MRP Rs.50 / MRP: 50 / Maximum Retail Price ₹50 / MRP & 250.00
    """
    patterns = [
        re.compile(
            r'(?:MRP|M\.R\.P\.?|Maximum\s+Retail\s+Price)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*[&]?\s*([0-9]+(?:\.[0-9]{1,2})?)',
            re.IGNORECASE
        ),
        re.compile(
            r'(?:Rs\.?|₹|INR)\s*([0-9]+(?:\.[0-9]{1,2})?)',
            re.IGNORECASE
        ),
    ]

    for pat in patterns:
        m = pat.search(full_text)
        if m:
            nearby = [w for w in words if "mrp" in w["text"].lower() or "₹" in w["text"] or "rs" in w["text"].lower() or any(ch.isdigit() for ch in w["text"]) ]
            avg_conf = sum(w["confidence"] for w in nearby) / len(nearby) if nearby else 0.7
            return {
                "value": f"₹{m.group(1)}",
                "confidence": _combine_confidence(_confidence_from_ocr(avg_conf), True),
                "evidence_text": m.group(0),
            }

    if source_image:
        try:
            mrp_crop = _get_mrp_crop_from_image(source_image, words)
            if mrp_crop is not None:
                cleaned_crop = preprocess_mrp_crop(mrp_crop)
                text = pytesseract.image_to_string(cleaned_crop, config=r'--psm 6 -c tessedit_char_whitelist=0123456789.')
                digit_text = re.sub(r'[^0-9.]', '', text.strip())
                if digit_text and re.fullmatch(r'\d+(?:\.\d+)?', digit_text):
                    return {
                        "value": f"₹{digit_text}",
                        "confidence": "MEDIUM",
                        "evidence_text": digit_text,
                    }
        except Exception as exc:
            logger.warning("Targeted MRP OCR failed: %s", exc)

    return _empty_field()


def extract_net_quantity(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect net quantity:
      Net Qty 100g / Net Quantity: 500 ml / 1 L / 250 grams / 6 Pieces
    """
    strong = re.compile(
        r'(?:Net\s+(?:Qty|Quantity|Wt\.?|Weight|Vol\.?|Volume|Content))\s*[:\-]?\s*'
        r'([0-9]+(?:\.[0-9]+)?\s*(?:kg|g|gm|grams?|ml|mL|litre|liter|L|pieces?|pcs|units?|tabs?|tablets?))',
        re.IGNORECASE
    )
    m = strong.search(full_text)
    if m:
        qty_words = [w for w in words if re.search(r'net', w["text"], re.I)]
        avg_conf = sum(w["confidence"] for w in qty_words) / len(qty_words) if qty_words else 0.7
        return {
            "value": m.group(1).strip(),
            "confidence": _combine_confidence(_confidence_from_ocr(avg_conf), True),
            "evidence_text": m.group(0),
        }

    # Standalone quantity (weaker)
    weak = re.compile(
        r'\b([0-9]+(?:\.[0-9]+)?\s*(?:kg|g|gm|grams?|ml|mL|litre|liter|[Ll]b?|pieces?|pcs))\b',
        re.IGNORECASE
    )
    m = weak.search(full_text)
    if m:
        return {
            "value": m.group(1).strip(),
            "confidence": "LOW",
            "evidence_text": m.group(0),
        }

    return _empty_field()


def extract_manufacturer(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect manufacturer / packer / importer with address fragment.
    """
    patterns = [
        re.compile(
            r'(?:Manufactured\s+(?:and\s+)?(?:Packed\s+)?by|Mfd\.\s+by|Mfr\.\s+by|'
            r'Packed\s+by|Packer\s*:|Imported\s+by|Distributed\s+by|Marketed\s+by)[:\s]+([^\n\.]{10,220})',
            re.IGNORECASE
        ),
        re.compile(
            r'(?:Manufacturer|Packer|Importer)\s*[:\-]\s*([^\n\.]{10,220})',
            re.IGNORECASE
        ),
    ]
    for pat in patterns:
        m = pat.search(full_text)
        if m:
            manufacturer_text = m.group(1).strip()
            if re.search(r'Plot\s+No\.|Industrial\s+Area|Pune|India|No\.', manufacturer_text, re.I):
                manufacturer_text = manufacturer_text[:220]
            mfr_words = [w for w in words if re.search(r'manufactur|packed|importer|packer|plot|industrial|pune', w["text"], re.I)]
            avg_conf = sum(w["confidence"] for w in mfr_words) / len(mfr_words) if mfr_words else 0.7
            return {
                "value": manufacturer_text[:220],
                "confidence": _combine_confidence(_confidence_from_ocr(avg_conf), True),
                "evidence_text": m.group(0)[:250],
            }
    return _empty_field()


def extract_manufacturing_date(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect manufacturing / packing date.
    Patterns: MFD, Mfg Date, Manufactured on, Packed on
    Dates: MM/YYYY, MM-YYYY, Month YYYY, DD/MM/YYYY
    """
    # keyword + date
    strong = re.compile(
        r'(?:MFD|Mfg\.?\s*Date?|Manufactured\s+(?:on|date)?|Packed\s+on|Mfd\.?)\s*[:\-]?\s*'
        r'((?:\d{1,2}[\/\-]\d{4})|(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})|'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4})',
        re.IGNORECASE
    )
    m = strong.search(full_text)
    if m:
        date_words = [w for w in words if re.search(r'mfd|mfg|manufactur|packed', w["text"], re.I)]
        avg_conf = sum(w["confidence"] for w in date_words) / len(date_words) if date_words else 0.7
        return {
            "value": m.group(1).strip(),
            "confidence": _combine_confidence(_confidence_from_ocr(avg_conf), True),
            "evidence_text": m.group(0),
        }
    return _empty_field()


def extract_consumer_care(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect consumer care details: phone, email, or keyword lines.
    """
    # Phone number detection (Indian: 10 digits, or with +91, or toll-free 1800-)
    phone_pat = re.compile(
        r'(?:Consumer\s+Care|Customer\s+Care|Helpline|Care\s+No\.?|Toll\s+Free)?\s*[:\-]?\s*'
        r'(\+?91[-\s]?\d{10}|1800[-\s]?\d{3,4}[-\s]?\d{4,6}|\d{10,11})',
        re.IGNORECASE
    )
    m = phone_pat.search(full_text)
    if m:
        care_words = [w for w in words if re.search(r'consumer|customer|care|helpline|toll', w["text"], re.I)]
        avg_conf = sum(w["confidence"] for w in care_words) / len(care_words) if care_words else 0.7
        return {
            "value": m.group(0).strip(),
            "confidence": _combine_confidence(_confidence_from_ocr(avg_conf), True),
            "evidence_text": m.group(0),
        }

    # Email detection
    email_pat = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', re.IGNORECASE)
    m = email_pat.search(full_text)
    if m:
        return {
            "value": m.group(0).strip(),
            "confidence": "MEDIUM",
            "evidence_text": m.group(0),
        }

    # Keyword line only
    keyword_pat = re.compile(
        r'(?:Consumer\s+Care|Customer\s+Care|Helpline|Care\s+Line)[^\n]{0,80}',
        re.IGNORECASE
    )
    m = keyword_pat.search(full_text)
    if m:
        return {
            "value": m.group(0).strip()[:120],
            "confidence": "LOW",
            "evidence_text": m.group(0),
        }

    return _empty_field()


def extract_country_of_origin(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect country of origin.
    """
    strong = re.compile(
        r'(?:Country\s+of\s+Origin|Country\s*:|Origin\s*:)\s*([A-Za-z ]+?)(?:[,\n\.]|$)',
        re.IGNORECASE
    )
    m = strong.search(full_text)
    if m:
        coo_words = [w for w in words if re.search(r'country|origin', w["text"], re.I)]
        avg_conf = sum(w["confidence"] for w in coo_words) / len(coo_words) if coo_words else 0.7
        return {
            "value": m.group(1).strip(),
            "confidence": _combine_confidence(_confidence_from_ocr(avg_conf), True),
            "evidence_text": m.group(0),
        }

    # "Made in X" pattern
    made_in = re.compile(r'Made\s+in\s+([A-Za-z ]+?)(?:[,\n\.]|$)', re.IGNORECASE)
    m = made_in.search(full_text)
    if m:
        return {
            "value": m.group(1).strip(),
            "confidence": "MEDIUM",
            "evidence_text": m.group(0),
        }

    return _empty_field()


def extract_best_before(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect best before / expiry / use by date.
    """
    strong = re.compile(
        r'(?:Best\s+Before|Best\s+By|Use\s+By|Use\s+Before|Expiry|Exp\.?\s*Date?|BB)\s*[:\-]?\s*'
        r'((?:\d{1,2}[\/\-]\d{1,4})|(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})|'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|'
        r'(?:\d+\s+(?:months?|days?|years?)\s+from\s+(?:mfd|mfg|mfg\s+date|manufacture|packing|packing\s+date)))',
        re.IGNORECASE
    )
    m = strong.search(full_text)
    if m:
        bb_words = [w for w in words if re.search(r'best|before|expiry|exp\.?|use by', w["text"], re.I)]
        avg_conf = sum(w["confidence"] for w in bb_words) / len(bb_words) if bb_words else 0.7
        return {
            "value": m.group(1).strip(),
            "confidence": _combine_confidence(_confidence_from_ocr(avg_conf), True),
            "evidence_text": m.group(0),
        }
    return _empty_field()


def extract_unit_sale_price(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect unit sale price (per kg, per litre).
    """
    pat = re.compile(
        r'(?:Unit\s+(?:Sale\s+)?Price|Price\s+per\s+(?:kg|litre|liter|100g|unit))\s*[:\-]?\s*'
        r'(?:Rs\.?|₹|INR)?\s*([0-9]+(?:\.[0-9]{1,2})?)',
        re.IGNORECASE
    )
    m = pat.search(full_text)
    if m:
        return {
            "value": f"₹{m.group(1)}",
            "confidence": "MEDIUM",
            "evidence_text": m.group(0),
        }
    return _empty_field()


def extract_product_name(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Prefer the product title before the Net Qty or MRP label, rather than a single word."""
    label_match = re.search(r'(.+?)(?=\s*(?:Net\s+Qty|Net\s+Quantity|MRP|Maximum\s+Retail\s+Price))', full_text, re.IGNORECASE | re.DOTALL)
    if label_match:
        candidate = re.sub(r'\s+', ' ', label_match.group(1)).strip(' .,:;-|/')
        if len(candidate) >= 3 and not re.fullmatch(r'^[\d\s\W]+$', candidate):
            top_words = [w for w in words if w["text"].lower() in candidate.lower().split()]
            avg_conf = sum(w["confidence"] for w in top_words) / len(top_words) if top_words else 0.7
            return {
                "value": candidate[:100],
                "confidence": _confidence_from_ocr(avg_conf),
                "evidence_text": candidate,
            }

    lines = [l.strip() for l in full_text.split('\n') if l.strip()]
    for line in lines:
        if len(line) >= 3 and not re.match(r'^[\d\s\W]+$', line):
            if not re.search(r'MRP|Rs\.|₹|MFD|Best\s+Before|Net\s+Qty|Manufactured|Country\s+of\s+Origin|Consumer\s+Care', line, re.I):
                return {
                    "value": line[:100],
                    "confidence": "LOW",
                    "evidence_text": line,
                }
    return _empty_field()


# ---------------------------------------------------------------------------
# Main extraction entry point
# ---------------------------------------------------------------------------

def extract_all(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all extractors on the OCR result.
    Returns dict matching ExtractionResult schema.
    """
    full_text = ocr_result.get("full_text", "")
    words = ocr_result.get("words", [])
    source_image = ocr_result.get("source_image")

    # Reconstruct multi-line text from words (PaddleOCR loses newlines in full_text)
    # We'll use the full_text as-is since we've already joined words
    # For better extraction, also try newline-joined version
    multiline_text = "\n".join(w["text"] for w in words) + "\n" + full_text

    return {
        "product_name": extract_product_name(multiline_text, words),
        "mrp": extract_mrp(multiline_text, words, source_image=source_image),
        "net_quantity": extract_net_quantity(multiline_text, words),
        "manufacturer": extract_manufacturer(multiline_text, words),
        "manufacturing_date": extract_manufacturing_date(multiline_text, words),
        "consumer_care": extract_consumer_care(multiline_text, words),
        "country_of_origin": extract_country_of_origin(multiline_text, words),
        "best_before": extract_best_before(multiline_text, words),
        "unit_sale_price": extract_unit_sale_price(multiline_text, words),
    }

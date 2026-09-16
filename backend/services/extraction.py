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


def _normalize_ocr_text(value: str) -> str:
    text = str(value or "")
    text = text.replace("\r", " ").replace("\n", " ")
    text = text.replace("\t", " ")
    replacements = {
        "QUANT1TY": "QUANTITY",
        "QUANT1T Y": "QUANTITY",
        "QUANTI TY": "QUANTITY",
        "NET WT": "NET WEIGHT",
        "NET WT.": "NET WEIGHT",
        "MRP :": "MRP:",
        "MRP:": "MRP",
        "MRP : ": "MRP:",
        "Rs.": "RS",
    }
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _is_nutrition_keyword(value: str) -> bool:
    return bool(re.search(
        r'^(energy|protein|carbohydrate|total\s+sugars|added\s+sugars|total\s+fat|saturated|trans|sodium|fibre|calories|kcal|g|mg|ml|per\s+100g)$',
        _normalize_ocr_text(value).lower().strip(),
        re.I,
    ))


def _is_declaration_keyword(value: str) -> bool:
    lowered = _normalize_ocr_text(value).lower()
    return bool(re.search(
        r'^(net\s*(qty|quantity|wt|weight|vol|volume)|mrp|max(?:imum)?\s*retail\s*price|manufactur(?:ed|er)|packed\s+by|manufactured\s*&\s*packed\s+by|mfd|best\s+before|use\s+by|country\s+of\s+origin|consumer\s+care|imported\s+by|packer|batch|no\.)$',
        lowered,
        re.I,
    ))


# ---------------------------------------------------------------------------
# Individual Field Extractors
# ---------------------------------------------------------------------------

def extract_mrp(full_text: str, words: List[Dict[str, Any]], source_image: Optional[str] = None) -> Dict[str, Any]:
    """Extract MRP only when it is explicitly associated with an MRP keyword and nearby value."""
    normalized_text = _normalize_ocr_text(full_text)
    pattern = re.compile(
        r'(?:MRP|M\.R\.P\.?|Maximum\s+Retail\s+Price)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*[&]?\s*([0-9]+(?:\.[0-9]{1,2})?)',
        re.IGNORECASE,
    )
    m = pattern.search(normalized_text)
    if m:
        val = f"₹{m.group(1)}"
        nearby = [w for w in words if "mrp" in _normalize_ocr_text(w["text"]).lower() or "₹" in w["text"] or "rs" in _normalize_ocr_text(w["text"]).lower() or any(ch.isdigit() for ch in w["text"])]
        avg_conf = sum(w["confidence"] for w in nearby) / len(nearby) if nearby else 0.8
        return {
            "value": val,
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


_QUANTITY_UNIT_PATTERN = r'(?:mg|g|gm|gram|grams|kg|ml|l|litre|liter|pieces?|pcs|units?)'
_QUANTITY_NUMBER_PATTERN = r'(?:\d+(?:[\.,]\d+)?)'
_QUANTITY_VALUE_PATTERN = re.compile(
    rf'(?P<number>{_QUANTITY_NUMBER_PATTERN})\s*(?P<unit>{_QUANTITY_UNIT_PATTERN})',
    re.IGNORECASE,
)


def _normalize_quantity_token(value: str) -> str:
    """Correct OCR errors only while parsing a quantity candidate."""
    text = _normalize_ocr_text(value).strip(' ,:;()[]{}')
    text = re.sub(r'(?<=\d)[Oo](?=\d)', '0', text, flags=re.IGNORECASE)
    text = re.sub(r'^[Oo](?=[.,]\d)', '0', text, flags=re.IGNORECASE)
    text = re.sub(r'(?<=\d)[Oo](?=\s*[a-zA-Z])', '0', text, flags=re.IGNORECASE)
    text = re.sub(r'(?<=\d),(?=\d)', '.', text)
    text = re.sub(r'(?P<number>\d{2,4})9(?=$|\s*[a-zA-Z])', r'\g<number> g', text)
    return re.sub(r'\s+', ' ', text).strip()


def _format_quantity(number: str, unit: str) -> str:
    return f'{number.replace(",", ".")} {unit.lower()}'


def _quantity_from_tokens(tokens: List[str]) -> Optional[Tuple[str, str]]:
    """Return (formatted value, evidence) from one or two nearby OCR tokens."""
    normalized = [_normalize_quantity_token(token) for token in tokens if token]
    joined = _normalize_quantity_token(' '.join(normalized))
    match = _QUANTITY_VALUE_PATTERN.search(joined)
    if not match:
        return None
    value = _format_quantity(match.group('number'), match.group('unit'))
    return value, joined


def _bbox(word: Dict[str, Any]) -> Optional[Tuple[float, float, float, float]]:
    values = word.get('bbox') or []
    if len(values) < 4:
        return None
    return tuple(float(value) for value in values[:4])


def _quantity_keyword_span(words: List[Dict[str, Any]]) -> Optional[Tuple[int, int, str]]:
    normalized = [_normalize_ocr_text(word.get('text', '')).strip(' .,:;').lower() for word in words]
    aliases = {
        'qty': 'QTY', 'quantity': 'QUANTITY', 'weight': 'WEIGHT',
        'wt': 'WEIGHT', 'volume': 'VOLUME', 'vol': 'VOLUME',
    }
    for index, token in enumerate(normalized):
        token = token.replace('1', 'i')
        if token == 'net' and index + 1 < len(normalized):
            next_token = normalized[index + 1].replace('1', 'i')
            if next_token in aliases:
                return index, index + 1, f'NET {aliases[next_token]}'
        if token in {'quantity', 'qty', 'weight', 'wt', 'volume', 'vol'}:
            return index, index, aliases.get(token, token.upper())
    return None


def extract_net_quantity(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract net quantity from an explicitly labelled, spatially nearby value."""
    keyword_span = _quantity_keyword_span(words)
    if keyword_span:
        start, end, label = keyword_span
        label_box = _bbox(words[start])
        end_box = _bbox(words[end])
        if label_box and end_box:
            label_box = (
                min(label_box[0], end_box[0]), min(label_box[1], end_box[1]),
                max(label_box[2], end_box[2]), max(label_box[3], end_box[3]),
            )
        candidates = []
        stop_words = {'mrp', 'manufactured', 'packed', 'mfd', 'best', 'before', 'use', 'country', 'consumer', 'batch'}
        for index in range(end + 1, min(len(words), end + 10)):
            token = _normalize_ocr_text(words[index].get('text', ''))
            if not token:
                continue
            if token.lower().strip(' .,:;') in stop_words:
                break
            for span in (1, 2):
                if index + span > len(words):
                    continue
                token_words = words[index:index + span]
                parsed = _quantity_from_tokens([word.get('text', '') for word in token_words])
                if not parsed:
                    continue
                candidate_box = _bbox(token_words[0])
                if len(token_words) == 2 and _bbox(token_words[1]):
                    second_box = _bbox(token_words[1])
                    candidate_box = (
                        min(candidate_box[0], second_box[0]), min(candidate_box[1], second_box[1]),
                        max(candidate_box[2], second_box[2]), max(candidate_box[3], second_box[3]),
                    ) if candidate_box else second_box
                if not label_box or not candidate_box:
                    score = 50.0
                else:
                    same_line = abs(((label_box[1] + label_box[3]) / 2) - ((candidate_box[1] + candidate_box[3]) / 2)) <= max(label_box[3] - label_box[1], 24) * 1.8
                    horizontal_gap = max(0.0, candidate_box[0] - label_box[2])
                    vertical_gap = max(0.0, candidate_box[1] - label_box[3])
                    below_label = vertical_gap <= 180 and candidate_box[2] >= label_box[0] and candidate_box[0] <= label_box[2]
                    nearby = same_line or below_label
                    if not nearby:
                        continue
                    score = 100.0 if same_line else 85.0
                    score -= min(horizontal_gap / 100.0, 20.0)
                    score -= min(vertical_gap / 100.0, 20.0)
                confidence = sum(float(word.get('confidence', 0.0)) for word in token_words) / len(token_words)
                candidates.append((score, confidence, parsed, token_words))
                break

        if candidates:
            score, ocr_conf, (value, evidence), selected_words = max(candidates, key=lambda item: (item[0], item[1]))
            logger.info('Net quantity: label=%s value=%s score=%.1f bbox=%s', label, value, score, _bbox(selected_words[0]))
            confidence = 'HIGH' if score >= 80 and ocr_conf >= 0.75 else 'MEDIUM'
            return {'value': value, 'confidence': confidence, 'evidence_text': f'{label} {evidence}'}
        logger.info('Net quantity label=%s found but no nearby valid candidate', label)
        return _empty_field()

    weak = _QUANTITY_VALUE_PATTERN.search(_normalize_ocr_text(full_text))
    if weak:
        value = _format_quantity(weak.group('number'), weak.group('unit'))
        return {'value': value, 'confidence': 'LOW', 'evidence_text': weak.group(0)}
    return _empty_field()


def extract_manufacturer(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Collect the text immediately after a manufacturer/packer declaration keyword until the next declaration block."""
    normalized_text = _normalize_ocr_text(full_text)
    keyword_re = re.compile(r'(?:MANUFACTURED\s*(?:&\s*PACKED)?\s*BY|PACKED\s*BY|MANUFACTURED\s*BY|PACKER|MANUFACTURER|IMPORTED\s*BY|DISTRIBUTED\s*BY|MARKETED\s*BY)', re.IGNORECASE)
    match = keyword_re.search(normalized_text)
    if match:
        tail = normalized_text[match.end():]
        cutoff = re.search(r'(?i)(?:\bNET\s+QTY\b|\bNET\s+QUANTITY\b|\bMRP\b|\bBEST\s+BEFORE\b|\bUSE\s+BY\b|\bMFD\b|\bCOUNTRY\s+OF\s+ORIGIN\b|\bCONSUMER\s+CARE\b|\bFOR\s+CONSUMER\s+COMPLAINTS\b|\bCALL\b)', tail)
        if cutoff:
            tail = tail[:cutoff.start()]
        tail = re.sub(r'\b(?:ENERGY|PROTEIN|CARBOHYDRATE|TOTAL|FAT|SODIUM|SUGARS|ADDED|FLAVOUR|FLAVOR|INGREDIENTS|POTATO|CHIPS|OIL|SALT|SERVE|VALUES|APPROX|INFORMATION|PER|WATER)\b.*', '', tail, flags=re.IGNORECASE)
        tail = re.sub(r'\b\d+(?:\.\d+)?\b', ' ', tail)
        value = re.sub(r'\s+', ' ', tail).strip(' .,:;')
        # Keep only company-like text; avoid nutrition names and raw addresses without a legal entity name
        if len(value) >= 10 and any(ch.isalpha() for ch in value):
            return {'value': value[:220], 'confidence': 'HIGH', 'evidence_text': tail[:250]}

    for i, word in enumerate(words):
        text = _normalize_ocr_text(word.get('text', ''))
        if re.search(r'^(MANUFACTURED|PACKED|PACKER|MANUFACTURER|IMPORTED|DISTRIBUTED|MARKETED)$', text, re.I):
            group = []
            for j in range(i + 1, min(len(words), i + 18)):
                next_text = _normalize_ocr_text(words[j].get('text', ''))
                if not next_text:
                    continue
                if re.search(r'^(?:NET|QTY|QUANTITY|MRP|BEST|BEFORE|USE|BY|MFD|COUNTRY|CONSUMER|CALL|EMAIL|WWW|FOR)$', next_text, re.I):
                    break
                if re.fullmatch(r'\d+(?:\.\d+)?', next_text):
                    continue
                if re.search(r'^(?:ENERGY|PROTEIN|CARBOHYDRATE|TOTAL|FAT|SODIUM|SUGARS|ADDED|FLAVOUR|FLAVOR|INGREDIENTS|POTATO|CHIPS|OIL|SALT|VALUES|APPROX|INFORMATION|PER|SERVE)$', next_text, re.I):
                    continue
                if re.search(r'^(?:BY|&|,|\.|:)$', next_text, re.I):
                    continue
                group.append(next_text)
            value = ' '.join(group).strip(' ,.;:')
            if len(value) >= 10 and any(ch.isalpha() for ch in value):
                return {'value': value[:220], 'confidence': 'MEDIUM', 'evidence_text': value}

    return _empty_field()


def extract_manufacturing_date(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect manufacturing / packing date with explicit date keyword context."""
    strong = re.compile(
        r'(?:MFD|Mfg\.?\s*Date?|Manufactured\s+(?:on|date)?|Packed\s+on|Mfd\.?)\s*[:\-]?\s*'
        r'((?:\d{1,2}[\/\-]\d{4})|(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})|'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4})',
        re.IGNORECASE,
    )
    m = strong.search(_normalize_ocr_text(full_text))
    if m:
        date_words = [w for w in words if re.search(r'mfd|mfg|manufactur|packed', _normalize_ocr_text(w['text']), re.I)]
        avg_conf = sum(w['confidence'] for w in date_words) / len(date_words) if date_words else 0.7
        return {
            'value': m.group(1).strip(),
            'confidence': _combine_confidence(_confidence_from_ocr(avg_conf), True),
            'evidence_text': m.group(0),
        }
    return _empty_field()


def extract_consumer_care(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect consumer care details: phone, email, or keyword lines."""
    phone_pat = re.compile(
        r'(?:Consumer\s+Care|Customer\s+Care|Helpline|Care\s+No\.?|Toll\s+Free)?\s*[:\-]?\s*(\+?91[-\s]?\d{10}|1800[-\s]?\d{3,4}[-\s]?\d{4,6}|\d{10,11})',
        re.IGNORECASE,
    )
    m = phone_pat.search(_normalize_ocr_text(full_text))
    if m:
        care_words = [w for w in words if re.search(r'consumer|customer|care|helpline|toll', _normalize_ocr_text(w['text']), re.I)]
        avg_conf = sum(w['confidence'] for w in care_words) / len(care_words) if care_words else 0.7
        return {'value': m.group(0).strip(), 'confidence': _combine_confidence(_confidence_from_ocr(avg_conf), True), 'evidence_text': m.group(0)}

    email_pat = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', re.IGNORECASE)
    m = email_pat.search(_normalize_ocr_text(full_text))
    if m:
        return {'value': m.group(0).strip(), 'confidence': 'MEDIUM', 'evidence_text': m.group(0)}

    keyword_pat = re.compile(r'(?:Consumer\s+Care|Customer\s+Care|Helpline|Care\s+Line)[^\n]{0,80}', re.IGNORECASE)
    m = keyword_pat.search(_normalize_ocr_text(full_text))
    if m:
        return {'value': m.group(0).strip()[:120], 'confidence': 'LOW', 'evidence_text': m.group(0)}

    return _empty_field()


def extract_country_of_origin(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect country of origin."""
    strong = re.compile(
        r'(?:Country\s+of\s+Origin|Country\s*:|Origin\s*:)\s*'
        r'([A-Za-z][A-Za-z\s\-]*?)(?=\s*(?:[,.]|$|(?:Consumer|Customer)\s+Care|Helpline|Toll\s+Free))',
        re.IGNORECASE,
    )
    m = strong.search(_normalize_ocr_text(full_text))
    if m:
        coo_words = [w for w in words if re.search(r'country|origin', _normalize_ocr_text(w['text']), re.I)]
        avg_conf = sum(w['confidence'] for w in coo_words) / len(coo_words) if coo_words else 0.7
        value = m.group(1).strip()
        if value:
            return {'value': value, 'confidence': _combine_confidence(_confidence_from_ocr(avg_conf), True), 'evidence_text': m.group(0)}

    made_in = re.compile(r'Made\s+in\s+([A-Za-z ]+?)(?:[,\n\.]|$)', re.IGNORECASE)
    m = made_in.search(_normalize_ocr_text(full_text))
    if m:
        return {'value': m.group(1).strip(), 'confidence': 'MEDIUM', 'evidence_text': m.group(0)}

    return _empty_field()


def extract_best_before(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect best before / expiry / use by date with keyword context."""
    strong = re.compile(
        r'(?:Best\s+Before|Best\s+By|Use\s+By|Use\s+Before|Expiry|Exp\.?\s*Date?|BB)\s*[:\-]?\s*'
        r'((?:\d{1,2}[\/\-]\d{1,4})|(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})|'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|'
        r'(?:\d+\s+(?:months?|days?|years?)\s+from\s+(?:mfd|mfg|mfg\s+date|manufacture|packing|packing\s+date)))',
        re.IGNORECASE,
    )
    m = strong.search(_normalize_ocr_text(full_text))
    if m:
        bb_words = [w for w in words if re.search(r'best|before|expiry|exp\.?|use by', _normalize_ocr_text(w['text']), re.I)]
        avg_conf = sum(w['confidence'] for w in bb_words) / len(bb_words) if bb_words else 0.7
        return {'value': m.group(1).strip(), 'confidence': _combine_confidence(_confidence_from_ocr(avg_conf), True), 'evidence_text': m.group(0)}
    return _empty_field()


def extract_unit_sale_price(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect unit sale price (per kg, per litre)."""
    pat = re.compile(r'(?:Unit\s+(?:Sale\s+)?Price|Price\s+per\s+(?:kg|litre|liter|100g|unit))\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([0-9]+(?:\.[0-9]{1,2})?)', re.IGNORECASE)
    m = pat.search(_normalize_ocr_text(full_text))
    if m:
        return {'value': f'₹{m.group(1)}', 'confidence': 'MEDIUM', 'evidence_text': m.group(0)}
    return _empty_field()


def extract_product_name(full_text: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Prefer a title-like phrase near the package name, not a nutrition table block."""
    normalized_text = _normalize_ocr_text(full_text)
    stop_keywords = [
        'NET', 'QTY', 'QUANTITY', 'WT', 'WEIGHT', 'MRP', 'MAXIMUM', 'RETAIL', 'PRICE',
        'MANUFACTURED', 'PACKED', 'MFD', 'BEST', 'BEFORE', 'USE', 'BY', 'COUNTRY', 'ORIGIN',
        'CONSUMER', 'CARE', 'CALL', 'EMAIL', 'WWW', 'SERVE', 'BATCH', 'LOT', 'PLOT'
    ]

    # Repeated adjacent words are a strong, product-agnostic title signal on
    # package fronts that show the same name in more than one location.
    repeated_pairs = []
    for i in range(len(words) - 1):
        first = _normalize_ocr_text(words[i].get('text', '')).strip(' .,:;')
        second = _normalize_ocr_text(words[i + 1].get('text', '')).strip(' .,:;')
        if not (re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", first) and re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", second)):
            continue
        first_y = (words[i].get('bbox') or [0, 0, 0, 0])[1]
        second_y = (words[i + 1].get('bbox') or [0, 0, 0, 0])[1]
        if abs(float(first_y) - float(second_y)) > 45:
            continue
        pair = (first.lower(), second.lower())
        if any(
            pair == (
                _normalize_ocr_text(words[j].get('text', '')).strip(' .,:;').lower(),
                _normalize_ocr_text(words[j + 1].get('text', '')).strip(' .,:;').lower(),
            )
            for j in range(i + 2, len(words) - 1)
        ):
            repeated_pairs.append((i, f'{first} {second}'))
    if repeated_pairs:
        value = repeated_pairs[0][1]
        return {'value': value, 'confidence': 'HIGH', 'evidence_text': value}

    stop_index = None
    for idx, word in enumerate(words):
        text = _normalize_ocr_text(word.get('text', ''))
        if any(re.fullmatch(re.escape(keyword), text, re.I) for keyword in stop_keywords):
            stop_index = idx
            break
        if re.fullmatch(r'(?:NUTRI\w*|ENERGY|INGREDIENTS|CONTAINS|MANUFACTURED)', text, re.I):
            stop_index = idx
            break

    candidate_words = []
    for word in words[:stop_index] if stop_index is not None else words:
        text = _normalize_ocr_text(word.get('text', ''))
        if not text:
            continue
        if re.fullmatch(r'\d+(?:\.\d+)?', text):
            continue
        if re.search(r'^(?:ENERGY|PROTEIN|CARBOHYDRATE|TOTAL|FAT|SODIUM|ADDED|SUGARS|VALUES|APPROX|INFORMATION|PER|SERVE|INGREDIENTS|FLAVOUR|FLAVOR|OIL|SALT|POTATO|CHIPS|KCAL|G|MG|ML|CALORIES)$', text, re.I):
            continue
        if re.search(r'^(?:INFO|INFORMATION|NUTRITION|VALUES|APPROX)$', text, re.I):
            continue
        if re.search(r'^[^A-Za-z\'\-]+$', text):
            continue
        candidate_words.append(text)

    # Prefer a later, title-like phrase near the product name rather than the nutrition block.
    phrase = []
    for token in reversed(candidate_words):
        if re.search(r'^(?:BY|THE|AND|OF|FOR|AT|IN|ON|&|\.|:|,|\(|\))$', token, re.I):
            continue
        if re.search(r'^(?:ENERGY|PROTEIN|CARBOHYDRATE|TOTAL|FAT|SODIUM|ADDED|SUGARS|VALUES|APPROX|INFORMATION|PER|SERVE|INGREDIENTS|FLAVOUR|FLAVOR|OIL|SALT|POTATO|CHIPS|KCAL|G|MG|ML)$', token, re.I):
            continue
        phrase.append(token)
        if len(phrase) >= 6:
            break
    phrase = list(reversed(phrase))
    cleaned = re.sub(r'\s+', ' ', ' '.join(phrase)).strip(' .,:;')
    if len(cleaned.split()) >= 2 and re.search(r'[A-Za-z]', cleaned):
        return {'value': cleaned[:100], 'confidence': 'HIGH', 'evidence_text': cleaned}

    # Fallback: allow a short product title if it appears after nutrition and before declaration keywords.
    for idx, word in enumerate(words):
        text = _normalize_ocr_text(word.get('text', ''))
        if re.search(r'^(?:LAYS|LAY\'S|CLASSIC|SALTED|SUNRISE|ATTA|BASMATI|HONEY|CHIPS|POTATO|FRESH|GOLDEN|NATURE|ORANGE|COFFEE|TEA|RICE|OATS|BISCUITS|SOAP|SHAMPOO|DETERGENT|COSMETIC|BISCUIT)$', text, re.I):
            joined = []
            for j in range(idx, min(len(words), idx + 4)):
                token = _normalize_ocr_text(words[j].get('text', ''))
                if not token:
                    continue
                if re.search(r'^(?:NET|QTY|QUANTITY|MRP|BEST|BEFORE|USE|BY|MFD|COUNTRY|ORIGIN|CONSUMER|CARE|CALL|EMAIL|WWW|BATCH|LOT|PLOT)$', token, re.I):
                    break
                if re.fullmatch(r'\d+(?:\.\d+)?', token):
                    break
                if re.search(r'^(?:ENERGY|PROTEIN|CARBOHYDRATE|TOTAL|FAT|SODIUM|ADDED|SUGARS|VALUES|APPROX|INFORMATION|PER|SERVE|INGREDIENTS|FLAVOUR|FLAVOR|OIL|SALT|POTATO|CHIPS)$', token, re.I):
                    break
                joined.append(token)
            joined_text = re.sub(r'\s+', ' ', ' '.join(joined)).strip(' .,:;')
            if len(joined_text.split()) >= 2:
                return {'value': joined_text[:100], 'confidence': 'MEDIUM', 'evidence_text': joined_text}

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

"""
SMART-LM OCR Service
=====================
Primary: PaddleOCR
Fallback: pytesseract (Tesseract 5)

Returns a list of OCRWord dicts:
  { "text": str, "confidence": float, "bbox": [x1, y1, x2, y2] }

If both engines fail, returns a safe error dict — does NOT raise.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
import cv2

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine detection — import at module level so we know what is available
# ---------------------------------------------------------------------------

_PADDLE_AVAILABLE = False
_TESSERACT_AVAILABLE = False

try:
    from paddleocr import PaddleOCR as _PaddleOCR
    _PADDLE_AVAILABLE = True
    logger.info("PaddleOCR detected — will use as primary OCR engine.")
except ImportError:
    logger.warning("PaddleOCR not installed. Trying Tesseract fallback.")

if not _PADDLE_AVAILABLE:
    try:
        import pytesseract as _pytesseract
        from PIL import Image as _PILImage
        import os as _os
        
        # Windows-specific check for Tesseract installation if not in PATH
        if _os.name == 'nt':
            _possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                _os.path.expandvars(r'%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe')
            ]
            for _p in _possible_paths:
                if _os.path.exists(_p):
                    _pytesseract.pytesseract.tesseract_cmd = _p
                    break

        _TESSERACT_AVAILABLE = True
        logger.info("Tesseract (pytesseract) detected — will use as OCR engine.")
    except ImportError:
        logger.error(
            "Neither PaddleOCR nor pytesseract is installed. "
            "OCR will not function. Install one of them."
        )

# Lazy-initialised PaddleOCR instance (avoids slow model load at import time)
_paddle_instance: Optional[Any] = None


def _get_paddle() -> Any:
    global _paddle_instance
    if _paddle_instance is None:
        _paddle_instance = _PaddleOCR(
            use_angle_cls=True,
            lang="en",
            show_log=False,
        )
    return _paddle_instance


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_ocr(image_path: str) -> Dict[str, Any]:
    """
    Run OCR on the given image path.

    Returns dict matching OCRResult schema:
    {
        "words": [ {"text", "confidence", "bbox"}, ... ],
        "full_text": str,
        "engine": "paddleocr" | "tesseract" | "none",
        "success": bool,
        "error": str | None
    }
    """
    if _PADDLE_AVAILABLE:
        return _run_paddle(image_path)
    elif _TESSERACT_AVAILABLE:
        return _run_tesseract(image_path)
    else:
        return _no_engine_result()


# ---------------------------------------------------------------------------
# PaddleOCR implementation
# ---------------------------------------------------------------------------

def _run_paddle(image_path: str) -> Dict[str, Any]:
    try:
        ocr = _get_paddle()
        result = ocr.ocr(image_path, cls=True)

        words: List[Dict[str, Any]] = []

        if result is None or (len(result) == 1 and result[0] is None):
            return {
                "words": [],
                "full_text": "",
                "engine": "paddleocr",
                "success": True,
                "error": None,
            }

        for line_group in result:
            if line_group is None:
                continue
            for detection in line_group:
                # detection = [bbox_points, (text, confidence)]
                bbox_points, (text, confidence) = detection
                # Convert quad to [x1, y1, x2, y2] bounding box
                xs = [pt[0] for pt in bbox_points]
                ys = [pt[1] for pt in bbox_points]
                bbox = [min(xs), min(ys), max(xs), max(ys)]
                words.append({
                    "text": text.strip(),
                    "confidence": round(float(confidence), 4),
                    "bbox": [round(v, 1) for v in bbox],
                })

        full_text = " ".join(w["text"] for w in words)
        return {
            "words": words,
            "full_text": full_text,
            "engine": "paddleocr",
            "success": True,
            "error": None,
        }

    except Exception as exc:
        logger.error("PaddleOCR failed: %s", exc)
        # Try tesseract as secondary fallback
        if _TESSERACT_AVAILABLE:
            logger.info("Attempting Tesseract fallback after PaddleOCR failure.")
            result = _run_tesseract(image_path)
            result["engine"] = "tesseract-fallback"
            return result
        return {
            "words": [],
            "full_text": "",
            "engine": "paddleocr",
            "success": False,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Tesseract implementation
# ---------------------------------------------------------------------------

def _run_tesseract(image_path: str) -> Dict[str, Any]:
    try:
        img = _PILImage.open(image_path).convert("RGB")
        data = _pytesseract.image_to_data(
            img,
            output_type=_pytesseract.Output.DICT,
            config="--oem 3 --psm 3",
        )

        words: List[Dict[str, Any]] = []
        n = len(data["text"])
        for i in range(n):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])
            if not text or conf < 0:
                continue
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            words.append({
                "text": text,
                "confidence": round(conf / 100.0, 4),
                "bbox": [float(x), float(y), float(x + w), float(y + h)],
            })

        full_text = " ".join(w["text"] for w in words)
        return {
            "words": words,
            "full_text": full_text,
            "engine": "tesseract",
            "success": True,
            "error": None,
        }

    except Exception as exc:
        logger.error("Tesseract OCR failed: %s", exc)
        return {
            "words": [],
            "full_text": "",
            "engine": "tesseract",
            "success": False,
            "error": str(exc),
        }


def _no_engine_result() -> Dict[str, Any]:
    return {
        "words": [],
        "full_text": "",
        "engine": "none",
        "success": False,
        "error": (
            "No OCR engine available. "
            "Install paddleocr (pip install paddleocr paddlepaddle) "
            "or tesseract + pytesseract."
        ),
    }

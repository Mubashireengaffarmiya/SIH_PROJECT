"""
SMART-LM Image Processing Service
===================================
Loads, preprocesses, and scores image quality.
Returns quality metrics used downstream to decide if OCR is worth running.
"""

import logging
from typing import Dict, Any

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Quality thresholds
BLUR_THRESHOLD_POOR = 50.0        # Laplacian variance below this → too blurry
BLUR_THRESHOLD_ACCEPTABLE = 120.0  # Below this → acceptable
BRIGHTNESS_LOW = 50.0             # Mean pixel value below this → too dark
BRIGHTNESS_HIGH = 220.0           # Above this → overexposed
MAX_DIMENSION = 2048              # Resize long edge to this
MIN_READABLE_DIMENSION = 320


def load_and_preprocess(image_path: str) -> Dict[str, Any]:
    """
    Load an image from disk, preprocess it, and return quality metrics.

    Returns dict compatible with ImageQualityResult schema.
    """
    try:
        # Load via OpenCV
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            return _error_result("Could not load image. File may be corrupt or unsupported format.")

        original_h, original_w = img_bgr.shape[:2]

        # --- Resize if too large (preserve aspect ratio) ---
        img_bgr = _resize_image(img_bgr, MAX_DIMENSION)
        h, w = img_bgr.shape[:2]

        # --- Grayscale for analysis ---
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # --- Blur detection: Laplacian variance ---
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # --- Brightness: mean pixel value ---
        brightness = float(np.mean(gray))

        # --- Contrast: standard deviation of pixel values ---
        contrast = float(np.std(gray))

        # --- Decide quality ---
        quality, message = _assess_quality(blur_score, brightness, contrast)

        return {
            "quality": quality,
            "blur_score": round(blur_score, 2),
            "brightness": round(brightness, 2),
            "contrast": round(contrast, 2),
            "message": message,
            "width": w,
            "height": h,
            "_preprocessed_bgr": img_bgr,  # passed internally, not serialised
        }

    except Exception as exc:
        logger.error("Image processing error: %s", exc)
        return _error_result(f"Image processing failed: {str(exc)}")


def _resize_image(img: np.ndarray, max_dim: int) -> np.ndarray:
    """Resize so the longest edge is at most max_dim, preserving aspect ratio."""
    h, w = img.shape[:2]
    if max(h, w) <= max_dim:
        return img
    scale = max_dim / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def assess_quality(blur: float, brightness: float, contrast: float):
    """Return (quality_string, human_message) for a measured image."""
    issues = []

    if blur < BLUR_THRESHOLD_POOR:
        issues.append("Image is too blurry")
    if brightness < BRIGHTNESS_LOW:
        issues.append("Image is too dark")
    if brightness > BRIGHTNESS_HIGH:
        issues.append("Image is overexposed")
    if contrast < 15:
        issues.append("Image has very low contrast")

    if not issues:
        if blur < BLUR_THRESHOLD_ACCEPTABLE:
            return "ACCEPTABLE", "Image quality is acceptable but slightly blurry. Results may be less accurate."
        return "GOOD", "Image suitable for analysis."

    if blur < BLUR_THRESHOLD_POOR or brightness < BRIGHTNESS_LOW:
        return "DIFFICULT", " | ".join(issues) + ". Please retake the image for accurate results."
    return "ACCEPTABLE", " | ".join(issues) + ". Results may be less accurate."


def _assess_quality(blur_score: float, brightness: float, contrast: float):
    """Backward-compatible wrapper used by the existing app. Returns POOR for difficult cases."""
    quality, message = assess_quality(blur_score, brightness, contrast)
    if quality == "DIFFICULT":
        return "POOR", message
    return quality, message


def _ensure_3channel(image: np.ndarray) -> np.ndarray:
    if image is None or image.size == 0:
        return image
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image.copy()


def _resize_for_ocr(image: np.ndarray) -> np.ndarray:
    img = _ensure_3channel(image)
    h, w = img.shape[:2]
    max_dim = max(h, w)
    if max_dim < 1200:
        scale = 1.5
    elif max_dim > 2400:
        scale = 1800 / max_dim
    else:
        scale = 1.0
    if scale != 1.0:
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    return img


def _contrast_enhance(gray: np.ndarray) -> np.ndarray:
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def generate_preprocessed_variants(image: np.ndarray, force_enhanced: bool = False):
    """Create a compact set of OCR-friendly variants.

    Fast first-pass: original + grayscale + contrast + threshold
    Enhanced retry: adds sharpened and thresholded/deskew-style variants when needed.
    """
    if image is None or image.size == 0:
        return []

    base = _resize_for_ocr(image)
    variants = []
    variants.append({"name": "original", "image": base.copy()})

    gray = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY)
    variants.append({"name": "grayscale", "image": cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)})

    enhanced_gray = _contrast_enhance(gray)
    variants.append({"name": "contrast", "image": cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)})

    _, threshold = cv2.threshold(enhanced_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append({"name": "threshold", "image": cv2.cvtColor(threshold, cv2.COLOR_GRAY2BGR)})

    if force_enhanced:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        sharpened = cv2.filter2D(enhanced_gray, -1, kernel)
        variants.append({"name": "sharpened", "image": cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)})

        adaptive = cv2.adaptiveThreshold(
            enhanced_gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            10,
        )
        variants.append({"name": "adaptive_threshold", "image": cv2.cvtColor(adaptive, cv2.COLOR_GRAY2BGR)})

    return variants


def enhance_for_ocr(img_bgr: np.ndarray) -> np.ndarray:
    """
    Apply basic preprocessing to improve OCR accuracy:
    - Convert to grayscale
    - Adaptive histogram equalisation
    - Denoise
    Returns BGR image suitable for PaddleOCR / Tesseract.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    # Adaptive equalisation
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)
    # Mild denoise
    denoised = cv2.fastNlMeansDenoising(equalized, h=10)
    # Back to BGR so PaddleOCR is happy
    return cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)


def _error_result(message: str) -> Dict[str, Any]:
    return {
        "quality": "POOR",
        "blur_score": 0.0,
        "brightness": 0.0,
        "contrast": 0.0,
        "message": message,
        "width": 0,
        "height": 0,
        "_preprocessed_bgr": None,
    }


def quality_gate(quality_result: Dict[str, Any]) -> Dict[str, str]:
    """Describe whether missing fields can be treated as genuinely undetected."""
    width = int(quality_result.get("width", 0) or 0)
    height = int(quality_result.get("height", 0) or 0)
    quality = quality_result.get("quality", "POOR")
    if min(width, height) < MIN_READABLE_DIMENSION or quality == "POOR":
        return {
            "status": "NOT_VERIFIABLE",
            "message": quality_result.get("message", "Image quality is insufficient for reliable field extraction."),
        }
    return {"status": "READABLE", "message": quality_result.get("message", "Image quality is sufficient for field extraction.")}

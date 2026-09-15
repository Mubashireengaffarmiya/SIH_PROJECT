import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from services.image_processing import generate_preprocessed_variants, assess_quality
from services.ocr import run_ocr


def test_preprocessed_variants_are_generated_for_difficult_images():
    base = np.zeros((200, 200, 3), dtype=np.uint8)
    variants = generate_preprocessed_variants(base)
    assert len(variants) >= 3
    assert all(v["image"].shape[2] == 3 for v in variants)
    assert any(v["name"] in {"grayscale", "threshold", "sharpened"} for v in variants)


def test_assess_quality_can_report_difficult_and_acceptable():
    assert assess_quality(blur=5, brightness=20, contrast=8)[0] in {"POOR", "DIFFICULT"}
    assert assess_quality(blur=150, brightness=140, contrast=40)[0] in {"GOOD", "ACCEPTABLE"}


def test_run_ocr_returns_safe_error_when_no_engine_available(monkeypatch):
    monkeypatch.setattr("services.ocr._PADDLE_AVAILABLE", False)
    monkeypatch.setattr("services.ocr._TESSERACT_AVAILABLE", False)
    result = run_ocr("does_not_exist.jpg")
    assert result["success"] is False
    assert "error" in result

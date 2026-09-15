import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ocr import detect_tesseract, get_ocr_health


def test_detect_tesseract_returns_structure():
    info = detect_tesseract()
    assert isinstance(info, dict)
    assert "available" in info
    assert "engine" in info


def test_ocr_health_returns_status_data():
    health = get_ocr_health()
    assert isinstance(health, dict)
    assert "available" in health
    assert "engine" in health

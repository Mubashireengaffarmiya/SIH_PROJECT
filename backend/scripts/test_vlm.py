"""Run PaddleOCR-VL against one real upload without touching the database."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from ocr.vlm_engine import PaddleOCRVLEngine  # noqa: E402


def choose_image() -> Path:
    candidates = [
        path for path in (BACKEND_DIR / "uploads").rglob("*")
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    ]
    if not candidates:
        raise FileNotFoundError(f"No package image found in {BACKEND_DIR / 'uploads'}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def main() -> None:
    image = choose_image()
    output = PROJECT_DIR / "data" / "paddle_test_output" / "smartlm_vlm"
    print(f"Image: {image}")
    print(f"Output: {output}")
    result = PaddleOCRVLEngine(pipeline_version="v1.5").run(str(image), str(output))
    print(f"Status: {result['status']}")
    print(f"Engine: {result['engine']}")
    print(f"Pipeline: {result['pipeline_version']}")
    if result.get("error"):
        print(f"Error: {result['error']}")
    for name, field in result.get("fields", {}).items():
        print(f"\n{name}")
        print(f"  value: {field.get('value')}")
        print(f"  confidence: {field.get('confidence')}")
        print(f"  evidence: {field.get('evidence_text')}")
        print(f"  bounding_box: {field.get('bounding_box')}")
        print(f"  status: {field.get('status')}")
    print("\nRaw VLM blocks:")
    for block in result.get("blocks", []):
        print(f"  [{block.get('block_label')}] {block.get('block_content')}")


if __name__ == "__main__":
    main()
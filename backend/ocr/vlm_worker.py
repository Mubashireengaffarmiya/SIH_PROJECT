"""Subprocess worker used when FastAPI runs outside paddle_env."""

from __future__ import annotations

import json
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from paddleocr import PaddleOCRVL

from ocr.vlm_engine import _parse_blocks


def main() -> None:
    image_path = Path(sys.argv[1])
    pipeline_version = sys.argv[2] if len(sys.argv) > 2 else "v1.5"
    output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    with contextlib.redirect_stdout(sys.stderr):
        engine = PaddleOCRVL(
            pipeline_version=pipeline_version,
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_layout_detection=True,
            use_chart_recognition=False,
            use_seal_recognition=False,
            use_ocr_for_image_block=True,
        )
        result = next(iter(engine.predict(str(image_path), use_doc_orientation_classify=True, use_doc_unwarping=True)))
    payload = result.json if isinstance(result.json, dict) else json.loads(result.json)
    data = payload.get("res", payload)
    blocks = data.get("parsing_res_list", [])
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        with contextlib.redirect_stdout(sys.stderr):
            result.save_to_json(str(output_dir))
            result.save_to_img(str(output_dir))
            result.save_to_markdown(str(output_dir))
    response = {
        "status": "success",
        "engine": "paddleocr-vl",
        "pipeline_version": pipeline_version,
        "fields": _parse_blocks(blocks, str(image_path)),
        "source_image": str(image_path),
        "markdown": (result.markdown or {}).get("markdown_texts", "") if isinstance(result.markdown, dict) else "",
        "blocks": blocks,
        "error": None,
    }
    print(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    main()
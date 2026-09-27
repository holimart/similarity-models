"""Command-line entry point for repeatable local OCR runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .core import OCRConfig, config_dict, installed_versions, run_ocr


def image_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local OCR with selectable PaddleOCR or RapidOCR harness.")
    parser.add_argument("image", help="Path to an input image")
    parser.add_argument("--harness", choices=("paddleocr", "rapidocr"), default=None)
    parser.add_argument("--config", help="Optional JSON config; CLI options override file values")
    parser.add_argument("--output", help="Write result JSON to this path; defaults to stdout")
    parser.add_argument("--device", default=None, help="cpu, gpu:0, cuda:0, etc. Support depends on harness/backend")
    parser.add_argument("--lang", default=None, help="Recognition model language key, for example en or latin")
    parser.add_argument("--engine", default=None, help="Inference backend (RapidOCR: onnxruntime/openvino/paddle/torch/mnn/tensorrt; PaddleOCR: paddle_static/onnxruntime when supported)")
    parser.add_argument("--model-family", default=None, help="Model family label, e.g. PP-OCRv5")
    parser.add_argument("--model-size", default=None, help="mobile/server/tiny/small/medium (metadata label)")
    parser.add_argument("--det-limit-side-len", type=int, default=None)
    parser.add_argument("--det-limit-type", choices=("min", "max"), default=None)
    parser.add_argument("--det-thresh", type=float, default=None)
    parser.add_argument("--box-thresh", type=float, default=None)
    parser.add_argument("--unclip-ratio", type=float, default=None)
    parser.add_argument("--rec-score-thresh", type=float, default=None)
    parser.add_argument("--no-orientation", action="store_true", help="Disable text-line orientation classifier")
    parser.add_argument("--det-model-path", default=None)
    parser.add_argument("--rec-model-path", default=None)
    parser.add_argument("--cls-model-path", default=None)
    parser.add_argument("--rec-keys-path", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    image_path = Path(args.image).expanduser().resolve()
    if not image_path.is_file():
        raise SystemExit(f"Image not found: {image_path}")

    values: dict[str, Any] = {}
    if args.config:
        values = config_dict(OCRConfig.from_json(args.config))
    for key in ("harness", "device", "lang", "engine", "model_family", "model_size", "det_limit_side_len", "det_limit_type", "det_thresh", "box_thresh", "unclip_ratio", "rec_score_thresh", "det_model_path", "rec_model_path", "cls_model_path", "rec_keys_path"):
        value = getattr(args, key)
        if value is not None:
            values[key] = value
    if args.no_orientation:
        values["use_orientation"] = False
    config = OCRConfig(**values)

    started = time.perf_counter()
    records, backend_meta = run_ocr(image_path, config)
    wall_seconds = time.perf_counter() - started
    output = {
        "schema_version": 1,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "harness_version": __version__,
        "image": {"path": str(image_path), "sha256": image_sha256(image_path), "bytes": image_path.stat().st_size},
        "config": config_dict(config),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": installed_versions(),
            "wall_seconds_including_initialization": wall_seconds,
            **backend_meta,
        },
        "text_instances": records,
    }
    serialized = json.dumps(output, ensure_ascii=False, indent=2, default=str)
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

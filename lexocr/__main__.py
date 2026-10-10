"""CLI entry point for ``python -m lexocr``.

    python -m lexocr batch --batch-dir DIR --output FILE [--device cpu|cuda]
                           [--workers N] [--dpi 200] [--max-seconds S] [--min-chars 200]
    python -m lexocr probe
"""

from __future__ import annotations

import argparse
import json
import sys

from .batch import run_batch
from .engine import cuda_available, ocr_available


def _providers() -> list[str]:
    try:
        import onnxruntime as ort

        return list(ort.get_available_providers())
    except Exception:
        return []


def _cmd_probe(_args: argparse.Namespace) -> int:
    report = {
        "ocr_available": ocr_available(),
        "cuda_available": cuda_available(),
        "providers": _providers(),
    }
    print(json.dumps(report, indent=2))
    return 0


def _cmd_batch(args: argparse.Namespace) -> int:
    stats = run_batch(
        args.batch_dir,
        args.output,
        device=args.device,
        dpi=args.dpi,
        max_seconds=args.max_seconds,
        min_chars=args.min_chars,
        workers=args.workers,
    )
    print(json.dumps(stats, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lexocr", description="Legal PDF OCR")
    sub = parser.add_subparsers(dest="command", required=True)

    batch = sub.add_parser("batch", help="OCR every *.pdf in a directory -> JSONL")
    batch.add_argument("--batch-dir", required=True, help="directory containing *.pdf files")
    batch.add_argument("--output", required=True, help="output JSONL path")
    batch.add_argument("--device", default="cpu", help="cpu or cuda[:N] (default: cpu)")
    batch.add_argument("--workers", type=int, default=1, help="process pool size (CPU only)")
    batch.add_argument("--dpi", type=int, default=200, help="render DPI hint (default: 200)")
    batch.add_argument(
        "--max-seconds", type=int, default=0, help="stop early after N seconds (0 = no limit)"
    )
    batch.add_argument("--min-chars", type=int, default=200, help="readability min chars")
    batch.set_defaults(func=_cmd_batch)

    probe = sub.add_parser("probe", help="print OCR/CUDA availability and providers")
    probe.set_defaults(func=_cmd_probe)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

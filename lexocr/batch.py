"""Batch OCR over a directory of legal PDFs.

Every ``*.pdf`` in ``batch_dir`` is OCR'd (filename stem == ``source_id``) and
written as one JSON object per line to ``output``. Designed for the remote/HPC
"10-minute budget" flow: ``max_seconds`` stops the run early and leaves whatever
was already written in place.

The process pool accepts only CPU work; ``device="cuda"`` forces a single worker
because a CUDA engine is not safe to share across forked processes on all setups.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .engine import is_readable, pdf_to_text_from_path


def _process_one(path: str, device: str, min_chars: int) -> dict[str, Any]:
    """OCR a single PDF into a JSONL record. Never raises."""
    stem = Path(path).stem
    try:
        result = pdf_to_text_from_path(path, ocr=True, device=device)
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "source_id": stem,
            "text": "",
            "pages": 0,
            "ocr_pages": 0,
            "used_ocr": False,
            "dpi": 0,
            "device": device,
            "readable": False,
            "reason": f"error: {exc}",
            "chars": 0,
        }

    report = is_readable(result.text, min_chars=min_chars)
    return {
        "source_id": stem,
        "text": result.text,
        "pages": result.pages,
        "ocr_pages": result.ocr_pages,
        "used_ocr": result.used_ocr,
        "dpi": result.dpi,
        "device": device,
        "readable": report.readable,
        "reason": report.reason,
        "chars": report.chars,
    }


def _pdfs(batch_dir: Path) -> list[Path]:
    if not batch_dir.is_dir():
        return []
    return sorted(p for p in batch_dir.iterdir() if p.suffix.lower() == ".pdf")


def run_batch(
    batch_dir,
    output,
    *,
    device: str = "cpu",
    dpi: int = 200,
    max_seconds: int = 0,
    min_chars: int = 200,
    workers: int = 1,
) -> dict[str, int]:
    """OCR every ``*.pdf`` in ``batch_dir`` (stem == source_id) -> JSONL.

    Each line: ``{"source_id","text","pages","ocr_pages","used_ocr","dpi",
    "device","readable","reason","chars"}``.
    ``max_seconds`` > 0 stops early (10-minute HPC budget). ``workers`` > 1 uses a
    process pool (CPU only); ``device="cuda"`` forces ``workers=1``.
    Returns ``{"documents","readable","ocr_pages"}``.
    """
    batch_path = Path(batch_dir)
    output_path = Path(output)
    pdfs = _pdfs(batch_path)

    if device.startswith("cuda"):
        workers = 1

    stats = {"documents": 0, "readable": 0, "ocr_pages": 0}
    deadline = time.monotonic() + max_seconds if max_seconds and max_seconds > 0 else None

    def _emit(lines, fh):
        for line in lines:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
            stats["documents"] += 1
            stats["ocr_pages"] += int(line.get("ocr_pages", 0))
            if line.get("readable"):
                stats["readable"] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        if workers > 1 and pdfs:
            import concurrent.futures

            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(_process_one, str(p), device, min_chars): p for p in pdfs
                }
                for future in concurrent.futures.as_completed(futures):
                    if deadline is not None and time.monotonic() >= deadline:
                        for f in futures:
                            f.cancel()
                        break
                    try:
                        _emit([future.result()], fh)
                    except Exception:  # pragma: no cover - defensive
                        _emit([_process_one(str(futures[future]), device, min_chars)], fh)
        else:
            for pdf in pdfs:
                if deadline is not None and time.monotonic() >= deadline:
                    break
                _emit([_process_one(str(pdf), device, min_chars)], fh)

    return stats

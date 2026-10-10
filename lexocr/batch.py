"""Batch OCR over a directory of legal PDFs.

Every ``*.pdf`` in ``batch_dir`` is OCR'd (filename stem == ``source_id``) and
written as one JSON object per line to ``output``. Designed for the remote/HPC
"10-minute budget" flow: ``max_seconds`` stops the run early and leaves whatever
was already written in place.

CPU uses a **process pool** (independent onnxruntime instances). GPU uses a
**page-level render/OCR pipeline**: a small pool of render threads decodes pages
to BGR arrays (no PNG round-trip) and feeds a bounded queue consumed by several
OCR threads sharing one RapidOCR engine. A single OCR call is CPU-bound in
RapidOCR's Python/OpenCV pre/post, so filling the GPU with concurrent calls
scales throughput several-fold (measured ~1.2 -> ~5 pages/s, GPU-bound, on one
L40S with 8 cores).
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
from pathlib import Path
from typing import Any

from .engine import _ocr_image, _page_to_numpy, is_readable, pdf_to_text_from_path


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


def _default_workers(device: str) -> int:
    """Concurrent OCR consumers: a few per GPU, one per CPU core otherwise."""
    if device.startswith("cuda"):
        # A single RapidOCR call underuses the GPU; run several per card.
        return 8
    return max(1, min(8, os.cpu_count() or 2))


def _record(
    stem: str, device: str, text: str, pages: int, ocr_pages: int, dpi: int, min_chars: int
) -> dict[str, Any]:
    report = is_readable(text, min_chars=min_chars)
    return {
        "source_id": stem,
        "text": text,
        "pages": pages,
        "ocr_pages": ocr_pages,
        "used_ocr": True,
        "dpi": dpi,
        "device": device,
        "readable": report.readable,
        "reason": report.reason,
        "chars": report.chars,
    }


def _run_gpu(
    pdfs: list[Path],
    device: str,
    dpi: int,
    deadline: float | None,
    min_chars: int,
    workers: int,
    emit,
) -> None:
    """OCR a batch on one GPU with a page-level render/OCR pipeline.

    Rendering (JPEG-2000 decode + scale, CPU) runs on a small pool of producer
    threads; OCR runs on ``workers`` consumer threads sharing one RapidOCR
    engine. A single OCR call is CPU-bound in RapidOCR's Python/OpenCV pre/post,
    so several in flight fill the GPU. Pages feed a bounded queue, so rendering
    is hidden behind inference and pages from many documents (or one big
    document) OCR in parallel.
    """
    import pymupdf

    from .engine import get_engine

    render_workers = max(1, min(2, workers))

    # Discover documents and flatten to page tasks.
    tasks: list[tuple[str, str, int]] = []
    empty: list[tuple[str, str]] = []
    for path in pdfs:
        stem = path.stem
        try:
            doc = pymupdf.open(str(path))
            n = doc.page_count
            doc.close()
        except Exception:
            n = 0
        if n <= 0:
            empty.append((stem, str(path)))
            continue
        tasks += [(stem, str(path), i) for i in range(n)]

    # Documents with no readable pages still yield a record.
    for stem, path in empty:
        emit([_process_one(path, device, min_chars)])

    if not tasks:
        return

    get_engine(device)  # warm once, shared by all consumers
    q: queue.Queue[Any] = queue.Queue(maxsize=max(2, render_workers * 4))
    sentinel = object()
    index = {"i": 0}
    index_lock = threading.Lock()

    parts: dict[str, list[tuple[int, str]]] = {}
    remaining: dict[str, int] = {}
    counts: dict[str, int] = {}
    for stem, _path, _pi in tasks:
        counts[stem] = counts.get(stem, 0) + 1
    remaining.update(counts)

    def render() -> None:
        handles: dict[str, Any] = {}
        while True:
            with index_lock:
                i = index["i"]
                if i >= len(tasks):
                    return
                index["i"] = i + 1
            stem, path, pi = tasks[i]
            if deadline is not None and time.monotonic() >= deadline:
                continue
            doc = handles.get(path)
            if doc is None:
                try:
                    doc = pymupdf.open(path)
                except Exception:
                    doc = None
                handles[path] = doc
            arr = None
            if doc is not None:
                try:
                    arr = _page_to_numpy(doc[pi], dpi)
                except Exception:
                    arr = None
            q.put((stem, pi, arr))

    def consume() -> None:
        while True:
            item = q.get()
            if item is sentinel:
                return
            stem, pi, arr = item
            try:
                text = _ocr_image(arr, device) if arr is not None else ""
            except Exception:
                text = ""
            with index_lock:
                parts.setdefault(stem, []).append((pi, text))
                remaining[stem] -= 1
                if remaining[stem] > 0:
                    continue
                done = sorted(parts.pop(stem))
            ocr_pages = sum(1 for _pi, t in done if t.strip())
            full = "\n\n".join(t.strip() for _pi, t in done if t.strip())
            emit([_record(stem, device, full, counts[stem], ocr_pages, dpi, min_chars)])

    renderers = [
        threading.Thread(target=render, name=f"lexocr-render{i}") for i in range(render_workers)
    ]
    consumers = [threading.Thread(target=consume, name=f"lexocr-ocr{i}") for i in range(workers)]
    for t in renderers:
        t.start()
    for t in consumers:
        t.start()
    for t in renderers:
        t.join()
    for _ in consumers:
        q.put(sentinel)
    for t in consumers:
        t.join()


def run_batch(
    batch_dir,
    output,
    *,
    device: str = "cpu",
    dpi: int = 200,
    max_seconds: int = 0,
    min_chars: int = 200,
    workers: int = 0,
) -> dict[str, int]:
    """OCR every ``*.pdf`` in ``batch_dir`` (stem == source_id) -> JSONL.

    Each line: ``{"source_id","text","pages","ocr_pages","used_ocr","dpi",
    "device","readable","reason","chars"}``.
    ``max_seconds`` > 0 stops early (10-minute HPC budget). ``workers=0`` picks a
    sensible default (8 for GPU, CPU count for CPU). CPU runs a process pool;
    GPU runs a page-level render/OCR pipeline sharing one engine.
    """
    batch_path = Path(batch_dir)
    output_path = Path(output)
    pdfs = _pdfs(batch_path)

    if workers <= 0:
        workers = _default_workers(device)
    is_gpu = device.startswith("cuda")

    stats = {"documents": 0, "readable": 0, "ocr_pages": 0}
    deadline = time.monotonic() + max_seconds if max_seconds and max_seconds > 0 else None

    def _emit(lines, fh):
        for line in lines:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
            fh.flush()
            stats["documents"] += 1
            stats["ocr_pages"] += int(line.get("ocr_pages", 0))
            if line.get("readable"):
                stats["readable"] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        emit_lock = threading.Lock()

        def _emit(lines) -> None:
            with emit_lock:
                for line in lines:
                    fh.write(json.dumps(line, ensure_ascii=False) + "\n")
                    stats["documents"] += 1
                    stats["ocr_pages"] += int(line.get("ocr_pages", 0))
                    if line.get("readable"):
                        stats["readable"] += 1
                fh.flush()

        if is_gpu and pdfs:
            _run_gpu(pdfs, device, dpi, deadline, min_chars, max(1, workers), _emit)
        elif workers > 1 and pdfs:
            import concurrent.futures

            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(_process_one, str(p), device, min_chars): p for p in pdfs}
                for future in concurrent.futures.as_completed(futures):
                    if deadline is not None and time.monotonic() >= deadline:
                        for f in futures:
                            f.cancel()
                        break
                    try:
                        _emit([future.result()])
                    except Exception:  # pragma: no cover - defensive
                        _emit([_process_one(str(futures[future]), device, min_chars)])
        else:
            for pdf in pdfs:
                if deadline is not None and time.monotonic() >= deadline:
                    break
                _emit([_process_one(str(pdf), device, min_chars)])

    return stats

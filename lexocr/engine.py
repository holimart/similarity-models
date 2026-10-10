"""Legal PDF OCR engine: text-layer extraction with a RapidOCR fallback.

Many court/legislation PDFs are pure page scans with no text layer. This module
renders each page with PyMuPDF and recognizes it with RapidOCR (PP-OCRv6, ONNX
Runtime), reusing a single engine per process.

Public entry point is :func:`pdf_to_text`, which:

1. tries the embedded text layer first;
2. falls back to OCR page-by-page when the layer is missing/thin;
3. verifies the result with :func:`is_readable` and escalates render DPI until
   the text looks like real language (or the attempt budget is exhausted).

OCR is optional: if RapidOCR is not installed, text-layer extraction still works
and image-only PDFs are reported as unavailable (``skip``) rather than crashing.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --- Readability heuristic -------------------------------------------------

_CZ_LETTER_RE = re.compile(r"[a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]")
_WORD_RE = re.compile(r"[A-Za-zÁ-Ža-zá-ž]{2,}")
_DIACRITIC_RE = re.compile(r"[áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]")

MIN_TEXT_CHARS = 200


@dataclass
class ReadabilityReport:
    readable: bool
    chars: int
    letter_ratio: float
    word_ratio: float
    diacritic_ratio: float
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "readable": self.readable,
            "chars": self.chars,
            "letter_ratio": round(self.letter_ratio, 3),
            "word_ratio": round(self.word_ratio, 3),
            "diacritic_ratio": round(self.diacritic_ratio, 3),
            "reason": self.reason,
        }


def is_readable(text: str, *, min_chars: int = MIN_TEXT_CHARS) -> ReadabilityReport:
    """Heuristically decide whether OCR output looks like real text.

    Signals: enough characters, a high proportion of letters, a high proportion
    of word-like tokens, and (softly) some Czech diacritics for Czech documents.
    """
    stripped = (text or "").strip()
    chars = len(stripped)
    if chars < min_chars:
        return ReadabilityReport(False, chars, 0.0, 0.0, 0.0, f"too short ({chars}<{min_chars})")

    sample = stripped[:20000]
    letters = len(_CZ_LETTER_RE.findall(sample))
    letter_ratio = letters / len(sample)
    tokens = sample.split()
    words = _WORD_RE.findall(sample)
    word_ratio = len(words) / max(1, len(tokens))
    diacritics = len(_DIACRITIC_RE.findall(sample))
    diacritic_ratio = diacritics / max(1, letters)

    if letter_ratio < 0.5:
        return ReadabilityReport(
            False,
            chars,
            letter_ratio,
            word_ratio,
            diacritic_ratio,
            f"low letter ratio ({letter_ratio:.2f})",
        )
    if word_ratio < 0.5:
        return ReadabilityReport(
            False,
            chars,
            letter_ratio,
            word_ratio,
            diacritic_ratio,
            f"low word ratio ({word_ratio:.2f})",
        )
    return ReadabilityReport(True, chars, letter_ratio, word_ratio, diacritic_ratio, "ok")


# --- OCR engine (lazy, one per process) ------------------------------------

_ENGINES: dict[str, Any] = {}
_ENGINE_FAILED = False


def ocr_available() -> bool:
    """True if RapidOCR can be imported in this environment."""
    global _ENGINE_FAILED
    if _ENGINES:
        return True
    if _ENGINE_FAILED:
        return False
    try:
        import rapidocr  # noqa: F401
    except Exception:
        _ENGINE_FAILED = True
        return False
    return True


def cuda_available() -> bool:
    """True if onnxruntime reports a usable CUDA execution provider."""
    try:
        import onnxruntime as ort

        if "CUDAExecutionProvider" not in ort.get_available_providers():
            return False
        # A GPU device must actually be present (provider list alone isn't enough).
        try:
            import subprocess

            subprocess.run(["nvidia-smi", "-L"], capture_output=True, check=True, timeout=15)
        except Exception:
            return False
        return True
    except Exception:
        return False


def ensure_cuda_libs() -> None:
    """Put pip-installed ``nvidia-*-cu12`` lib dirs on ``LD_LIBRARY_PATH``.

    RapidOCR's onnxruntime dlopens libcudnn/libcublas at inference time; when the
    CUDA/cuDNN wheels are installed via pip (rather than system modules) their
    directories must be on the loader path. Harmless if nothing is found.
    """
    import site

    libs: list[str] = []
    for sp in site.getsitepackages():
        nvidia = Path(sp) / "nvidia"
        if nvidia.is_dir():
            libs.extend(str(p) for p in sorted(nvidia.glob("*/lib")))
    if libs:
        existing = os.environ.get("LD_LIBRARY_PATH", "")
        os.environ["LD_LIBRARY_PATH"] = ":".join(libs + ([existing] if existing else []))


def get_engine(device: str = "cpu") -> Any:
    """Return a process-wide RapidOCR engine for ``device`` (cpu or cuda[:N])."""
    global _ENGINE_FAILED
    key = "cuda" if device.startswith("cuda") else "cpu"
    if key in _ENGINES:
        return _ENGINES[key]
    try:
        from rapidocr import RapidOCR
    except Exception as exc:  # pragma: no cover - optional dependency
        _ENGINE_FAILED = True
        raise RuntimeError("RapidOCR is not installed; OCR unavailable") from exc

    params: dict[str, Any] = {"Global.log_level": "error"}
    if key == "cuda":
        ensure_cuda_libs()
        params["EngineConfig.onnxruntime.use_cuda"] = True
        if ":" in device:
            params["EngineConfig.onnxruntime.cuda_ep_cfg.device_id"] = int(device.split(":", 1)[1])
    else:
        # Bound CPU threads to the configured worker budget.
        threads = int(os.environ.get("OCR_CPU_THREADS", "2") or "2")
        params["EngineConfig.onnxruntime.intra_op_num_threads"] = threads
    _ENGINES[key] = RapidOCR(params=params)
    return _ENGINES[key]


def _ocr_image(image_bytes: bytes, device: str = "cpu") -> str:
    """Recognize one rendered page; return its text (lines joined)."""
    engine = get_engine(device)
    result = engine(image_bytes)
    texts = getattr(result, "txts", None) or []
    return "\n".join(t for t in texts if t and t.strip())


# --- PDF processing --------------------------------------------------------


@dataclass
class PdfTextResult:
    text: str
    pages: int
    ocr_pages: int
    used_ocr: bool
    dpi: int
    readability: ReadabilityReport
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pages": self.pages,
            "ocr_pages": self.ocr_pages,
            "used_ocr": self.used_ocr,
            "dpi": self.dpi,
            "readability": self.readability.to_dict(),
            **self.meta,
        }


def _open_pdf(data: bytes):
    import pymupdf

    return pymupdf.open(stream=data, filetype="pdf")


def _text_layer(doc) -> str:
    parts: list[str] = []
    for page in doc:
        try:
            t = page.get_text("text")
        except Exception:
            t = ""
        if t and t.strip():
            parts.append(t.strip())
    return "\n\n".join(parts)


def _ocr_pages(doc, dpi: int, device: str = "cpu") -> tuple[str, int]:
    parts: list[str] = []
    ocr_pages = 0
    for page in doc:
        try:
            pix = page.get_pixmap(dpi=dpi)
            image_bytes = pix.tobytes("png")
        except Exception:
            continue
        try:
            text = _ocr_image(image_bytes, device)
        except Exception:
            text = ""
        if text.strip():
            parts.append(text.strip())
            ocr_pages += 1
    return "\n\n".join(parts), ocr_pages


def pdf_to_text(data: bytes, *, ocr: bool = True, device: str = "cpu") -> PdfTextResult:
    """Extract text from PDF bytes, using OCR only when the text layer is thin.

    Escalates DPI (200 → 300) while the result is unreadable, so slightly rough
    scans still produce usable text. Never raises for unreadable content; callers
    inspect ``readability`` / ``text``.
    """
    try:
        doc = _open_pdf(data)
    except Exception as exc:
        return PdfTextResult(
            "", 0, 0, False, 0, ReadabilityReport(False, 0, 0, 0, 0, f"open failed: {exc}")
        )

    pages = doc.page_count
    if pages == 0:
        doc.close()
        return PdfTextResult("", 0, 0, False, 0, ReadabilityReport(False, 0, 0, 0, 0, "empty pdf"))

    text = _text_layer(doc)
    report = is_readable(text)
    if report.readable or not ocr or not ocr_available():
        doc.close()
        return PdfTextResult(
            text,
            pages,
            0,
            False,
            0,
            report,
            {"note": "" if ocr else "ocr disabled"},
        )

    # Text layer insufficient → OCR, escalating DPI until readable.
    best_text = text
    best_report = report
    used_dpi = 0
    ocr_pages = 0
    for dpi in (200, 300):
        ocr_text, n = _ocr_pages(doc, dpi, device)
        if ocr_text.strip():
            r = is_readable(ocr_text)
            # Keep the longest/readable OCR result.
            if r.readable or not best_report.readable:
                best_text, best_report, used_dpi, ocr_pages = ocr_text, r, dpi, n
            if r.readable:
                break
    doc.close()
    return PdfTextResult(best_text, pages, ocr_pages, True, used_dpi, best_report)


def pdf_to_text_from_path(path: str, *, ocr: bool = True, device: str = "cpu") -> PdfTextResult:
    with open(path, "rb") as fh:
        return pdf_to_text(fh.read(), ocr=ocr, device=device)


def ocr_page_image(  # pragma: no cover
    image_bytes: bytes, dpi: int = 200, device: str = "cpu"
) -> str:
    """OCR a standalone image (used by tests/tools)."""
    return _ocr_image(image_bytes, device)

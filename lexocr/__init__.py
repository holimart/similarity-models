"""lexocr — legal PDF OCR (text-layer + RapidOCR fallback) for Lawy.

Public API (frozen; Lawy and the remote run-cmd depend on these exact names)::

    from lexocr import (
        ReadabilityReport, PdfTextResult,
        is_readable, pdf_to_text, pdf_to_text_from_path,
        ocr_available, cuda_available, ensure_cuda_libs,
        run_batch,
    )
"""

from .batch import run_batch
from .engine import (
    PdfTextResult,
    ReadabilityReport,
    cuda_available,
    ensure_cuda_libs,
    is_readable,
    ocr_available,
    pdf_to_text,
    pdf_to_text_from_path,
)

__all__ = [
    "ReadabilityReport",
    "PdfTextResult",
    "is_readable",
    "pdf_to_text",
    "pdf_to_text_from_path",
    "ocr_available",
    "cuda_available",
    "ensure_cuda_libs",
    "run_batch",
]

__version__ = "0.1.0"

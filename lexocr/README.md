# lexocr — legal PDF OCR

`lexocr` extracts text from legal PDFs. It reads the embedded text layer with
[PyMuPDF](https://pymupdf.readthedocs.io/) first and only falls back to
[RapidOCR](https://github.com/RapidAI/RapidOCR) (PP-OCRv6 via ONNX Runtime) for
pages that are scans / image-only. Rendered pages are OCR'd at 200 dpi, then
300 dpi, keeping the first readable result.

This package is a thin dependency of the Lawy project; it is generic and
contains **no cluster-, host- or user-specific values** — every remote value is
a parameter.

## Install

```bash
# CPU (default usage)
uv pip install ".[cpu]"          # or: pip install ".[cpu]"
# GPU (onnxruntime-gpu; CUDA EP selected with --device cuda)
uv pip install ".[gpu]"
# core only (text layer, no OCR)
uv pip install .
```

## Python API (frozen)

```python
from lexocr import (
    ReadabilityReport, PdfTextResult,
    is_readable, pdf_to_text, pdf_to_text_from_path,
    ocr_available, cuda_available, ensure_cuda_libs,
    run_batch,
)

res = pdf_to_text_from_path("scan.pdf", ocr=True, device="cpu")
print(res.readability.to_dict(), res.pages, res.ocr_pages)

stats = run_batch("batch-dir", "out.jsonl", device="cuda", workers=1, max_seconds=600)
print(stats)  # {"documents": ..., "readable": ..., "ocr_pages": ...}
```

- `is_readable(text, *, min_chars=200)` — heuristic: length, letter ratio and
  word ratio over the first 20000 chars.
- `pdf_to_text(data, *, ocr=True, device="cpu")` / `pdf_to_text_from_path(path, ...)`.
- `device="cuda"` (or `cuda:N`) calls `ensure_cuda_libs()` and selects the
  onnxruntime CUDA EP; `"cpu"` bounds intra-op threads via `OCR_CPU_THREADS`
  (default 2). One engine is cached per process.

## CLI

```bash
python -m lexocr probe
python -m lexocr batch --batch-dir DIR --output out.jsonl \
    [--device cpu|cuda] [--workers N] [--dpi 200] [--max-seconds S] [--min-chars 200]
```

`probe` prints `ocr_available`, `cuda_available` and the available ONNX Runtime
providers. `batch` OCRs every `*.pdf` in `--batch-dir` (filename stem is the
`source_id`) and writes one JSON object per line:

```json
{"source_id":"12345","text":"...","pages":4,"ocr_pages":4,"used_ocr":true,
 "dpi":200,"device":"cpu","readable":true,"reason":"ok","chars":5231}
```

`--max-seconds > 0` stops early and leaves whatever was already written — useful
for fixed compute budgets. `--workers > 1` uses a process pool (CPU only);
`--device cuda` forces a single worker.

## Remote / batch setup

`setup_remote.sh` builds a self-contained venv **inside a parameterized
workspace** (never `$HOME`):

```bash
LEXOCR_WORKSPACE=/path/to/workspace \
LEXOCR_SRC=/path/to/lexocr \
    bash lexocr/setup_remote.sh /path/to/workspace python3 --cpu
# or: setup_remote.sh WORKSPACE [PYTHON] [--cpu]
```

It creates `$WORKSPACE/venv-ocr`, installs `rapidocr`, `onnxruntime-gpu` (or
`onnxruntime` with `--cpu`), `pymupdf`, and, if `LEXOCR_SRC` is set, this
package. It uses `uv` when available and falls back to `python -m pip`, and is
idempotent.

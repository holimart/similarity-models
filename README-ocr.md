# Local OCR lab

The `ocr_lab` package is a small, offline-friendly test harness for running one image through either PaddleOCR 3.x or RapidOCR 3.x. It writes normalized word/line polygons, recognized strings and confidences together with a config and image hash. It is intentionally separate from the repository's legacy TensorFlow/Keras environment.

## Setup

Use Python 3.10+ in a virtual environment. Install CPU OCR support with `python -m pip install -r requirements-ocr.txt`. For a GPU setup, replace the CPU PaddlePaddle package with the wheel matching the machine's CUDA/driver using PaddlePaddle's official installation selector; RapidOCR acceleration depends on the selected backend's GPU runtime (for example `onnxruntime-gpu` for ONNX Runtime CUDA).

Model weights are downloaded by the selected OCR package on first use unless explicit local model paths are supplied. Pre-download them before operating offline. PaddleOCR stores pipeline model files under `~/.paddlex/official_models`; RapidOCR includes its default ONNX models with the installed package. `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` skips PaddleX's host connectivity check, but does not substitute for downloading any missing weights. Every output records package versions and image hash; keep the selected model artifacts and config alongside the outputs for exact reproduction.

Dataset paths are read from `DATASETS_ROOT` in `.env` (or the process environment). The local workspace is `/mnt/sportsmarket/datasets`; `COCO_ROOT` remains pointed at its `coco2017/` child. Python commands load `.env` directly. To use the same paths in shell command arguments, load the file first:

```bash
set -a
. ./.env
set +a
```

The workspace is organized into `source/` (downloaded datasets), `derived/` (exports), `manual/` (local annotations), and `coco2017/` (the existing COCO benchmark copy). These local datasets and manual labels remain outside the repository and are not redistributed by this code.

## Run

```bash
python -m ocr_lab path/to/receipt.jpg --harness rapidocr --config ocr_lab/configs/rapidocr_cpu.json --output runs/receipt-rapid.json
python -m ocr_lab path/to/receipt.jpg --harness paddleocr --config ocr_lab/configs/paddleocr_cpu.json --output runs/receipt-paddle.json
```

The checked-in `rapidocr_cpu.json` selects PP-OCRv6 small, ONNX Runtime CPU, and Czech language configuration (PP-OCRv6 uses one multilingual recognizer). For a functional paired comparison on one image, use the same file with both harnesses. For a dataset run, the evaluator reuses a loaded engine, performs an optional warmup, writes per-image JSONL, and calculates CER/WER against CORD's word transcripts:

```bash
python -m ocr_lab.evaluate --config ocr_lab/configs/rapidocr_cpu_no_orientation.json --output runs/cord-rapid.jsonl
python -m ocr_lab.evaluate --config ocr_lab/configs/paddleocr_cpu.json --output runs/cord-paddle.jsonl
python -m ocr_lab.evaluate --labels "$DATASETS_ROOT/derived/textzoom/test_export/labels.jsonl" --resolution lr --limit 100 --output runs/textzoom-lr-rapid.jsonl
python -m ocr_lab.evaluate --harness paddleocr --config ocr_lab/configs/paddleocr_cpu.json --labels "$DATASETS_ROOT/derived/textzoom/test_export/labels.jsonl" --resolution lr --limit 100 --output runs/textzoom-lr-paddle.jsonl
```

CORD is Indonesian, so its scores are only a pipeline smoke-test / cross-system comparison—not Czech quality estimates. TextZoom supplies single-word crops (real low-resolution camera captures plus high-resolution references), so `--resolution lr` / `hr` compares recognition through the full OCR pipeline. These local CER/WER summaries are diagnostic: inspect paired predictions and use official benchmark evaluation for formal claims.

### Reading the reported metrics

- **CER (character error rate)** = Levenshtein character edits (substitutions + deletions + insertions) ÷ number of normalized reference characters.
- **WER (word error rate)** = Levenshtein word edits ÷ number of normalized reference words.
- ASCII-fold scoring is now the default: case is ignored, punctuation/symbols are removed, and decomposable Latin diacritics are reduced to their base letters (`ř` → `r`). Other scripts are retained. Each output also includes case-sensitive and case-insensitive-only scores for comparison. Insertions mean CER/WER can exceed 1 (100%). Dataset totals are micro-averaged: total edits divided by total normalized reference characters/words, not a mean of image scores. Use `--normalization case-sensitive` or `--normalization case-insensitive` for alternate modes; `python -m ocr_lab.rescore` recalculates saved outputs without rerunning inference.
- ASCII-fold is a general text-OCR score only. Do **not** use it to judge monetary fields: removing decimal/thousands separators could make different amounts appear equal. Total extraction needs a separate locale-aware currency/decimal metric.
- `wall_seconds_per_image_p50` is the median wall time of an OCR call after one optional warm-up; model initialization is excluded. `wall_seconds_total` sums those measured calls. A one-image CLI run separately reports total wall time including model initialization.

Available options include device/backend, language, model family/size metadata, detector resize side/type, detector and box thresholds, unclip ratio, recognition score cutoff, orientation classification, and local model paths. Runtime argument compatibility changes between package versions; pin versions and use `--help` plus official docs if a parameter is rejected. The harness reports total wall time including model initialization, so run repeated calls in one process for meaningful steady-state timing in a future benchmark command; this initial CLI is for functional smoke tests.

## Datasets

Datasets are stored under `$DATASETS_ROOT`, outside the source tree. Local copies include 200 CORD-v2 receipts, the TextZoom test split, the 626-record corrected SROIE mirror subset, 350 XFUND validation forms, and COCO 2017. CORD is Indonesian—not Czech—and states CC BY 4.0; TextZoom has no clear dataset-specific redistribution license; the SROIE mirror MIT license does not clearly cover receipt images and this copy is local-only; XFUND states CC BY-NC-SA 4.0. Review each source's terms before reuse/redistribution. See `reports/Czech receipt OCR datasets.md` for research notes. Keep authorized Czech receipt photos in a separate local test set and do not commit them.

The official TextZoom test split (scene-text word crops, not receipts) can be downloaded and exported for recognition smoke tests:

```bash
python scripts/download_textzoom_test.py
python scripts/export_textzoom_test.py --resolution both
```

The upstream TextZoom repository links the LMDBs but does not state a clear dataset redistribution license; this is a private local evaluation copy. The exported crops and labels are also ignored by git.

The SROIE participant mirror's publicly accessible corrected `data/` subset can also be downloaded and converted into the harness manifest:

```bash
python scripts/download_sroie_mirror.py
python scripts/export_sroie.py
python -m ocr_lab.evaluate --labels "$DATASETS_ROOT/source/sroie-mirror/labels.jsonl" --limit 100 --config ocr_lab/configs/rapidocr_cpu_no_orientation.json --output runs/sroie-rapid.jsonl
python -m ocr_lab.evaluate --labels "$DATASETS_ROOT/source/sroie-mirror/labels.jsonl" --limit 100 --config ocr_lab/configs/paddleocr_cpu.json --output runs/sroie-paddle.jsonl
python scripts/make_ocr_examples.py --paddle runs/sroie-paddle.jsonl --rapid runs/sroie-rapid.jsonl --dataset-root "$DATASETS_ROOT/source/sroie-mirror" --dataset-name "SROIE mirror" --output "reports/SROIE example comparisons.md"
```

This mirror contains 626 examples, not the full 1,000-image official challenge. The repository's MIT code license is not clear proof of rights in receipt scans; this copy is retained for local nonprofit research only, with no redistribution. Check with the challenge organizers before sharing data or relying on a public mirror license.

The official XFUND v1.0 validation releases provide seven-language form images/annotations under the dataset's stated CC BY-NC-SA 4.0 terms (noncommercial, attribution, share-alike):

```bash
python scripts/download_xfund_val.py
python scripts/export_xfund.py
python -m ocr_lab.evaluate --labels "$DATASETS_ROOT/source/xfund-val/labels.jsonl" --limit 50 --config ocr_lab/configs/rapidocr_cpu_no_orientation.json --output runs/xfund-rapid.jsonl
```

XFUND is forms (German, Spanish, French, Italian, Japanese, Portuguese, Chinese), not Czech or receipts; it is supplementary multilingual text/layout testing.

## Receipt total extraction

The total-field evaluator compares amount candidates from OCR output with CORD `total_price` and SROIE key-field `total` labels. It reports an OCR candidate oracle (was the correct amount seen anywhere?), keyword/layout selection, bottommost/largest-number baselines, and an optional CORD-supervised logistic candidate ranker. CORD has total-value labels on 193/200 local receipts; the SROIE first 100 has 99 nonempty total labels. The ranker learns on CORD validation and can be evaluated on held-out CORD test or transferred to SROIE.

```bash
python3 scripts/evaluate_total_amount.py --dataset cord \
  --predictions runs/cord-paddleocr.jsonl --labels "$DATASETS_ROOT/source/cord-v2/labels.jsonl" \
  --split test --train-predictions runs/cord-paddleocr.jsonl \
  --train-labels "$DATASETS_ROOT/source/cord-v2/labels.jsonl" --train-split validation \
  --ranker-output runs/total-amount/cord-paddle-ranker.json \
  --output runs/total-amount/cord-paddle-test.json

python3 scripts/evaluate_total_amount.py --dataset sroie \
  --predictions runs/sroie-paddleocr-100.jsonl \
  --train-predictions runs/cord-paddleocr.jsonl \
  --train-labels "$DATASETS_ROOT/source/cord-v2/labels.jsonl" --train-root "$DATASETS_ROOT/source/cord-v2" \
  --train-dataset cord --train-split validation \
  --output runs/total-amount/sroie-paddle-trained-on-cord.json
```

Current development results: keyword-nearby total selection is 75.8% PaddleOCR / 77.9% RapidOCR on CORD test; the CORD-trained ranker reaches 82.1% / 85.3%. On the first 99 labeled SROIE receipts, the CORD-trained ranker transfers at 68.7% / 72.7%, versus the keyword baseline at 61.6% / 63.6%. The correct numeric value appears somewhere in the OCR candidates for 99/99 SROIE records (oracle upper bound), so most current misses are candidate selection rather than raw amount reading. See [`reports/Total amount extraction results.md`](reports/Total%20amount%20extraction%20results.md) for method definitions and full results.

Amount matching deliberately does not use ASCII-folding. CORD is compared by digits-only signatures (its Indonesian punctuation conventions vary); SROIE amounts are parsed into integer cents. For Czech documents, add a Czech/EU locale-aware parser before relying on totals: comma decimals and thousands separators must retain monetary meaning.

Receipt-level categorization uses one schema in naive and tuned modes: total/currency, purpose category and merchant evidence, tax, tip, service charge, plus a not-yet-extracted line-item collection with a future `assigned_person_id` slot. Tuned mode uses the CORD-trained total candidate ranker; currency/purpose/tax/tip are currently shared rule-based extensions in both modes. Results and ground-truth limitations are in [`reports/Receipt field categorization results.md`](reports/Receipt%20field%20categorization%20results.md).

Manual field annotations are evaluated separately from the original OCR/KIE labels. See [`reports/Manual receipt baseline evaluation.md`](reports/Manual%20receipt%20baseline%20evaluation.md) for held-out CORD and full SROIE PaddleOCR baseline results, including coverage and per-document artifacts.

```bash
python3 scripts/evaluate_receipt_fields.py --dataset cord --mode naive \
  --predictions runs/cord-paddleocr.jsonl --split test --output runs/receipt-fields/cord-naive.jsonl
python3 scripts/evaluate_receipt_fields.py --dataset cord --mode tuned \
  --predictions runs/cord-paddleocr.jsonl --split test \
  --ranker runs/total-amount/cord-paddle-ranker.json --output runs/receipt-fields/cord-tuned.jsonl
```

### Optional local LLM selector

`scripts/evaluate_total_amount_llm.py` sends only the OCR transcript, total/payment label lines, and amount candidates to Ollama; it does not send receipt images. The constrained JSON response must select a candidate ID or abstain. The first CPU pilot outputs are in `reports/LLM total amount pilot.md`.

```bash
python3 scripts/evaluate_total_amount_llm.py --model qwen3:4b --dataset sroie \
  --predictions runs/sroie-paddleocr-100.jsonl --row-ids 0 23 50 \
  --output runs/amount-llm/qwen3-4b-sroie-pilot.jsonl --threads 12
python3 scripts/evaluate_total_amount_llm.py --model gpt-oss:20b --dataset sroie \
  --predictions runs/sroie-paddleocr-100.jsonl --row-ids 0 23 50 \
  --output runs/amount-llm/gpt-oss-20b-sroie-pilot.jsonl --think low --num-predict 128 --threads 12
```

## Current scope

- One image per command; no GUI, camera feed, tuning sweep, or automatic model download manager yet.
- PaddleOCR and RapidOCR output is normalized to `text_instances` with `polygon`, `text`, and `confidence`; backend metadata/raw source output should be retained for detailed evaluation.
- The same PP-OCR-derived weights through PaddleOCR and RapidOCR are mainly a backend/runtime comparison. Different model versions/configurations are a package-level comparison, not a controlled model-quality comparison.

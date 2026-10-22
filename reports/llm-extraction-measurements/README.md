# LLM receipt extraction: measured artifacts

This directory contains the committed results behind
[`../LLM receipt extraction cost measurement.md`](../LLM%20receipt%20extraction%20cost%20measurement.md).

**Measured:** 22 October 2026  
**Corpus:** 20 CORD-v2 validation receipts  
**Models:** `deepseek/deepseek-v4.1-flash`, `z-ai/glm-5.3-flash`  
**Input modes:** `image`, `ocr`, `both`  
**Prompt version:** `receipt-extraction-v1`  
**Image preprocessing:** max side 1600 px, JPEG quality 90  
**Temperature:** 0  
**Provider:** OpenRouter, pinned to `OpenInference` where available  
**OCR:** local Tesseract, cached  
**Reasoning:** DeepSeek disabled; GLM fell back to `effort=low` because the endpoint requires reasoning

## Files

| Path | Contents |
|---|---|
| `summary.md` | Human-readable token/cost table for the combined run. |
| `summary.json` | Machine-readable averages, percentiles, cost extrapolations, paired modality deltas and error counts. |
| `results.jsonl` | One line per successful model/mode/document extraction with token usage, cost, provider and normalized extraction JSON. |
| `consensus.jsonl` | Per-document agreement/disagreement on critical fields across models and modes. All 20 documents are flagged for review, which is expected when six extractions per image are compared. |
| `ground_truth/all_extractions.jsonl` | Every successful extraction with provenance (model, mode, image hash, prompt version, usage, cost). This is the full LLM-as-annotator layer. |
| `ground_truth/canonical/*.json` | One canonical extraction per receipt, chosen as DeepSeek `both` if available, then DeepSeek `image`, then DeepSeek `ocr`, then the GLM equivalent. Intended as a practical seed for review, not human truth. |
| `deepseek-v4.1-flash/` | DeepSeek-only results and summary. |
| `glm-5.3-flash/` | GLM-only results and summary (low-reasoning fallback). |

Image paths are relative to `$DATASETS_ROOT/source` (for example
`cord-v2/images/validation/0000.jpg`). Receipt images themselves are not
committed; download them locally with:

```bash
python3 scripts/download_cord.py --splits validation --limit-per-split 20
```

## Reproduction

```bash
python3 scripts/measure_receipt_llm.py \
  --manifest "$DATASETS_ROOT/source/cord-v2/labels.jsonl" \
  --limit 20 \
  --models deepseek/deepseek-v4.1-flash z-ai/glm-5.3-flash \
  --input-mode image ocr both \
  --out-dir runs/llm-extraction/cord20 \
  --ground-truth-dir runs/llm-extraction/cord20/ground_truth \
  --consensus \
  --provider-order OpenInference \
  --max-image-side 1600 --jpeg-quality 90
```

The OpenRouter key is read from `OPENROUTER_API_KEY` or the OpenCode credential
store and is never written to these files.

## How to read the numbers

- `billed $/receipt` is the provider-reported OpenRouter charge, including any
  endpoint-specific discount.
- `list $/receipt` uses the pricing table in `ocr_lab/receipt_extraction.py`
  (USD per 1M tokens) and is the more stable planning number.
- `in` includes the extraction instructions, compact schema, and image and/or
  OCR transcript. `out` is visible JSON; `reasoning` is billed separately.
- Cost deltas are paired per document and then averaged. Negative cost deltas
  can happen when adding OCR changes the model's output/reasoning length enough
  to offset the extra input tokens. Treat prompt-token deltas as the stable
  modality measurement.
- DeepSeek's OpenInference endpoint billed less than the model headline list
  price in this run; both numbers are retained.

## Caveats

- CORD receipts are short, Indonesian, and not a Czech/US invoice sample. Run
  the same script on the production corpus before using these numbers for
  budgeting.
- These are LLM-generated labels. `consensus.jsonl` is a review queue, not a
  truth oracle. Human review is still required for payment-critical fields.
- Image tokenization depends on the upstream provider. Pin `--provider-order`
  when comparing engines.
- OCR is local, so its compute cost is excluded from token totals. OCR quality
  still changes output length and reasoning.

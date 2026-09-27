# Total amount extraction baseline results

## What was measured

This benchmark evaluates the **field extraction step**, not OCR character error. For each receipt, the target is CORD's `gt_parse.total.total_price` or SROIE's key-field `total`. Amounts are compared with dataset-specific canonicalization: CORD uses the digit signature because its Indonesian labels use mixed group punctuation; SROIE is parsed as integer cents with comma grouping and dot decimals. The generic ASCII-fold text metric is deliberately not used for monetary values.

The saved PaddleOCR and RapidOCR detections feed four methods:

1. **OCR candidate oracle (upper bound):** does any numeric OCR candidate exactly match the labeled total? It does not select among candidates, so this is a recognition-and-detection ceiling, not a deployable extractor.
2. **Keyword nearby:** select the numeric candidate nearest a label such as “TOTAL”, “TOTAL DUE”, or “AMOUNT PAYABLE”, with a weak lower-page prior.
3. **Bottommost / largest amount:** simple negative baselines illustrating why location-only or amount-size-only selection is unreliable.
4. **Learned candidate ranker:** weighted logistic regression over numeric candidate context, total-keyword proximity, page position, OCR confidence, amount formatting/length, and excluded cash/tax/discount context. It is trained on CORD validation OCR candidates and total labels, then scored on the held-out CORD test set and transferred to SROIE without SROIE training.

“Exact accuracy” is the fraction of labeled documents whose selected normalized amount equals the ground truth. A miss or wrong selection counts as incorrect. The oracle’s accuracy is the fraction for which the correct amount appears anywhere in OCR output.

## Results

### CORD held-out test split

The CORD rankers were trained on the validation split; 95 test receipts have `total_price` labels.

| OCR harness | Oracle: correct value present | Keyword nearby | Bottommost | Largest amount | CORD-trained ranker |
|---|---:|---:|---:|---:|---:|
| PaddleOCR | 89/95 (**93.7%**) | 72/95 (**75.8%**) | 44/95 (46.3%) | 48/95 (50.5%) | 78/95 (**82.1%**) |
| RapidOCR | 91/95 (**95.8%**) | 74/95 (**77.9%**) | 47/95 (49.5%) | 49/95 (51.6%) | 81/95 (**85.3%**) |

### SROIE corrected mirror, first 100 images

There are 99 nonempty labeled `total` fields in this 100-image subset. The learned ranker was trained on CORD validation only; this is a cross-dataset transfer result.

| OCR harness | Oracle: correct value present | Keyword nearby | Bottommost | Largest amount | CORD-trained ranker on SROIE |
|---|---:|---:|---:|---:|---:|
| PaddleOCR | 99/99 (**100%**) | 61/99 (**61.6%**) | 8/99 (8.1%) | 0/99 (0%) | 68/99 (**68.7%**) |
| RapidOCR | 99/99 (**100%**) | 63/99 (**63.6%**) | 8/99 (8.1%) | 0/99 (0%) | 72/99 (**72.7%**) |

The important gap is between **correct amount recognized somewhere** and **correct amount selected**: SROIE's OCR candidate set contained the labeled total in every scored receipt, while the simple keyword rule chose it in only about 62–64%. The CORD-trained ranker adds about 7–9 percentage points on SROIE, but still needs better annotations and validation before production. Bottommost and largest-number rules fail often because receipts place cash/change after totals and contain large IDs, dates, and barcodes.

Two concrete ranking fixes:

- On CORD test image `data/cord-v2/images/test/0000.jpg`, the reference total is `60.000`. The OCR text line is `TOTAL (Qty 2.00 60.000`; keyword-nearby selects the first numeric token (`2.00`, the quantity), while the CORD-trained candidate ranker selects `60.000`.
- On SROIE image `data/sroie-mirror/img/023.jpg`, the reference total is `27.55`. The PaddleOCR keyword baseline chooses `26.00`; the CORD-trained ranker chooses the `27.55` candidate already present in the OCR detections.

## Ground-truth coverage and caveats

- The local CORD subset has 193/200 nonempty `total.total_price` labels; the five test records with no target were excluded from its test accuracy denominator. CORD is Indonesian and is only a method-development proxy.
- The first 100 SROIE mirror records have 99 nonempty key totals. The mirror contains 626 receipts, not the complete official 1,000-image challenge, and image reuse terms remain unclear; its data stay local to this nonprofit research workspace.
- CORD amount canonicalization treats all digits as the amount signature, fitting its mixed Indonesian punctuation but potentially equating strings whose decimal semantics differ. SROIE uses decimal-to-cents parsing. Czech deployment needs a Czech/EU locale parser, currency-aware targets, and exact validation in minor currency units.
- Scores are on two non-Czech datasets and should not be interpreted as Czech invoice/receipt quality. Split by merchant/time and avoid reusing supervised-training labels in the final test set.
- The learned ranker has no confidence/abstention threshold yet. Current exact accuracy counts a selected value for every document; adding calibration and a “send to review” option is the next practical improvement.

## Reproduce

```bash
python3 scripts/evaluate_total_amount.py --dataset cord \
  --predictions runs/cord-paddleocr.jsonl --labels data/cord-v2/labels.jsonl \
  --split test --train-predictions runs/cord-paddleocr.jsonl \
  --train-labels data/cord-v2/labels.jsonl --train-split validation \
  --ranker-output runs/total-amount/cord-paddle-ranker.json \
  --output runs/total-amount/cord-paddle-test.json

python3 scripts/evaluate_total_amount.py --dataset sroie \
  --predictions runs/sroie-paddleocr-100.jsonl \
  --train-predictions runs/cord-paddleocr.jsonl \
  --train-labels data/cord-v2/labels.jsonl --train-root data/cord-v2 \
  --train-dataset cord --train-split validation \
  --ranker-output runs/total-amount/cord-to-sroie-ranker.json \
  --output runs/total-amount/sroie-paddle.json
```

Per-document selected candidates and correctness flags are saved in the `runs/total-amount/` JSON outputs. The detector transcripts, total-label research, and dataset notes are in the existing local OCR workspace.

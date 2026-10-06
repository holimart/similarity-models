# Manual receipt-label baseline evaluation

The receipt-field extractors were evaluated against the manually reviewed manifest at `annotations/manual/receipt_field_annotations.jsonl` (versioned in this repository; the batch shards are alongside it). OCR prediction coverage is **100 held-out CORD test receipts** and **all 626 SROIE receipts**. The 100 CORD validation receipts are excluded from the total comparison because they were used to train the ranker. That gives 726 evaluated receipts from the 826-row manual manifest. TextZoom and XFUND are non-receipt corpora and are out of scope.

The tuned selector uses the existing CORD-trained amount ranker. CORD test remains held out from ranker training; the same ranker is transferred to SROIE. Bottommost/largest baselines and keyword-nearby are scored on the same saved PaddleOCR detections. Results are exact normalized amount matches; selection coverage is reported separately.

## Total amount

| Dataset / predictions | Manual total labels | Keyword-nearby | Bottommost | Largest amount | CORD-trained ranker |
|---|---:|---:|---:|---:|---:|
| CORD test, 100 receipts | 95 | 67/95 (70.5%) | 42/95 (44.2%) | 47/95 (49.5%) | 73/95 (76.8%) |
| SROIE mirror, all 626 receipts | 621 | 398/621 (64.1%) | 79/621 (12.7%) | 0/621 (0.0%) | 444/621 (71.5%) |

All total methods selected an amount on 93/95 CORD test labels (97.9%) and 621/621 SROIE labels. The ranker was exact on 73 of its 93 selected CORD values (78.5% conditional accuracy); its SROIE coverage was 100%.

## Other manually labeled fields

Auxiliary field extraction is shared between naive and tuned modes; only total selection differs. Figures below are exact field-value matches over manually positive labels unless stated otherwise.

| Field | CORD test | SROIE first 100 |
|---|---:|---:|
| Tax amount | 11/41 exact (26.8%); selected on 13/41, 84.6% exact when selected | 228/596 exact (38.3%); selected on 594/596 |
| Service charge | 3/12 exact (25.0%); selected on 4/12 | 18/35 exact (51.4%); selected on 20/35 |
| Tip | No positive examples; all 97 known CORD statuses and all 626 SROIE statuses were absent | Same |
| Purpose category | 19/94 clear labels exact (20.2%); category emitted on 22/94 | 151/610 exact (24.8%); category emitted on 311/610 |
| Currency code | 5/9 visible-code labels exact (55.6%); code emitted on 5/9 | 444/484 exact (91.7%); code emitted on 444/484 |
| Merchant name | 0/7 present labels exact; candidate emitted on 5/7 | 342/626 present labels exact (54.6%); candidate emitted on 623/626 |

Tax presence classification accuracy was 71.1% on CORD and 98.1% on SROIE. Service-charge presence accuracy was 91.8% and 97.4%, respectively. Tips have no positive examples in these labels, so the all-absent result does not establish tip recall.

## Coverage and artifacts

- `runs/manual-baseline-evaluation/cord-paddle-test.json`
- `runs/manual-baseline-evaluation/sroie-paddle-full.json`
- Reproduce with `scripts/evaluate_manual_receipt_fields.py`; results include per-document predictions and manual targets.
- The full SROIE prediction file was completed by resuming an interrupted inference run at row 491.
- These diagnostic datasets are Indonesian/Malaysian receipts and are not estimates of Czech receipt performance. Purpose/merchant exact-match results also depend on OCR quality and conservative lexical rules.

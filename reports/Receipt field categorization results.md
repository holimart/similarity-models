# Receipt field categorization extension

## Receipt output schema

`ocr_lab/receipt_fields.py` now exposes one shared receipt record in both `naive` and `tuned` modes:

- **Total:** raw OCR amount, dataset-normalized value, currency inference, confidence/evidence, and the extraction method.
- **Currency:** ISO code and evidence marker when a recognized currency code/symbol is present; a lone `$` stays ambiguous rather than being guessed as USD.
- **Purpose:** a heuristic category and text evidence (`food_dining`, `groceries`, `fuel`, `transport`, `lodging`, `healthcare`, `office_supplies`, `utilities`, `entertainment`, or `unknown`). A top-header merchant-name candidate is kept separately.
- **Tax, tip, service charge:** separate nullable fields. Tax labels include tax/VAT/GST/DPH; tip labels include tip/gratuity/propina/spropitné. Service charge is not silently counted as tip.
- **Future item splitting:** a typed line-item/assignment shape is present (`description`, `quantity`, `amount_raw`, `assigned_person_id`, `assignment_status`), but `items` remains empty and explicitly `not_extracted_yet`.

Naive mode selects total with the keyword-nearby rule. Tuned mode selects total with the CORD-trained candidate ranker. Both modes currently use the same lexical currency, purpose, tax, tip, and service-charge extraction rules because the available benchmarks do not provide training labels for currency/purpose/tip. Thus the tuned/naive comparison below is specifically the amount-field selection comparison, not a claim that every added field has a learned model.

## Results on available labels

| Dataset / labeled fields | Mode | Total exact | Total coverage | Tax exact | Tax coverage | Service charge exact | Service charge coverage |
|---|---|---:|---:|---:|---:|---:|---:|
| CORD held-out test (95 total labels, 43 tax, 12 service-charge labels) | naive | 72/95 (75.8%) | 93/95 (97.9%) | 11/43 (25.6%) | 13/43 (30.2%) | 4/12 (33.3%) | 5/12 (41.7%) |
| CORD held-out test | tuned | 78/95 (82.1%) | 93/95 (97.9%) | 11/43 (25.6%) | 13/43 (30.2%) | 4/12 (33.3%) | 5/12 (41.7%) |
| SROIE first 100 (99 nonempty total labels; no tax/tip/service-charge KIE labels) | naive | 61/99 (61.6%) | 99/99 (100%) | — | — | — | — |
| SROIE first 100 | tuned, CORD-trained ranker | 68/99 (68.7%) | 99/99 (100%) | — | — | — | — |

For the CORD tax extractor, 11 of 13 selected values were exact (84.6% conditional accuracy), but it found a tax candidate on only 30.2% of tax-labeled receipts. For service charges, 4 of 5 selected amounts were exact (80%) and the field was found on 41.7% of labeled documents. Low coverage—not numeric reading accuracy on the selected subset—is the main limitation in these rule-based auxiliary fields.

CORD's `total.total_price`, `sub_total.tax_price`, and `sub_total.service_price` supply the available labels; its local validation/test sample contains Indonesian receipts. SROIE's `key.total` labels support total evaluation, but the public corrected mirror does not label tax/tip or line items as key fields. These scores are not Czech accuracy estimates. Neither dataset supplies ground-truth currency or purpose categories, so those outputs currently have no defensible accuracy score. Tip ground truth is absent from both; tip extraction is enabled but unscored.

Amount normalization is dataset-specific: CORD is compared by digit signature because Indonesian punctuation varies, while SROIE is parsed to integer cents with its dot-decimal format. This is **not** the general ASCII-fold text metric; Czech total evaluation must use locale-aware separators and currencies. The receipts feature set is described in [`README-ocr.md`](../README-ocr.md), and row-level predictions are in `runs/receipt-fields/`.

## Try both paths

```bash
python3 scripts/evaluate_receipt_fields.py --dataset cord --mode naive \
  --predictions runs/cord-paddleocr.jsonl --split test \
  --output runs/receipt-fields/cord-naive.jsonl

python3 scripts/evaluate_receipt_fields.py --dataset cord --mode tuned \
  --predictions runs/cord-paddleocr.jsonl --split test \
  --ranker runs/total-amount/cord-paddle-ranker.json \
  --output runs/receipt-fields/cord-tuned.jsonl
```

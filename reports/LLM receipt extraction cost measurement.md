# LLM receipt and invoice extraction: token cost measurement

**Measured:** 22 October 2026  
**Corpus:** 20 CORD-v2 validation receipts (Indonesian; short receipts, not a Czech/US sample)  
**Models:** DeepSeek V4.1 Flash, GLM 5.3 Flash  
**Prompt:** `receipt-extraction-v1` in `ocr_lab/receipt_extraction.py`  
**Tool:** `scripts/measure_receipt_llm.py`

The measurement answers the planning question: **how many input/output tokens does one receipt cost, and what does that imply at 1k / 100k / 1M receipts?** It is not a quality benchmark. The same script emits per-document JSON that can be used as an LLM-generated ground-truth layer and as a consensus/review queue.

The committed run artifacts — full results, summaries, consensus and the canonical ground-truth extractions — are in [`reports/llm-extraction-measurements/`](llm-extraction-measurements/README.md).

## How to run it

```bash
# Compare image, OCR-only and image+OCR on the same documents.
python3 scripts/measure_receipt_llm.py \
  --images /path/to/receipts \
  --models deepseek/deepseek-v4.1-flash z-ai/glm-5.3-flash \
  --input-mode image ocr both \
  --out-dir runs/llm-extraction \
  --ground-truth-dir runs/llm-extraction/ground_truth \
  --consensus
```

Useful switches:

| Switch | Effect |
|---|---|
| `--input-mode image` | Vision-only baseline. Includes image tokens. |
| `--input-mode ocr` | Text-only. Uses local Tesseract/RapidOCR or a precomputed OCR JSONL. No image tokens. |
| `--input-mode both` | Image + OCR transcript in one request. This is the "image AND its OCR both" cost. |
| `--ocr-backend tesseract\|rapidocr\|none` | Local OCR. Cached by image hash, backend, language and PSM. |
| `--precomputed-ocr file.jsonl` | Reuse an existing OCR corpus instead of running OCR. |
| `--max-image-side` / `--jpeg-quality` | Controls image tokenization; keep fixed across models. |
| `--reasoning disabled\|low\|auto` | `disabled` is cheapest where supported. Mandatory-reasoning models fall back to `low`. |
| `--provider-order OpenInference --no-allow-fallbacks` | Pins an OpenRouter upstream endpoint so image tokenization does not change mid-run. |
| `--ground-truth-dir` | Writes one extraction JSON per model/mode/document plus a `ground_truth.jsonl` index. |
| `--consensus` | Groups extractions by document and flags critical fields that disagree. |
| `--backend opencode` | Uses the installed `opencode` CLI and subtracts a trivial-prompt baseline to remove the agent system prompt. Direct OpenRouter is preferred for clean measurement. |

The script reads the OpenRouter key from `OPENROUTER_API_KEY` or, if absent, from the OpenCode credential store. Keys are never printed.

## Measured token counts

All runs used 1600 px maximum image side, JPEG quality 90, temperature 0, and the same prompt/schema. `in` is the complete prompt (instructions + schema + image and/or OCR), `out` is visible output, `reasoning` is provider-billed reasoning output. A few DeepSeek rows returned upstream 429s and were retried/fell back to another provider; the table shows the successful OpenInference rows, which is why some `n` values are below 20. The script records these attempts and can resume them.

### DeepSeek V4.1 Flash

Pinned to the OpenInference endpoint. Headline OpenRouter list price used below: **$0.30/M input, $1.20/M output**. The endpoint actually billed **$0.07/M input, $0.50/M output**, so billed cost is lower than the list estimate.

| Input | n | In tok | Out tok | Reasoning | List $/receipt | List $/1k | List $/100k | List $/1M | JSON ok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| image | 18 | 1,113 | 678 | 0 | $0.001147 | $1.15 | $115 | $1,147 | 100% |
| ocr | 20 | 1,067 | 602 | 0 | $0.000975 | $0.98 | $98 | $975 | 100% |
| image+ocr | 17 | 1,269 | 575 | 0 | $0.001071 | $1.07 | $107 | $1,071 | 100% |

Paired per-document deltas (OpenInference):

| Comparison | Pairs | Prompt Δ | Out+reasoning Δ | List cost Δ |
|---|---:|---:|---:|---:|
| OCR added to image | 17 | +156 | -100 | -$0.000073 |
| Image added to OCR | 17 | +202 | -26 | +$0.000109 |
| Image vs OCR | 18 | +37 | +74 | +$0.000175 |

The negative "OCR added to image" cost is not a discount: adding OCR changed the model's output length enough to offset the extra input. **Use the token deltas as the stable modality measurement and the average receipt cost for budgeting.** With more receipts the cost delta should converge.

### GLM 5.3 Flash

Pinned to OpenInference. List price: **$0.0107/M input, $0.1707/M output**. This endpoint requires reasoning; the script's `disabled` setting fell back to `reasoning.effort=low`, which produced much lower reasoning than the model default.

| Input | n | In tok | Out tok | Reasoning | List $/receipt | List $/1k | List $/100k | List $/1M | JSON ok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| image | 20 | 948 | 646 | 109 | $0.000120 | $0.12 | $12 | $120 | 100% |
| ocr | 20 | 1,043 | 1,203 | 728 | $0.000217 | $0.22 | $22 | $217 | 100% |
| image+ocr | 20 | 1,102 | 619 | 89 | $0.000118 | $0.12 | $12 | $118 | 100% |

Paired per-document deltas:

| Comparison | Pairs | Prompt Δ | Out+reasoning Δ | List cost Δ |
|---|---:|---:|---:|---:|
| OCR added to image | 20 | +154 | -46 | -$0.000003 |
| Image added to OCR | 20 | +58 | -1,223 | -$0.000099 |
| Image vs OCR | 20 | -96 | -1,176 | -$0.000096 |

The important result: **OCR-only is not automatically cheaper.** GLM reasoned much more over the noisy OCR transcript (728 reasoning tokens on average) than over the image (109), so the OCR-only route cost about 1.8× the image route. Image+OCR was effectively the same price as image-only, with ~154 extra input tokens.

## What this implies

For these short CORD receipts, the working rule of thumb is:

- **DeepSeek V4.1 Flash:** ~1.1k input and ~0.6–0.7k visible output tokens per receipt; ~$0.0011/receipt at headline list price (≈$1.15 per 1k, ≈$115 per 100k, ≈$1,147 per 1M).
- **GLM 5.3 Flash:** ~0.95–1.1k input and ~0.65–1.2k visible output plus 0.1–0.7k reasoning tokens; ~$0.00012/receipt at list price (≈$0.12 per 1k, ≈$12 per 100k, ≈$118 per 1M) when reasoning is held to low effort.
- **Image+OCR is not additive in cost** in these tests. It adds roughly 150 input tokens over image-only, but output/reasoning variance dominates. Use it when OCR improves field accuracy, not as a cost-saving measure.
- **Reasoning is the biggest cost lever.** DeepSeek with `reasoning=low` was catastrophic in the pilot: multiple 4k-reasoning-token responses that hit the output cap and failed JSON parsing. Keep `disabled` for DeepSeek. If GLM is forced to reason, `low` is materially cheaper than default.
- **Invoices with many line items scale with output tokens.** A 50-line invoice can easily emit 3–8k JSON tokens; cost per document will be several times the short-receipt numbers above.

Cost formula for your own corpus:

```
cost_per_document = input_tokens × input_price/1e6
                  + (output_tokens + reasoning_tokens) × output_price/1e6
cost_per_1k = mean(cost_per_document) × 1,000
```

## What else is worth extracting

The schema in `ocr_lab/receipt_extraction_schema.json` combines the standard fields used by AWS Textract AnalyzeExpense and Mindee's receipt model and adds fields useful for an expense app. The practical checklist:

### Document identity and compliance

- Document type: receipt, invoice, credit note, refund, other.
- Receipt/invoice/order number; transaction ID; PO number.
- Issue date and time; due date; payment terms.
- Currency (ISO 4217) and country; language/locale.
- Tax-document status; reverse-charge flag; VAT/GST breakdown.
- Supplier and customer tax IDs (VAT, GST, ABN, EIN, IČO, DIČ, TIN).
- Invoice legal requirements: supplier/customer names and addresses, VAT rates and amounts per rate, taxable base, total excluding/including VAT. EU invoices require these elements; check the current national rules before treating extraction as compliance-grade.

### Merchant and context

- Customer-facing merchant name and legal entity name.
- Full address, phone, email, website.
- Store/branch number, cashier, table/check/guest number.
- Receipt language and country; useful for locale-aware amount parsing.
- Loyalty/account/customer number.

### Amounts and taxes (the critical block)

- Subtotal (net), document-level discounts, line-level discounts.
- `tax_total` plus a **tax array**: label, rate %, taxable base, tax amount, jurisdiction, and whether tax is included in the printed price.
- Tip/gratuity, auto-gratuity, service charge, delivery fee, shipping, rounding.
- Total (final amount paid or due), amount paid, change, amount due, prior balance.
- Arithmetic check: subtotal + tax + tip + service + fees − discounts = total within rounding.
- US specifics: state/city sales-tax jurisdiction, tax-exempt flag, tip vs mandatory service charge, card tip line, auto-gratuity for large parties.
- EU specifics: VAT rate per line, VAT-inclusive pricing, reverse charge, customer VAT ID.

### Line items

- Description, SKU/product code, quantity, unit (pcs/kg/l/hour), unit price.
- Gross line amount, line discount, net line amount, tax rate/code.
- Modifiers/add-ons attached to the parent item (important for restaurants).
- Item-level category (for expense analytics) and optional person assignment for splitting a receipt.
- Keep printed order; do not reorder rows in a way that loses layout context.

### Payment

- Method (cash/card/mobile/bank transfer), card brand and last four digits.
- Transaction ID, authorization code, payment status.
- For invoices: bank details, IBAN, remittance reference, amount due and due date.

### Classification and app behaviour

- `purpose_summary`: short English phrase answering "what was bought and why" (e.g. "Team lunch at Italian restaurant").
- Primary category from a fixed taxonomy (food, groceries, fuel, transport, lodging, healthcare, office supplies, utilities, entertainment, travel, retail, services, other) plus subcategory.
- Business/personal flag only when the document makes it clear; otherwise null.
- Project/cost centre, tags, reimbursement status.
- Duplicate-receipt suspicion (same merchant/date/total), warranty/return window when printed.

### Quality and audit

- Legibility, blur, glare, crop, rotation, handwritten content.
- Per-field confidence and overall confidence; unresolved warnings.
- Verbatim evidence snippet for merchant, date, total, tax and tip (optional; costs output tokens).
- Original OCR transcript, image hash, model/version, prompt version, timestamp. This is what makes an LLM-generated ground truth auditable.
- PII handling: card last four only; avoid storing full card numbers, full customer identifiers or signatures unless explicitly required.

### Deliberately out of scope for the first pass

- Human-verified ground truth. The script produces **LLM-as-annotator** ground truth; `--consensus` flags disagreements for review rather than pretending they are truth.
- Full multi-page invoice reconciliation and supplier master-data matching.
- Tax advice or legal compliance. Extraction is not validation.

## Method caveats

- CORD is Indonesian and contains short receipts. Czech receipts, US sales-tax receipts and multi-page invoices will have different line-item counts, layouts and output lengths. Run the script on your own corpus before committing to a budget.
- Image token counts depend on the upstream provider's resize/tile policy. Pin `--provider-order` for a fair comparison and record the provider in results.
- OpenRouter's actual billed cost can differ from the model headline price (DeepSeek's OpenInference endpoint was about 3× cheaper than the headline list price in this run). The report shows both; use list price for conservative planning.
- OCR is local and its compute cost is excluded from token totals. OCR quality affects output length and reasoning, especially for GLM.
- PDF input is rendered at 200 DPI and only the first page is measured. Multi-page invoices need a page-splitting step or one request per page; output tokens and cost scale with pages and line items.
- The `opencode` backend adds a large agent system prompt. The script subtracts a trivial-prompt baseline per model/version, but the result is still a proxy. Direct provider calls are the cleaner measurement.
- Images and/or OCR transcripts are sent to the selected cloud provider. Receipts can contain personal and payment data; use a DPA-covered endpoint, redact what you do not need, or switch to a self-hosted model if that is required.
- Prices and model IDs change. Re-check the current rate card and pin model revisions before procurement.

## Sources

- AWS Textract, standard expense fields: <https://docs.aws.amazon.com/textract/latest/dg/invoices-receipts.html>
- Mindee receipt model fields (taxes, tips, line items, purchase category, locale): <https://docs.mindee.com/use-cases/extraction-models/receipt.md>
- Google Document AI processor list and OCR/image-quality capabilities: <https://cloud.google.com/document-ai/docs/processors-list>
- EU VAT invoice requirements: <https://europa.eu/youreurope/business/taxation/vat/vat-invoices/index_en.htm>
- OpenRouter model/pricing metadata: <https://openrouter.ai/models>
- OpenRouter chat completions and usage accounting: <https://openrouter.ai/docs/api-reference/chat-completion>

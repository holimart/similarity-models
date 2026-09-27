# Local LLM total-amount extraction pilot

## Setup

The four Ollama models were tested on OCR text—not invoice images. The shared input was PaddleOCR PP-OCRv6-small output from three SROIE records (`img/000.jpg`, `img/023.jpg`, `img/050.jpg`). The prompt includes OCR total/payment label lines and numeric candidates with source line and vertical position. Models must select a listed candidate ID or abstain; their answer is mapped back to the exact OCR amount. This prevents unsupported numeric hallucinations from counting as valid extraction.

Hardware: dual Intel Xeon E5649, 24 logical CPUs, no GPU; system RAM is 94 GiB. All models ran on CPU via local Ollama with deterministic sampling and thinking disabled for Qwen3, low reasoning for GPT-OSS. Models available locally: Qwen3-4B Q4_K_M (2.5 GB download), Qwen3-8B Q4_K_M (5.2 GB), Qwen3-14B Q4_K_M (9.3 GB), and GPT-OSS-20B MXFP4 (13 GB). Model licenses: Qwen3 and GPT-OSS are Apache 2.0 according to their model/release pages.

## Exact total-field results

Only three receipts were used as a CPU pilot. These are directional examples, not a statistically reliable leaderboard.

| Method/model | Correct totals | Exact accuracy | Median time per receipt |
|---|---:|---:|---:|
| Keyword-nearby baseline | 1/3 | 33.3% | negligible after OCR |
| CORD-trained candidate ranker | 3/3 | 100% | negligible after OCR |
| Qwen3-4B Q4_K_M | 0/3 | 0% | 119 s |
| Qwen3-8B Q4_K_M | 1/3 | 33.3% | 271 s |
| Qwen3-14B Q4_K_M | 2/3 | 66.7% | 395 s |
| GPT-OSS-20B MXFP4 | 3/3 | 100% | 399 s |

The OCR candidate oracle found the exact labeled total somewhere in OCR for **3/3** receipts. Thus the task here is candidate selection, not recovering text OCR never produced. On `img/000.jpg` (GT `9.00`), Qwen3-4B and 8B selected `10.00` cash tender; Qwen3-14B made the same mistake; GPT-OSS selected `9.00`. On `img/023.jpg` (GT `27.55`), Qwen3-4B selected `26.00`, while Qwen3-8B, Qwen3-14B and GPT-OSS selected `27.55`. On the more complex `img/050.jpg` (GT `593.10`), the Qwen3-4B and 8B pilots selected `33.57` tax; Qwen3-14B and GPT-OSS selected `593.10`.

These samples show promising behavior from GPT-OSS and Qwen3-14B, but the CORD-trained ranker also went 3/3 and is dramatically faster. The LLM value may be in handling long-tail semantic labels and new layouts; that requires a much larger vendor-held-out evaluation. The present CPU run is especially slow on this older Xeon, even though RAM is ample. Keep the LLM on a selective exception lane or consider a smaller distilled classifier/ranker for routine extraction.

## Outputs and reproduction

Per-document prompts/results are saved in `runs/amount-llm/*-sroie-pilot-final.jsonl`; model totals are in adjacent `.summary.json` files. Baseline predictions and amount-ranker outputs are under `runs/total-amount/`.

```bash
python3 scripts/evaluate_total_amount_llm.py --model qwen3:4b --dataset sroie \
  --predictions runs/sroie-paddleocr-100.jsonl --row-ids 0 23 50 \
  --output runs/amount-llm/qwen3-4b-sroie-pilot.jsonl --threads 12

python3 scripts/evaluate_total_amount_llm.py --model gpt-oss:20b --dataset sroie \
  --predictions runs/sroie-paddleocr-100.jsonl --row-ids 0 23 50 \
  --output runs/amount-llm/gpt-oss-20b-sroie-pilot.jsonl --think low --num-predict 128 --threads 12
```

The current amount parser uses dataset-specific normalization (CORD digit signatures; SROIE decimal currency to integer cents). Do not apply the generic punctuation-stripping ASCII-fold OCR metric to monetary values. A Czech deployment needs a Czech locale/currency parser and a Czech-labeled test set.

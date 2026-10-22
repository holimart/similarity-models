# LLM receipt extraction cost measurement

Generated: 2026-10-22T15:23:44+00:00  
Prompt version: `receipt-extraction-v1`  
Rows: 60 unique documents/model/mode (60 attempt rows, 0 unresolved errors)


| model | input | n | in tok | out tok | reasoning | billed $/receipt | list $/receipt | list $/1k | list $/100k | list $/1M | JSON ok |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| z-ai/glm-5.3-flash | OpenInference / both | 20 | 1102 | 619 | 89 | $0.000122 | $0.000118 | $0.12 | $12 | $118 | 100% |
| z-ai/glm-5.3-flash | OpenInference / image | 20 | 948 | 646 | 109 | $0.000126 | $0.000120 | $0.12 | $12 | $120 | 100% |
| z-ai/glm-5.3-flash | OpenInference / ocr | 20 | 1043 | 1203 | 728 | $0.000228 | $0.000217 | $0.22 | $22 | $217 | 100% |

## Paired incremental cost

Differences are computed per document, then averaged. Cost deltas use stable list prices; actual billed deltas are also in `summary.json`.

| model | provider / comparison | pairs | list $ delta | actual $ delta | prompt tok delta | out+reasoning tok delta |
|---|---|---:|---:|---:|---:|---:|
| z-ai/glm-5.3-flash | OpenInference / ocr_added_to_image | 20 | $-0.000003 | $-0.000004 | +154 | -46 |
| z-ai/glm-5.3-flash | OpenInference / image_added_to_ocr | 20 | $-0.000099 | $-0.000106 | +58 | -1223 |
| z-ai/glm-5.3-flash | OpenInference / image_minus_ocr | 20 | $-0.000096 | $-0.000102 | -96 | -1176 |

## Method notes

- Billed cost is provider-reported by OpenRouter; list cost is computed from the pricing table (USD per 1M tokens) for stable planning and cross-provider comparison.
- Token counts include the extraction prompt and schema. For `--backend opencode`, a per-model trivial-prompt baseline is subtracted to remove the CLI agent system prompt.
- Reasoning tokens are provider output tokens and are included in cost. Use `--reasoning disabled` where the provider supports it.
- OCR runs locally and is cached; its compute cost is not included in the token totals.
- Compare engines on the same image size: `--max-image-side` and JPEG quality change image-token counts.

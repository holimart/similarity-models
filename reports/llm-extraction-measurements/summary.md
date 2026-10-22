# LLM receipt extraction cost measurement

Generated: 2026-10-22T15:23:44+00:00  
Prompt version: `receipt-extraction-v1`  
Rows: 120 unique documents/model/mode (120 attempt rows, 0 unresolved errors)


| model | input | n | in tok | out tok | reasoning | billed $/receipt | list $/receipt | list $/1k | list $/100k | list $/1M | JSON ok |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek/deepseek-v4.1-flash | InferenceNet / both | 3 | 1741 | 711 | 0 | $0.000688 | $0.001376 | $1.38 | $138 | $1376 | 100% |
| deepseek/deepseek-v4.1-flash | OpenInference / both | 17 | 1269 | 575 | 0 | $0.000376 | $0.001071 | $1.07 | $107 | $1071 | 100% |
| deepseek/deepseek-v4.1-flash | InferenceNet / image | 2 | 1418 | 732 | 0 | $0.000670 | $0.001304 | $1.30 | $130 | $1304 | 100% |
| deepseek/deepseek-v4.1-flash | OpenInference / image | 18 | 1113 | 678 | 0 | $0.000417 | $0.001147 | $1.15 | $115 | $1147 | 100% |
| deepseek/deepseek-v4.1-flash | OpenInference / ocr | 20 | 1067 | 602 | 0 | $0.000362 | $0.000975 | $0.98 | $98 | $975 | 100% |
| z-ai/glm-5.3-flash | OpenInference / both | 20 | 1102 | 619 | 89 | $0.000122 | $0.000118 | $0.12 | $12 | $118 | 100% |
| z-ai/glm-5.3-flash | OpenInference / image | 20 | 948 | 646 | 109 | $0.000126 | $0.000120 | $0.12 | $12 | $120 | 100% |
| z-ai/glm-5.3-flash | OpenInference / ocr | 20 | 1043 | 1203 | 728 | $0.000228 | $0.000217 | $0.22 | $22 | $217 | 100% |

## Paired incremental cost

Differences are computed per document, then averaged. Cost deltas use stable list prices; actual billed deltas are also in `summary.json`.

| model | provider / comparison | pairs | list $ delta | actual $ delta | prompt tok delta | out+reasoning tok delta |
|---|---|---:|---:|---:|---:|---:|
| deepseek/deepseek-v4.1-flash | OpenInference / ocr_added_to_image | 17 | $-0.000073 | $-0.000039 | +156 | -100 |
| deepseek/deepseek-v4.1-flash | OpenInference / image_added_to_ocr | 17 | $+0.000109 | $+0.000018 | +202 | -26 |
| deepseek/deepseek-v4.1-flash | OpenInference / image_minus_ocr | 18 | $+0.000175 | $+0.000056 | +37 | +74 |
| deepseek/deepseek-v4.1-flash | InferenceNet / ocr_added_to_image | 2 | $-0.000009 | $-0.000011 | +76 | -26 |
| z-ai/glm-5.3-flash | OpenInference / ocr_added_to_image | 20 | $-0.000003 | $-0.000004 | +154 | -46 |
| z-ai/glm-5.3-flash | OpenInference / image_added_to_ocr | 20 | $-0.000099 | $-0.000106 | +58 | -1223 |
| z-ai/glm-5.3-flash | OpenInference / image_minus_ocr | 20 | $-0.000096 | $-0.000102 | -96 | -1176 |

## Method notes

- Billed cost is provider-reported by OpenRouter; list cost is computed from the pricing table (USD per 1M tokens) for stable planning and cross-provider comparison.
- Token counts include the extraction prompt and schema. For `--backend opencode`, a per-model trivial-prompt baseline is subtracted to remove the CLI agent system prompt.
- Reasoning tokens are provider output tokens and are included in cost. Use `--reasoning disabled` where the provider supports it.
- OCR runs locally and is cached; its compute cost is not included in the token totals.
- Compare engines on the same image size: `--max-image-side` and JPEG quality change image-token counts.

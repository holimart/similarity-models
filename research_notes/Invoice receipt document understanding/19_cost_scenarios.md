# Invoice and receipt extraction: comparative cost scenarios

**Pricing snapshot: 26 September 2026.** USD, list prices where published. This compares inference/document processing charges—not equivalent end-to-end products. For commercial decisions, confirm region, contract, quotas, service tier and pricing date with the vendor.

## 1. What do published-price options cost at 1k / 100k / 1m pages?

### Takeaway

The clearest like-for-like published document extraction prices are Google Document AI Invoice Parser at $0.10 per count (up to 10 pages), Amazon Textract Analyze Expense (per page; price schedule is region-specific), and published SaaS workflow block pricing from Nanonets. Rossum publishes an $18,000/year starting price, but not a page allowance, so it cannot be converted into a defensible per-page quote. Hosted VLM token charges can be modeled, but image tokenization makes a blanket “price per page” misleading; the figures below are explicitly illustrative.

### Cited Findings

- Google Document AI lists Invoice Parser at $0.10 per count; one count is up to 10 pages. A 10-page document costs $0.10, and more than 10 pages are charged in 10-page increments. Thus 1,000/100,000/1,000,000 single-page invoices (each one document) cost **$100/$10,000/$100,000** at list price. This counts documents, not pages; with 10-page invoice documents, the same page volumes cost **$10/$1,000/$10,000**. [Google Document AI pricing](https://cloud.google.com/document-ai/pricing)
- Google’s Form Parser is $30 per 1,000 pages through 1 million, then $20 per 1,000 above that; its published example totals $130,000 for 6 million pages. For 1k/100k/1m pages, that is **$30/$3,000/$30,000** (subject to monthly tier definition). Invoice Parser and Form Parser are different processors and should not be treated as interchangeable feature/accuracy equivalents. [Google Document AI pricing](https://cloud.google.com/document-ai/pricing)
- AWS says Analyze Expense includes OCR and provides a region-specific pricing table and high-volume custom quote channel. The retrieved pricing page explicitly shows the US West (Oregon) per-page schedule for other Textract features, but this extraction did not reliably expose the Analyze Expense row. Consequently **no numeric Textract Analyze Expense total is asserted here**; use its live regional calculator/table rather than transplanting OCR or Forms pricing. [Amazon Textract pricing](https://aws.amazon.com/textract/pricing/)
- Nanonets’ published pricing is block-based: $0.02 per simple block, $0.10 per standard AI block, and $0.30 per complex AI block. It says typical invoice workflows use 4–6 blocks per document, but the precise mix depends on the workflow. At an illustrative workflow mix of one $0.30 extraction block plus three to five $0.02 simple blocks, the arithmetic is **$0.36–$0.40/document**, or **$360–$400 / $36,000–$40,000 / $360,000–$400,000** for 1k/100k/1m single-page invoices. This is not a vendor quote: actual workflow composition and block qualification need validation, and its Growth/Enterprise volume discounts are quote-based (up to 40% stated). [Nanonets pricing](https://nanonets.com/pricing)
- Rossum Starter is advertised “starting at $18,000 per year”; plan prices beyond Starter are quote-based. Rossum says pricing depends on page/document volume and workflow complexity and has a one-year minimum contract. A hypothetical full-year Starter commitment therefore has a known minimum annual amount, but **no trustworthy per-page tier cost** can be calculated at any of these page volumes from public data. [Rossum pricing](https://rossum.ai/pricing/)
- Azure Document Intelligence publishes a pricing page with region- and SKU-dependent pricing, but the accessible public page did not return a usable current invoice model rate in this research pass. No Azure totals are estimated. Confirm the model and region in the Azure calculator. [Azure Document Intelligence pricing](https://azure.microsoft.com/en-us/pricing/details/document-intelligence/)

### Inferences

- The Google Invoice Parser totals above are especially sensitive to the document/page distinction: if “1m pages” means 1m one-page receipts, the list-price cost is $100k; if the same pages arrive in 10-page documents, it is $10k. Invoice length distribution is therefore an essential input to any quote comparison.
- Nanonets’ block model means a single per-page rate is not intrinsic to the published price. The range models one extraction block and three-to-five inexpensive supporting blocks; adding extra AI blocks can materially raise spend. The published “up to 40%” discount is not a guaranteed discount at any particular volume.

### Gaps

- Textract Analyze Expense and Azure invoice prebuilt pricing were not available as an unambiguous current price in accessible source output; the numbers are intentionally left unknown rather than filled from memory or another SKU.
- Public pages do not provide a single common accuracy, field schema, exception rate, or inclusion-of-human-validation specification. The prices above are not a quality-adjusted or feature-equivalent benchmark.

## 2. What are the explicit assumptions for hosted VLM and self-hosted open-weight scenarios?

### Takeaway

VLM API inference can be costed from published token rates only after fixing the model, prompt/output length, image resolution and provider image-token accounting. The VLM example below deliberately uses text-token assumptions only and is a lower-bound-style proxy, not a complete image invoice quote. Self-hosted open-weight inference has no universal per-page price: model throughput, hardware choice/utilization and operating labor dominate, and public model weights do not make serving free.

### Cited Findings

- OpenAI’s API pricing lists GPT-4.1 mini at $0.40 per million input text tokens and $1.60 per million output tokens; GPT-4.1 is $2/$8 per million. Batch prices are separately listed and lower for eligible async requests. The pricing documentation directs image-input estimates to a calculator, rather than supplying a fixed image-page price. [OpenAI API pricing](https://platform.openai.com/docs/pricing)
- Anthropic’s current API pricing page lists model-specific input/output token rates and says batch processing saves 50%; image/document calls also incur model input tokens, so input length is workload-dependent. Do not use consumer Claude seat prices as API inference pricing. [Anthropic pricing](https://www.anthropic.com/pricing#api)
- Google lists pretrained Invoice Parser at $0.10 per count (up to 10 pages), and separately lists OCR and Form Parser rates. [Google Document AI pricing](https://cloud.google.com/document-ai/pricing)

### Inferences

- **Illustrative hosted VLM token-only calculation (OpenAI GPT-4.1 mini):** assume one image/page; 1,000 billed input tokens/page inclusive of prompt and any image-token representation; 300 output tokens/page for structured JSON; no retries, cache, batch, tool calls or validation. At $0.40/M input and $1.60/M output, cost is $0.0004 + $0.00048 = **$0.00088/page**: **$0.88/$88/$880** at 1k/100k/1m pages. This is a scenario, not a provider page quote. Actual image tokens may exceed 1,000; measure usage from representative pages. Each additional 1,000 input tokens adds $0.40 per 1,000 pages, $40 per 100k, and $400 per million; each additional 100 output tokens adds $0.16/$16/$160.
- A realistic VLM system can require retries, image preprocessing, OCR fallback, schema repair, confidence thresholds and human review. If 10% of pages are retried once under the same assumptions, model token charges rise approximately 10%; human review can outweigh raw inference charges by orders of magnitude.
- **Self-hosted open-weight cost model:** monthly serving cost = accelerator/node rental or amortization + CPU/RAM/storage/network + orchestration/monitoring + engineering and on-call + evaluation/data labeling + human exception processing. Per-page infrastructure cost can be computed as (total allocated serving cost) ÷ successfully processed pages. Without a specified model, GPU, region, workload, throughput benchmark, utilization and availability target, numeric per-page totals would be invented; no self-hosted dollar totals are supplied.

### Gaps

- The model-side image tokens depend on image dimensions, patch/crop policy and endpoint. The 1,000-token assumption is deliberately not presented as a documented image tokenization rule.
- No single self-hosted public source can determine a universal workload cost. Benchmark the candidate model at the target resolution, batch size, concurrency, quantization and latency objective, then price the selected hardware/hosting region.
- Hosted VLM providers’ input/output token pricing does not establish invoice extraction accuracy, JSON validity, or compliance suitability.

## 3. How should labor, engineering and sensitivity change the decision?

### Takeaway

At 1k pages, integration/validation effort and commercial minimum commitments can dominate inference charges; at 100k–1m pages, per-page pricing, workflow complexity, review rate and serving utilization matter increasingly. Compare total cost per accepted invoice, not nominal API cost per page, and ask vendors for written volume tiers and explicit inclusion of onboarding, validation, storage, support and exception handling.

### Cited Findings

- Rossum’s minimum contract term is one year and Starter starts at $18,000/year; its pricing depends on page/document volume and workflow complexity. [Rossum pricing](https://rossum.ai/pricing/)
- Nanonets describes block-based billing, says typical workflows run 4–6 blocks per document and advertises up to 40% volume discounts on higher plans; Growth pricing itself requires a quote. [Nanonets pricing](https://nanonets.com/pricing)
- Google’s Invoice Parser price is per 10-page count, while its Form Parser page rate has a lower rate above 1 million pages; these are distinct billing units and processor offerings. [Google Document AI pricing](https://cloud.google.com/document-ai/pricing)
- AWS offers custom pricing proposals for high-volume use cases, in addition to published regional rates. [Amazon Textract pricing](https://aws.amazon.com/textract/pricing/)

### Inferences

- **Labor sensitivity formula:** human review cost/page = review fraction × minutes/reviewed page ÷ 60 × fully loaded hourly labor cost. For illustration only, at $30/hour and 1 minute of review on 5% of pages, labor is $0.025/page (= $25/$2,500/$25,000 for the three volumes). At 20% needing 2 minutes, it becomes $0.20/page (= $200/$20,000/$200,000). These are scenario assumptions, not sourced wage or accuracy claims.
- **Engineering sensitivity:** model setup, integrations, data governance, observability, retries, QA and ongoing model/version management are fixed or semi-fixed costs. As an illustrative break-even calculation, every $10,000 of additional annual engineering cost equals $10/page at 1k pages, $0.10/page at 100k, and $0.01/page at 1m. This shows why low variable cost does not imply low total cost at small scale.
- For hosted VLMs, cost scales approximately linearly with image/input tokens, output size and retries; prompt/image design can change the per-page rate. For SaaS workflows, each additional $0.10 block adds $100/$10,000/$100,000 across the three volumes. For Google invoice parser, changing average pages/document changes billing count. For self-hosting, utilization is pivotal: idle reserved GPU capacity increases cost/page, while higher throughput may reduce it until latency, memory or reliability targets bind.
- Make the operational denominator **accepted invoices**. If a provider costs $0.10 per page and 10% of pages need manual review at $0.025/page each, the effective cost becomes $0.1025/page before engineering; at higher review burden, labor quickly overtakes inference.

### Gaps

- No reviewed public source disclosed Rossum’s page allowance at its starting price, negotiated quote, implementation services fees or overage rate. No price should be imputed from its $18,000 annual floor.
- No reliable, current public negotiated price was found for SaaS enterprise tiers, Google/AWS/Azure committed discounts or the self-hosted compute configuration; obtain quotes or conduct an in-region benchmark.
- The cost model excludes taxes, currency conversion, network transfer, archival/storage charges, compliance controls, labeled evaluation data, procurement costs, application engineering, ongoing support and manual review unless explicitly described. Their omission should not be mistaken for zero cost.

### Scenario table (USD, variable processing costs only unless noted)

| Route / explicit scenario | 1k pages | 100k pages | 1m pages | What the number means |
|---|---:|---:|---:|---|
| Google Document AI Invoice Parser, 1-page docs | $100 | $10,000 | $100,000 | $0.10/count, each document up to 10 pages |
| Google Document AI Invoice Parser, 10-page docs | $10 | $1,000 | $10,000 | Same published price; 10x fewer billed counts |
| Google Document AI Form Parser | $30 | $3,000 | $30,000 | $30/1,000 pages through 1m; not identical to Invoice Parser |
| Nanonets modeled workflow | $360–$400 | $36,000–$40,000 | $360,000–$400,000 | One $0.30 extraction block + 3–5 $0.02 simple blocks/page; no discount assumed |
| Rossum Starter published floor | $18,000/year* | $18,000/year* | $18,000/year* | Annual starting price; page allowance and volume quote unknown; not a per-page estimate |
| OpenAI GPT-4.1 mini VLM token-only illustration | $0.88 | $88 | $880 | 1,000 input + 300 output tokens/page, excluding uncertain image-token charge/ops |
| AWS Textract Analyze Expense | Unknown | Unknown | Unknown | Current regional rate needs verification/quote |
| Azure prebuilt invoice | Unknown | Unknown | Unknown | Current SKU/region rate could not be retrieved reliably |
| Self-hosted open weights | Unknown | Unknown | Unknown | Requires measured throughput and specified infrastructure; formula above |

\* Full annual commitment at the advertised starting level, assuming the subscription applies; actual eligible volume is not disclosed. Not a claim that the same contract covers all three workloads.

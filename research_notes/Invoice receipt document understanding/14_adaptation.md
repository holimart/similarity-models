# Practical adaptation and fine-tuning for invoice/receipt extraction

## Which adaptation strategies are demonstrated for document models and open VLMs?

### Takeaway
Task fine-tuning is well demonstrated for specialist document models, including invoice extraction; general open VLM LoRA/QLoRA is a practical route but direct, controlled evidence specific to invoice/receipt extraction is thinner. Separate established results from engineering hypotheses and validate on vendor- and template-held-out documents.

### Cited Findings
- Donut is an OCR-free encoder-decoder document model, and its paper reports evaluation on document tasks including invoices; it also releases SynthDoG, a synthetic document generator for pretraining across domains and languages. This demonstrates the usefulness of document-specific pretraining and task fine-tuning, not that synthetic data alone guarantees real-world transfer. [Donut paper](https://arxiv.org/abs/2111.15664); [official code/data](https://github.com/clovaai/donut)
- LayoutLMv3 is pretrained jointly on text and image with word-patch alignment and evaluated on document understanding tasks. It represents OCR/layout-based rather than OCR-free adaptation. [LayoutLMv3](https://arxiv.org/abs/2204.08387)
- DocLLM proposes a lightweight document understanding model using text plus spatial information without a full image encoder, and reports results on multiple document benchmarks. It supports considering layout-aware language models where OCR is available; it is not itself evidence of a specific LoRA recipe for an arbitrary VLM. [DocLLM](https://arxiv.org/abs/2401.00908)
- QLoRA's original work demonstrates 4-bit quantized base weights with trainable LoRA adapters and reports finetuning a 65B model on a single 48GB GPU. This is a general LLM memory result, not a measured hardware requirement for document VLM fine-tuning; images, resolution, vision tower and sequence length add memory costs. [QLoRA](https://arxiv.org/abs/2305.14314)
- Hugging Face PEFT documents the common 4-bit NF4 + double quantization + bf16 compute pattern and adapter setup, and notes that targeting all linear layers is a QLoRA-style configuration. These are supported implementation options, not a guarantee of best invoice accuracy. [PEFT quantization guide](https://huggingface.co/docs/peft/main/en/developer_guides/quantization)
- Practical candidate model families include Donut (OCR-free), LayoutLMv3 (OCR/token/layout), and open image-language models with vision encoders and causal decoders. Compare by task and constraints; no cited source establishes one universal winner across current open VLMs and invoice domains.

### Inferences
- For a structured extraction target, start with supervised examples formatted as a stable schema (JSON or a fixed token sequence), explicit null/absent-field behavior, and field-level normalization rules. On open VLMs, LoRA/QLoRA is a sensible first adaptation experiment because it lowers trainable-state and optimizer-memory requirements; the actual vision-language module targets and supported training path are model-specific.
- For OCR/layout specialist models, adapt the task head or encoder-decoder using the model's native input representation rather than assuming language-model QLoRA recipes transfer unchanged.
- If labeled data is scarce, run a baseline with prompting and few-shot examples before fine-tuning; then compare the same fixed test set against a fine-tuned model. Prompting is low-cost and reversible, but there is no guarantee it will fix visual reading errors or systematic schema errors.

### Gaps
- No reliable cross-model study located that compares prompt-only, LoRA, QLoRA and full fine-tuning on the same invoice/receipt data, splits, image resolutions and compute budget.
- Exact adapter target modules, rank, learning rate, batch size and steps for the current open VLM candidates require per-model experiments; generic settings should not be presented as demonstrated invoice optima.

## What role should synthetic data, prompting and OCR augmentation play?

### Takeaway
Synthetic document generation is directly demonstrated as a pretraining/domain-coverage tool in Donut, while the best recipe for synthetic supervised invoice labels is not settled by that evidence. OCR-assisted and OCR-free routes address different failure modes; treat OCR augmentation as an ablation rather than an assumed improvement.

### Cited Findings
- Donut's authors provide SynthDoG, generating document images and corresponding text with controllable domains/languages, and describe its use in model pretraining. [Donut paper and repository](https://github.com/clovaai/donut)
- Donut specifically identifies OCR error propagation, language/document inflexibility, and the computation of running OCR as limitations of OCR-based VDU; OCR-free generation is proposed to avoid that dependency. [Donut paper](https://arxiv.org/abs/2111.15664)
- LayoutLMv3's joint image/text approach and DocLLM's use of text and spatial information exemplify OCR/text-informed pathways, whereas Donut exemplifies image-to-structured-sequence extraction. [LayoutLMv3](https://arxiv.org/abs/2204.08387); [DocLLM](https://arxiv.org/abs/2401.00908)
- PEFT's quantization guide describes parameter-efficient adaptation mechanics but does not prescribe synthetic-data mixing or prompt design for document extraction. [PEFT guide](https://huggingface.co/docs/peft/main/en/developer_guides/quantization)

### Inferences
- Synthetic training examples can cheaply cover schema combinations, layouts, currencies, date formats, and rare field presence. To avoid teaching unrealistic visual/text correlations, vary typography, layout, scan quality, skew, blur, compression and locale, and retain a substantial real-document validation set. This is a practical recommendation, not a quantified universal benefit established by the cited studies.
- Prompting should specify the schema, exact field semantics, whether to return null for absent/illegible values, and output-only constraints. Evaluate prompt variants on fixed held-out examples; do not use test examples as demonstrations.
- For OCR augmentation, compare (a) image only, (b) OCR text only with boxes, and (c) image plus OCR text/boxes. OCR text may help with small print and long line items, while OCR mistakes, reading order errors and duplicated visual/text evidence can hurt. Keep an explicit distinction between OCR-generated text and model visual reading.

### Gaps
- The sources reviewed do not establish an optimal real-to-synthetic ratio, synthetic rendering fidelity threshold, or amount of synthetic data for receipt/invoice extraction.
- No controlled evidence found establishing that attaching OCR text to an open VLM improves extraction over image-only prompting/fine-tuning across varied receipt conditions.

## How much annotation, training compute and evaluation are practical?

### Takeaway
There is no defensible universal minimum labeled-set size or compute budget: both depend on template diversity, field rarity, image resolution, base model and task definition. Use a small pilot and learning curves, and report held-out document performance with exact field-level metrics and leakage-resistant splits.

### Cited Findings
- Donut reports benchmark-specific results and a synthetic pretraining setup, but its results should not be interpreted as a generic labeled-example requirement for adapting another model. [Donut](https://arxiv.org/abs/2111.15664)
- QLoRA reports the 65B-on-48GB result in its own language-model setting; it gives a useful memory-efficiency reference point, but not the runtime/compute for visual document training. [QLoRA](https://arxiv.org/abs/2305.14314)
- PEFT details 4-bit configuration choices and adapter application, but does not specify invoice dataset size or training duration. [PEFT guide](https://huggingface.co/docs/peft/main/en/developer_guides/quantization)
- FUNSD is a 199-document form-understanding benchmark with entity and relation annotations, illustrating that small document benchmarks are useful for research comparisons but are not necessarily representative of production invoices/receipts. [FUNSD paper](https://arxiv.org/abs/1905.13538)

### Inferences
- Annotate a pilot spanning distinct vendors/templates, capture conditions, languages/currencies, long and short receipts, and rare/optional fields. Track counts by template and field, then add examples where validation error analysis shows failures. A learning curve (e.g., nested 25/50/100% training subsets) is more informative than an unsupported fixed annotation target.
- Prefer document-level and vendor/template-aware splits. If the deployment goal includes new merchants, reserve whole vendors/templates for validation/test; otherwise a random page split may overstate generalization through near-duplicate layouts. Deduplicate scans and prevent receipts from the same transaction appearing across splits.
- Record training configuration and wall-clock: model/checkpoint, image resize/crop policy, adapter target modules/rank, precision/quantization, optimizer, effective batch, epochs/steps, GPU type/count, peak memory and elapsed time. Compare quality at matched budgets where possible.
- Evaluate exact normalized field match and per-field precision/recall/F1, plus document-level exact match and schema/parse validity. Define normalization (currency symbols, decimal separators, dates, whitespace) before scoring; report raw-value accuracy separately where normalization could conceal errors. For line items, score row/column assignment and item-level precision/recall rather than only flattened text.
- Include confidence/abstention and illegible/missing-field cases; manually review high-impact numeric errors (totals, tax, currency) and report performance slices by field, vendor novelty, image quality, language and document type. Preserve a fixed untouched test set for final reporting.

### Gaps
- Public sources reviewed do not supply a transferable annotation-volume curve, invoice-specific LoRA compute benchmark, or evidence-based annotation-to-compute ratio.
- Exact-match and field-level metric definitions differ across papers and datasets; cross-paper scores should not be directly compared without aligning schemas, normalization, split policy and test distribution.

## Suggested evidence-led pilot

### Takeaway
Run a compact, controlled comparison before committing to large-scale labeling or training: prompted image-only baseline, OCR/layout baseline, then adapter fine-tuning, with synthetic and OCR inputs isolated as separate ablations.

### Cited Findings
- OCR-free Donut and OCR-informed LayoutLMv3/DocLLM demonstrate materially different document-modeling choices, motivating modality ablations rather than assuming a single architecture. [Donut](https://arxiv.org/abs/2111.15664); [LayoutLMv3](https://arxiv.org/abs/2204.08387); [DocLLM](https://arxiv.org/abs/2401.00908)
- LoRA/QLoRA are supported parameter-efficient approaches for adapting quantized language models; PEFT documents practical configuration patterns. [QLoRA](https://arxiv.org/abs/2305.14314); [PEFT](https://huggingface.co/docs/peft/main/en/developer_guides/quantization)

### Inferences
- Suggested sequence: (1) define canonical schema and scoring; (2) establish prompt-only and OCR/layout baselines; (3) fine-tune a specialist document model and one open VLM adapter using identical real training/validation splits; (4) add synthetic-only and mixed-data runs; (5) compare image-only versus image+OCR; (6) plot quality against labeled examples and GPU-hours.
- Mark every conclusion by evidence level: *demonstrated* for a result measured in the cited setup, *plausible/inference* for proposed recipes, and *unknown* when controlled evidence is unavailable. In particular, don't claim QLoRA itself improves extraction versus LoRA/full fine-tuning: its primary demonstrated advantage is lower memory cost.

### Gaps
- This is a research-backed experimental design, not a published head-to-head invoice benchmark; numerical outcomes must come from the target dataset.

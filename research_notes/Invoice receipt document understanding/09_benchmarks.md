# Visual document understanding and invoice extraction benchmarks

## What the named benchmarks measure, and their strengths and limitations

### Takeaway
The named benchmarks span distinct tasks: question answering (DocVQA, InfographicVQA), OCR/VLM capability probing (OCRBench), structured PDF parsing (OmniDocBench), and end-to-end document linearization (olmOCR-Bench). None alone establishes invoice-field extraction quality; they are useful complementary stress tests, while the most task-aligned measure is held-out invoice-level and field-level evaluation on representative internal data.

### Cited Findings
- DocVQA contains 50,000 questions over more than 12,000 document images; its questions target information retrieval and document understanding, including structurally dependent questions. The paper reports human performance of 94.36% under its evaluation and a notable gap for questions requiring document structure. [Original paper](https://arxiv.org/abs/2007.00398); [official DocVQA site/leaderboard](https://www.docvqa.org/)
- DocVQA uses Average Normalized Levenshtein Similarity (ANLS): normalized edit similarity is used to credit near-matches, with similarities below a 0.5 threshold set to zero; scores are aggregated over questions. This is more tolerant than strict exact match, but can award partial credit when a critical invoice value is wrong by a small edit. [DocVQA paper](https://arxiv.org/abs/2007.00398); [official evaluation repository](https://github.com/VisoFIS/DocVQA)
- InfographicVQA targets infographics and questions requiring joint reasoning over text, layout, graphics, charts, and basic arithmetic; this makes it a useful visual reasoning complement, but its infographic domain is not representative of routine invoice/receipt forms. [Original paper](https://arxiv.org/abs/2104.12756); [official DocVQA site](https://www.docvqa.org/)
- InfographicVQA is evaluated with ANLS in the DocVQA benchmark framework. The score measures answer-string similarity, not whether a system extracted all required fields, validated totals, or preserved line-item structure. [Original paper](https://arxiv.org/abs/2104.12756); [official evaluation repository](https://github.com/VisoFIS/DocVQA)
- OCRBench was introduced as a benchmark for evaluating OCR capabilities of multimodal large language models. It combines 29 datasets across text recognition, scene-text-centric VQA, document-oriented VQA, key information extraction, and handwritten mathematical expression recognition. Its breadth is useful for capability diagnosis, but a single aggregate obscures differences among subtasks and does not represent invoice-specific end-to-end accuracy. [OCRBench original paper](https://arxiv.org/abs/2305.07895); [official project/leaderboard](https://github.com/Yuliang-Liu/MultimodalOCR)
- OCRBench's evaluation includes task-specific answer correctness and reports an aggregate correct-answer score across included task samples; that aggregate should not be conflated with character error rate, ANLS, or invoice field F1. Consult the official evaluator for the precise benchmark version and normalization rules before reproducing a score. [OCRBench paper](https://arxiv.org/abs/2305.07895); [official evaluation code](https://github.com/Yuliang-Liu/MultimodalOCR)
- OmniDocBench is a diverse PDF parsing benchmark with annotations across nine document sources and supports end-to-end, task-specific, and attribute-level evaluation; it includes 19 layout categories and 15 attribute labels. It is valuable for diagnosing layout and parsing error modes, but PDF reconstruction quality and invoice key-value extraction are related rather than equivalent objectives. [Original CVPR 2025 paper](https://arxiv.org/abs/2412.07626); [official dataset/code](https://github.com/opendatalab/OmniDocBench)
- olmOCR-Bench, distributed with the olmOCR toolkit, reports more than 7,000 test cases across 1,400 documents and category-level scores for document OCR/linearization conditions. It directly stress-tests difficult PDF parsing cases, but is maintained by the olmOCR authors and is not an invoice-field benchmark; comparisons should use matching benchmark version, evaluator, and inference conditions. [Official benchmark documentation and results](https://github.com/allenai/olmocr/tree/main/olmocr/bench); [olmOCR technical report](https://arxiv.org/abs/2502.18443)
- The olmOCR repository describes the project as converting image/PDF documents into readable Markdown, supporting tables, equations, handwriting and complex layouts; this underscores its emphasis on document linearization rather than fixed-schema invoice extraction. [Official repository](https://github.com/allenai/olmocr)

### Inferences
- A benchmark panel should report each benchmark independently rather than averaging scores across them: their input domains, targets, and scoring semantics are not commensurate.
- For invoices and receipts, DocVQA/InfographicVQA test visual question answering, OCRBench offers broad OCR diagnostics, and OmniDocBench/olmOCR-Bench stress parsing quality; internal field metrics must carry the acceptance decision.

### Gaps
- The OCRBench repository is the official project/results source; leaderboard standings are not necessarily a stable archived snapshot and should be captured with a date and evaluator version.
- Leaderboard rankings and current scores are time-sensitive. No cross-benchmark current ranking is asserted here.

## Exact match, ANLS, F1, and field-level validation for invoices

### Takeaway
Use strict normalized field exact match and invoice-level all-required-fields exact match as primary operational metrics, supplemented with field-wise precision/recall/F1 and carefully specified tolerance-based numeric measures. ANLS is useful for open-ended answer strings and OCR diagnostics, but should not replace exact correctness for money, dates, identifiers, or tax fields.

### Cited Findings
- Exact match is a binary comparison between normalized prediction and reference. Normalization must be explicitly documented (e.g. whitespace, Unicode, case, punctuation, currency symbols, date formatting); otherwise scores can change because of evaluator conventions rather than extraction quality. For DocVQA, the official metric is ANLS, not invoice structured exact match. [DocVQA evaluation repository](https://github.com/VisoFIS/DocVQA)
- ANLS uses normalized Levenshtein similarity and a 0.5 cutoff (lower similarities receive zero), then averages over examples. It gives partial credit for near-correct textual answers and was designed for VQA answer strings; it can hide a one-character but consequential error in an invoice number or amount. [DocVQA paper](https://arxiv.org/abs/2007.00398)
- For a field treated as a positive extraction, precision = TP/(TP+FP), recall = TP/(TP+FN), and F1 is their harmonic mean. These measures expose omission and hallucination tradeoffs that an answer similarity score does not. Define TP/FP/FN at the field/document level and how missing or inapplicable fields are handled.
- Recommended internal reporting: per-field exact-match rate and support; macro-average across fields; micro aggregate across field instances; document-level exact match requiring all mandatory fields to pass; and separate line-item/table metrics (row matching plus cell-level scores). Report raw counts and confidence intervals, and stratify by document source, quality, language, template novelty, and scan/digital origin.
- Field-level validation should separately test extraction and business rules: typed parsing; currency and decimal conventions; date validity; tax/total arithmetic and subtotal reconciliation; required-field presence; duplicate/line-item handling; and allowed ranges. Report validation-pass rate and extraction accuracy separately so deterministic post-processing does not conceal model mistakes.
- For monetary values, publish both canonical exact equality after safe normalization (e.g. decimal minor units where appropriate) and an explicitly stated tolerance metric when operationally justified. Do not use fuzzy edit distance alone for amounts. For dates, compare parsed calendar values while retaining a separate raw-string metric if formatting is material.

### Inferences
- The right headline metric depends on the business loss: exactness for high-impact values, macro-F1 for field balance, and invoice-level exact match for whether the whole record is usable.
- Add calibration/abstention coverage if the system can defer low-confidence cases to review; compare accuracy at fixed automation coverage and the share routed to human review.

### Gaps
- There is no universal published invoice metric or universal tolerance definition applicable across currencies, tax regimes, and workflows. Choose and document business-specific validation rules.
- Specific commercial invoice-extraction leaderboards and their evaluation protocols were not established in the verified sources above.

## Comparability, leakage, and recommended benchmark practice

### Takeaway
Published scores are comparable only when dataset split, benchmark/evaluator version, prompt, model snapshot, input rendering, OCR/context access, and aggregation are aligned. Public document benchmarks create plausible contamination risk for models trained on web-scale data, but benchmark exposure alone does not prove leakage; maintain a private, temporally refreshed invoice test set and disclose contamination controls.

### Cited Findings
- DocVQA and InfographicVQA are separate task/dataset distributions, and their VQA answer metrics do not measure the same target as OCR transcription or PDF parsing. Their papers define distinct tasks and datasets. [DocVQA paper](https://arxiv.org/abs/2007.00398); [InfographicVQA paper](https://arxiv.org/abs/2104.12756)
- OmniDocBench explicitly motivates broad document sources and fine-grained evaluation because narrow coverage and simplified procedures can make document-parsing assessment unrealistic. Its official paper and dataset provide the benchmark definition and evaluation artifacts. [OmniDocBench paper](https://arxiv.org/abs/2412.07626); [official repository](https://github.com/opendatalab/OmniDocBench)
- olmOCR-Bench results are published alongside a changing open-source project; the repository shows versioned releases and benchmark results, so record the exact benchmark commit/release and model/pipeline version when reproducing or comparing scores. [Official olmOCR repository](https://github.com/allenai/olmocr)
- A leaderboard score should be paired with the official submission protocol and evaluator. Do not compare an API vision model given the rendered page against an OCR+LLM pipeline with extracted text unless the benchmark protocol explicitly permits those different information inputs and the distinction is disclosed.
- Public test exposure, training data inclusion, prompt tuning against test examples, and repeated leaderboard feedback are distinct leakage pathways. Check published data provenance and model training disclosures where available; absent disclosures, label contamination status unknown rather than asserting clean or leaked.
- Internal invoice evaluation should split by supplier/template and preferably time, not only randomly by page, to reduce near-duplicate/template leakage. Deduplicate document images and records, reserve unseen suppliers and document variants, and keep test annotations and feedback inaccessible during model tuning.

### Inferences
- A defensible report should include a benchmark card per result: dataset/version/split, sample count, evaluator commit, preprocessing/render DPI, OCR availability, prompt, model identifier/date, decoding settings, and whether test feedback informed development.
- For practical selection, pair public suites with (1) a frozen internal representative test set, (2) a supplier/template-held-out challenge set, and (3) a live drift set reviewed under privacy controls.

### Gaps
- Public benchmarks generally cannot establish that a proprietary model did not train on their public examples. Treat leakage status as unknown unless the model provider discloses verifiable training exclusions or an independent audit exists.
- Current official leaderboard standings can change. Capture dated snapshots and cite the leaderboard's own protocol rather than quoting undated scores.

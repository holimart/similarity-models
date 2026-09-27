# OCR-free Document Understanding for Invoices and Receipts

## How do Donut and related OCR-free models extract fields, and how reliable is exact field extraction?

### Takeaway
Donut is a direct image-to-structured-sequence encoder–decoder, useful when a document schema and labeled examples can be provided. On the small CORD receipt benchmark it reports strong field and structure metrics, but exact string matching is unforgiving and the evidence does not establish equivalent accuracy on diverse commercial invoices. Nougat is a scientific-document OCR/markup model, not a receipt/invoice IE successor.

### Cited Findings
- Donut combines a Swin visual encoder with a BART-derived text decoder; it generates output tokens autoregressively from the image without an OCR engine, then converts the generated sequence to a structured representation such as JSON. The paper describes field tags and start/end markers; malformed field structures are treated as missing fields. — [Donut paper](https://arxiv.org/abs/2111.15664)
- Donut's document IE evaluation uses field-level F1 and tree-edit-distance (TED) accuracy. The paper explicitly says F1 treats a field as failed if even one character is missed and does not capture partial overlap or nested structure; TED-based accuracy evaluates tree structure as well as content. — [Donut paper](https://arxiv.org/abs/2111.15664)
- On CORD, Donut reports 84.1 field F1 and 90.9 TED accuracy at 1.2 seconds/image (reported on a P40 GPU); the OCR-based LayoutLMv2 baseline reports 78.9 F1 and 82.4 TED accuracy at 1.7 seconds/image. Results are from the authors' experimental setup and are not a cross-paper, controlled hardware comparison. — [Donut paper](https://arxiv.org/abs/2111.15664)
- On the authors' private Korean in-service receipt set (81 unique fields; complex structures), Donut reports 78.6 F1 and 88.6 TED accuracy at 1.9 seconds/image. The data are not fully public, limiting independent reproduction. — [Donut paper](https://arxiv.org/abs/2111.15664)
- The official repo documents the predicted receipt parse as nested JSON-like data (e.g., `menu` arrays and `total` objects), serialized into special-token sequences during model generation. This accommodates variable-length line items and nested groups, but imposes a schema/token-ordering convention that downstream consumers must parse and validate. — [Donut repository](https://github.com/clovaai/donut)
- Donut's authors identify a resolution tradeoff: higher input resolution improves results, particularly for tiny text, but increases computation. They show Donut can miss tiny text in large documents at its input-resolution constraint. — [Donut paper](https://arxiv.org/abs/2111.15664)
- Nougat is based on Donut's encoder–decoder approach but targets page-image-to-markup transcription for academic documents, with 350M-parameter base / 250M small variants and a 4,096 / 3,584 maximum token sequence. It does not provide invoice/receipt key-field schemas or benchmark evidence, so it is pertinent as an architectural descendant, not as an established invoice model. — [Nougat paper](https://arxiv.org/abs/2308.13418)

### Inferences
- For high-assurance workflows (invoice number, tax ID, currency/amounts, totals), benchmark scores alone are insufficient: exact-match field metrics, numeric/date normalization, schema validation, arithmetic consistency checks, and human-review thresholds should be measured on the target domain. This follows from Donut's character-sensitive F1 and its autoregressive output format.
- OCR-free generation avoids a separate OCR-to-parser handoff but moves reading and structuring into one generative model. A plausible operational failure is a coherent-looking but incorrect value; output validity checks do not prove the value was read correctly.

### Gaps
- The cited Donut work does not provide a public, broad commercial-invoice benchmark evaluation. No reliable exact per-field precision/recall for invoice identifiers, vendor, dates, tax, currency, or totals was found in these primary sources.
- The private receipt set's full data, annotation instructions, and independent re-evaluation are unavailable in the cited paper.

## What data and benchmarks support conclusions for receipts and invoices?

### Takeaway
CORD is the directly relevant public receipt parsing benchmark, but it is small and Indonesian; SROIE is another receipt benchmark with distinct OCR and key-information tasks. Donut's reported results are promising on CORD and on private receipts, while neither cited source establishes broad invoice generalization.

### Cited Findings
- CORD is a receipt dataset for post-OCR parsing with over 11,000 Indonesian receipts described on its repository page; its released v1/v2 benchmark splits each contain 800 train, 100 validation, and 100 test images. It includes fine-grained receipt labels and hierarchical/group information. — [CORD repository](https://github.com/clovaai/cord)
- The CORD v2 Hugging Face dataset card identifies CC BY 4.0 licensing and 1,000 total samples (800/100/100). It shows structured labels including menu entries, subtotal, tax, total, payment and change. — [CORD v2 dataset card](https://huggingface.co/datasets/naver-clova-ix/cord-v2)
- CORD's original scope is specifically “post-OCR parsing”; its images and labels support OCR and semantic parsing, so Donut uses its structured parse labels for end-to-end training rather than relying on the benchmark's OCR pipeline. — [CORD repository](https://github.com/clovaai/cord); [Donut repository](https://github.com/clovaai/donut)
- SROIE defines scanned-receipt text localization, OCR, and key-information extraction tasks and introduces 1,000 whole scanned receipt images with annotations. — [ICDAR 2019 SROIE competition paper](https://arxiv.org/abs/2103.10213)
- Donut's receipt training/evaluation disclosures include CORD and a private Korean dataset. The paper also evaluates train tickets and business cards, not invoices, and reports results on the authors' own evaluation setup. — [Donut paper](https://arxiv.org/abs/2111.15664)
- Donut pretraining uses 11M scanned English IIT-CDIP documents with pseudo-text labels from CLOVA OCR and 0.5M SynthDoG samples per language in English, Chinese, Japanese, and Korean. SynthDoG generates varied document-like images from background/document textures, Wikipedia text, and rule-generated layouts. — [Donut paper](https://arxiv.org/abs/2111.15664); [Donut repository](https://github.com/clovaai/donut)
- The official Donut repository says the published multilingual `donut-base` pretraining run used 64 A100 GPUs for about 2.5 days; the training setup is also documented in the paper (200K steps, effective mini-batch 196). — [Donut repository](https://github.com/clovaai/donut); [Donut paper](https://arxiv.org/abs/2111.15664)

### Inferences
- CORD is suitable for a reproducible receipt-parser baseline and schema experimentation, but its 100-image test split and single-country receipt context make it weak evidence for cross-retailer, cross-country, or invoice readiness. Target-domain validation is essential.
- For invoices, training data should represent the actual supplier/template distribution, languages, scan quality, line-item depth, and jurisdiction-specific tax/field conventions; broad document pretraining does not replace labeled task examples.

### Gaps
- The cited primary sources do not establish Donut performance on common invoice-specific public benchmarks such as a diverse vendor invoice corpus. Invoice-specific transfer results and field-level results were not located.
- Cross-dataset comparisons among CORD, SROIE, and commercial invoice tasks are not directly comparable because labels, splits, metrics, and input/task definitions differ.

## What are inference, deployment, failure-mode, weights, and license considerations?

### Takeaway
Donut is substantially smaller and faster than its full pretraining cost might imply at inference, and pretrained receipt weights are readily downloadable. Production use still needs GPU/resource benchmarking, output validation, dependency testing, and a careful check that software, weights, and data licenses all fit the use case.

### Cited Findings
- Donut's paper reports a 143M-parameter model and CORD inference of 1.2 s/image on an NVIDIA P40; it also reports 0.7 s/image at 1280×960 with TED accuracy 91.1, versus the higher-resolution configuration's 90.9/91.3 score variants reported in the official table. Latency depends on task, input resolution, batch/implementation, and hardware. — [Donut paper](https://arxiv.org/abs/2111.15664); [official model table](https://github.com/clovaai/donut)
- The CORD v2 fine-tuned model repository provides a PyTorch checkpoint of about 806 MB (repository total about 812 MB) and is marked MIT licensed; the checkpoint is listed as a pickle-format `.bin`. — [Donut CORD-v2 model repository](https://huggingface.co/naver-clova-ix/donut-base-finetuned-cord-v2/tree/main)
- The Donut implementation repository is MIT licensed and cautions that updated dependencies have created configuration/testing difficulties for `donut-python`; it lists an older tested stack and provides Colab demos. — [Donut repository](https://github.com/clovaai/donut)
- CORD itself is published under CC BY 4.0, separately from the Donut code and weights. — [CORD repository](https://github.com/clovaai/cord); [CORD v2 dataset card](https://huggingface.co/datasets/naver-clova-ix/cord-v2)
- Donut's paper shows sensitivity to image resolution and the possibility of missing tiny text; its CORD setup can reach better performance with higher resolution at added compute cost. — [Donut paper](https://arxiv.org/abs/2111.15664)
- Nougat reports a repetitive-generation loop on 1.5% of its in-domain test pages, increasing out of domain; with greedy decoding it may fail to recover. Its paper reports that on an NVIDIA A10G 24GB, six pages can be processed in parallel, with about 19.5 seconds per batch for base at roughly 1,400 generated tokens/page, without inference optimization. These are Nougat-specific academic-document findings, not Donut receipt benchmarks. — [Nougat paper](https://arxiv.org/abs/2308.13418)
- Nougat's declared training distribution is overwhelmingly academic documents (over 91.5% arXiv); the paper reports weaker performance on scanned books than digital-born academic documents and warns that non-Latin scripts can produce immediate repetition. — [Nougat paper](https://arxiv.org/abs/2308.13418)

### Inferences
- A CORD-finetuned Donut checkpoint is a practical starting point for receipt prototyping, but its domain and schema are CORD-specific; fine-tuning and local evaluation should precede production use on invoices or other receipt geographies.
- “OCR-free” does not mean compute-free: image encoding plus token-by-token decoding means output length and resolution affect throughput. Deployment sizing should measure realistic document images and generation limits on the intended hardware.
- MIT code/weights and CC BY dataset terms are distinct objects; verify the exact model revision and its files' license metadata, and review dataset rights independently before redistributing trained artifacts.

### Gaps
- Donut primary sources do not state a minimum inference VRAM, CPU-only throughput, quantized performance, or an exhaustive hardware matrix. Inference should be profiled on intended deployment equipment.
- The accessed Nougat paper/repository evidence does not confirm a current weight license suitable for every commercial use; check the exact official model-card and weight terms before adoption. Nougat is not recommended as an invoice/receipt extractor based on the cited benchmark evidence.
- No independent, controlled same-hardware comparison of Donut against current OCR-plus-IE systems on a representative invoice corpus was located.

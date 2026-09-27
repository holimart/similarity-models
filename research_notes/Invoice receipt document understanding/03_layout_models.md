# Layout-aware document AI and token/tagging models for invoice and receipt extraction

## How the model families represent document structure

### Takeaway
These systems range from text-plus-box token taggers to multimodal image/text Transformers and explicit relation parsers. For scanned invoices and receipts, the practical choice is usually a pretrained token classifier when OCR words/boxes are available, versus an image-aware model when visual evidence beyond OCR (logos, checkboxes, typography, image defects) matters.

### Cited Findings
- LayoutLM jointly represents wordpiece text, 2D bounding-box position, and (in its image-aware variant) visual embeddings; its document pretraining uses masked visual-language modeling. The paper reported form-understanding score 79.27, receipt-understanding score 95.24, and document classification 94.42, improving over its BERT baselines. [LayoutLM paper](https://arxiv.org/abs/1912.13318)
- LayoutLMv2 combines text and image streams in a multimodal Transformer, adds spatial-aware self-attention, and pretrains with masked visual-language modeling, text-image alignment, and text-image matching. Reported benchmark scores include CORD 0.9601 and SROIE 0.9781. [LayoutLMv2 paper](https://arxiv.org/abs/2012.14740)
- LayoutLMv3 uses a unified text/image Transformer with image patch embeddings (rather than LayoutLMv2's CNN visual backbone), masked language modeling, masked image modeling, and word-patch alignment. It reports state-of-the-art results on text- and image-centric document tasks, including receipts. [LayoutLMv3 paper](https://arxiv.org/abs/2204.08387); [official Microsoft repository](https://github.com/microsoft/unilm/tree/master/layoutlmv3)
- BROS (BERT Relying On Spatiality) deliberately omits image features: it encodes relative 2D positions between text regions and pretrains on unlabeled documents with area masking. Its paper reports competitive or better results on FUNSD, SROIE*, CORD, and SciTSR, emphasizing KIE and robustness to text-ordering errors and limited downstream labels. [BROS paper](https://arxiv.org/abs/2108.04539); [official ClovaAI repository](https://github.com/clovaai/bros)
- SPADE (Spatial Dependency Parsing) casts extraction as parsing relations among text entities, rather than independent BIO tagging. The decoder predicts semantic relations/edges, from which structured key-value outputs are assembled; this directly models relationships such as a field label linked to its value. [Paper search/source record](https://aclanthology.org/search/?q=SPADE%20document%20information%20extraction); implementation: [clovaai/spade](https://github.com/clovaai/spade)
- LiLT (Language-independent Layout Transformer) separates language-specific text representation from language-agnostic layout representation and is designed to transfer layout knowledge across languages. It can pair its layout network with a language model suited to the target script/language. [LiLT paper](https://arxiv.org/abs/2202.13669); [official repository](https://github.com/jpzhangacs/LiLT)
- StrucTexT is a multimodal document model aimed at text, visual appearance, and layout structure; it combines textual semantics, visual features, and spatial structure with pretraining objectives for document understanding. [StrucTexT paper](https://arxiv.org/abs/2108.02394); [PaddleOCR implementation](https://github.com/PaddlePaddle/PaddleOCR/tree/release/2.7/ppstructure)
- TILT uses a pretrained encoder-decoder Transformer with layout represented as attention bias and contextual image features; the decoder unifies extraction, document QA, and related generation tasks. Its paper reports strong results on DocVQA, CORD, and SROIE. [TILT paper](https://arxiv.org/abs/2102.09550)

### Inferences
- Token tagging is a natural fit for normalized invoice fields with word-level annotations; relation parsing can better preserve key/value and line-item associations when output structure is relational or repeated.
- BROS and LiLT reduce dependence on pixel appearance, potentially lowering preprocessing and inference cost; they cannot recover visual-only cues that OCR text and geometry do not expose.
- The image stream in LayoutLMv2/v3 and StrucTexT may help on poor scans, stamps, logos, and visual grouping, but increases system complexity and compute.

### Gaps
- Exact SPADE/StrucTexT bibliographic metadata and reproducible benchmark table values were not confirmed from the source pages retrieved; avoid treating non-primary repository summaries as paper results.
- Published benchmark numbers are not directly comparable unless OCR, data splits, annotation schemes, and scoring protocols match.

## Benchmarks, datasets, results, and multilingual coverage

### Takeaway
CORD and SROIE provide common receipt extraction tests, while FUNSD tests noisy forms and XFUND tests multilingual form understanding. Strong benchmark scores demonstrate transfer on those curated domains, not guaranteed performance on diverse production invoices or languages absent from pretraining/fine-tuning.

### Cited Findings
- LayoutLM reports receipt-understanding 95.24 versus 94.02 for its baseline; LayoutLMv2 reports CORD 0.9601 and SROIE 0.9781, compared with LayoutLM's 0.9493 and 0.9524 respectively in the paper's table. [LayoutLM](https://arxiv.org/abs/1912.13318); [LayoutLMv2](https://arxiv.org/abs/2012.14740)
- LayoutLMv2 also reports FUNSD 0.8420 versus 0.7895 and DocVQA 0.8672 versus 0.7295, showing gains beyond receipt extraction. [LayoutLMv2 paper](https://arxiv.org/abs/2012.14740)
- BROS evaluates FUNSD, SROIE*, CORD, and SciTSR, and explicitly studies sensitivity to incorrect OCR text ordering and few downstream examples. [BROS paper](https://arxiv.org/abs/2108.04539)
- LayoutLMv3's official code documents fine-tuning on FUNSD and XFUND and offers a Chinese pretrained checkpoint; repository example results include FUNSD F1 0.9059 (base) and 0.9215 (large), and Chinese XFUND F1 0.9202. These are implementation-reported results, not a cross-paper controlled comparison. [LayoutLMv3 repo](https://github.com/microsoft/unilm/tree/master/layoutlmv3)
- LayoutLMv3's official repository specifies English base/large and Chinese base checkpoints, and includes an XFUND Chinese fine-tuning example. [LayoutLMv3 repo](https://github.com/microsoft/unilm/tree/master/layoutlmv3)
- LiLT's stated goal is cross-lingual document understanding via language-independent layout modeling; that does not by itself make text semantics language-independent—the paired text encoder and its script coverage still matter. [LiLT paper](https://arxiv.org/abs/2202.13669)
- LayoutLMv3 uses byte-level BPE, expects word-level normalized boxes (0–1000), and its documented image processor defaults to Tesseract English OCR unless configured otherwise. [Transformers LayoutLMv3 docs](https://huggingface.co/docs/transformers/model_doc/layoutlmv3)

### Inferences
- For multilingual deployment, choose a strong multilingual language encoder or language-specific checkpoint, validate OCR accuracy per language/script, and create representative labeled examples; geometric transfer alone does not guarantee semantic transfer.
- Receipt results should not be assumed to predict invoice performance: invoices tend to have variable page counts, complex tables, and repeated line-item structures that differ from receipt benchmark fields.
- OCR ordering and box normalization are model inputs and sources of error, not incidental preprocessing details.

### Gaps
- No retrieved primary source provided a consistent head-to-head multilingual invoice/receipt evaluation across all listed families.
- A precise language-by-language coverage matrix and supported scripts for each checkpoint require verification against current model cards and tokenizer vocabularies.

## Fine-tuning feasibility, strengths, and limitations

### Takeaway
Fine-tuning pretrained checkpoints for token classification is practical with modest task datasets and one or a few GPUs, but preprocessing/OCR alignment and annotation quality dominate much of the engineering effort. Full pretraining is a very different compute scale; reproducing benchmark papers' pretraining is generally not necessary for an application.

### Cited Findings
- The official LayoutLMv3 repo's FUNSD fine-tuning example uses the base checkpoint, batch size 2 per device, learning rate 1e-5, 1,000 steps, and an eight-process launch; the XFUND example also uses 1,000 steps and batch size 2 per device. These settings show a reference distributed recipe, not a minimum hardware requirement. [LayoutLMv3 repository](https://github.com/microsoft/unilm/tree/master/layoutlmv3)
- Hugging Face documents token-classification heads and processors for LayoutLMv3 and word labels aligned to word-level bounding boxes; image input is resized and normalized, and labels can be assigned to first subwords. [Transformers LayoutLMv3 documentation](https://huggingface.co/docs/transformers/model_doc/layoutlmv3)
- LayoutLMv3's official setup lists PyTorch, Detectron2 and CUDA-specific install steps for its original repository; the Hugging Face Transformers integration offers a simpler fine-tuning path for common token-classification tasks. [Official repo](https://github.com/microsoft/unilm/tree/master/layoutlmv3); [Transformers docs](https://huggingface.co/docs/transformers/model_doc/layoutlmv3)
- BROS's text-and-layout-only design avoids the image feature stream and is presented as effective for few-example KIE fine-tuning. [BROS paper](https://arxiv.org/abs/2108.04539)
- LayoutLMv2/v3's multimodal inputs require image processing in addition to OCR words and boxes; v3's patch embeddings and common 512-token sequence limit are reflected in the reference configuration/documentation. [LayoutLMv2](https://arxiv.org/abs/2012.14740); [LayoutLMv3 config/docs](https://huggingface.co/docs/transformers/model_doc/layoutlmv3)

### Inferences
- A strong initial baseline is a pretrained base-size token tagger with fixed OCR, word boxes, and field-level BIO labels; compare a text/layout model (BROS or LiLT) against an image-aware LayoutLMv3 model on the same held-out documents.
- Include end-to-end entity/value exact match and document-level field accuracy, not token F1 alone; add line-item row association and numeric/date normalization checks for invoices.
- Consider sequence chunking or page-level processing when OCR exceeds a model's token limit, preserving page IDs and spatial references when merging predictions.
- Fine-tune from weights rather than pretraining from scratch; use parameter-efficient tuning only if model and tooling support it, since the surveyed benchmark recipes primarily show ordinary supervised fine-tuning.

### Gaps
- Sources retrieved do not establish reliable GPU memory, elapsed-time, or cost minima for comparable fine-tuning runs across these architectures; hardware and image resolution/batch settings make such estimates deployment-specific.
- No cited paper establishes expected performance on a particular private invoice distribution; evaluation requires a representative, vendor/template-separated test set.

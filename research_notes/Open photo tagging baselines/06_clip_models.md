# Open CLIP-Compatible Zero-Shot Image Models

## Which model families are practical for local CPU/GPU photo tagging, and how easy are they to run?

### Takeaway

All three families can score a user-supplied list of text labels against an image locally with PyTorch; no hosted inference service is required. OpenAI CLIP is the smallest, narrowest/easiest baseline; OpenCLIP is the broadest model/checkpoint ecosystem; SigLIP is straightforward through Transformers and produces independent label scores that fit multi-tagging naturally.

### Cited Findings

- OpenAI's official `clip.load()` downloads one of its named models or accepts a local checkpoint path, selects CPU when CUDA is unavailable, and returns preprocessing alongside the model. Its example ranks text labels by similarity/softmax. [OpenAI CLIP repository](https://github.com/openai/CLIP)
- OpenAI's official released architectures include RN50, RN101, RN50x4/x16/x64, ViT-B/32, ViT-B/16, ViT-L/14, and ViT-L/14@336px. [OpenAI CLIP model card](https://github.com/openai/CLIP/blob/main/model-card.md)
- OpenCLIP installs with `pip install open_clip_torch`; its documented inference path loads named model + pretrained checkpoint through `create_model_and_transforms`, or a local checkpoint path, and supplies a tokenizer. Checkpoint and model lists are queryable in the library. [OpenCLIP repository](https://github.com/mlfoundations/open_clip)
- OpenCLIP hosts many architecture/checkpoint/data combinations, including ViT-B/32 through much larger ViT-H/g/bigG and SigLIP-family options; its pretrained documentation points to model-specific Hub cards and reports zero-shot results across 38 datasets. [OpenCLIP pretrained models](https://github.com/mlfoundations/open_clip/blob/main/docs/PRETRAINED.md)
- Hugging Face Transformers documents SigLIP as a local PyTorch `AutoModel` + `AutoProcessor` workflow and offers a `zero-shot-image-classification` pipeline. SigLIP prompts may be prepared as `This is a photo of {label}.`; its tokenizer should pad to `max_length`. [Transformers SigLIP guide](https://huggingface.co/docs/transformers/model_doc/siglip)
- The Google `siglip-base-patch16-224` Hub card documents its model usage, zero-shot classification, Apache-2.0 license, and size of 0.2B parameters. [SigLIP base model card](https://huggingface.co/google/siglip-base-patch16-224)
- OpenCLIP's README explicitly warns that pretrained checkpoints may require model definitions with `-quickgelu` to match training activation, and notes that the helper returns checkpoint-appropriate transforms. [OpenCLIP repository](https://github.com/mlfoundations/open_clip)

### Inferences

- For lowest-friction experiments where a compact, well-known baseline is enough, begin with OpenAI ViT-B/32 or RN50. For experimentation across training recipes and model sizes, OpenCLIP's broad registry is the most flexible. For multilabel scoring and a polished Transformers API, SigLIP is especially convenient.
- All families run on CPU in principle; GPU is beneficial for throughput, especially when scoring many images or using larger checkpoints. CPU suitability is not a promise of interactive speed: inference throughput depends on CPU, precision, image resolution, batch size, and checkpoint size.
- Rule-of-thumb raw weight storage at FP32 is about 4 bytes per parameter (e.g., 0.2B parameters ≈0.8 GB decimal, before runtime/activations); FP16/BF16 weights are about half that. Treat this as a memory estimate, not a published checkpoint download size or peak RAM/VRAM requirement.

### Gaps

- The official OpenAI README/model card does not give a clean comparable parameter-count/download-size table or CPU throughput benchmark for every released checkpoint.
- OpenCLIP has too many independently licensed checkpoints for a single family-wide license or disk-size figure; assess the exact Hub model card and checkpoint before adoption.
- No comparable CPU/GPU latency benchmark under a fixed setup was found in the cited official materials.

## How do sizes and licenses compare, and what should be checked before choosing a checkpoint?

### Takeaway

Architecture name and family name alone do not settle resource requirements or usage rights. Choose a specific checkpoint with documented weights, intended image resolution, and model license; among readily documented examples, SigLIP base is 0.2B parameters and Apache-2.0, while OpenAI CLIP code is MIT but its model card makes restrictive deployment recommendations.

### Cited Findings

- OpenAI's repository is MIT-licensed, but that code license should not be conflated with a blanket statement about model use. [OpenAI CLIP repository](https://github.com/openai/CLIP)
- The OpenAI model card says the model was intended as a research output; deployed use (commercial or otherwise) is out of scope, and even constrained image search is not recommended without thorough in-domain testing with a fixed taxonomy. It also says use should be limited to English. [OpenAI CLIP model card](https://github.com/openai/CLIP/blob/main/model-card.md)
- OpenCLIP is an implementation supporting models trained by different organizations on different datasets; its pretrained documentation identifies licenses for some subfamilies (for example, SigLIP Apache-2.0, MetaCLIP CC-BY-NC, EVA-CLIP MIT, and CLIPA Apache-2.0), rather than assigning one license to every checkpoint. [OpenCLIP pretrained models](https://github.com/mlfoundations/open_clip/blob/main/docs/PRETRAINED.md)
- The Google SigLIP base Hub card lists Apache-2.0, 0.2B parameters, 224×224 image resolution and a 64-token text padding length; it describes WebLI English image-text pretraining. [SigLIP base model card](https://huggingface.co/google/siglip-base-patch16-224)
- OpenCLIP reports that its ViT-B/32 LAION-2B model obtains 65.62% zero-shot ImageNet top-1, and larger architectures/checkpoints are available; these numbers are benchmark results, not guarantees for photo-tagging taxonomies. [OpenCLIP pretrained models](https://github.com/mlfoundations/open_clip/blob/main/docs/PRETRAINED.md)
- SigLIP's model card describes separate image and text encoders and a sigmoid pairwise objective; its documentation example applies sigmoid to image-text logits to obtain per-pair scores. [SigLIP base model card](https://huggingface.co/google/siglip-base-patch16-224); [Transformers SigLIP guide](https://huggingface.co/docs/transformers/model_doc/siglip)

### Inferences

- For local photo tagging where licensing simplicity matters, a named SigLIP checkpoint labeled Apache-2.0 is easier to evaluate legally than assuming all OpenCLIP checkpoints share the code repository's license. Verify the exact card and any additional terms for downstream use.
- OpenAI CLIP's MIT repository license permits use of the code under MIT terms, but the model card's explicit out-of-scope deployment statement is a separate important constraint; it is not the most straightforward choice for a deployed tagging product.
- Use model architecture/parameter count as a rough resource indicator only. Parameter count does not capture preprocessing, text encoder, runtime overhead, precision, or larger input resolution; compare actual checkpoint files and test peak memory locally.

### Gaps

- Official checkpoint pages vary in whether they clearly state the license and file size; no universal license or storage figure can be asserted for OpenCLIP.
- The SigLIP base card is HF-authored and explicitly says Google did not write a model card for that release; it points to Google's original Big Vision repository for the initial release. [SigLIP base model card](https://huggingface.co/google/siglip-base-patch16-224)

## How should prompts, zero-shot tags, and score thresholds be handled?

### Takeaway

Use natural-language photo prompts and treat scores as model- and candidate-set-dependent ranking signals, not universal calibrated confidence. For multiple simultaneous tags, SigLIP's independent sigmoid scores avoid CLIP's competition between labels in a candidate-set softmax; thresholds should be tuned on a representative labeled sample.

### Cited Findings

- OpenAI's canonical zero-shot example creates one prompt per class (`a photo of a {class}`), computes image/text embeddings, normalizes them, then applies a softmax across the provided class labels. Its model forward returns cosine similarities scaled by 100. [OpenAI CLIP repository](https://github.com/openai/CLIP)
- OpenAI's model card warns that performance can vary significantly with class design and which categories are included/excluded; it also notes limitations in fine-grained classification and object counting. [OpenAI CLIP model card](https://github.com/openai/CLIP/blob/main/model-card.md)
- The Hugging Face SigLIP guide recommends matching the pipeline prompt template, `This is a photo of {label}.`, and shows sigmoid of image-text logits for probabilities; it explicitly uses max-length padding. [Transformers SigLIP guide](https://huggingface.co/docs/transformers/model_doc/siglip)
- The SigLIP model card demonstrates the same use for candidate labels and describes its output as sigmoid probabilities for individual image/text pairs. [SigLIP base model card](https://huggingface.co/google/siglip-base-patch16-224)
- OpenCLIP's documented inference example normalizes the image/text embeddings and applies softmax across text candidates, paralleling original CLIP; its models are evaluated zero-shot using task-specific datasets and protocols. [OpenCLIP repository](https://github.com/mlfoundations/open_clip); [OpenCLIP pretrained models](https://github.com/mlfoundations/open_clip/blob/main/docs/PRETRAINED.md)

### Inferences

- For exclusive classification, CLIP/OpenCLIP softmax is useful to rank a fixed set. For open-vocabulary tags that can co-occur (e.g., “beach,” “sunset,” and “people”), CLIP softmax scores sum to one over the supplied labels and change when candidates are added/removed; do not interpret these as independent tag probabilities. SigLIP sigmoid scores are per-prompt and need not sum to one, which better matches independent multi-label decisions, but still require calibration.
- Build a stable label vocabulary and use consistent prompt syntax (e.g., `a photo of {tag}`); compare prompt variants on sample images because wording, specificity, synonyms, and negative/competing labels can change rankings. Cache text embeddings for fixed prompts where the library permits.
- For any family, tune per-label or global thresholds against a small representative validation set, optimizing the desired precision/recall tradeoff. Review false positives and missed tags; there is no justified universal cutoff supplied by the cited project documentation.
- If tag presence is the goal, score each tag independently rather than forcing one winner. Consider both prompt ensembles (averaging embeddings or scores across phrasing variants) and hierarchical tags, but validate any such choices empirically.

### Gaps

- Official sources do not prescribe universal probability thresholds or provide calibrated confidence guarantees for arbitrary photo collections and custom tag vocabularies.
- Comparative zero-shot tagging accuracy for a specific personal-photo domain cannot be inferred from ImageNet headline scores; it requires a domain-specific evaluation set.

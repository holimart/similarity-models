# Local open image-captioning VLMs for photo tagging

## Which checkpoints are practical captioning baselines, and how do they differ?

### Takeaway

For straightforward single-sentence photo captions, start with BLIP image-captioning-base and Florence-2-base-ft: both are compact enough to run locally, and their task interfaces are purpose-built for image-to-text. Add GIT-base-coco as a simple MIT-licensed comparison; treat BLIP-2, PaliGemma, SmolVLM, and Qwen2.5-VL as broader generative VLMs rather than interchangeable caption-only models.

### Cited Findings

- **BLIP image-captioning-base** is a COCO-caption-finetuned ViT-base image captioner. Its card explicitly demonstrates unconditional captions and prompt-conditioned captions (for example, prefixing “a photography of”); card license is BSD-3-Clause. [Model card](https://huggingface.co/Salesforce/blip-image-captioning-base); [BLIP paper](https://arxiv.org/abs/2201.12086)
- **BLIP image-captioning-large** is the same captioning family with a ViT-large backbone. Its model card reports 0.5B parameters and BSD-3-Clause, versus base’s smaller backbone; both cards show direct CPU loading and CUDA/FP16 examples. [Large model card](https://huggingface.co/Salesforce/blip-image-captioning-large); [base model card](https://huggingface.co/Salesforce/blip-image-captioning-base)
- **BLIP-2 OPT-2.7B** is not just “larger BLIP captioning”: it combines an image encoder, Q-Former, and OPT language model; the checkpoint is pre-trained rather than a caption-specific COCO fine-tune. The card lists MIT for this checkpoint and shows CPU and GPU examples. It can generate image descriptions, but the multi-billion-parameter language model adds substantial deployment cost for routine tagging. [Model card](https://huggingface.co/Salesforce/blip2-opt-2.7b); [BLIP-2 paper](https://arxiv.org/abs/2301.12597)
- **GIT-base-coco** is a base-sized generative image-to-text checkpoint fine-tuned on COCO; HF’s card says the base model was trained on 10M image-text pairs before COCO fine-tuning, and describes a CLIP-like image encoder plus text decoder. Card license is MIT. It is an uncomplicated, caption-focused baseline, but the card does not itself publish runtime or comparative evaluation numbers. [Model card](https://huggingface.co/microsoft/git-base-coco); [GIT paper](https://arxiv.org/abs/2205.14100)
- **Florence-2-base-ft** is a 0.23B-parameter, MIT-licensed multi-task vision model fine-tuned on downstream tasks; it provides explicit `<CAPTION>`, `<DETAILED_CAPTION>`, and `<MORE_DETAILED_CAPTION>` prompts, as well as detection, OCR, and region-caption tasks. The model card reports COCO Caption Karpathy test CIDEr 140.0 for base-ft and 143.3 for large-ft, but this is the authors’ reported benchmark rather than a guarantee of photo-tagging quality on a new collection. [Base model card](https://huggingface.co/microsoft/Florence-2-base-ft); [Florence-2 paper](https://arxiv.org/abs/2311.06242)
- **SmolVLM-500M-Instruct** (2025) is an Apache-2.0, 0.5B-parameter conversational VLM, not a dedicated captioning checkpoint. Its card says it supports image descriptions and reports 1.23 GB GPU RAM for one-image inference; its image compression and 93M-parameter vision encoder are designed for efficiency. The instruction interface accepts a prompt such as “Describe this image.” [Model card](https://huggingface.co/HuggingFaceTB/SmolVLM-500M-Instruct); [SmolVLM paper](https://arxiv.org/abs/2504.05299)
- **PaliGemma 3B pt-224** illustrates an important checkpoint distinction: the `pt` checkpoint is pre-trained for transfer, while the card says the family works best after task-specific fine-tuning and is not designed to be used directly; `mix` variants are fine-tuned mixtures more suitable for interactive trials. The 3B model has a Gemma license (Google terms/conditions apply), so do not call it permissively open-source. [Model card](https://huggingface.co/google/paligemma-3b-pt-224); [PaliGemma paper](https://arxiv.org/abs/2407.07726)
- **Qwen2.5-VL-3B-Instruct** is a recent general-purpose instruct VLM with dynamic image resolution and image localization/structured-output capabilities. The card’s one-image example uses a free-form “Describe this image” prompt; its range of visual token counts means compute depends materially on image resolution. The card specifies 3B parameters; model availability is open on HF, but check the repository’s current license metadata and terms before redistribution or commercial deployment. [Model card](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct); [Qwen2-VL paper cited by the card](https://arxiv.org/abs/2409.12191)

### Inferences

- The cleanest apples-to-apples caption benchmark set is BLIP-base, BLIP-large, GIT-base-coco, and Florence-2-base-ft: their released weights are caption-finetuned or include a defined caption task. Use natural-language VLMs as a second tier if prompt flexibility, OCR, or richer descriptions matter.
- For controlled photo tagging, test both short and detailed caption modes on Florence-2 and use a fixed short prompt on instruction models. Longer, more elaborate descriptions are not automatically better tags and create more opportunity for unsupported details.
- “Open” should be separated into downloadable weights and permissive licensing. MIT, BSD-3-Clause, and Apache-2.0 are relatively permissive; Gemma terms are a distinct license regime. Confirm the precise license of the exact checkpoint and its component dependencies for a production decision.

### Gaps

- No single controlled evaluation across these checkpoints on the target photo collection was located; public COCO CIDEr scores do not settle relative precision, useful tag density, hallucination, or domain suitability.
- Upstream model cards do not provide comparable CPU throughput or end-to-end batch latency for a fixed machine and image size.

## What do weights, licenses, and memory imply for local CPU and GPU use?

### Takeaway

BLIP-base and Florence-2-base-ft are the strongest low-friction local starts; SmolVLM is the very-small generalist alternative, while BLIP-2/PaliGemma/Qwen are heavier generalists. Parameter count gives only a lower-bound estimate of weight storage; actual peak RAM/VRAM also includes activations, image resolution, generation cache, framework overhead, and batching.

### Cited Findings

- HF reports about 0.23B parameters for Florence-2-base and base-ft and 0.77B for large variants; the card says released model weights were trained in FP16, and its example explicitly selects FP32 for CPU and FP16 for CUDA. Approximate raw parameter storage is therefore 0.46 GB at FP16 or 0.92 GB at FP32 for 0.23B parameters, before runtime overhead. [Florence-2 card](https://huggingface.co/microsoft/Florence-2-base)
- SmolVLM-500M’s card directly reports 1.23 GB GPU RAM for one-image inference, recommends BF16 where supported, and supports quantization methods including bitsandbytes, torchao, or Quanto. This is the most concrete one-image GPU-memory figure among the reviewed small checkpoints, but it is not a CPU speed figure. [SmolVLM card](https://huggingface.co/HuggingFaceTB/SmolVLM-500M-Instruct)
- BLIP-base’s model card includes an actual CPU inference example and CUDA FP32 and FP16 examples, confirming supported execution paths; it publishes no timing or RAM/VRAM number. BLIP-large’s card likewise shows CPU and GPU inference paths. [BLIP-base card](https://huggingface.co/Salesforce/blip-image-captioning-base); [BLIP-large card](https://huggingface.co/Salesforce/blip-image-captioning-large)
- BLIP-2 OPT-2.7B’s card gives approximate model-size memory (not full inference peak) of 7.21 GB at FP16/BF16, 3.61 GB at INT8, and 1.8 GB at INT4. Its separate “largest layer/residual group” and “training using Adam” columns should not be confused with inference-memory requirements. CPU and CUDA examples are provided, but no CPU throughput claim is made. [BLIP-2 card](https://huggingface.co/Salesforce/blip2-opt-2.7b)
- PaliGemma’s model card documents FP32 CPU inference and BF16/FP16 CUDA, plus 4-/8-bit loading with bitsandbytes; the 3B checkpoint’s raw parameter storage is approximately 6 GB FP16 or 12 GB FP32, before overhead. The card requires accepting Google’s usage terms to access weights. [PaliGemma card](https://huggingface.co/google/paligemma-3b-pt-224)
- Qwen2.5-VL-3B’s model card recommends `device_map="auto"` and BF16/FlashAttention 2 for CUDA, and explains that input image token count varies with resolution (the card gives a 256–1280 visual-token range as one speed/memory tradeoff). Thus fixed “per-image” memory estimates are especially misleading without a specified resize policy. [Qwen2.5-VL card](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct)
- GIT-base-coco’s card confirms the MIT checkpoint and points to Transformers usage but does not include hardware memory/timing data; parameter count/runtime should be verified from the actual repository weights and tested in the intended stack rather than inferred from the broader GIT paper’s much larger configurations. [GIT-base-coco card](https://huggingface.co/microsoft/git-base-coco); [GIT paper](https://arxiv.org/abs/2205.14100)

### Inferences

- In FP32, weight-only storage is approximately 4 bytes per parameter; FP16/BF16 is approximately 2 bytes, INT8 about 1 byte, and INT4 about 0.5 byte. These are arithmetic estimates, not reported end-to-end RAM/VRAM measurements; quantization metadata and non-weight tensors add overhead.
- Modern consumer GPUs with several GB of free VRAM are a reasonable target for the sub-billion-parameter group at FP16/BF16, but the SmolVLM 1.23-GB figure is the only reviewed card’s explicit peak-like figure. On CPU, all listed cards that provide explicit usage examples demonstrate CPU execution for BLIP/BLIP-2/PaliGemma, and Florence supplies a CPU code path; that establishes feasibility, not acceptable throughput.
- For a CPU-only photo archive, begin with BLIP-base or Florence-2-base-ft and measure images/second on the actual host. Avoid promising “real-time” or fleet-scale throughput from model size alone.
- Keep input resolution and output-token limits fixed in comparisons. Higher-resolution crops and longer generated text can dominate the cost of a nominally small model.

### Gaps

- Comparable measured CPU latency, throughput, peak system RAM, GPU VRAM, quantized quality loss, and batch-size scaling are not published consistently by the cited model cards. These require a local benchmark on the target hardware/software.
- Exact downloadable file sizes can vary by format/revision (FP32, FP16, BF16, safetensors); check the selected Hub revision rather than treating parameter-count estimates as download sizes.

## Which models should be included in a photo-tagging bake-off?

### Takeaway

Use a small, diverse shortlist: BLIP-base (caption-native baseline), Florence-2-base-ft (small multi-task, controllable caption styles), GIT-base-coco (MIT caption-specialized comparator), and SmolVLM-500M-Instruct (recent tiny generalist). Include one larger instruction VLM such as Qwen2.5-VL-3B only if flexible prompts, text reading, or higher-resolution inspection are genuine requirements.

### Cited Findings

- The Florence-2 card distinguishes the base pretrained checkpoints from `-ft` checkpoints fine-tuned on a collection of downstream tasks and exposes separate caption/detail-caption prompts. The base-ft card’s reported COCO caption CIDEr is 140.0. [Florence-2 base card](https://huggingface.co/microsoft/Florence-2-base); [base-ft card](https://huggingface.co/microsoft/Florence-2-base-ft)
- The BLIP captioning model card describes the base as COCO-pretrained-for-captioning and demonstrates unconditional and conditional generation; it labels its license BSD-3-Clause and provides CPU/GPU code. [BLIP-base card](https://huggingface.co/Salesforce/blip-image-captioning-base)
- GIT-base-coco is explicitly fine-tuned on COCO and MIT licensed, making it useful as a distinct architecture and license comparator. [GIT card](https://huggingface.co/microsoft/git-base-coco)
- SmolVLM-500M-Instruct is Apache-2.0, 0.5B, and supports image description; its training mix card reports includes 18% image-captioning emphasis. [SmolVLM card](https://huggingface.co/HuggingFaceTB/SmolVLM-500M-Instruct)
- Qwen2.5-VL supports variable-resolution images and describes visual localization, OCR-related visual analysis, and structured output in the card, but the model is a 3B generalist and its image-input compute varies with visual token count. [Qwen2.5-VL card](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct)
- BLIP-2’s official HF card documents a 7.21-GB FP16/BF16 model-size figure for the OPT-2.7B version and a 1.8-GB INT4 model-size figure, illustrating the resource jump compared with sub-billion captioners. [BLIP-2 card](https://huggingface.co/Salesforce/blip2-opt-2.7b)

### Inferences

- Evaluate on a representative, manually reviewed image sample and score: correct main subject, useful secondary objects/actions, specificity without invention, caption length, repeated phrasing, and acceptable performance on indoor/outdoor, people, pets, low-light, and text-bearing photos.
- Save the raw generated sentence separately from normalized tags. Derive tags with a deterministic post-processing layer or evaluate a tagging prompt explicitly; free-form caption generation and controlled multi-label classification are different tasks.
- First-pass operational recommendation: Florence-2-base-ft with `<CAPTION>` for concise captions, or BLIP-base if the simplest unconditional COCO-captioning behavior is desired. Add `<DETAILED_CAPTION>` only if human review confirms that the extra detail is accurate and useful.
- Do not interpret benchmark CIDEr differences between different model papers as a head-to-head ranking unless datasets, splits, decoding, image preprocessing, and evaluation protocol match.

### Gaps

- Actual tagging quality and best caption style depend on the user’s image distribution and desired tag vocabulary; no cited source determines that choice universally.
- The Qwen model card’s license should be confirmed from current repository metadata and applicable terms before commercial adoption; avoid assuming all downloadable weights share a permissive license.

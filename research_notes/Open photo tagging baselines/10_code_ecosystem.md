# Open Python ecosystem for photo-tagging baselines

## Which maintained open repositories/packages cover image tagging and captioning, dataset loading, and evaluation?

### Takeaway
Use Hugging Face Datasets for local/Hub datasets, Transformers for pretrained captioning and classification pipelines, and OpenCLIP for prompt-based multi-label tagging; use COCO API only when evaluating against COCO annotations, with TorchMetrics for conventional classification/detection measures and task-specific caption metrics (for example, `evaluate`/`pycocotools`) as needed. These projects show active public development infrastructure and current documentation, but package licenses do not determine model-checkpoint or dataset licenses.

### Cited Findings
- Hugging Face Datasets supports local files, Hub datasets, image features, `ImageFolder` plus metadata for image-text pairs, and streaming; its project README identifies Apache-2.0 licensing. [Datasets docs](https://huggingface.co/docs/datasets/index); [ImageFolder/image-captioning docs](https://huggingface.co/docs/datasets/image_dataset); [repository/license](https://github.com/huggingface/datasets)
- Transformers supplies pretrained inference/training interfaces across vision and multimodal tasks; its image-captioning guide demonstrates processor/model generation, while its README identifies Apache-2.0 licensing. [Transformers docs](https://huggingface.co/docs/transformers/index); [image-captioning task guide](https://huggingface.co/docs/transformers/tasks/image_captioning); [repository/license](https://github.com/huggingface/transformers)
- OpenCLIP provides image/text encoders and preprocessing, pretrained checkpoint selection, normalized image-text similarity, and a CoCa caption-generation example. The repository has a permissive MIT-style license for code. [OpenCLIP README](https://github.com/mlfoundations/open_clip); [license](https://github.com/mlfoundations/open_clip/blob/main/LICENSE)
- TorchMetrics provides reusable PyTorch metrics, including classification, detection, image and text domains, batch accumulation and distributed synchronization. Its repository specifies Apache-2.0. [TorchMetrics README](https://github.com/Lightning-AI/torchmetrics); [metric documentation](https://lightning.ai/docs/torchmetrics/stable/); [license](https://github.com/Lightning-AI/torchmetrics/blob/master/LICENSE)
- COCO API loads/parses/visualizes COCO annotation formats, including caption annotations; Python API installation includes native build steps. Its `license.txt` grants BSD-style redistribution rights with notice/disclaimer conditions. [COCO API README](https://github.com/cocodataset/cocoapi); [license](https://github.com/cocodataset/cocoapi/blob/master/license.txt)
- The current repositories expose commit history, releases or CI, which are useful maintenance signals: [Datasets commits](https://github.com/huggingface/datasets/commits/main/), [Transformers releases](https://github.com/huggingface/transformers/releases), [OpenCLIP commits](https://github.com/mlfoundations/open_clip/commits/main/), [TorchMetrics CI](https://github.com/Lightning-AI/torchmetrics/actions), [COCO API history](https://github.com/cocodataset/cocoapi/commits/master/). COCO API has a comparatively old-looking, compact project surface; verify compatibility with the chosen Python/NumPy toolchain before making it a required dependency.
- Transformers' captioning guide uses `evaluate` for WER as an example, but notes that captioning is typically assessed with metrics such as ROUGE or WER; these are not substitutes for COCO's conventional caption metrics (e.g., CIDEr/SPICE) where benchmark comparability matters. [Captioning guide](https://huggingface.co/docs/transformers/tasks/image_captioning); [COCO API](https://github.com/cocodataset/cocoapi)

### Inferences
- For a general photo library, OpenCLIP zero-shot similarity is the quickest reproducible tagging baseline: map a configurable vocabulary of prompts to scores and retain the top-k or thresholded labels. A vocabulary and threshold are user-facing model configuration, not intrinsic labels emitted by CLIP.
- Captioning is a separate generative baseline. Transformers provides broad model integration and processor conventions; OpenCLIP's CoCa supports generation but its documented generation example uses a caption-finetuned pretrained checkpoint. Compare both only after selecting and pinning specific checkpoints.
- Treat library, checkpoint, and dataset licensing as separate review items. Hub model cards and dataset cards carry terms/limitations that may differ from the Python library license; record exact model ID, revision, model-card license, and dataset source/license in run metadata.
- Avoid making HF Datasets or COCO API mandatory for a minimal folder-based CLI. A plain filesystem/Pillow loader is simpler for user-supplied folders; add Datasets as an optional adapter for Hub datasets and COCO parsing as an optional benchmark adapter.

### Gaps
- The cited documentation does not establish license/usage terms for every Transformers or OpenCLIP checkpoint, nor for each Hugging Face dataset; exact model and dataset cards must be checked before choosing artifacts.
- Current Python-version/platform compatibility and wheel availability for `pycocotools` vary by environment and were not systematically tested here.

## What practical architecture makes a runnable baseline CLI?

### Takeaway
Build a small Python CLI around explicit input adapters, interchangeable inference backends, and JSONL/CSV outputs. Make the default path local-folder inference with OpenCLIP tags plus an optional Transformers captioner, and keep dataset/benchmark integrations and heavyweight dependencies optional.

### Cited Findings
- Datasets `ImageFolder` can read folder layouts and metadata columns such as captions from CSV/JSONL; its image-processing tools support local and Hub sources. [Image dataset guide](https://huggingface.co/docs/datasets/image_dataset); [loading/processing docs](https://huggingface.co/docs/datasets/loading)
- OpenCLIP documents `create_model_and_transforms`, tokenizer setup, normalized image/text embedding similarity and pretrained checkpoint selection. [OpenCLIP inference usage](https://github.com/mlfoundations/open_clip#usage); [pretrained model list](https://github.com/mlfoundations/open_clip/blob/main/docs/PRETRAINED.md)
- Transformers documents task pipelines and image captioning via processor, model generation and decoded output. [Pipelines](https://huggingface.co/docs/transformers/pipeline_tutorial); [captioning guide](https://huggingface.co/docs/transformers/tasks/image_captioning)
- TorchMetrics metric modules accumulate state across batches and can synchronize across devices, while COCO API serves annotation-format parsing/evaluation support. [TorchMetrics](https://github.com/Lightning-AI/torchmetrics); [COCO API](https://github.com/cocodataset/cocoapi)

### Inferences
- Suggested modules: `cli.py` (argparse/Typer commands), `inputs.py` (recursive image-folder and optional Datasets adapters), `models/clip_tags.py`, `models/captioner.py`, `outputs.py`, `metrics.py`, and `run_metadata.py`. Keep backend contracts simple: `predict_tags(images, labels, threshold/top_k)` and `caption(images)`.
- CLI baseline: `photo-tags run --input DIR --output results.jsonl --backend open_clip --model ViT-B-32 --pretrained laion2b_s34b_b79k --labels labels.txt --top-k 5`. Add `--caption-model MODEL_ID` as optional, and `--device auto|cpu|cuda`, `--batch-size`, `--recursive`, `--extensions`, and `--limit` to make runs controllable.
- Use one shared image iterator that opens images safely, applies EXIF orientation, converts to RGB, and emits stable relative paths. Batch preprocessing/inference; preserve input order and record failures per image instead of aborting the whole directory.
- JSONL is a practical primary result format: one record per image containing relative path, tags with raw scores, optional caption, backend/checkpoint/revision, prompt vocabulary or its hash, timestamp, and error field. Offer CSV as a flattened convenience export. Write a run-level manifest with package versions, device, seed/config, and model/dataset license references.
- Keep evaluation a separate command: `evaluate` takes predictions plus a ground-truth file and an explicitly named task/metric. Use TorchMetrics for classification/multilabel metrics where target vectors exist; use COCO-format annotations and COCO-compatible caption metrics for benchmark claims. Report metric name, preprocessing, split, and checkpoint with every score.
- Provide a tiny smoke-test mode that runs a handful of local files and a synthetic or user-supplied label list; avoid silently downloading training datasets. Cache downloaded checkpoints through upstream tooling and provide a clear first-run network/download message.
- Declare base dependencies narrowly (Pillow, torch, open_clip_torch, typer/argparse); put `transformers`, `datasets`, `torchmetrics`, and `pycocotools` behind optional extras. Pin tested dependency ranges and document CUDA/PyTorch installation separately because PyTorch wheels are platform-specific.
- Bundle no dataset or checkpoint by default. Users should supply a label vocabulary and choose model IDs; record model-card/source/license information because open-source wrapper packages do not confer rights to model weights or evaluation data.

### Gaps
- Exact default checkpoints and their license/terms cannot be recommended without knowing deployment/commercial constraints and target hardware; inspect each checkpoint model card and benchmark actual latency/quality on representative photos.
- Metric package dependencies and implementations change over time; pin versions and validate benchmark protocol (tokenization, references, split, and preprocessing) against the intended benchmark's official instructions.

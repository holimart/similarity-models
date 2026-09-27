# Local photo-tagging baselines

Small, inference-only benchmarks for photo tags. This is separate from the repository's legacy OCR environment. It does not train or fine-tune models.

## First benchmark: COCO 2017 validation

COCO is not a stock-photo search benchmark, but it gives a reproducible, shared 80-category object vocabulary. Download the official `val2017` images and `annotations_trainval2017.zip` from [cocodataset.org](https://cocodataset.org/#download), and extract them locally. The benchmark needs:

```text
/path/to/coco/
  val2017/                 # JPEGs
  annotations/instances_val2017.json
```

The repository `.env` can set `COCO_ROOT` to this dataset directory (the benchmark reads it automatically). To override it for one run, use the CLI paths. Run the closed-vocabulary baselines:

```bash
.venv-image-tagging/bin/python image_tagger/benchmark.py --model clip --limit 200 \
  --output image_tagger/results/coco-smoke.json
```

Supported choices are `clip`, `fasterrcnn`, `siglip2`, `ram_plus`, and `all` (all defaults to clip). CLIP, Faster R-CNN, and SigLIP 2 run in `.venv-image-tagging`; RAM++ uses `.venv-tagging-advanced` because its upstream code needs an older Transformers/timm stack. Run individual models in their respective environments; omit `--limit` for all 5,000 images. All are pretrained inference models; no fine-tuning is performed. First use downloads weights; later use can run offline from the local cache.

```bash
.venv-image-tagging/bin/python image_tagger/benchmark.py --model siglip2 --limit 50
.venv-tagging-advanced/bin/python image_tagger/benchmark.py --model ram_plus --limit 50
```

## Isolated setup

The repository `.env` currently sets `COCO_ROOT=/mnt/sportsmarket/datasets/coco2017`, which the benchmark reads automatically. A separate uv-managed CPU environment was installed here so the legacy OCR environment remains untouched:

```bash
uv venv --python /usr/bin/python3 .venv-image-tagging
uv pip install --python .venv-image-tagging/bin/python torch torchvision \
  --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv-image-tagging/bin/python open_clip_torch transformers

# RAM++ compatibility environment
uv venv --python /usr/bin/python3 .venv-tagging-advanced
uv pip install --python .venv-tagging-advanced/bin/python torch torchvision \
  --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv-tagging-advanced/bin/python \
  transformers==4.51.3 timm==0.4.12 scipy fairscale
```

Installed primary versions: Python 3.10.12, PyTorch 2.14.0+cpu, TorchVision 0.29.0+cpu, OpenCLIP 3.3.0, Transformers 5.17.0. The RAM++ environment uses Transformers 4.51.3, timm 0.4.12, SciPy, and fairscale. `RAM_REPO` and `RAM_CHECKPOINT` are in `.env`; source and weights are under `/mnt/sportsmarket/model-cache`. This host has no CUDA device/tooling, so only CPU inference has been measured. For CUDA, select the matching PyTorch command from the [official selector](https://pytorch.org/get-started/locally/). Both environments are isolated from legacy OCR requirements.

## What the numbers mean

The script reports macro/micro precision, recall and F1 at a declared score threshold, macro mean average precision (mAP), precision@5, wall-clock seconds/image and peak CUDA memory where available. AP is computed from continuous model scores; threshold metrics use `--threshold` (default 0.25). COCO's object annotations are a useful first test for objects, not a complete list of valid scene, mood, composition or commercial-use tags. Do not interpret COCO scores as predicted stock-search uplift. Use a separately human-reviewed photo set for those concepts.

Results are only comparable when the same IDs, checkpoint revisions, transforms, device and package versions are used. The program records selected model, device, evaluated IDs, runtime, threshold, and metrics in JSON. Model checkpoint and data/image licenses are separate; check the upstream terms before any commercial use.

## Scope and next baselines

The comparison includes prompt-based CLIP and SigLIP 2, a conventional COCO detector, and RAM++ as a direct broad-vocabulary tagger. The detector emits boxes collapsed to image-level class scores; the encoders score the same 80 candidate labels; RAM++ scores its tag inventory mapped to COCO labels. Add Open Images verified positive/negative labels, caption benchmarks, calibrated thresholds on a separate split, and human judgments of tag relevance. Do not tune prompts/threshold on the test split and then report it as untouched evaluation.

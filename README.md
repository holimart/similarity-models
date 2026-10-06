# Similarity models
Similarity and data extraction

Source codes to accompany the following publications:
- https://ieeexplore.ieee.org/document/8892877 (older manuscript: https://arxiv.org/abs/1904.12577)
- https://rdcu.be/cmoAk (or manuscript here: https://arxiv.org/abs/2011.07964) 

Dataset is hosted under kaggle datasets:
- https://www.kaggle.com/martholi/anonymized-invoices
- Note that there can never be any pictures or text content, as the data must be anonymized!

All codes and datasets are published under the LICENSE attached (GNU AFFERO GENERAL PUBLIC LICENSE).
Any derivative work or service should be published under the same license (for any other licensing options, feel free to reach out).

We kindly ask you to cite the abovementioned papers in Your reserach. Or your "Thank You" page 
together with the author's name (https://www.linkedin.com/in/martin-holecek/) and a link to https://rossum.ai/.

Testing baseline command (note the limit and n_epochs params):
```
experiments_ft.py --verbose=1 --sqlite_source="article_anon_a.sqlite" --neighbours=1 --debug=True
--cls_extract_types="['amount_total', 'amount_total_base', 'amount_total_tax', 'amount_rounding', 'amount_paid', 'amount_due', 'tax_detail_base', 'tax_detail_rate', 'tax_detail_tax', 'tax_detail_total', 'account_num', 'bank_num', 'iban', 'bic', 'const_sym', 'spec_sym', 'var_sym', 'invoice_id', 'order_id', 'customer_id', 'date_issue', 'date_uzp', 'date_due', 'terms', 'sender_ic', 'sender_dic', 'recipient_ic', 'recipient_dic', 'sender_name', 'sender_addrline', 'recipient_name', 'recipient_addrline', 'page_current', 'page_total', 'phone_num']"
--weights_separate --key_metric=custom --key_metric_mode=max --n_epochs=2 --limit=400
```

For running the same experiments as were in the article, the commands in experiments.txt were used.

This README also documents the 2026 additions: an offline OCR/evaluation lab,
photo-tagging baselines, and free-tooling and dataset notes (see below).

## 2026 additions: free tooling and datasets

Alongside the original thesis models, this repository now carries small,
offline-first tooling for receipt/invoice OCR and photo tagging, plus research
notes. Everything here was built with freely available models, packages, and
datasets; no paid API is required.

### OCR and evaluation lab (`ocr_lab/`)

An offline test harness that runs one image through PaddleOCR 3.x or RapidOCR
3.x, normalizes results to word/line polygons + text + confidence, and scores
CER/WER and receipt fields. See [`README-ocr.md`](README-ocr.md) for full setup,
commands, and metric definitions.

- OCR engines: **PaddleOCR 3.x** and **RapidOCR 3.x**, both using the same
  **PP-OCRv6-small** weights on CPU ONNX Runtime. This is a backend/runtime
  comparison, not a model-quality comparison.
- Receipt amount selection: "naive" keyword-nearby rule (no model) vs "tuned"
  **CORD-trained logistic candidate ranker** (the only trained artifact in this
  repo; see `runs/total-amount/cord-paddle-ranker.json`).
- Optional local LLM selector: Qwen3-4B/8B/14B and GPT-OSS-20B via Ollama,
  reading OCR text (not images).
- Headline diagnostics (non-Czech): total exact on CORD test / SROIE first 100 —
  Paddle keyword 75.8% / 61.6%, ranker 82.1% / 68.7%; RapidOCR ranker 85.3% /
  72.7%. Reports: [`reports/`](reports/).

### Photo-tagging baselines (`image_tagger/`)

Inference-only COCO 2017 benchmarks for **CLIP**, **SigLIP 2**, **Faster R-CNN**,
and **RAM++**. No fine-tuning. See [`image_tagger/README.md`](image_tagger/README.md).

### Research notes (`research_notes/`)

Cited notes on Czech receipt datasets, invoice/receipt document understanding,
real-image and real-time scene-text OCR, open photo tagging, open camera
translation projects, and Shutterstock creator economics. Condensed reports are
in [`reports/`](reports/). Key takeaway for Czech work: **no publicly
downloadable Czech účtenka/faktura image+transcript dataset was verified**; the
local proxies are Indonesian CORD and English/Malaysian SROIE, neither of which
estimates Czech accuracy.

## Datasets: what is needed and where it lives

Data and model weights are **not committed** (most have unclear redistribution
terms and are large). They live outside the source tree under a shared
workspace configured by `.env` (copy from [`.env.example`](.env.example)):

```
DATASETS_ROOT=/path/to/datasets        # source/, derived/, manual/, coco2017/
COCO_ROOT=/path/to/datasets/coco2017   # image_tagger benchmark
HF_HOME / TORCH_HOME                   # model caches
RAM_REPO / RAM_CHECKPOINT              # RAM++ source + weights
```

| Dataset | Role | Size | Terms |
|---|---|---|---|
| `source/cord-v2/` | Indonesian receipts (main proxy) | ~31 MB | CC BY 4.0 (project) |
| `source/sroie-mirror/` | English/Malaysian scanned receipts (626 subset) | ~348 MB | local-only; image rights unclear |
| `source/textzoom/` | Scene-text word crops (not receipts) | ~30 MB | no clear data license |
| `source/xfund-val/` | 7-language forms | ~343 MB | CC BY-NC-SA 4.0 |
| `coco2017/` | Photo-tagging benchmark | ~2.6 GB | COCO terms |

## Reproduce: download what is needed

```bash
set -a; . ./.env; set +a
python scripts/download_datasets.py          # CORD, SROIE mirror, TextZoom, XFUND
```

Download scripts pin upstream revisions so re-downloads are reproducible:

- CORD: pinned HF dataset revision `7f0115a4b758a71d6473b8d085751692da2fef98`.
- SROIE mirror: pinned commit `27be4271b251c256f695acbade9a801bffe85994`.
- XFUND: pinned release tag `v1.0`.

Manual (registration/network) steps — reported by the script, not automated:

- **COCO 2017**: download `val2017/` and `annotations_trainval2017.zip` from
  https://cocodataset.org/#download and extract under `$COCO_ROOT`.
- **RAM++**: clone https://github.com/xinyu1205/recognize-anything and download
  `ram_plus_swin_large_14m.pth`; set `RAM_REPO` and `RAM_CHECKPOINT` in `.env`.

### Verify what you have: the dataset manifest

Rather than publishing data through Git LFS, the repository ships a SHA-256
manifest ([`datasets.manifest.json`](datasets.manifest.json)) describing the
expected workspace files (path, size, hash). Generate or verify it with:

```bash
python scripts/generate_manifest.py --check datasets.manifest.json --base "$DATASETS_ROOT"
```

This gives reproducibility without redistributing data whose image rights are
unclear, and without Git LFS size/host limits. Model weights are intentionally
excluded from the manifest.

## Versioned annotations and artifacts

- `annotations/manual/` — manually reviewed receipt-field labels for 826
  receipts (100 CORD validation + 100 CORD test + 626 SROIE mirrors), the
  merged `receipt_field_annotations.jsonl`, batch shards, and coverage notes.
  These are derived labels that reference source image paths; the images
  themselves are never committed. `scripts/merge_manual_annotations.py`
  validates and regenerates the merged manifest.
- `runs/total-amount/*-ranker.json` — the small trained candidate rankers used
  for the "tuned" results. All other `runs/` contents (raw OCR transcripts and
  large ledgers) stay local and are regenerated from the datasets above.

## Free tooling and datasets found in 2026 (notes)

Short pointers; full cited notes are under [`research_notes/`](research_notes/).

- **OCR frameworks:** PaddleOCR (Apache-2.0), RapidOCR (Apache-2.0, multi-runtime
  ONNX/OpenVINO/MNN deployment), EasyOCR (Apache-2.0), docTR (Apache-2.0),
  MMOCR (Apache-2.0), Tesseract (Apache-2.0, recognition engine only). See
  [`research_notes/Real time scene text OCR/`](research_notes/Real%20time%20scene%20text%20OCR/01_ocr_frameworks.md).
- **Open-weight VLMs for documents:** Qwen2.5-VL / Qwen3-VL and InternVL3.5 and
  Pixtral (Apache-2.0), GLM-4.1V (MIT), GOT-OCR2 (Apache-2.0), Gemma 3 and
  Llama 3.2 Vision (custom terms). See
  [`research_notes/Invoice receipt document understanding/06_open_vlms.md`](research_notes/Invoice%20receipt%20document%20understanding/06_open_vlms.md).
- **Document/receipt datasets:** CORD, SROIE, DocILE, FUNSD/XFUND, Kleister,
  EPHOIE, RVL-CDIP/IIT-CDIP. See
  [`research_notes/Invoice receipt document understanding/08_datasets.md`](research_notes/Invoice%20receipt%20document%20understanding/08_datasets.md)
  and [`research_notes/Real image OCR datasets/`](research_notes/Real%20image%20OCR%20datasets/).
- **Photo-tagging models:** OpenAI CLIP, OpenCLIP, and SigLIP. See
  [`research_notes/Open photo tagging baselines/06_clip_models.md`](research_notes/Open%20photo%20tagging%20baselines/06_clip_models.md).
- **Czech receipt/invoice data:** bounded negative finding — no verified public
  Czech image+transcript corpus; only receipt-processing apps. See
  [`research_notes/Czech receipt OCR datasets/`](research_notes/Czech%20receipt%20OCR%20datasets/)
  and [`reports/Czech receipt OCR datasets.md`](reports/Czech%20receipt%20OCR%20datasets.md).

*Note: "current through 2026" reflects sources reviewed at research time. Model
cards, licenses, leaderboards, and download portals change; re-check upstream
revisions before publishing or deploying.*

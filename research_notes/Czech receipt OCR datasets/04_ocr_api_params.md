# OCR Python API parameters for one-image inference and repeatable local benchmarks

Research checked 2026-09-26. This note covers the maintained `paddleocr` 3.x pipeline API and RapidOCR's `rapidocr` 3.x Python package, rather than legacy PaddleOCR 2.x `ocr.ocr()` examples or the separate `rapidocr_onnxruntime` package. Pin exact package versions and keep this distinction explicit: both APIs are evolving.

## Key question 1: What should be configurable for single-image inference?

### Takeaway

For a reproducible one-image run, explicitly record image path, package versions, model family/size and local model artifacts, inference engine/device, language choice, orientation/preprocessing switches, detector resize and thresholds, recognition score filtering, and the returned text/boxes/scores. Both packages accept one image path directly; construct the engine once and reuse it for repeated measurements.

### Cited Findings

- PaddleOCR 3.x's documented Python entry point constructs `PaddleOCR(...)`, then calls `.predict(image_path)`; each input returns a Result object supporting `.print()`, `.save_to_json()` and `.save_to_img()`. The documented example disables document orientation classification, document unwarping, and text-line orientation classification explicitly. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- PaddleOCR configuration supports `text_detection_model_name` / `_dir`, `text_recognition_model_name` / `_dir`, and corresponding model-name/path settings for document orientation, unwarping, and text-line orientation. An unset model directory means the official model may be downloaded; model names select the pipeline model. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- Current PaddleOCR examples use `ocr_version` for PP-OCRv4/v5 and default to PP-OCRv6. The documented pipeline model set includes PP-OCRv6 tiny/small/medium; PP-OCRv5/v4 server/mobile variants; and language-specific recognition models. For Czech Latin-script receipts, verify a chosen recognition model's supported script/languages in the current model list rather than assuming `lang="cs"` selects a Czech-exclusive model. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- PaddleOCR constructor/pipeline fields include `lang`, `ocr_version`, `device`, and optional module switches `use_doc_orientation_classify`, `use_doc_unwarping`, and `use_textline_orientation`. Paddle docs describe `device` values such as `gpu:0` and `cpu`; engine choice can also be specified (`paddle_static`, `transformers`, `onnxruntime`) subject to compatible dependencies. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html); [Inference Engine and Configuration](https://www.paddleocr.ai/latest/en/version3.x/inference_deployment/local_inference/inference_engine.html)
- PaddleOCR detection controls include `text_det_limit_side_len`, `text_det_limit_type` (`min`/`max`), `text_det_thresh`, `text_det_box_thresh`, and `text_det_unclip_ratio`; docs currently describe constructor-initialized defaults of 64, `min`, 0.3, 0.6, and 2.0, respectively. `text_rec_score_thresh` filters recognition rows; default 0.0 retains all. The current docs also allow recognition/detection input-shape controls. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- Important version-sensitive detail: the live PaddleOCR page's Python/CLI parameter tables document one configuration surface, while pipeline/model configs and historical values may differ. For repeatability use explicit values and verify them against the installed `paddleocr`/PaddleX version; do not rely on a remembered default. In particular, the page labels an initialized detection side-limit default of 64 while module/pipeline examples commonly expose 736, so record the effective `text_det_params` reported in output. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- PaddleOCR prediction results expose detection polygons/scores and recognized text/scores (among other fields), with `res.json` available as a dictionary and `save_to_json()` as a file export. Recognition text and score lists can be filtered by `text_rec_score_thresh`; preserve Unicode in stored outputs for Czech diacritics. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- RapidOCR's current package usage is `from rapidocr import RapidOCR`, `engine = RapidOCR(...)`, then `result = engine(image_path)`. A `RapidOCROutput` exposes aligned `boxes`, `txts`, `scores`, plus `elapse_list`/`elapse`; `result.vis(...)` is optional. — [RapidOCR Quick Start](https://rapidai.github.io/RapidOCRDocs/main/quickstart/)
- RapidOCR 3.9+ config uses per-stage keys such as `Det.engine_type`, `Det.lang_type`, `Det.model_type`, `Det.ocr_version`, and matching `Rec.*`/`Cls.*`; current versions list ONNX Runtime and OpenVINO, with Paddle/Torch/MNN added in 3.9.1 and TensorRT in 3.9.2. Model families PP-OCRv4/v5 use mobile/server; PP-OCRv6 uses tiny/small/medium. Language is stage-specific (`LangDet`, `LangRec`); PP-OCRv6 uses one multilingual model and `lang_type` does not swap its weights. — [RapidOCR Model List](https://rapidai.github.io/RapidOCRDocs/main/model_list/)
- RapidOCR supports local models through `Det.model_path` / `Rec.model_path` / `Cls.model_path` for non-Paddle formats, or `model_dir` for Paddle format; recognition may additionally require `Rec.rec_keys_path`. `Global.model_root_dir` selects the model cache/root. Its docs state models can otherwise be automatically downloaded. — [RapidOCR Offline Model Usage](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/how_to_use_offline_model/); [RapidOCR Parameters](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/parameters/)
- RapidOCR config exposes `Det.limit_side_len` (736), `limit_type` (`min`), `thresh` (0.3), `box_thresh` (0.5), `max_candidates` (1000), `unclip_ratio` (1.6), `use_dilation`, and `score_mode`; global image-size controls `min_side_len` (30) and `max_side_len` (2000) are also available. RapidOCR additionally documents padding/preprocess controls in newer versions. Set the applicable limits explicitly and record the effective config. — [RapidOCR Parameters](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/parameters/)
- RapidOCR global `text_score` (default 0.5) is a recognition-result confidence cutoff; global `use_det`, `use_cls`, `use_rec`, and `use_preprocess_img` toggle stages. `Cls.cls_thresh` defaults to 0.9 and its classifier is a 0°/180° text-line orientation classifier (not full-page 0/90/180/270 correction). — [RapidOCR Parameters](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/parameters/)
- RapidOCR output's `boxes`, `txts`, and `scores` are aligned result sequences; the docs' example reports per-stage elapsed values and total elapsed. Avoid using visualization in timed runs because it adds work and can trigger a font download. — [RapidOCR Quick Start](https://rapidai.github.io/RapidOCRDocs/main/quickstart/)

### Inferences

- For Czech receipt OCR, a practical baseline is a multilingual/Latin recognition model with Czech confirmed in that model's supported-language list, with automatic page/line orientation either consistently enabled or consistently disabled. PP-OCRv6 medium/small and PP-OCRv5 Latin/mobile are plausible candidates, but language coverage and actual Czech accuracy must be measured on the target receipts.
- Save a manifest per run: Python and package versions, OS/runtime versions, CPU/GPU model and device index, engine/backend and precision, model names plus resolved local paths and checksums, image dimensions/hash, all non-default preprocessing and thresholds, warmup/repetition policy, and result schema. This makes a local benchmark repeatable despite upstream defaults changing.

### Gaps

- PaddleOCR's official docs do not provide a complete version-pinned, stable table of every parameter default across backends; current docs and installed runtime can differ. Confirm runtime-effective config/output fields in the selected environment.
- RapidOCR and PaddleOCR do not expose perfectly equivalent configuration semantics. A one-to-one threshold/device mapping cannot be assumed across pipeline implementations or backend-specific preprocessing.

## Key question 2: How do APIs differ, and how should output and orientation be handled?

### Takeaway

PaddleOCR 3.x is a higher-level pipeline with structured Result objects and broad document preprocessing controls; RapidOCR is a configurable engine with separately-addressed detector, classifier, and recognizer models and a compact output dataclass. Normalize both to ordered `(polygon, text, confidence)` records for analysis, while retaining raw outputs and timings.

### Cited Findings

- PaddleOCR's `predict()` returns a list of per-sample Result objects; Result output includes `dt_polys`, `dt_scores`, `rec_texts`, `rec_scores`, `rec_polys`, and `rec_boxes`, along with detector parameter metadata and orientation details. Its JSON representation converts NumPy arrays to lists; text is retained as strings. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- PaddleOCR separates document orientation classification (four orientations 0°/90°/180°/270°), document image unwarping, and text-line orientation classification (0°/180°). All are optional pipeline features and should be fixed across comparisons. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- RapidOCR's documented output has `boxes`, `txts`, and `scores`; orientation classification is represented as optional `Cls` and covers 0°/180° text-line orientation. Detection and recognition are independently configured per-stage. — [RapidOCR Quick Start](https://rapidai.github.io/RapidOCRDocs/main/quickstart/); [RapidOCR Parameters](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/parameters/)
- RapidOCR detector language configuration (`Det.lang_type`) and recognition language (`Rec.lang_type`) are not interchangeable: detector options are documented as Chinese/English/multilingual for applicable versions, while recognition language selects a recognition model. Czech appears among the languages supported by PP-OCRv5 Latin-script model documentation; PP-OCRv6 has broad Latin-language support but one model. — [RapidOCR Model List](https://rapidai.github.io/RapidOCRDocs/main/model_list/)

### Inferences

- Comparing quality should use normalized text and ground-truth metrics (e.g., CER/WER or field-level receipt accuracy) with explicit Unicode normalization policy; spatial matching must account for different polygon ordering/coordinate output conventions.
- For detection-inclusive end-to-end evaluation, report both recognition accuracy and detection/line segmentation behavior. Recognition confidence scores from distinct implementations should not be presumed calibrated to the same scale.

### Gaps

- Neither project's cited quick-start establishes a standardized shared output schema or cross-framework confidence calibration.

## Key question 3: What makes a repeatable benchmark, and what is the same-model comparison caveat?

### Takeaway

Separate cold-start/initialization/download time from warmed inference, reuse the initialized object, run the same local image bytes, and report stage and end-to-end timing with all preprocessing fixed. “Same model” does not guarantee an apples-to-apples PaddleOCR-versus-RapidOCR comparison: RapidOCR commonly runs converted model artifacts and different runtimes/pre/postprocessing, not PaddleOCR's exact execution path.

### Cited Findings

- PaddleOCR's own published timing notes distinguish model inference from pre/post-processing and report standard versus high-performance modes, with backend and precision changes (e.g., Paddle static versus optimized Paddle/OpenVINO/TensorRT). Its listed timing environment names GPU, CPU, CUDA/cuDNN/TensorRT, PaddlePaddle, and PaddleOCR versions. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- RapidOCR describes its origin as converting PaddleOCR models to ONNX for portable deployment and supports multiple engines, including ONNX Runtime, OpenVINO, MNN, Paddle, TensorRT, and Torch (availability varies by RapidOCR version). Its docs also list multiple model formats including Paddle, ONNX, MNN, TensorRT, and PyTorch. — [RapidOCR GitHub README](https://github.com/RapidAI/RapidOCR); [RapidOCR Model List](https://rapidai.github.io/RapidOCRDocs/main/model_list/)
- PaddleOCR's official model table marks PP-OCRv6 benchmark metrics as evaluated on an internal multi-scenario set and PP-OCRv5/v4 on a general evaluation set, warning those metrics are not directly comparable. — [PaddleOCR General OCR Pipeline Usage](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- RapidOCR's v3.9+ documentation exposes engine selection independently for Det/Cls/Rec and version-specific engine support; the same named model/version may therefore execute through different runtimes and precision/device configurations. — [RapidOCR Model List](https://rapidai.github.io/RapidOCRDocs/main/model_list/); [RapidOCR Parameters](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/parameters/)

### Inferences

- “Same-model comparison” should mean the same upstream architecture/weights and dictionary where possible—not merely matching labels such as PP-OCRv5. RapidOCR ONNX conversions can differ from Paddle native inference due to conversion, operators, runtime kernels, numeric precision, preprocessing/postprocessing, thresholds, and package defaults. State whether the question is deployment-system performance (end-to-end packages) or model-only quality/speed; the former intentionally includes these differences.
- For robust measurements: pre-download and checksum models; instantiate once; perform unreported warmups; repeat enough runs and report median and spread; avoid image/result visualization, file writing, network fetches and model loading inside timed region; synchronize accelerator work when required by the chosen backend; retain per-stage timings where available and also measure wall-clock end-to-end latency.
- Keep an identical source image, orientation, color channel order, resize policy, detection/recognition thresholds, line classifier state, and output filtering for a controlled package comparison. If parameters have no exact counterpart, disclose the mismatch instead of suggesting strict equivalence.

### Gaps

- Official sources do not publish a standardized benchmark protocol comparing current PaddleOCR 3.x with current RapidOCR 3.x on identical hardware, weights, preprocessing, and datasets. The notes therefore define controls but do not claim measured package speed or accuracy.
- Exact conversion equivalence, checksums, and operator-level parity are model/backend-specific; verify the selected artifacts and installed RapidOCR version for a rigorous same-weights experiment.

# Architecture comparison for an open camera translator

Research snapshot: 2026-09-26. Scope is a live camera experience that recognizes scene text, translates Czech↔English, removes original lettering, and draws translated text back into the scene. “Reported” numbers below come from named source benchmarks. No end-to-end app latency benchmark covering this complete pipeline was found. Any deployment timing discussed here should therefore be measured on target devices, not inferred from component marketing claims.

## Executive recommendation

For the shortest reproducible route to a credible prototype, build Android native (Kotlin + CameraX) with ML Kit Text Recognition v2 and on-device Translation, then render translated text as stable translucent cards positioned over tracked text regions. This gets camera frames, boxes, Czech OCR and Czech-English offline translation from maintained mobile SDKs without operating a server. It does not deliver true background reconstruction. Add OpenCV inpainting only as a low-effort test for small text on smooth backgrounds; for natural-looking removal use a GPU-hosted LaMa service as an optional, asynchronous enhancement, not in the live critical path.

For an open, reproducible GPU/developer reference, use Python/OpenCV + PaddleOCR or EasyOCR + Helsinki-NLP OPUS-MT English↔Czech model + OpenCV/LaMa + browser or OpenCV overlay. PaddleOCR is the stronger multilingual/throughput candidate; EasyOCR is easier to start with but less obviously suited to mobile deployment. Benchmark those components independently and report p50/p95 with the exact hardware, frame resolution, number of regions, warm/cold model state, and network conditions. A consumer product should prefer ML Kit on device for OCR/MT, and defer generative inpainting while moving or under load.

## Architecture comparison

| Layer | Consumer-phone path | Open GPU/reference path | Main tradeoff |
|---|---|---|---|
| Camera loop | CameraX `ImageAnalysis`, latest-frame backpressure, preview composited with overlay | OpenCV VideoCapture or a browser camera; a thin API passes frames to GPU worker | CameraX is the practical Android integration. Drop stale frames rather than queueing them; inference does not need every preview frame. |
| OCR + geometry | ML Kit Text Recognition v2, Latin script; returns hierarchy and bounding geometry | PaddleOCR scene-text detector/recognizer, or EasyOCR `readtext` with quadrilaterals, strings, confidence | ML Kit is easiest mobile integration; PaddleOCR has explicit model/deployment/benchmark tooling; EasyOCR is very approachable, Python-first. |
| Region identity | Associate current boxes to prior boxes using overlap, text similarity, and optional optical flow; smooth geometry | Same association layer, e.g. IoU/Hungarian matching + OpenCV optical flow | OCR SDK output is per-frame detection, not a stable-ID scene tracker. Region tracking and temporal smoothing are application work. |
| Translation | ML Kit Translation language models, Czech (`cs`)↔English (`en`), offline after models are available | Helsinki-NLP OPUS-MT `en-cs` / `cs-en` Marian models; or online MT API | On-device ML Kit is simplest; OPUS models are open and reproducible but need packaging/serving and quality validation. |
| Source-text removal | Initially do not erase; use a filled card behind translated text. Optional OpenCV `inpaint` for small, textured-free regions | OpenCV Telea/NS for simple cases; LaMa for larger/contextual removals | Inpainting is the largest visual-quality and compute risk. Classical local interpolation fails on structured backgrounds; neural inpainting costs GPU and may hallucinate. |
| Overlay | Native Canvas/Compose overlay in preview coordinates, mapping crop/rotation/scale and letterbox offsets | OpenCV drawing, WebGL/canvas or browser DOM overlay | Text fitting, translation expansion, alignment, and transform correctness are more product-critical than overlay compute. |

### Recommended frame/data flow

1. Camera preview renders continuously. Send only a bounded cadence of downscaled analysis frames; configure latest-frame behavior and close every camera image promptly.
2. Run OCR and retain region polygon/quad, recognized text, confidence, and frame transform. Filter short/low-confidence detections and merge words into lines where possible.
3. Associate detections to stable region IDs using geometry plus text similarity. Apply hysteresis: require a stable recognition before changing displayed source/translation; smooth corners and suppress flicker.
4. Translate only when a region’s recognized text changes (debounce and cache exact strings). Batch text regions in a frame when the API supports it. Keep the previous translation visible during refresh.
5. Expand the quad to a removal mask. Do not inpaint the whole video frame repeatedly: run only after geometry/text stabilizes, cache the result per region/background crop, and invalidate when the camera moves enough.
6. Draw into preview coordinates using the original image-to-preview transform. Fit translated text into region cards; preserve reading order; let user tap to show original text and manually correct OCR/translation.

Continuous camera “live” need not mean running the full pipeline at display refresh rate. A more robust UX is a smooth preview and a lower-frequency, asynchronous recognition/update loop. No source reviewed supplied an apples-to-apples measured update rate for the full stack.

## Sources and evidence by component

### Camera loop and tracking

- Android CameraX `ImageAnalysis` is the intended analyzer use case; official guidance: https://developer.android.com/media/camera/camerax/analyze . The page was unavailable through this research fetch, so use the official docs when implementing to verify analyzer/backpressure and image-closing details.
- ML Kit’s recognizer returns blocks, lines, elements, symbols, boxes, corner points, rotation and confidence; its overview says it supports real-time recognition on a wide range of devices, but publishes no latency figure on the overview page: https://developers.google.com/ml-kit/vision/text-recognition/v2
- OpenCV provides optical-flow primitives (e.g. Lucas–Kanade) but no text-region association solution as a turnkey camera translation system: https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html . Region lifecycle, track IDs and flicker reduction remain application logic.

### OCR

- ML Kit v2 explicitly covers Latin script; its evaluated language table lists Czech (`cs`) as supported. This makes it a direct match for Czech printed Latin text rather than assuming Czech works because English does: https://developers.google.com/ml-kit/vision/text-recognition/v2/languages
- Google documents hierarchical boxes and confidence, useful for overlay placement, and supports real-time OCR, but does not disclose a universal ms/frame number: https://developers.google.com/ml-kit/vision/text-recognition/v2
- PaddleOCR repository describes multilingual scene OCR and CPU/GPU/accelerator deployment, as well as a benchmarking feature that measures end-to-end pipeline and module/layer latency. It reports PP-OCRv6 figures including 0.13 s on A100 and a 5.2× CPU speedup (OpenVINO); these are upstream claims for its stated models/configuration, not a fair comparison to ML Kit or the full camera pipeline. Current README is moving and contains future-dated releases relative to this research date in portions of fetched content, so confirm a pinned actual release before basing a build on version-specific claims: https://github.com/PaddlePaddle/PaddleOCR
- EasyOCR is a simple Python API (`Reader([...]).readtext`) that returns box, text and confidence, supports CPU-only operation, downloads language weights at first use, and says initialization takes time but is only needed once. Its README says 80+ languages, but its landing page does not provide comparable Czech scene-text latency/accuracy benchmarks: https://github.com/JaidedAI/EasyOCR
- For app decisions, validate OCR on photographed Czech text with diacritics (č/ř/ž/ě/š/ů/ý/á/í/é), small print, perspective, glare, curved packaging, and motion blur. OCR errors propagate directly into MT and patch masks. Public scene-text benchmarks rarely provide a directly applicable Czech-mobile-camera score; no credible, comparable Czech-English end-to-end camera benchmark was identified here.

### Czech-English translation and benchmark interpretation

- ML Kit Translation supports Czech and English codes (`cs`, `en`). It runs on device with dynamically managed downloadable models. Google says these models use English as pivot for non-English language pairs and positions them for casual/simple translation rather than highest-fidelity use; directly translating Czech↔English does not require a non-English pivot. Evaluate its quality on actual signage/menu/packaging text: https://developers.google.com/ml-kit/language/translation and https://developers.google.com/ml-kit/language/translation/translation-language-support
- OPUS-MT is based on Marian, provides downloadable pretrained models and a service setup, with model weights available under CC-BY 4.0 according to its repository. Its maintainers explicitly caution that many reported automatic evaluations are short/simple Tatoeba sentences and can be optimistic for realistic use; they note limited domain adaptation and automatic test-set quality control: https://github.com/Helsinki-NLP/Opus-MT
- The English→Czech OPUS model page lists WMT news test BLEU/chr-F results: e.g. the `opus-2019-12-04` transformer reports BLEU 24.3 / chr-F 0.499 for newstest2019 and 48.2 / 0.658 on Tatoeba; its `opus-2019-12-18` transformer-align reports 24.9 / 0.518 and 46.1 / 0.647 respectively. These are corpus MT scores, not latency or camera translation quality; source prose warns against over-reading Tatoeba results. The page gives no inference latency: https://github.com/Helsinki-NLP/OPUS-MT-train/tree/master/models/en-cs
- Marian is a pure C++ NMT framework with CPU and GPU translation and a focus on efficient inference; no applicable per-sentence Czech-English phone latency was found in its project landing page: https://github.com/marian-nmt/marian-dev
- Do not compare BLEU/chr-F directly against proprietary Google app output unless evaluated on identical image-derived OCR strings and test references. For a practical Czech↔English pilot, curate hundreds of representative sign/menu/product lines, report human adequacy/fluency and terminology errors, and separately score translation on perfect OCR text versus OCR output to isolate OCR damage.

### Inpainting and compositing

- OpenCV `inpaint` takes a same-sized mask whose non-zero pixels mark the region. Its two documented methods are Telea fast-marching and Navier–Stokes-based propagation; these are neighborhood-based approaches appropriate to small blemishes/strokes, not semantically reconstructing text-covered scenery: https://docs.opencv.org/4.x/df/d3d/tutorial_py_inpainting.html
- LaMa is a research-backed neural inpainting implementation, designed for large masks and claimed resolution robustness to around 2k; its README documents inference setup and provides an interactive Colab/repo demo, but does not publish a stable mobile-camera latency benchmark. The repository environment pins old Torch dependencies in examples and model distribution/setup introduces packaging and maintenance friction: https://github.com/advimman/lama and paper https://arxiv.org/abs/2109.07161
- In scene translation, inpainting’s challenge is not merely model runtime: text masks must be complete without eating surrounding texture, perspective and camera motion make cached repairs invalid, and repeated repainting causes visible shimmer. These are engineering inferences from per-frame geometry and mask-based inpainting; no published end-to-end benchmark quantifying them was found.
- Filled cards are a useful design decision, not a compromise to hide: Google Translate-like visual replacement is perceptually demanding. A simple semi-opaque background under the translated text avoids requiring reconstruction and ensures legibility. Consider an “original/translated” toggle or tap-to-reveal for exact context.

## Performance: what is known and what must be measured

| Component | Evidence available | Interpretation |
|---|---|---|
| Camera preview | Platform preview capability, no stack-specific figure collected | Treat as device/platform performance; preview should be decoupled from inference. |
| ML Kit OCR | “Real-time” capability claim; no ms/frame published on overview | Unknown actual p50/p95; benchmark cold model and steady state on selected phones. |
| PaddleOCR | Repository-reported PP-OCRv6 0.13 s on A100; CPU speedup claim (OpenVINO) | Explicitly model/config/hardware-specific, and not end-to-end. Do not claim phone performance from A100. |
| ML Kit MT | On-device/dynamic language models; no per-string latency published | Translation may not dominate for short text; model availability/download and cold start matter. Measure. |
| OPUS-MT | Quality corpus metrics cited above, no suitable latency result | GPU server and CPU/mobile timings depend heavily on model, runtime, sentence length, and batch. Measure independently. |
| OpenCV inpaint / LaMa | Algorithm/repo demos, no relevant live-camera timing found | Benchmark mask area/resolution and CPU/GPU, but visual quality and temporal stability are as important as throughput. |
| Full pipeline | No primary-source apples-to-apples Czech-English camera benchmark found | Any total-latency figure would be an estimate; do not invent one. Instrument pipeline before setting UX targets. |

If capacity planning needs an initial envelope before hardware testing, label it explicitly as an **engineering estimate**, not an observed result. A plausible prototype can have OCR/MT run asynchronously and update overlays a few times per second while preview remains smooth; this is a design target, not a published performance result. True per-frame neural inpainting is unlikely to be the simplest reliable path. The correct measurement is end-to-end time from camera frame timestamp to first stable overlay, then steady-state overlay update interval, p50/p95, dropped frames, thermals, and battery draw.

## Practical bottlenecks and maturity gaps

1. **No unified pipeline or comparable benchmark.** Component repositories offer demos and isolated metrics; no vetted open project found combines live capture, Czech OCR, Czech-English MT, tracking, high-quality inpainting and temporally stable overlay with measurements on consumer phones.
2. **Tracking is under-productized.** OCR detections are not temporal object tracks. Without IDs, smoothing and change thresholds, words reflow/flicker as the camera moves. Region matching also needs to survive partial visibility and re-recognition.
3. **Czech language quality is not the main availability risk.** ML Kit lists Czech in both OCR and translation support, and OPUS has a Czech-English checkpoint. However, OCR quality on accented low-resolution scene text and MT quality on fragments, brand names, abbreviations, prices, and line breaks still need custom evaluation.
4. **Latency data is incomplete and non-comparable.** OCR model claims may be desktop/GPU or isolated inference; MT benchmark numbers are translation quality not speed; SDK docs avoid guarantees. Cold model download/initialization and mobile thermal throttling are often omitted.
5. **Text removal is a maturity gap.** Classical inpaint is easy to reproduce but only works acceptably for limited backgrounds/masks. LaMa demonstrates stronger reconstruction in static images but lacks a convenient, clearly benchmarked, cross-platform realtime mobile package in sources reviewed.
6. **Overlay localization is easy to get wrong.** Camera crop, rotation, front/back camera mirroring, stabilization, preview scaling and letterboxing must all be represented by one tested coordinate transform. Translation changes line length/height; reflowing can overlap nearby objects or adjacent source blocks.
7. **Model/runtime and legal/product logistics.** ML Kit language packs are dynamically downloaded and Google requires following its translation attribution/usage guidelines. OPUS model artifacts cite CC-BY 4.0; preserve attribution and validate specific model artifact terms. Neural inpainting model dependencies are less turnkey than the mobile SDK path.

## Suggested reproducible prototype sequence

1. **Android spike (simplest phone stack):** Kotlin + CameraX Preview/ImageAnalysis, ML Kit Text Recognition v2, ML Kit Translation `cs`↔`en`, Canvas/Compose overlay. Start with colored boxes and translated cards; no inpainting. Keep a fixed test set of Czech sign/menu images and videos.
2. **Add tracking and latency instrumentation:** log per-stage start/end times, frame age, box count, cache hits, overlay stabilization delay, p50/p95, dropped frames and device temperature. Replay saved video as well as live camera.
3. **Compare one open OCR alternative:** PaddleOCR first for multilingual deployment/benchmark infrastructure; EasyOCR as a quick Python demo baseline. Use identical cropped, annotated Czech images and report character/word error plus detection IoU/recall, not only a few demo screenshots.
4. **Compare MT:** ML Kit versus OPUS-MT both directions on identical human-authored reference lines. Assess human ratings and adequacy; retain both source text and translated text for error analysis. Use OPUS/Marian locally on GPU for reproducibility, not an assumed phone build.
5. **Test text removal on representative backgrounds:** OpenCV Telea/NS as baseline, then LaMa on GPU for photographs. Track quality by human visual review and temporal flicker; time mask-generation, inference and composite independently. In final UX, permit card fallback whenever repair is slow or poor.
6. **Only then optimize.** Downscale OCR input, cache translations and repairs, run inference on newest frame, and adapt frame cadence based on motion/thermal state. Avoid doing full-resolution inpainting for every camera frame.

## Bottom line

The easiest credible consumer-phone implementation is CameraX + ML Kit OCR + ML Kit on-device translation + native tracked text cards. This has direct documented Czech coverage and avoids server infrastructure, but quality/latency must be measured locally and it is not an open-weight end-to-end clone. The easiest reproducible open GPU version is PaddleOCR + OPUS-MT/Marian + OpenCV, with LaMa as a separate GPU enhancement; its pieces are mature enough for a demo, but live region tracking, pixel-accurate compositing, background reconstruction and comparable Czech-phone performance remain application engineering rather than solved repository features. Use no latency number beyond named, bounded source measurements; report local p50/p95 when available.

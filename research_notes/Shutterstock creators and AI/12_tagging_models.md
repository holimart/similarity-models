# Technical state of the art: photo captioning and keyword generation for stock metadata

## Which model families are useful for stock-photo captions and keywords, and what does their performance mean in practice?

### Takeaway
The most useful approach is a layered one: use a vision-language model (VLM) to draft a concise, grounded description; use image-text similarity and/or open-vocabulary detection to propose and verify concrete concepts; use OCR and image metadata for specialized evidence; then have a person approve claims that affect search, identity, or commercial meaning. Published scores on captioning, retrieval, and object-detection benchmarks do not establish stock-keyword precision or factual correctness on an arbitrary contributor portfolio.

### Cited Findings
- CLIP learns a shared image/text representation from 400 million image-text pairs and supports zero-shot transfer by comparing an image with text prompts. The original work reports broad transfer across more than 30 tasks, including OCR, geolocation, and fine-grained classification; CLIP is fundamentally a similarity/scoring model, not a reliable free-form caption generator. — [Radford et al., Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020)
- BLIP combines image-text understanding and generation and bootstraps noisy web captions with a captioner/filter. Its paper reports improvements on standard image-text retrieval, image captioning (CIDEr), and VQA benchmarks; those are benchmark results, not measured stock-metadata keyword precision. — [Li et al., BLIP](https://arxiv.org/abs/2201.12086)
- Instruction-tuned VLMs such as LLaVA and InstructBLIP can answer open-ended visual questions and generate descriptions in requested formats. LLaVA's original paper reports results on its synthetic instruction-following evaluation and ScienceQA; InstructBLIP evaluates zero-shot transfer across held-out vision-language datasets. Neither paper claims stock-specific metadata quality. — [Liu et al., Visual Instruction Tuning](https://arxiv.org/abs/2304.08485); [Dai et al., InstructBLIP](https://arxiv.org/abs/2305.06500)
- Open-vocabulary detectors such as Grounding DINO take text labels/referring expressions and return localized boxes. Its paper reports 52.5 AP on zero-shot COCO transfer and 26.1 mean AP on ODinW; these benchmark numbers show localization utility, not comprehensive detection of every relevant object or a calibrated probability that a keyword is safe to publish. — [Liu et al., Grounding DINO](https://arxiv.org/abs/2303.05499)
- OCR is a distinct capability. Google ML Kit documents text recognition as extracting text from images; image-labeling and object-detection APIs are separate capabilities. This separation reflects the practical value of running OCR on text-heavy photographs rather than expecting a general captioner to transcribe small print exactly. — [Google ML Kit Vision APIs](https://developers.google.com/ml-kit)
- A useful stock-metadata draft is usually a factual sentence plus a controlled list of distinct, relevant concepts—not a verbose narrative. This is an operational recommendation inferred from the different roles of generative captions, similarity ranking, object localization, and OCR; the cited academic benchmarks do not directly test keyword relevance, buyer search behavior, or stock licensing outcomes.

### Inferences
- Use a VLM for scene-level relations and a readable first draft; use similarity/detection to test whether specific candidate nouns appear; use OCR when text itself is relevant; retain human review for proper names, exact species/product/model, demographics, emotions, activity, location, and other consequential claims.
- CLIP-like scores are best interpreted comparatively among candidates under a consistent prompt template. A high score is not a calibrated truth probability, and scores from differently worded prompts should not be treated as directly comparable without validation.
- For long keyword lists, generate candidates from observed entities, attributes, setting, and activity, then deduplicate and remove unsupported synonyms or speculative concepts. This is more defensible than asking one generative model to produce a large list and accepting it wholesale.

### Gaps
- No cited study here evaluates end-to-end caption-plus-keyword generation against stock-agency acceptance, search relevance, contributor corrections, or buyer downloads on a representative Shutterstock/Adobe Stock corpus.
- Published model benchmarks rarely measure the precision of fine-grained stock claims (e.g., exact breed, make/model, location, or culturally specific activity) under real contributor-image conditions. Portfolio-specific tests with human-labeled examples are needed to quantify it.
- Commercial model availability, exact versions, image resolution handling, privacy terms, and inference costs change quickly; verify current provider documentation before selecting a production service.

## How accurate are these systems, and what failure modes should a stock workflow anticipate?

### Takeaway
Models are useful proposal tools, but no general benchmark gives a safe “accuracy percentage” for stock metadata. The central failure mode is plausible unsupported specificity: generated language can confidently add objects, actions, relationships, text, identities, or context that are not in the pixels. Search/retrieval and object detection can reduce uncertainty for visible concepts, but they do not prove invisible context or exact identity.

### Cited Findings
- POPE systematically evaluates object hallucination in large VLMs and reports that representative models exhibit substantial object hallucination; frequently occurring instruction concepts and co-occurring objects are especially prone to being named. Its authors also caution that evaluation can be sensitive to question wording and generation style. — [Li et al., Evaluating Object Hallucination in Large Vision-Language Models](https://arxiv.org/abs/2305.10355)
- The POPE result is particularly relevant to keywording: an invented object may sound ordinary in a caption and become an apparently searchable keyword even though it is absent. The paper evaluates object presence, not every stock-specific error category such as commercial intent, emotion, or geographic attribution. — [POPE paper](https://arxiv.org/abs/2305.10355)
- CLIP's broad zero-shot transfer includes OCR and geolocation tasks, but the paper describes classification/transfer performance on specified datasets; it does not establish dependable transcription or precise GPS-level localization for arbitrary stock photos. — [CLIP paper](https://arxiv.org/abs/2103.00020)
- Grounding DINO's open-set results demonstrate that prompted categories can be grounded to image regions. A box can support “a dog is visible,” for example, but does not establish breed, ownership, event, intent, or unseen scene context. This limitation follows from what the detector predicts (category-conditioned localization), rather than a claim made by its benchmark. — [Grounding DINO paper](https://arxiv.org/abs/2303.05499)
- Captioning benchmarks such as CIDEr measure similarity to reference captions, while retrieval benchmarks measure ranking and detection benchmarks measure localization/classification. None alone is equivalent to precision/recall of production stock keywords; benchmark results should not be translated into a claim like “X% of tags are correct.” — [BLIP paper](https://arxiv.org/abs/2201.12086); [Grounding DINO paper](https://arxiv.org/abs/2303.05499)
- OCR output can be incomplete or wrong on small, angled, obscured, stylized, or low-resolution text; any transcription used as a factual keyword should be checked against the image. Google documents its OCR capability but does not guarantee exact recognition for every image. — [Google ML Kit](https://developers.google.com/ml-kit/vision/text-recognition/v2)
- Image geolocation is an inference problem, not a direct observation unless supported by trustworthy capture metadata or recognizable evidence. The CLIP paper's inclusion of a geo-localization benchmark is evidence that models can be tested on that task, not evidence that a scenic image's exact place can be safely inferred. — [CLIP paper](https://arxiv.org/abs/2103.00020)

### Inferences
- Risk is uneven across tags. Generic visible objects and broad scene descriptions are usually more verifiable than exact species, brand/model, named landmark, inferred nationality, emotion, occupation, relationship, or purpose. Treat increased specificity as requiring stronger direct evidence.
- A practical quality metric should be measured on a representative held-out set: human-verified precision of proposed tags (especially top-ranked tags), omission rate for salient subjects, unsupported-specificity rate, OCR exact-match rate where relevant, and review/edit time. Report per-category results and confidence intervals rather than a single benchmark number.
- Agreement among independent signals (caption, detector region, image-text match, source metadata) can prioritize review, but correlated models can share training-data biases and make the same error. Agreement is evidence to inspect, not proof.
- Prompt wording changes outputs and candidate rankings. Preserve prompts/model versions and evaluate using fixed templates; otherwise apparent improvements may be prompt or version drift rather than model quality.

### Gaps
- Public work cited here does not provide a universal, current ranking of commercial VLMs on stock-photo caption truthfulness, nor a dependable per-image probability calibration suitable for automated publication.
- Performance varies with image quality, crop, domain, demographics, language, and concept frequency. The cited papers do not supply an error rate for an individual contributor's specific collection.
- No source cited here establishes a safe method to infer a real person's identity, exact location, or commercial/model-release status from pixels. These require authoritative source information and human judgment, not visual-language inference.

## What should a practical stock-tagging pipeline do with detection, OCR, and geolocation?

### Takeaway
Treat each method as an evidence channel with a defined scope. Detection grounds candidate objects spatially; OCR reads visible text; EXIF/GPS and creator-supplied context are stronger provenance for location than visual guesswork; VLMs synthesize a caption and suggest relationships. A conservative review-and-edit stage should control final metadata, with traceable evidence and an explicit “unknown” option.

### Cited Findings
- Grounding DINO accepts category names or referring expressions to detect open-set objects and evaluates grounding/localization on COCO, LVIS, ODinW, and referring-expression benchmarks. This makes it useful for checking whether named candidate objects have visible support and for finding salient regions. — [Grounding DINO](https://arxiv.org/abs/2303.05499)
- CLIP enables zero-shot comparison between images and natural-language descriptions; it can rank controlled candidate phrases (e.g., “person riding a bicycle” vs. “person standing beside a bicycle”) but is not a bounding-box detector and its score is not a truth guarantee. — [CLIP](https://arxiv.org/abs/2103.00020)
- Google ML Kit provides separate image-labeling, object-detection, and text-recognition APIs, illustrating a practical modular design for visual tags, localization, and OCR. — [ML Kit Vision APIs](https://developers.google.com/ml-kit)
- EXIF can carry capture metadata such as GPS coordinates, but metadata may be absent, edited, or stripped during processing; its provenance should be considered. The ExifTool documentation describes GPS tags and supported metadata fields. — [ExifTool GPS Tags](https://exiftool.org/TagNames/GPS.html)
- Google documents geocoding as conversion between geographic coordinates and place addresses; reverse geocoding gives a label for supplied coordinates, not a way to derive coordinates reliably from image content. — [Google Maps Platform: Reverse geocoding](https://developers.google.com/maps/documentation/geocoding/reverse-geocoding)
- For usability and factual correctness, benchmark scope matters: BLIP's captioning results use caption metrics; open-vocabulary detector papers use AP; the POPE evaluation probes object hallucination. These measures answer different questions and should be combined with task-specific human review. — [BLIP](https://arxiv.org/abs/2201.12086); [Grounding DINO](https://arxiv.org/abs/2303.05499); [POPE](https://arxiv.org/abs/2305.10355)

### Inferences
- Suggested workflow: (1) preserve the original and read available EXIF/IPTC fields; (2) produce one concise VLM draft with instructions to state only visible evidence and mark uncertain details; (3) extract OCR separately when text is material; (4) detect or ground the main objects and compare against a restrained candidate vocabulary; (5) use CLIP-like ranking to order alternative broad descriptors; (6) deduplicate and normalize tags; (7) expose evidence/conflicts and let a person approve the final title and keywords.
- For geographic terms, prefer creator-confirmed location, trustworthy GPS metadata, and verified reverse-geocoding. If there is no reliable provenance, use visible geographic descriptions (e.g., “coastal cliff”) rather than naming a country, city, or landmark from resemblance alone.
- Keep model-generated suggestions separate from accepted metadata. Store source/model, prompt, score or region where available, and human edits; this supports audits and allows quality monitoring when models change.
- Use a threshold-and-review policy rather than forced completion. A system that returns fewer, well-supported tags plus “uncertain” is safer than one optimized to fill a maximum tag count with plausible guesses.

### Gaps
- The source set does not settle which current commercial VLM or detector is best for a particular stock portfolio, language, or budget; representative side-by-side evaluation is required.
- No cited study quantifies the incremental value of combining VLM, CLIP, detection, OCR, and EXIF for stock keyword precision. The layered workflow is a reasoned engineering recommendation based on their documented task capabilities.
- Agency-specific current keyword limits, AI-content policies, title requirements, and acceptance rules should be checked directly in the relevant contributor portal. Adobe's metadata documentation was inaccessible during this research session; do not assume one agency's constraints transfer to another.

### Selected references
- Radford et al. (2021), CLIP — https://arxiv.org/abs/2103.00020
- Li et al. (2022), BLIP — https://arxiv.org/abs/2201.12086
- Liu et al. (2023), LLaVA — https://arxiv.org/abs/2304.08485
- Dai et al. (2023), InstructBLIP — https://arxiv.org/abs/2305.06500
- Liu et al. (2023; revised 2024), Grounding DINO — https://arxiv.org/abs/2303.05499
- Li et al. (2023), POPE — https://arxiv.org/abs/2305.10355
- Google ML Kit OCR — https://developers.google.com/ml-kit/vision/text-recognition/v2
- ExifTool GPS tag reference — https://exiftool.org/TagNames/GPS.html
- Google Maps Platform reverse geocoding — https://developers.google.com/maps/documentation/geocoding/reverse-geocoding

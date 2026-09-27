# Image Tagging Validity: Stock Metadata and Discoverability

## How image-tagging output relates to stock metadata and discoverability

### Takeaway
Image tags can help supply searchable visual concepts, but stock metadata serves a broader commercial search task: it needs to represent what is visibly present while anticipating the buyer's intended use and query language. Thus, tag correctness alone is not evidence that a system improves stock discoverability; retrieval relevance or human judgments against realistic search intents are needed.

### Cited Findings
- Getty Images describes the customer-facing goal as customers finding files when those files match their searches, and says relevant content aligned to customer needs is most in demand. This links discoverability to buyer intent and licensing use, not simply object recognition. [Getty Images contributor information](https://www.gettyimages.com/workwithus)
- COCO was created to advance object recognition and scene understanding using common objects in context; its 91 object categories and instance annotations are not a stock-keyword or commercial-intent taxonomy. [Lin et al., “Microsoft COCO: Common Objects in Context”](https://arxiv.org/abs/1405.0312)
- COCO Captions collects five independent human-written captions per training/validation image to support caption-generation evaluation. Captions describe images in natural language; they are not equivalent to exhaustive metadata or search-query annotations. [Chen et al., “Microsoft COCO Captions: Data Collection and Evaluation Server”](https://arxiv.org/abs/1504.00325)
- Getty's contributor material frames customer needs in terms of stories visuals can show, with examples including health, travel, work, family, and diversity. These themes are contextual or conceptual and extend beyond a closed list of visible object labels. [Getty Images contributor information](https://www.gettyimages.com/workwithus)

### Inferences
- Treat machine-generated tags as candidate indexing terms. A useful pipeline should distinguish directly observable content (objects, setting, actions, color, composition) from inferred use/theme terms (e.g., “teamwork,” “wellness”) and should avoid asserting the latter without a defensible visual basis.
- Measure discoverability by whether relevant images are retrieved for representative buyer queries (e.g., search-result relevance or recall at a fixed rank), alongside factual tag precision and coverage. The sources establish search relevance as the business objective, but do not prescribe a particular evaluation protocol.

### Gaps
- Public sources reviewed do not disclose stock platforms' ranking formulas, exact metadata schemas, or the measured causal effect of adding machine tags on licensing/search outcomes.
- Adobe's official keywording help endpoint returned 403 during this research, so this note does not make platform-specific claims about Adobe keyword limits or ordering rules.

## What COCO/ImageNet labels, caption hallucination, and annotation omissions can and cannot tell us

### Takeaway
COCO and ImageNet are valuable task benchmarks, not comprehensive truth sets for stock metadata. Their category/task design constrains what can be scored, annotations may omit visible content, and fluent captions can introduce unsupported objects; therefore, benchmark agreement or caption quality metrics alone cannot certify tag validity.

### Cited Findings
- COCO's original scope is 91 recognizable object types, with 2.5 million labeled instances in 328,000 images, gathered through crowd-worker category detection, instance spotting, and segmentation. Its deliberately bounded object vocabulary cannot represent every useful stock descriptor, concept, or buyer intent. [Lin et al., “Microsoft COCO: Common Objects in Context”](https://arxiv.org/abs/1405.0312)
- ImageNet Large Scale Visual Recognition Challenge evaluates object-category classification and detection over hundreds of categories and millions of images, and its authors discuss the challenges of large-scale ground-truth annotation. A classification benchmark's category labels answer a narrower question than “what metadata would make this image findable?” [Russakovsky et al., “ImageNet Large Scale Visual Recognition Challenge”](https://arxiv.org/abs/1409.0575)
- Open Images V4 illustrates how annotation design affects what counts as labeled: it provides image-level labels for 19.8k concepts and boxes for 600 object classes, with roughly eight annotated objects per image on average. Its authors describe large-scale annotation and validation, but the average annotation count itself cautions against assuming every image has an exhaustive inventory of all visible details. [Kuznetsova et al., “The Open Images Dataset V4”](https://arxiv.org/abs/1811.00982)
- Rohrbach et al. report that captioning models hallucinate objects not present in scenes. They also find standard sentence metrics may not capture image relevance, and models with better standard metric scores do not necessarily hallucinate less; hallucinations are often driven by language priors. [Rohrbach et al., “Object Hallucination in Image Captioning”](https://arxiv.org/abs/1809.02156)
- COCO Captions has five independent captions for each training/validation image, not a single exhaustive canonical description. Multiple captions represent varied human descriptions, but do not establish that all true details are mentioned in any one caption. [Chen et al., “Microsoft COCO Captions”](https://arxiv.org/abs/1504.00325)

### Inferences
- A benchmark's unmentioned label should generally be treated as “not annotated/not judged,” rather than automatically “false.” Conversely, a predicted tag absent from the reference list should not be counted as a hallucination until a human checks the image.
- Separate errors into at least: false positive (unsupported tag), omission (useful visible descriptor missed), granularity/synonym mismatch, and speculative/contextual claim. This makes the limitations of closed vocabularies and incomplete references explicit.
- Caption hallucination findings directly establish the risk for generative captions. They motivate auditing tags from caption-derived systems, but do not prove that every image-tagging model has the same hallucination rate.

### Gaps
- The cited benchmark abstracts do not give a universal estimate of annotator omission rates for the particular image population or tagging model under evaluation. Do not transfer a single benchmark's annotation completeness to a different dataset without checking.
- No reviewed source quantifies how frequently current stock-tagging systems produce incorrect location, identity, emotion, or commercial-use claims; these should be specifically audited if in scope.

## Building a small human-rated set for tagging validity and discoverability

### Takeaway
Create a compact, image-grounded evaluation set with independently authored labels and explicit “not enough evidence” options, then rate both individual tag validity and retrieval usefulness. A small, carefully sampled set is best treated as a diagnostic benchmark with uncertainty, not as a definitive estimate of performance across all stock imagery.

### Cited Findings
- COCO's annotation pipeline used crowd workers for category detection, instance spotting, and segmentation, demonstrating that annotation tasks should be operationally specified rather than left as a vague request to “describe the image.” [Lin et al., “Microsoft COCO: Common Objects in Context”](https://arxiv.org/abs/1405.0312)
- COCO Captions uses five independent human-generated captions per image in train/validation, a precedent for collecting multiple descriptions rather than relying on one annotator's wording. [Chen et al., “Microsoft COCO Captions”](https://arxiv.org/abs/1504.00325)
- The object-hallucination study evaluates captions with veridical visual labels and finds common sentence metrics may not capture image relevance. Human review should therefore assess whether each claim is supported by the actual image, separately from fluency or similarity to a reference phrase. [Rohrbach et al., “Object Hallucination in Image Captioning”](https://arxiv.org/abs/1809.02156)
- Getty describes discoverability in terms of matching customer searches, providing a rationale for including query-to-image relevance judgments in addition to per-tag truth judgments. [Getty Images contributor information](https://www.gettyimages.com/workwithus)

### Inferences
- Practical pilot design (recommended, not a published universal standard): sample roughly 100–300 images from the intended deployment domain, stratifying across scenes, close-ups, people, products, nature, text-heavy images, and ambiguous/low-quality examples. Include ordinary random examples plus a smaller challenge slice; report results separately so oversampling hard cases does not distort an overall estimate.
- For every image, collect system output and two independent raters' judgments. Ask raters to mark each proposed tag as **supported**, **unsupported**, **ambiguous/not visible**, or **wrong granularity**, and to identify a limited set of important missing descriptors. Provide “unknown/cannot tell”; do not require guesses about exact location, identity, intent, or emotion.
- Collect a separate open-ended reference pass before showing model output (or use separate annotator groups) to reduce anchoring. Use adjudication for disagreements and preserve both initial ratings. Record annotator confidence and inter-rater agreement; define acceptable synonyms and taxonomy mappings before scoring.
- Include 3–5 realistic search intents per image or use a pooled set of candidate images for each query. Have raters judge relevance without seeing model tags, then evaluate whether tagging-enabled retrieval improves precision/recall at chosen ranks over a baseline. This distinguishes semantic truth from practical retrieval benefit.
- Report tag precision (supported predictions / predictions), useful-tag coverage against the human-identified salient set, unsupported-claim rate, omission rate, ambiguity rate, and query-level ranking metrics. Give denominators and confidence intervals; with a small set, emphasize per-category error patterns and treat estimates as preliminary.
- Keep the image, model/version, raw output, normalized tags, rater decisions, adjudication notes, and query judgments together in a versioned table. Pilot the rubric on a small batch, revise unclear definitions, then freeze the rubric before the main rating round.

### Gaps
- The cited sources do not establish a statistically sufficient sample size for this project's desired precision, nor one universally correct number of annotators. Choose sample size based on acceptable uncertainty and available review capacity; publish the set's sampling frame and limitations.
- There is no single ground-truth “complete tag list”: what is salient depends on the intended stock search audience and use. The set should encode its intended domain and query distribution rather than imply universal metadata completeness.

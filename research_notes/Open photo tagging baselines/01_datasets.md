# Public image-tagging datasets for no-training evaluation

## What supervision each dataset provides

### Takeaway

For evaluating ready-made auto-taggers against human semantic tags, Open Images V7 and NUS-WIDE are the closest direct multi-label benchmarks, while COCO Captions/Flickr30k provide language descriptions rather than complete tag lists. VOC is a useful small, clean sanity check but far too narrow for stock-photo vocabulary. None of these benchmarks is a representative, rights-cleared stock-photography test set.

### Cited Findings

- Open Images V7 provides image-level labels over 20,638 classes and 61.4M labels; the official page distinguishes human-verified positive/negative labels from machine-generated labels. Its 1.9M-image densely annotated subset additionally has boxes, relationships, masks, point labels, and localized narratives. [Open Images V7 description](https://storage.googleapis.com/openimages/web/factsfigures_v7.html)
- The Open Images V7 download page lists human-verified label CSVs, separate machine-generated label CSVs, class descriptions, and per-image metadata including original/landing URL, author, title, and license. The page reports human-verified train labels across 7,337,077 images. [Open Images V7 download](https://storage.googleapis.com/openimages/web/download_v7.html)
- COCO is organized around object-instance annotations and a separate 2015 captioning task; it is not a large general-purpose multi-label vocabulary. Its official site provides dataset overview, downloads, and terms. [COCO](https://cocodataset.org/#home)
- PASCAL VOC classification/detection has 20 object classes: person; six animals; seven vehicles; and six indoor objects. VOC2012 train/validation labels are object classes plus boxes; segmentation exists for a subset, and action labels are a separate task. [VOC2012 challenge page](http://host.robots.ox.ac.uk/pascal/VOC/voc2012/index.html)
- Flickr30k has five human-written descriptions per image (31,783 images in the commonly described release); its dataset page distributes captions and image links/tokenized captions in a publicly distributable version, and offers image archive access separately for non-commercial research/education. [Flickr30k dataset page](https://shannon.cs.illinois.edu/DenotationGraph/data/index.html) [Flickr30k caption/link data](https://shannon.cs.illinois.edu/DenotationGraph/data/flickr30k.html)
- NUS-WIDE is a multi-label web image dataset with 81 concepts and user-tag metadata; the original dataset resource describes 269,648 images gathered from Flickr and manually annotated labels. Official resource endpoint could not be retrieved in this research run; the primary project URL is retained here. [NUS-WIDE project page](https://lms.comp.nus.edu.sg/wp-content/uploads/2019/research/nuswide/NUS-WIDE.html)

### Inferences

- Open Images is the strongest of these for explicit, broad object-tag benchmarking and distinguishing false positives from omitted/unknown labels because its evaluation split has verified positives and negatives. It remains object-centric, and its verified ontology is not equivalent to stock keywords such as mood, composition, lighting, intended use, or nuanced scene concepts.
- For a tagger returning unrestricted natural language, Flickr30k and COCO captions permit semantic matching, but captions describe salient content rather than enumerate every valid tag. Caption-derived reference tags should be treated as positive-only evidence, never as exhaustive ground truth.
- NUS-WIDE is valuable for evaluating an established, fixed multi-label concept set and user-tag vocabulary. Compared with current tagging taxonomies, its concept list and Flickr-era tags are limited and may include ambiguity/noise.
- VOC's compact vocabulary makes it practical for a quick baseline and per-class analysis; its narrow categories and comparatively constrained compositions make it a poor headline measure for stock-photo semantic coverage.

### Gaps

- Direct retrieval of the official NUS-WIDE page failed; exact current download status, archive integrity, detailed split sizes and present license terms should be checked manually before relying on it. Older papers describe counts, but those figures were not independently confirmed against a live primary source here.
- COCO page content did not expose detailed statistics or license wording through the page fetch. Verify the specific COCO release and image/annotation terms on the download and terms anchors before distributing a derived test set.

## Licensing, access, and practical download considerations

### Takeaway

These are research datasets assembled from third-party photographs, not blanket licenses to reuse the images. Open Images is operationally easiest at scale and explicitly warns users to verify image licenses individually. Flickr30k is particularly explicit about non-commercial research/education limits; VOC likewise directs users to Flickr terms. Treat the images as temporary evaluation inputs and track per-image rights where commercial use matters.

### Cited Findings

- Open Images V7 states that annotations are licensed under CC BY 4.0 and images are listed as CC BY 2.0, but makes no warranty about each image's status and instructs users to verify each image's license. The image metadata includes an image-specific license field and source URL. [Open Images licenses](https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses) [Open Images image metadata/download](https://storage.googleapis.com/openimages/web/download_v7.html#df-image-information)
- Open Images has manual downloads and a downloader script for selected IDs; the official page also documents image labels for 9M images and the 1.9M dense subset. This allows small filtered subsets rather than downloading all pixels. [Open Images download](https://storage.googleapis.com/openimages/web/download_v7.html)
- Flickr30k authors state that they do not own image copyrights; images are provided at the linked archive for researchers and educators for non-commercial research and/or educational purposes, and use must abide by Flickr terms. The publicly distributable version is image links plus captions. [Flickr30k dataset page](https://shannon.cs.illinois.edu/DenotationGraph/data/index.html)
- Flickr's current terms prohibit scraping/data-mining and commercial use of Flickr Services/materials, while distinguishing user content from Flickr-owned materials. The dataset was created under older Flickr terms; current terms should not be assumed to authorize bulk image retrieval or onward commercial use. [Flickr current terms](https://www.flickr.com/help/terms)
- VOC states its images include Flickr photographs and use must respect Flickr terms; VOC2012 provides a 2GB train/validation archive through its development-kit link, while test ground truth is not publicly released for most years. [VOC homepage/database rights](http://host.robots.ox.ac.uk/pascal/VOC/) [VOC2012 data/download](http://host.robots.ox.ac.uk/pascal/VOC/voc2012/index.html)
- The COCO website exposes dataset downloads and a “Terms of Use” anchor, but the page content retrieved here did not include the complete terms text. [COCO official site](https://cocodataset.org/#termsofuse)
- NUS-WIDE images originate on Flickr; the exact applicable dataset/image license and current download mechanisms were not verified due to the inaccessible official endpoint. [NUS-WIDE project URL](https://lms.comp.nus.edu.sg/wp-content/uploads/2019/research/nuswide/NUS-WIDE.html)

### Inferences

- For reproducible evaluation, save image IDs, original landing-page URLs, annotation version, and per-image license metadata rather than treating any image bundle as uniformly licensed.
- A useful compliant workflow is to store labels/IDs and fetch only an evaluation subset from official channels, with access restricted to the evaluation environment and no redistribution of pixels absent a verified right.
- Open Images has the best documented and scalable download path; Flickr30k link/caption distribution reduces redistribution of copyrighted pixels but makes access dependent on image availability and current platform rules.

### Gaps

- Exact COCO image license terms and any distinction among images/annotations need review directly on the terms page in a browser; the official page fetch returned only navigation content.
- NUS-WIDE present-day terms/download route need direct verification. Flickr terms can change, so legal interpretation for a production/commercial evaluation should be reviewed against each image and applicable terms.

## Label quality and fit for stock-photo semantic tags without training

### Takeaway

Use Open Images verified labels as the best available off-the-shelf precision/recall benchmark for object tags; add a modest caption set to assess scene-level semantics; treat NUS-WIDE as a legacy noisy-tag comparison and VOC as a narrow smoke test. For stock-photo search usefulness, the central limitation is mismatch in label ontology and completeness, not model-training requirements.

### Cited Findings

- Open Images reports that human verification practically eliminates false positives but can leave false negatives; labels not explicitly marked positive or negative are unknown. The official page recommends verified labels for classification evaluation. [Open Images V7 label methodology](https://storage.googleapis.com/openimages/web/factsfigures_v7.html#image-level-labels)
- Open Images boxes are mostly manually drawn by professional annotators; its description says the held-out validation/test box annotations are exhaustive for available positive image labels, with group-of exceptions. [Open Images V7 boxes](https://storage.googleapis.com/openimages/web/factsfigures_v7.html#bounding-boxes)
- The Open Images image-level vocabulary is broad (20,638 classes), but labels are strongly frequency-skewed; only 9,668 classes meet its trainable threshold of 100 human-positive training labels. [Open Images V7 description](https://storage.googleapis.com/openimages/web/factsfigures_v7.html#image-level-labels)
- VOC's 20-category taxonomy, fixed from VOC2007 onward, is explicit and annotated under shared guidelines; annotation test labels for VOC2012 are held back and require the evaluation server. [VOC homepage](http://host.robots.ox.ac.uk/pascal/VOC/) [VOC2012 challenge page](http://host.robots.ox.ac.uk/pascal/VOC/voc2012/index.html)
- Flickr30k descriptions are natural-language captions, not standardized multi-label annotations; the source describes the dataset as five descriptions per image. This makes them useful for matching concepts and scene relations but not exhaustive tag recall. [Flickr30k paper/dataset page](https://shannon.cs.illinois.edu/DenotationGraph/data/index.html)
- COCO captions similarly supply descriptions alongside object annotations; its object categories and caption focus make it a useful bridge between tags and language, rather than an exhaustive stock-keyword reference. [COCO official site](https://cocodataset.org/#home)
- NUS-WIDE's image concepts were manually assigned for the benchmark while Flickr user tags are also available; user tags are user-generated metadata and not equivalent to expert-confirmed, exhaustive semantic indexing. [NUS-WIDE project page](https://lms.comp.nus.edu.sg/wp-content/uploads/2019/research/nuswide/NUS-WIDE.html)

### Inferences

- Recommended evaluation stack: (1) Open Images verified positive/negative image-level labels, mapping the auto-tagger outputs into the benchmark hierarchy; (2) caption-level semantic matching on COCO or Flickr30k, reported separately as weak positive evidence; (3) small human-reviewed stock-style sample for attributes and concepts absent from these ontologies.
- Report micro/macro precision and recall only on explicitly verified labels, and distinguish “not labeled” from verified negative. A tag absent from captions or sparse annotation must not automatically count as an error.
- Broad class mapping is unavoidable: benchmark labels often denote objects (“person,” “car”), while stock search also needs scenes (“teamwork,” “remote work”), activities, visual attributes (“copy space,” “backlit”), and abstract concepts. Those require a purpose-built audited reference set.
- No-training evaluation means running a frozen model/API as-is; it does not remove the need to define the mapping, thresholding, label normalization, and held-out subset before observing scores.

### Gaps

- There is no dataset in this comparison that establishes representative distribution coverage or exhaustive, professionally curated stock-photo tags. A stock-photo-specific audited evaluation subset is needed for strong claims about production search quality.
- NUS-WIDE precise annotation instructions, inter-annotator agreement, and active archive status could not be confirmed from its primary page during this run.

## Dataset comparison at a glance

| Dataset | Main supervision | Strength for frozen taggers | Main limitation | Access/license note |
|---|---|---|---|---|
| Open Images V7 | Verified image labels + explicit negatives; boxes and rich extras | Best large-scale object-tag evaluation; rich vocabulary and split labels | Object-centric, long-tail, partially labeled; unknowns must remain unknown | Selective downloader; image-level license metadata; verify per image; annotations CC BY 4.0, images listed CC BY 2.0 |
| COCO | Object instances; captions; segmentation/keypoints | Good common-object/caption cross-check with mature tooling | Narrower ontology and salient caption coverage, not exhaustive tags | Official downloads/terms; review exact release terms |
| NUS-WIDE | 81 manually annotated concepts plus Flickr tags | Multi-label benchmark resembling keyword classification | Legacy limited concept set; user-tag noise and potential gaps | Official endpoint unavailable in this research run; verify licensing/access |
| PASCAL VOC | 20 classes; presence, boxes, segmentation; action subset | Clean, easy sanity benchmark | Very narrow categories; held-out labels for newer years | Downloads from challenge page; Flickr image terms apply |
| Flickr30k | Five natural-language captions/image | Scene relations, actions, and language-semantic matching | Captions are incomplete and not standardized tags | Caption/link distribution; images for non-commercial research/education; Flickr terms apply |

### Recommendation

Start with a filtered Open Images V7 validation/test sample and human-verified labels as the primary quantitative baseline. Add COCO/Flickr30k caption comparison for broader descriptions, and VOC for a simple compatibility check. Keep image rights and annotation quality caveats attached to reported results, and validate stock-specific semantic concepts with a small human-audited set.

# Google Open Images for image-level multi-label tag evaluation

## Dataset fit, ontology, and annotation completeness

### Takeaway
Open Images V7 is a strong candidate for broad-vocabulary, image-level multi-label classification: it offers human-verified positive and negative labels across 20,638 classes, with full validation/test coverage. Its supervision is explicitly partial rather than exhaustive, however, so an evaluation protocol must treat unannotated class/image pairs as unknown—not negative. The large training set's automatically generated labels are particularly unsuitable as unquestioned ground truth.

### Cited Findings
- Open Images V7 describes roughly 9M images, including 61.4M image-level labels across 20,638 classes; the dataset page reports 9,011,219 training images, 41,620 validation images, and 125,436 test images. — [V7 description](https://storage.googleapis.com/openimages/web/factsfigures_v7.html)
- All images have machine-generated labels, which the dataset authors say have a substantial false-positive rate. Human-verified labels cover the full validation and test sets and part of training; verification practically eliminates false positives, but may miss true labels (false negatives). — [V7 description](https://storage.googleapis.com/openimages/web/factsfigures_v7.html)
- For human-verified labels, positive means present and negative means absent; other class/image pairs are unannotated. The verified negatives are described as reliable and usable for classifier training and evaluation. — [V7 description](https://storage.googleapis.com/openimages/web/factsfigures_v7.html); [V7 download/data format](https://storage.googleapis.com/openimages/web/download_v7.html)
- V7 has 9,668 trainable image-label classes (defined as at least 100 positive human verifications in V7 train); machine-generated labels cover 9,068 of those. The wider vocabulary comprises 20,638 classes. — [V7 description](https://storage.googleapis.com/openimages/web/factsfigures_v7.html)
- Classes are represented by MIDs (machine-generated identifiers) associated with Freebase/Knowledge Graph; class-description files map IDs to display names. A separate 600-class boxable ontology has a hierarchy; this boxable subset is not the whole 20,638-class image-label vocabulary. — [V7 description](https://storage.googleapis.com/openimages/web/factsfigures_v7.html); [V7 download](https://storage.googleapis.com/openimages/web/download_v7.html)
- V7 human-verified label counts include 58,783,034 train labels (21,144,175 positive; 37,638,859 negative), 618,184 validation labels (390,797 positive; 227,387 negative), and 2,003,748 test labels (1,319,751 positive; 683,997 negative). These are label decisions, not fully dense class-by-image matrices. — [V7 description](https://storage.googleapis.com/openimages/web/factsfigures_v7.html)

### Inferences
- This suits evaluation against a large but incomplete known-label set if metrics are computed only over explicit positive/negative decisions, or if unknowns are masked. Treating every missing label as negative will penalize valid predictions and bias estimates.
- For a robust benchmark, use the official human-verified validation/test annotations and state class coverage explicitly. Restricting to the 9,668 trainable classes yields a more defensible vocabulary than attempting all 20,638, but exact per-class held-out support should be checked from the released files.
- The MID/name mapping and hierarchy require care when comparing tags: label normalization, synonym handling, and parent/child credit should be declared rather than assumed. The challenge's hierarchy behavior pertains to its detection-class ontology and does not automatically define an image-tagging metric for all image-level labels.

### Gaps
- The official pages do not give a single current downloadable size for the image-label CSVs or the total storage needed for a chosen subset; estimate from actual selected files/images.
- The exact human-verification candidate-selection procedure and class-by-class completeness/recall are not summarized sufficiently to infer that missing labels are true negatives.

## Licensing and acquisition burden

### Takeaway
Annotations are CC BY 4.0, while the dataset lists the images as CC BY 2.0 but expressly disclaims warranties and asks users to verify each image's license. Metadata is relatively manageable; downloading pixels at scale is a substantial, failure-prone operation involving millions of externally hosted images. A filtered subset is practical and supported by the official downloader.

### Cited Findings
- Google licenses annotations under CC BY 4.0 and lists images as CC BY 2.0, while making no representation or warranty about individual image licensing and instructing users to verify each image's license. — [V7 description, Licenses](https://storage.googleapis.com/openimages/web/factsfigures_v7.html)
- The downloadable metadata includes image IDs, original and landing-page URLs, license, author, title, original size, and rotation. The image information is described as reflecting the destination websites. — [V7 download, image information](https://storage.googleapis.com/openimages/web/download_v7.html)
- Official V7 download instructions distinguish the 1.9M-image dense-annotation subset from the approximately 9M-image image-label collection; all 9,178,275 images are offered through CVDF/Google Storage Transfer. The page offers ID-list filtering and a Python downloader for a selected subset. — [V7 download](https://storage.googleapis.com/openimages/web/download_v7.html)
- The V7 download page notes that the TFDS V7 entry was listed as “To be released” in its September 2022 text; it also documents third-party FiftyOne access, which can filter split, label types, classes, and sample count. Availability of these integrations can change over time. — [V7 download](https://storage.googleapis.com/openimages/web/download_v7.html)
- The crowdsourced extension is distinct from the core dataset: its page reports 382,000+ images, 6,000+ categories, and about 80GB of images. This is an extension, not the download size of core Open Images. — [Open Images Extended](https://storage.googleapis.com/openimages/web/extended.html)

### Inferences
- Legal provenance needs per-image review for redistribution or commercial use; dataset-level CC labeling should not be treated as a blanket warranty.
- For a tagging benchmark, download annotation tables first, choose eligible IDs/classes, then fetch only required images. This avoids paying the storage and bandwidth cost for all pixels when only validation/test samples or a training subset are needed.
- Expect broken or changed source URLs because pixels are sourced from destination sites; the source documents do not provide a guaranteed completion rate or a stable total byte estimate for the core full download.

### Gaps
- No official current estimate found for total bytes of the 9M core images or expected URL failure rate.
- No per-image rights audit was performed; legal status must be checked for the specific images and intended use.

## Metrics and recommendation

### Takeaway
Open Images provides an official challenge metric for object detection that explicitly handles incomplete image-level annotation, negative labels, hierarchy, and group boxes; it is not itself an official general image-tagging metric. For image-level multi-label tagging, report ranking and thresholded metrics over explicitly verified labels, mask unannotated entries, and disclose class support and averaging choices.

### Cited Findings
- The official Open Images challenge detection metric is a VOC-style mAP at IoU > 0.5. Per image, unannotated classes are excluded/ignored, negative-labeled classes count as false positives, and positive-labeled classes have exhaustive boxes under the stated annotation protocol. The metric also specifies hierarchy expansion and special group-of treatment. — [Open Images evaluation protocols](https://storage.googleapis.com/openimages/web/evaluation.html)
- That metric's hierarchy and group-of rules are detection-specific; the official evaluation page describes detection, instance-segmentation, and visual-relationship protocols, not an image-level tag-classification score. — [Open Images evaluation protocols](https://storage.googleapis.com/openimages/web/evaluation.html)
- Human-verified CSV records encode confidence 1 for verified present and 0 for verified absent; machine labels have fractional confidence. — [V7 download, image-label format](https://storage.googleapis.com/openimages/web/download_v7.html)
- The challenge reports mean AP averaged across its 500 detection classes, but its class set and localization requirements differ from the full image-level tag vocabulary. — [Challenge overview](https://storage.googleapis.com/openimages/web/challenge_overview.html); [evaluation protocols](https://storage.googleapis.com/openimages/web/evaluation.html)

### Inferences
- Recommended evaluation: use verified positives as targets and verified negatives as known negatives; exclude unknown image/class pairs from both ranking ground truth and thresholded confusion counts. Compute per-class AP (or a clearly defined masked mAP) and macro-average over a prespecified eligible class set. Add micro-averaged AP or precision/recall only as a complementary prevalence-weighted view.
- If thresholded scores are needed, select thresholds on a separate validation partition, then report test precision/recall/F1 with the same unknown masking. Report number of positive and negative decisions per class, classes omitted for insufficient support, and the class-averaging convention.
- Do not import the detection challenge's mAP number as a comparable image-classification baseline: it ranks localized detections and has its own 500-class hierarchy protocol. The dataset is best viewed as a source of partial-label, broad-vocabulary evaluation data, not a turnkey exhaustive tagging benchmark.

### Gaps
- No official V7 image-level classification evaluation server or mandated image-tagging metric was located in the primary dataset documentation.
- The documentation gives aggregate verified-label counts but does not prescribe a universally appropriate image-level metric for the partially observed labels.

### Primary sources
- Open Images V7 dataset description and license statements: https://storage.googleapis.com/openimages/web/factsfigures_v7.html
- Open Images V7 download formats and acquisition instructions: https://storage.googleapis.com/openimages/web/download_v7.html
- Official Open Images evaluation protocols: https://storage.googleapis.com/openimages/web/evaluation.html
- Open Images Challenge overview: https://storage.googleapis.com/openimages/web/challenge_overview.html
- Open Images Extended overview: https://storage.googleapis.com/openimages/web/extended.html

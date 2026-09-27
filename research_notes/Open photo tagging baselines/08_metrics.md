# Defensible No-Training Evaluation Protocol for Image Tags and Captions

## Protocol and benchmark design

### Takeaway

Run a frozen, inference-only comparison on fixed public validation/test splits, separate tag prediction from free-form caption quality, and publish the complete operating point and runtime conditions. Treat benchmark labels as observed annotations rather than an exhaustive account of everything visible in an image.

### Cited Findings

- MS COCO provides instance-level object annotations and image captions; the dataset paper describes 328k images and 2.5 million labeled instances, while the caption paper describes five independently written captions per training/validation image. This makes COCO useful for complementary tag and caption evaluation, but does not make its object categories a complete scene ontology. [Lin et al., *Microsoft COCO: Common Objects in Context*](https://arxiv.org/abs/1405.0312); [Chen et al., *Microsoft COCO Captions: Data Collection and Evaluation Server*](https://arxiv.org/abs/1504.00325)
- PASCAL VOC uses a fixed 20-object-class recognition benchmark and reports class-wise precision-recall behavior / average precision, offering a compact, well-understood tag benchmark. [Everingham et al., *The PASCAL Visual Object Classes Challenge*](https://doi.org/10.1007/s11263-009-0275-4)
- NUS-WIDE is a large-scale web image dataset with 81 concepts and user/tag-derived labels; its source and collection process motivate caution about noisy and incomplete tags. [Chua et al., *NUS-WIDE: A Real-World Web Image Database from National University of Singapore*](https://doi.org/10.1109/ICIVC.2009.32)
- Open Images provides image-level labels and localized object annotations, and explicitly distinguishes positive, negative, and unlabeled image-level labels in its annotation design. [Kuznetsova et al., *The Open Images Dataset V4*](https://arxiv.org/abs/1811.00982)
- COCO caption evaluation uses multiple human references and reports metrics including BLEU, METEOR, ROUGE, and CIDEr; the paper describes the evaluation server as a means of consistent comparison. [Chen et al.](https://arxiv.org/abs/1504.00325)

### Inferences

- **Benchmark matrix:** Use at least (1) VOC 2007 test for directly comparable closed-set object recognition AP, (2) COCO validation (or a fixed, documented public split) for broad object tags plus captions, and optionally (3) Open Images or NUS-WIDE as a separate stress test for broader labels/noisy web tags. Report datasets separately; do not pool their scores because vocabularies and annotation policies differ.
- **No-training constraint:** Freeze each model/checkpoint and all prompts, preprocessing, decoding, and postprocessing before test inference. No gradient updates, few-shot examples, test-label-driven prompt iteration, or test-set threshold tuning. Prompt-based models can use a declared fixed prompt template; record every prompt. If a public validation set is used to calibrate thresholds, do not also present its result as untouched test generalization.
- **Reproducible unit:** Pin dataset version, split, image IDs, label files, model/checkpoint hash, software versions, device, image resize/crop policy, precision (FP32/FP16/INT8), batch size, and deterministic settings. Evaluate the same image set for every system; report exclusions and failures.
- **Captions:** Use official COCO caption evaluation tooling where applicable and report CIDEr-D as a conventional primary metric, with SPICE and one or more lexical metrics as complementary views. Include human assessment on a blinded, randomized subset for factuality, coverage, and fluency: n-gram metrics alone can reward reference overlap without establishing truthfulness. Keep caption metrics distinct from tag scores.
- **Caption-to-tag analysis:** If extracting tags from generated captions, make the text-to-ontology parser a fixed, separately identified component. Report tagger-only and caption-derived tags separately; otherwise improvements may reflect parser behavior rather than image understanding.

### Gaps

- Dataset versions and label policies may change; record the exact release and official evaluation code revision at execution time. No single public dataset supplies exhaustive image-level tags across a universally accepted ontology.

## Metrics, calibration, ontology, and annotation limits

### Takeaway

Use thresholded precision/recall/F1 to describe a declared operating point, ranking metrics (macro mAP and precision@k) to describe score ordering, and calibration to choose thresholds without test leakage. Map predictions into an explicit shared ontology and distinguish verified negatives from unknown labels.

### Cited Findings

- Precision is TP/(TP+FP), recall is TP/(TP+FN), and F1 is the harmonic mean of precision and recall; these depend on the selected decision threshold, unlike ranking metrics. [scikit-learn model evaluation documentation](https://scikit-learn.org/stable/modules/model_evaluation.html#precision-recall-f-measure-metrics)
- Average precision summarizes the precision-recall curve for a class by aggregating precision across recall increments; mean average precision (mAP) averages AP over classes. VOC defines a benchmark-specific AP protocol; implementation details (including interpolation convention) matter for comparability. [PASCAL VOC challenge paper](https://doi.org/10.1007/s11263-009-0275-4); [VOC evaluation development kit](http://host.robots.ox.ac.uk/pascal/VOC/voc2007/devkit_doc.pdf)
- COCO caption evaluation paper describes CIDEr as consensus-based caption evaluation and uses multiple human captions as references. [Vedantam et al., *CIDEr: Consensus-based Image Description Evaluation*](https://arxiv.org/abs/1411.5726); [Chen et al.](https://arxiv.org/abs/1504.00325)
- Open Images documents the distinction among positive, negative, and unlabeled labels, which is important where annotations do not establish that an unmentioned class is absent. [Kuznetsova et al.](https://arxiv.org/abs/1811.00982)

### Inferences

- **Precision, recall, F1:** For each class at threshold τ, a predicted class is positive when its score is ≥τ. Precision answers “of emitted tags, how many are annotated relevant?”; recall answers “of annotated relevant tags, how many were recovered?” F1 balances them. Report per-class values and macro-F1 (equal class weight); optionally micro-F1 (aggregate TP/FP/FN, dominated more by frequent classes). State zero-division handling and averaging explicitly.
- **mAP:** Compute one AP per class from the continuous confidence ranking, then take the unweighted mean over evaluable classes (macro mAP). This evaluates ranking over thresholds and should not be confused with F1 at one threshold. State exact AP convention and which classes are omitted (e.g., no positive examples); use benchmark-provided evaluator when possible.
- **Precision@k:** For each image, sort candidate labels by score and compute the fraction of the top k that are relevant; average across images. Report k values meaningful to product use (for example 1, 3, 5), define behavior when fewer than k tags are emitted, and acknowledge that precision@k ignores relevant labels below rank k and does not measure recall. For incomplete annotations, apparent false positives may be unannotated true tags.
- **Threshold calibration:** Preserve raw scores and report mAP independently of thresholding. Select one global threshold on a separate calibration split for the primary deployable operating point; optionally provide per-class thresholds as a clearly labeled validation-tuned secondary result. Choose by an explicit objective (e.g., maximize macro-F1 or meet a target precision), freeze thresholds before test evaluation, and publish them. Report a threshold-sweep PR curve or several fixed operating points as sensitivity analysis. Never optimize thresholds on the reported test set.
- **Score calibration:** A model score is not automatically a probability. If probability meaning matters, evaluate calibration (e.g., reliability plots/Brier score) on a separate calibration split and disclose any calibration transform; calibrating model scores is post-processing, not model training, but remains data-dependent. For strict no-training comparisons, report uncalibrated rankings as the primary result and mark calibration as a separate protocol.
- **Ontology mapping:** Define a versioned target vocabulary before evaluation. Normalize spelling/case and documented aliases; use an explicit mapping table from each dataset label and each predicted label to target concepts. Resolve synonyms one-to-one where justified; define whether a specific child concept earns credit for a parent (e.g., dog→animal) and avoid silently treating broad labels as specific ones. Exclude unmappable labels from scored classes, publish coverage and the mapping, and report exact-match and hierarchical-credit scores separately if hierarchy matters.
- **Missing / non-exhaustive labels:** Do not score unlabeled/unknown as negative. Use known-positive/known-negative masks when the dataset supplies them; otherwise either score only classes/images with defensible annotation coverage or present conventional metrics explicitly as “agreement with recorded annotations,” with likely false-positive bias. Keep unknown labels out of TP/FP/FN denominators rather than converting them to negative. COCO captions describe salient content and object annotations cover defined categories, not every visible attribute, relation, or object; web tags can be noisy. [COCO dataset paper](https://arxiv.org/abs/1405.0312); [NUS-WIDE paper](https://doi.org/10.1109/ICIVC.2009.32)
- **Caption scoring limitations:** Report CIDEr-D/SPICE and BLEU or METEOR only with references and a fixed evaluator. Multiple valid descriptions may use words absent from the references; therefore a low lexical score need not mean an incorrect caption. Separately audit unsupported entities/attributes/actions and omissions using blinded human ratings or a disclosed factuality protocol. [CIDEr paper](https://arxiv.org/abs/1411.5726); [COCO Captions paper](https://arxiv.org/abs/1504.00325)

### Gaps

- No mapping can remove annotation-policy mismatch completely; any hierarchy credit, ignore mask, or partial-label treatment changes the estimand and must be declared. Caption metrics do not provide a universal factuality measure.

## Efficiency, reporting, and decision rules

### Takeaway

Measure end-to-end inference under a fixed, realistic hardware/software setup, include model-loading and preprocessing assumptions, and report latency distributions and peak memory alongside quality. A speed claim is defensible only when the evaluated workload and batch/concurrency conditions are explicit.

### Cited Findings

- The COCO paper establishes benchmark-scale image evaluation across a large dataset, while the caption paper describes a server-based standardized evaluation workflow; neither prescribes a universal hardware-normalized speed metric. [Lin et al.](https://arxiv.org/abs/1405.0312); [Chen et al.](https://arxiv.org/abs/1504.00325)
- The FCN paper reports inference time for a typical image as part of its method results, illustrating the usefulness of pairing accuracy with inference cost, though its reported time is tied to that study’s hardware and implementation. [Shelhamer et al., *Fully Convolutional Networks for Semantic Segmentation*](https://arxiv.org/abs/1605.06211)

### Inferences

- **Measure:** Report cold start/model load separately from warm inference; end-to-end wall-clock latency including image decode, resize/preprocess, model forward pass, and tag/caption postprocessing; throughput in images/second; median and p95 per-image latency; peak host RAM and accelerator memory; model/checkpoint disk size; and timeout/error rate. Distinguish serial batch-1 latency from batched throughput.
- **Control:** Use the same machine, accelerator, runtime, thread settings, image dimensions, and precision where feasible. Warm up consistently; synchronize asynchronous accelerators around timed regions; run enough repetitions and report sample count. Report batch size and whether timing includes data transfer. Do not compare timing numbers taken from papers on different hardware as if directly comparable.
- **Quality-cost view:** Show a compact table with macro mAP, macro-F1 at the declared threshold, precision@k, caption metric(s), median/p95 latency, throughput, and peak memory. Discuss the quality/latency trade-off rather than choosing a winner from a single metric.
- **Decision protocol:** Predeclare the primary tag metric and caption metric, plus minimum quality and resource requirements. Rank taggers using macro mAP on fully evaluable classes, then use the calibrated operating point to discuss precision/recall balance. Treat caption scores and human factuality assessment as separate axes. Provide per-class results and confidence intervals from paired image-level bootstrap resampling where practical; keep resampling unit and interval method fixed across systems.

### Gaps

- Hardware-neutral inference speed cannot be inferred from model papers; benchmark all candidates locally on the intended deployment device and publish exact conditions. Confidence intervals quantify sampling uncertainty, not systematic dataset annotation incompleteness.

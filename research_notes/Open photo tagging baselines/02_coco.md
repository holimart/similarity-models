# MS COCO for Zero-Shot Image Tagging

## What are the dataset licenses and what do images/instances/captions contain?

### Takeaway
Use COCO 2017 validation images with instance annotations as the primary benchmark for zero-shot object-tagging: it has image-level object presence labels derivable from boxes/masks and is simpler to score than free-form captions. Treat image rights and annotation/code rights separately; COCO is not a blanket public-domain license for its photographs.

### Cited Findings
- COCO describes itself as a large dataset for object detection, segmentation, keypoints, stuff segmentation, and caption generation; its API supports instance and caption annotation files. [COCO API README](https://github.com/cocodataset/cocoapi); [COCO API code](https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocotools/coco.py)
- COCO's official site provides a Terms of Use section and download links; the dataset is composed of images sourced from Flickr, with attribution/terms tied to original photographers and Flickr terms. Review the current official terms and the individual image license/attribution before redistribution or commercial use; availability for research does not make all images freely sublicensable. [COCO Terms of Use](https://cocodataset.org/#termsofuse); [COCO download page](https://cocodataset.org/#download)
- The API code is licensed under the Simplified BSD License; that applies to the API software, not automatically to the images. [COCO API license](https://github.com/cocodataset/cocoapi/blob/master/license.txt); [COCO API README](https://github.com/cocodataset/cocoapi)
- Instance annotation JSON follows the common COCO structure with `images`, `annotations`, and `categories`; image records include `id`, `file_name`, width/height, and URL metadata. Instance annotations link by `image_id` and `category_id`, and commonly contain `bbox` in `[x,y,width,height]`, `area`, `iscrowd`, and `segmentation` (polygon or RLE). Categories provide IDs, names, and supercategories. [COCO API](https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocotools/coco.py); [COCO data format](https://cocodataset.org/#format-data)
- Caption annotations instead link `image_id` to a text `caption`; captions are multiple human-written descriptions per image and do not define a fixed class-vocabulary tag ground truth. [COCO API](https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocotools/coco.py); [COCO captions task](https://cocodataset.org/#captions-2015)

### Inferences
- For tags from a fixed object vocabulary, instance-category presence is the most direct supervision target: collapse all non-crowd instance annotations for an image into a binary vector over the 80 COCO object categories. This is image-level multi-label classification, not object detection; it does not evaluate localization.
- Treat crowd annotations explicitly. Simplest baseline: exclude `iscrowd=1` annotations from positive labels, and report this policy because crowd regions may contain objects not individually annotated.
- Captions are useful for qualitative text/tag exploration but are a noisier and less exhaustive source of labels than instances, so do not treat a missing caption word as a definite negative.

### Gaps
- The official site's interactive terms/download page did not expose its full page content in this research fetch. Confirm the exact current permitted-use wording and image attribution obligations on the live official page before redistribution or commercial deployment.
- Image licensing may vary at the underlying photo level. This note does not verify the license of any particular image.

## What is a reliable, simple download and evaluation path, and what subset/metric should be used?

### Takeaway
Start with the 2017 validation split (5,000 images) and its `instances_val2017.json`; obtain the matching validation JPEG archive from the official COCO download page, then load annotations with `pycocotools`. For an initial fast run, use a deterministic 1,000-image subset drawn from those validation IDs, preserving the full 80-category vocabulary; report macro mean average precision (mAP) from per-class ranking scores.

### Cited Findings
- COCO's official download page lists the images and annotations by task and year; 2017 validation images and instance annotations are available as the standard paired split. [COCO download](https://cocodataset.org/#download)
- The COCO API README says to download images and annotations separately and place images under an image directory and JSON files under an annotations directory; it provides a Python API to load, parse, and visualize annotations. [COCO API README](https://github.com/cocodataset/cocoapi)
- The `COCO` Python class loads a JSON annotation file and exposes indexed image, annotation, and category accessors including `getImgIds`, `getCatIds`, `loadImgs`, and `loadAnns`. [COCO API implementation](https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocotools/coco.py)
- An alternative for quick experimentation is a Hugging Face-hosted COCO-derived dataset, but it is a third-party packaged representation and may not preserve the original complete annotation semantics; prefer official split archives plus official JSON for reproducibility. [Example hosted COCO dataset](https://huggingface.co/datasets/merve/coco)
- Scikit-learn's `average_precision_score` accepts multi-label indicator matrices and decision scores; `average='macro'` computes the unweighted mean AP across labels, avoiding domination by common classes. [scikit-learn average_precision_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html)

### Inferences
- Recommended reproducible recipe: download `val2017.zip` and `annotations_trainval2017.zip` from the official page; load `instances_val2017.json`; sort image IDs and select the first 1,000 after a seeded permutation; resolve each `file_name` within the extracted `val2017/` directory. Save the selected IDs and the seed alongside predictions so results are repeatable. A 1,000-image subset is a manageable smoke-test size, not a statistically comprehensive benchmark; expand to all 5,000 validation images for final comparisons.
- If bandwidth or disk is the bottleneck, use `pycocotools.COCO` to select image records then download only those image URLs, but official prepacked validation ZIPs are less brittle than bespoke per-image downloads. The API's `download` helper uses each image's `coco_url`, but its implementation is simple sequential URL retrieval and may be less robust than the official archive for interrupted/retried downloads.
- Build `Y[i,c]=1` if an image has at least one non-crowd instance annotation of category c; otherwise 0. Keep model output as a score for every image/category pair, without tuning thresholds on the test subset.
- Primary metric: macro mAP across the 80 categories, calculated from continuous zero-shot scores and binary target matrix. Also show per-class AP and micro mAP as diagnostic context; macro mAP balances rare and common categories. Use a separate calibration/threshold set if reporting thresholded precision/recall or F1.
- This benchmark measures zero-shot recognition of COCO's predefined object categories, not open-vocabulary tagging across arbitrary concepts, tag wording quality, or localization. Avoid claiming direct comparability to official COCO detection AP, which requires scored boxes and IoU matching.

### Gaps
- COCO's official web page is JavaScript-driven and this fetch only surfaced the page shell; exact archive sizes, direct URLs, and current mirror availability could not be confirmed here. Use the official download page for live links rather than embedding potentially stale URLs.
- No single subset size is mandated. The 1,000-image recommendation is an operational judgment for an early baseline; its variance may be high for rare categories, so use all 5,000 validation images for stable reporting.

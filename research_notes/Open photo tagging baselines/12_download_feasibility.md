# Practical download feasibility for image-tagging benchmarks

## Which dataset gives the easiest first end-to-end benchmark?

### Takeaway
Use the Hugging Face `detection-datasets/coco` auto-converted Parquet dataset for a quick first image-tagging benchmark: its card/viewer exposes image payloads and labels together, allows straightforward row-level sampling, and avoids a separate image downloader. For a more provenance-controlled evaluation, use official COCO images plus annotations and `torchvision.datasets.CocoDetection`, but this is not a turnkey downloading API.

### Cited Findings
- The current Hub dataset page for [`detection-datasets/coco`](https://huggingface.co/datasets/detection-datasets/coco) shows an auto-converted Parquet dataset with 122k rows (117k train, 4.95k validation), image, dimensions, and object category/bounding-box fields; the viewer displays rendered images. This is a third-party Hub distribution/conversion, not the official COCO hosting channel.
- Hugging Face documents `load_dataset()`/ImageFolder patterns and image columns for image datasets; see [Hugging Face image dataset guide](https://huggingface.co/docs/datasets/image_dataset). The COCO card is directly loadable as a Hub dataset without requiring torchvision’s local `root` plus annotation JSON arrangement.
- Torchvision’s [`CocoDetection` API](https://docs.pytorch.org/vision/stable/generated/torchvision.datasets.CocoDetection.html) expects a local image root and annotation JSON and requires `pycocotools`; it does not provide COCO downloads. The API returns an image plus target annotations.
- Torchvision’s [dataset catalog](https://docs.pytorch.org/vision/stable/datasets.html) lists COCO for detection/segmentation and captions, but not as an image-tagging-focused dataset with a `download=True` convenience flow. `CocoDetection` is a dataset adapter, not an official dataset mirror.
- The [official COCO site](https://cocodataset.org/#download) remains the primary source for dataset information, downloads, and terms. COCO image files are separate from annotation files, so a local torchvision setup requires obtaining and arranging those files independently.
- The Hub COCO page embeds image files and object annotations, giving accessible actual pixels rather than only URL lists. Its object categories can be converted to multi-hot image-level tags by deduplicating categories per image; this is a derived label task, not a supplied COCO classification benchmark.
- For a first sample, select a small, deterministic subset from the train/validation split, make image-level targets from each example’s object `category` values, and record the Hub dataset revision plus selected row IDs. Treat it as a smoke/engineering benchmark, not a canonical leaderboard evaluation.

### Inferences
- COCO on HF is the most robust low-friction route when the requirement is to load images and labels quickly, because both image pixels and annotations are present together and a small row subset does not require downloading the full original image archive.
- The official-file route is preferable once reproducibility against the official distribution matters, but requires more setup and storage; the third-party Hub conversion may alter schema, filtering, or split semantics, so verify class mapping and image counts before reporting scores.
- A small arbitrary row slice is useful for verifying a training loop, but not for estimating generalization. A benchmark-grade split should be fixed and documented, and no validation/test examples should be used for training.

### Gaps
- The HF COCO card/viewer does not establish byte-for-byte identity to official COCO archives or provide an explicit per-row provenance audit. Verify image IDs, image hashes, annotations, and split conventions locally before treating results as official.
- Access to the official COCO download section was reachable but its page rendering did not expose detailed terms/content in the fetched text. Consult the current COCO terms page directly before redistribution or commercial use.

## How feasible are Open Images loaders, small subsets, and image access?

### Takeaway
Open Images is highly configurable but heavier and less deterministic for a first benchmark. The official V7 documentation offers a supported small-subset workflow through its image-ID downloader or FiftyOne; Hugging Face mirrors can provide direct image payloads, but remain third-party copies and can be very large even when represented as a convenient dataset object.

### Cited Findings
- The [official Open Images V7 download page](https://storage.googleapis.com/openimages/web/download_v7.html) distinguishes image-level labels for over 9M images from a dense subset of about 1.9M; it documents manual downloads and describes the TFDS option as “To be released” on that page.
- The official page documents using `downloader.py` with a text file of `split/imageID` entries, allowing targeted image retrieval instead of full-image downloads. It also points to the [official Open Images downloader repository](https://github.com/openimages/dataset), whose current README states Open Images has moved to the dataset website.
- The official Open Images docs recommend [FiftyOne’s Open Images V7 loader](https://voxel51.com/docs/fiftyone/dataset_zoo/datasets.html#open-images-v7) as another subset path: choose split, labels, classes, `max_samples`, or exact image IDs. FiftyOne is a third-party open-source loader collaborating with the dataset maintainers, not the official data host.
- The official V7 page reports 9,178,275 total images and describes downloading all images via CVDF; for the full label dataset it lists 7,337,077 train images with human-verified labels and 8,949,445 with machine-generated labels. See [Open Images V7 download](https://storage.googleapis.com/openimages/web/download_v7.html).
- The official image-information format includes `OriginalURL`, landing page, license, author, title, original size/MD5, thumbnail URL, and rotation; the page warns that thumbnails may differ in content/resolution over time. Image access therefore depends on the originally hosted source pixels and may not be stable forever. [Official image metadata documentation](https://storage.googleapis.com/openimages/web/download_v7.html#df-image-information).
- Hub search lists third-party mirrors including [`nlphuji/open_images_dataset_v7`](https://huggingface.co/datasets/nlphuji/open_images_dataset_v7), [`bitmind/open-images-v7-subset`](https://huggingface.co/datasets/bitmind/open-images-v7-subset), [`bitmind/open-images-v7`](https://huggingface.co/datasets/bitmind/open-images-v7), and [`dalle-mini/open-images`](https://huggingface.co/datasets/dalle-mini/open-images). The `nlphuji` card identifies itself as a test-set dataset, reports 7.03 GB, and has a viewer disabled because its loading script executes arbitrary Python; do not mistake it for a compact generic loader.
- The current [`bitmind/open-images-v7-subset` Hub page](https://huggingface.co/datasets/bitmind/open-images-v7-subset) exposes 1.74M rows in a Parquet-backed viewer, with rendered image payloads. This is third-party and still a substantial subset; its readily accessible payloads do not imply a small download or official curation.
- Open Images’ official formats supply multi-label image-level labels (including verified positives and verified negatives) across a very large class vocabulary. Machine-generated labels are confidence-valued; the official docs distinguish them from human verification. [Official label format](https://storage.googleapis.com/openimages/web/download_v7.html#df-image-labels).
- The official license/author metadata is image-specific and points to original landing pages/licenses. A dataset-level “Open Images” label should not be read as a blanket license for unrestricted reuse of every image. [Official Open Images metadata](https://storage.googleapis.com/openimages/web/download_v7.html#df-image-information).

### Inferences
- If Open Images is needed for the first experiment, create a class-filtered list of image IDs from human-verified image labels, use official downloader or FiftyOne with `max_samples`, and cache a fixed manifest of successfully retrieved IDs. This keeps pixel fetching controllable and makes failed/missing images visible.
- For faster prototyping without source-URL failures, a Hub Parquet mirror with embedded pixels is convenient; pin the repository revision and expect material disk/network use. Validate image-label joins and class hierarchy rather than assuming every mirror retains all official label types or splits.
- Open Images offers broader, more realistic tagging labels than COCO, but its large class ontology, partially verified labels, URL-based pixel provenance, and image-level license variation increase preparation overhead.

### Gaps
- A successful viewer preview confirms some image payload accessibility, not a complete integrity audit or guaranteed availability for all 1.74M rows. The mirror’s complete downloadable byte size was not established from the fetched page.
- This research did not test a full Open Images downloader run, measure image retrieval success rates, or inspect the exact current CVDF transfer commands end-to-end.

## What are NUS-WIDE’s access, mirror, and restriction tradeoffs?

### Takeaway
NUS-WIDE has tempting Hugging Face mirrors with directly viewable image payloads, but it is the least robust starter: the official university download endpoint could not be verified in this pass, Hub mirrors are third-party, and some listings have failed viewers or unclear file/label provenance. Use only after checking the mirror’s labels, splits, provenance, and usage terms against the NUS-WIDE paper/site.

### Cited Findings
- Hugging Face search currently surfaces several third-party NUS-WIDE repos, including [`moneyzz432/nus_wide`](https://huggingface.co/datasets/moneyzz432/nus_wide), [`mengfanlei/NUS-WIDE`](https://huggingface.co/datasets/mengfanlei/NUS-WIDE), [`Lxyhaha/NUS-WIDE`](https://huggingface.co/datasets/Lxyhaha/NUS-WIDE), and [`augety12/nuswide-images`](https://huggingface.co/datasets/augety12/nuswide-images). These are not university-operated official mirrors.
- The current [`moneyzz432/nus_wide` page](https://huggingface.co/datasets/moneyzz432/nus_wide) displays image payloads in its preview, demonstrating that at least some pixels can be served directly through HF storage. However, its dataset viewer reports a job-manager crash, and its page provides no evidence in the fetched view that labels, canonical splits, or all official images are included.
- The NUS-WIDE university page at the historical URL [`lms.comp.nus.edu.sg/.../NUS-WIDE.html`](https://lms.comp.nus.edu.sg/wp-content/uploads/2019/research/nuswide/NUS-WIDE.html) could not be fetched in this research environment (transport error). This is an access limitation of this investigation, not evidence that the official page or dataset is offline.
- Hugging Face’s dataset search results establish that mirrors exist, but do not certify their provenance, exact image count, annotation compatibility, or rights. A visible Hub image column can represent hosted image blobs, while other mirrors may use URL references or a loading script; inspect each repository’s files and card before selection. [HF NUS-WIDE search](https://huggingface.co/datasets?search=nus-wide); [HF image dataset guide](https://huggingface.co/docs/datasets/image_dataset).
- A commonly referenced NUS-WIDE publication is [Chua et al., “NUS-WIDE: A Real-World Web Image Database from National University of Singapore”](https://doi.org/10.1109/ICMR.2009.55). The accessible source in this investigation did not resolve the university-hosted download terms or a first-party current loader, so exact use restrictions should be checked at source before redistribution or commercial use.

### Inferences
- If choosing a third-party NUS-WIDE Hub mirror for an exploratory run, pin its commit and inspect card, repository files, image/label columns, duplicate IDs, class vocabulary, split files, and stated license. Compare records to the original NUS-WIDE specification before citing benchmark scores as NUS-WIDE results.
- For a minimal successful image-tagging pipeline, the observed HF mirror can demonstrate image access, but its crashed viewer and unclear label completeness make it weaker than the COCO Parquet distribution.

### Gaps
- I could not confirm the current official NUS-WIDE download endpoint, terms of use, current accessibility, or whether any named mirror was approved by NUS. Treat all Hub instances found here as third-party until proven otherwise.
- The pages fetched did not establish whether mirror images are all bundled pixels or a subset reconstructed from source URLs; the example page showed payloads for preview rows only.

## Recommendation and usage restrictions

### Takeaway
Start with the Hugging Face COCO Parquet dataset for a small, reproducible engineering benchmark; pin the dataset revision and create multi-hot image tags from object categories. Move to official COCO files for canonical reproducibility, and consider Open Images next for richer tagging; defer NUS-WIDE until the exact mirror and usage terms are validated.

### Cited Findings
- COCO’s current HF dataset exposes sampleable images and object categories together, while Torchvision provides a local-file adapter requiring image root, annotation JSON, and `pycocotools`. [HF COCO](https://huggingface.co/datasets/detection-datasets/coco); [Torchvision CocoDetection](https://docs.pytorch.org/vision/stable/generated/torchvision.datasets.CocoDetection.html).
- Open Images’ official process supports explicit class/image-ID subsets through its downloader and supports class limits and sample limits through FiftyOne. [Official download page](https://storage.googleapis.com/openimages/web/download_v7.html).
- Open Images metadata describes source-site licensing per image, and the official page describes the pixels as appearing as on destination websites. Preserve attribution/license metadata when using or sharing a derived corpus. [Official Open Images image-info format](https://storage.googleapis.com/openimages/web/download_v7.html#df-image-information).
- Hub-hosted replicas are distinct from official dataset sources: COCO’s Hub copy is under `detection-datasets`; Open Images mirrors are in community accounts; the discovered NUS-WIDE datasets are community accounts. Their convenience does not transfer authority over source data or remove the need to follow original terms. [COCO Hub card](https://huggingface.co/datasets/detection-datasets/coco); [Open Images Hub search](https://huggingface.co/datasets?search=open%20images); [NUS-WIDE Hub search](https://huggingface.co/datasets?search=nus-wide).
- HF’s [dataset-card guidance](https://huggingface.co/docs/hub/datasets-cards) provides dataset metadata/card conventions; these cards are useful for documenting a mirror but do not independently establish rights over underlying images.

### Inferences
- Recommended starter ranking for practical use: (1) HF COCO auto-converted Parquet for quickest smoke benchmark; (2) official Open Images subset via FiftyOne/downloader when image-level tag coverage is desired; (3) official COCO files plus torchvision when exact canonical data/control is more important than setup ease; (4) NUS-WIDE third-party mirror only after provenance/terms review.
- Keep a manifest with source URL, dataset ID/revision, image ID, label source, split, retrieval status, and any license/attribution fields. For a derived multi-label task, specify label construction (e.g., positive object categories only for COCO) and do not imply that synthesized labels are official image-level ground truth.
- Apply the original dataset/source terms and image-level license conditions, even when accessing through HF or a helper library. Do not assume an aggregator’s general license field covers third-party image copyrights.

### Gaps
- No legal determination is made here. Specific COCO/NUS-WIDE terms should be verified from current first-party pages before commercial use, redistribution, or publication of image files.
- No throughput, exact download size, or missing-image-rate benchmark was measured locally. The feasibility ranking reflects documented interfaces and observed page structure, not a completed full-scale download test.

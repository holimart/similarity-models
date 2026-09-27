# Hard-condition real-image OCR datasets

## Which image datasets target difficult capture conditions?

### Takeaway
TextZoom is the most direct benchmark for genuinely captured low-resolution word crops, with paired LR/HR views and transcription. For scene-level challenges, combine established incidental/skewed-text sets (ICDAR 2015, SVT-Perspective) with curved/arbitrary geometry (Total-Text, CTW1500, ArT) and multilingual data (ICDAR MLT); these generally provide still images, not video. There is no single public set here that cleanly labels and balances blur type, low light, perspective, curvature, scale, and language.

### Cited Findings
- TextZoom was introduced as paired real low-/high-resolution scene text captured with cameras at different focal lengths; the authors contrast this with synthetic bicubic downsampling and describe alignment/ambiguity among difficulty subsets. [Paper](https://arxiv.org/abs/2005.03341)
- The official TextZoom repository offers an LMDB download via Google Drive/Baidu Netdisk. Each sample includes LR and HR images plus a case-sensitive transcription (punctuation included), bounding-box type/direction, and original focal lengths; three subsets are called easy/medium/hard. These are word crops, not full original scene photographs. [Author repository](https://github.com/WenjiaWang0312/TextZoom)
- The same repository separately points to crops and bounding-box/word-label JSON for SR-RAW and RealSR, but requires downloading those source datasets for the original images. The JSON includes word polygons, transcription, orientation type, and source filename. [Author repository](https://github.com/WenjiaWang0312/TextZoom)
- Total-Text has 1,555 still scene images with horizontal, multi-oriented, and curved English text. Its repo provides image data and word-level ground truth; the release includes text-level and pixel-level annotations. This makes it useful for curved text recognition/detection, but the benchmark is not a blur/lighting-specific dataset. [Official repository](https://github.com/cs-chan/Total-Text-Dataset)
- Total-Text repository states BSD-3-Clause for the project and says commercial use requires contacting the dataset author; do not assume the code license grants unrestricted image rights. [Official repository](https://github.com/cs-chan/Total-Text-Dataset)
- SCUT-CTW1500 provides 1,000 training and 500 test still images and annotations; its line-level text regions use curved polygons, with additional per-character point annotations in training. The repository explicitly says Chinese text is marked ignore (`###`) in the updated annotations because there are too few instances, so it is not a useful Chinese transcription benchmark. Rights: free for academic research only; other uses require contacting the dataset owner. [Author repository](https://github.com/Yuliang-Liu/Curve-Text-Detector)
- ArT (ICDAR 2019 Arbitrary-Shaped Text) is a benchmark for detection, recognition, and spotting of arbitrary-shaped text. Its official challenge report says dataset, evaluation kit, and results are public; the paper/repo describe ArT as incorporating Total-Text and CTW1500 and provide broader arbitrary text shapes. The challenge site was inaccessible during this check, so exact current download steps, annotation schema details, and license terms could not be verified. [Challenge report](https://arxiv.org/abs/1909.07145); [Total-Text repository's ArT note](https://github.com/cs-chan/Total-Text-Dataset)
- ICDAR 2015 incidental scene text (often called the Challenge 4 dataset) is a standard still-image benchmark for incidental text; its rotated quadrilateral annotations support skewed/oriented scene text. The official RRC site could not be fetched in this research session, so current access rules and annotation field details require confirmation at the [challenge page](https://rrc.cvc.uab.es/?ch=4). A paper using it describes oriented quadrilateral text geometry, not a dedicated capture-condition taxonomy. [EAST paper](https://arxiv.org/abs/1704.03155)
- SVT-Perspective was created for perspective distortion in street-view imagery and is conventionally used for word recognition from perspective-cropped word images. This complements scene-level full-image detection sets, but the original official download/license source was not successfully verified here; treat redistribution and commercial-use rights as unresolved pending the dataset authors' terms. [Dataset paper search landing via Google Scholar](https://scholar.google.com/scholar?q=SVT-Perspective+dataset+scene+text+recognition)
- ICDAR 2017 MLT was designed as multilingual scene text detection data (nine languages/scripts in the benchmark), with full scene images and word-level polygon/transcription annotations for multilingual text. Use the challenge's official page for current release and terms; the RRC site endpoint could not be retrieved during this check. [Official challenge page](https://rrc.cvc.uab.es/?ch=9)
- No verified source in this pass established a public real-capture dataset with a comprehensive explicit label taxonomy for motion blur vs. defocus, low-light exposure, and blur severity. Such conditions occur in general scene datasets but should not be claimed as separately annotated without dataset-specific confirmation.

### Inferences
- TextZoom is appropriate for recognition robustness and SR under real optical resolution changes, but it cannot alone measure end-to-end localization in full scenes because its primary benchmark data are cropped words.
- A useful difficult-image suite can pair TextZoom (low resolution), ICDAR 2015/SVT-Perspective (incidental and perspective/oriented text), Total-Text or CTW1500/ArT (curved geometry), and MLT (script diversity). Condition-specific evaluation labels likely need to be curated or added by evaluators.
- For legal reuse, distinguish benchmark/code availability from image rights. Official terms should be checked before commercial use or redistribution; TextZoom's hosting links and open repo are not, by themselves, an explicit image license.

### Gaps
- Exact current access forms and licenses for TextZoom, ICDAR 2015, SVT-Perspective, MLT, and ArT were not all stated on the retrieved primary material; challenge portal pages were partly inaccessible. Confirm terms directly before deployment or redistribution.
- No source reviewed supported claims that the named still-image sets label blur subtype, low-light severity, or perspective severity as structured attributes.

## Do public video datasets support temporal OCR evaluation?

### Takeaway
Public video-text datasets and challenge benchmarks do exist, but the evidence gathered here does not establish a currently downloadable, rights-clear dataset with frame-by-frame transcriptions and identity/track annotations sufficient for standardized temporal OCR metrics. Treat video-based temporal OCR evaluation as possible but dataset/access-specific, and check whether the release includes original clips versus sampled frames.

### Cited Findings
- ICDAR 2015 RRC Challenge 3 is an official video text benchmark challenge (distinct from the still-image Challenge 4); the official RRC endpoint could not be fetched in this session, so clip availability, annotations, and terms cannot be reported as confirmed. [Official challenge page](https://rrc.cvc.uab.es/?ch=3)
- The Total-Text repository itself includes an animated GIF illustrating dataset examples, but its dataset is explicitly a collection of 1,555 images; this is not a video OCR corpus and does not provide temporal sequences. [Official repository](https://github.com/cs-chan/Total-Text-Dataset)
- TextZoom distributes paired still LR/HR word images in LMDB and not video sequences. [Official repository](https://github.com/WenjiaWang0312/TextZoom)
- The reviewed sources did not document temporal identity, frame-level text transcription, or sequence-level evaluation protocol for the image datasets above.

### Inferences
- For genuine temporal OCR evaluation, a valid release needs accessible consecutive frames/clips, text transcription per visible instance per frame, and a documented linkage/track identity or a protocol for aggregating recognition across frames. Merely extracting frames from a video detection dataset does not establish temporal ground truth.
- ICDAR video challenges are the most promising starting point in this set, but their current archive and annotations need direct verification before claiming they support repeatable temporal recognition evaluation.

### Gaps
- This research pass did not verify the current availability, format, licensing, annotation granularity, or evaluation protocol of ICDAR 2015 video Challenge 3, or locate a primary-source-hosted alternative such as YVT with current download terms. Consequently, no video dataset is recommended as confirmed rights-clear temporal OCR ground truth here.
- A follow-up should inspect the challenge archive/docs directly and determine whether it contains full videos, sampled frames, per-frame text labels, and persistent text-track IDs.

# Receipt/invoice OCR datasets: public access and downloads

## Which datasets have genuinely public direct downloads suitable for offline OCR experiments?

### Takeaway

CORD v0 is the best clearly public, small-ish receipt option surfaced here: its original project provides a direct Google Drive download link to a 1,000-image ZIP, and its stated license is CC BY 4.0. SROIE is a very relevant 1,000-image OCR benchmark with a publicly reachable Google Drive source link, but the current source does not disclose an archive size or a clearly scoped dataset license; treat it as a research lead rather than redistribution-ready local bundle content.

### Cited Findings

- CORD’s primary project repository describes a 1,000-receipt sample dataset with 800 train, 100 dev and 100 test images, and links directly to a Google Drive folder and a ZIP download folder for v0: [CORD project README](https://github.com/clovaai/cord).
- CORD’s repository identifies the work as CC BY 4.0; the project supplies the standard attribution license text: [CORD license](https://github.com/clovaai/cord/blob/master/LICENSE-CC-BY); [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/).
- CORD contains Indonesian receipts, box/text annotations and semantic labels; it is useful for general OCR mechanics, but not Czech-language evaluation. The current Hugging Face v2 card reports 1,000 rows and a total size of 2.31 GB, and identifies its format as Parquet: [CORD v2 card](https://huggingface.co/datasets/naver-clova-ix/cord-v2).
- CORD v2’s Hugging Face page is publicly viewable and licenses the dataset as CC BY 4.0, but the project’s downloadable version is not small (2.31 GB); it is a less practical bundle candidate than the original sample ZIP. The page does not show a login/approval gate in the fetched public view: [CORD v2 card](https://huggingface.co/datasets/naver-clova-ix/cord-v2).
- SROIE contains 1,000 scanned receipt images (600 train/validation, 400 test) and OCR text boxes/transcripts. The publicly available project README links to the original Google Drive dataset, as well as a Baidu alternative: [SROIE project README](https://github.com/zzzDavid/ICDAR-2019-SROIE).
- The SROIE project page itself is under an MIT license, but its README distinguishes the original competition dataset from the code repository. The MIT repository license therefore does not establish that receipt images are MIT-licensed: [SROIE repository and license](https://github.com/zzzDavid/ICDAR-2019-SROIE).
- The SROIE repository includes a corrected `data/` tree separated into `img`, `box`, and `key`, but it does not document a dataset archive format/size there: [SROIE data directory](https://github.com/zzzDavid/ICDAR-2019-SROIE/tree/master/data).

### Inferences

- For a quick local offline smoke test with clearer reuse terms, prefer CORD v0; download the ZIP from the linked Drive folder and unpack it locally. The direct public folder is confirmed by the project README, but the precise byte size and ZIP’s internal layout are not stated in the README and should be inspected at download time.
- CORD v2 is public-accessible without an apparent registration requirement, but its 2.31 GB reported file size makes it poorly suited to bundling with a lightweight application.
- SROIE is useful OCR data if the local experiment is strictly private/research and the user independently verifies the image rights and current Drive availability. Avoid republishing or bundling the source images based solely on the mirror repository’s MIT code license.

### Gaps

- CORD v0 Drive archive’s current exact URL target, byte size, and internal extraction tree were not exposed by the project README page; the README offers a ZIP-folder link rather than a stable direct-download URL. No download was performed.
- The original SROIE Drive link’s current response, archive size/format, and authoritative image-dataset license could not be verified from the accessible primary project pages. The official challenge site did not load in this research pass.

## Which sources require registration/Hugging Face access, and what should be excluded or flagged for restrictive image terms?

### Takeaway

CORD v2 is hosted openly on Hugging Face in Parquet form and appears ungated on its public card, while the smaller CORD v0 route uses public Google Drive folders. SROIE’s challenge-origin access and data rights remain less clear than its publicly linked mirror; keep its images out of a redistributable bundle until the competition terms are checked. Dataset licenses may not settle third-party rights in the receipt images themselves.

### Cited Findings

- CORD’s project repository explicitly links v0 sample/ZIP and directs v1/v2 users to Hugging Face: [CORD project README](https://github.com/clovaai/cord).
- The CORD v2 page lists CC BY 4.0, Parquet format, 1,000 rows, train/dev/test splits of 800/100/100, and total size 2.31 GB: [CORD v2 on Hugging Face](https://huggingface.co/datasets/naver-clova-ix/cord-v2).
- Hugging Face’s public dataset page offers metadata and a viewer without showing an access-request/approval notice in the inspected view; that is distinct from guaranteeing every download route will remain anonymous or stable: [CORD v2 dataset card](https://huggingface.co/datasets/naver-clova-ix/cord-v2).
- The CORD repository says some label categories were omitted from public release due to Indonesian legal issues, specifically `store_info`, `payment_info`, and `etc`: [CORD project README](https://github.com/clovaai/cord). This is a data-publication caveat, not a separate access gate.
- SROIE’s public mirror links the original data to Google Drive and Baidu but provides no dataset-specific terms in its README; its repository MIT notice is not an adequate basis for claiming the images are freely redistributable: [SROIE README](https://github.com/zzzDavid/ICDAR-2019-SROIE).
- CC BY 4.0 requires attribution when sharing licensed material and does not itself license rights the licensor does not control, including third-party rights: [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/); [CORD license file](https://github.com/clovaai/cord/blob/master/LICENSE-CC-BY).

### Inferences

- Practical choice: CORD v0 for compact experimentation, CORD v2 when exact public HF hosting and its 2.31 GB Parquet distribution are acceptable, and SROIE only after the image terms are independently confirmed.
- Preserve the source attribution/license with any CORD data you redistribute; investigate underlying receipt-image rights separately before bundling even where the dataset card says CC BY 4.0.
- This search did not establish any specifically Czech-language receipt OCR corpus with both clearly public direct downloads and verified permissive image terms. The benchmark examples above are Indonesian and Malaysian/English-facing respectively, so they are not Czech evaluation substitutes.

### Gaps

- No authoritative evidence was found in the inspected sources for whether SROIE challenge participants must register or accept additional terms to retrieve the official archive, nor for an image-specific license suitable for downstream redistribution.
- No precise archive size or stable direct-download endpoint was confirmed for the CORD v0 Drive ZIP or original SROIE archive.
- Other potentially relevant invoice/receipt corpora may be gated by registration or published with non-commercial/research-only image terms; this source pass did not verify a full catalog of those datasets and therefore does not label any such dataset as safely bundleable.

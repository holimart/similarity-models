# Real-image receipt and invoice OCR datasets

## Which datasets provide real receipt/invoice images and OCR supervision?

### Takeaway
For directly usable real receipt-image OCR, CORD and SROIE are the strongest straightforward candidates: both expose images and text-level localization/transcription labels, though SROIE’s original challenge split is not fully labeled for public training. EPHOIE is real scanned Chinese exam-paper imagery (not receipts/invoices) and requires institutional research access; DocILE is business-document KIE/LIR with gated access and precomputed OCR, while XFUND is primarily form understanding rather than receipt OCR. RVL-CDIP is relevant only for document image classification, not OCR labels.

### Cited Findings
- CORD describes 11,000+ collected Indonesian receipts in the full source set but publicly releases 1,000 images (800 train/100 dev/100 test) in v0/v1/v2; the Hugging Face v2 card lists 1,000 rows and image + structured JSON ground truth. [CORD repository](https://github.com/clovaai/cord); [CORD v2 on Hugging Face](https://huggingface.co/datasets/naver-clova-ix/cord-v2)
- CORD annotations include `valid_line` word-level text and quadrilateral coordinates, key flag, row/group ids and categories, plus hierarchical `gt_parse`; this supports word/line OCR recognition as well as receipt KIE/post-OCR parsing. It is Indonesian receipt content, often using Latin script. [CORD repository](https://github.com/clovaai/cord)
- CORD's repository states CC BY 4.0. Repository provides Google Drive links for original 1,000 sample and links v1/v2 to Hugging Face; v2 is directly browsable/downloadable via Hugging Face datasets tooling. There is no application/access gate stated. [CORD repository](https://github.com/clovaai/cord); [CORD v2](https://huggingface.co/datasets/naver-clova-ix/cord-v2)
- CORD's release announcement says some labels from the original taxonomy were removed due to Indonesian legal issues, including `store_info`, `payment_info`, and `etc`; user should not assume the public labels contain all sensitive business/store details. [CORD repository](https://github.com/clovaai/cord)
- SROIE challenge source describes 1,000 whole scanned receipts, 600 trainval and 400 test. OCR task labels are text bounding boxes and transcripts in per-image text files (eight corner coordinates and transcript, ICDAR-style); KIE labels provide company, address, date, total JSON. [SROIE challenge team repository](https://github.com/zzzDavid/ICDAR-2019-SROIE); [official ICDAR challenge page](https://rrc.cvc.uab.es/?ch=13&com=introduction)
- SROIE is principally English/Malay context and annotations are mainly digits and English characters. The official challenge has separate text localization, OCR and KIE tasks, making it suitable for OCR recognition (especially trainval) and key field extraction. The public repository is a participant's corrected mirror, not the official dataset host. [SROIE team repository](https://github.com/zzzDavid/ICDAR-2019-SROIE)
- Repository download instructions point to a Google Drive dataset link and Baidu Netdisk mirror; no application is described there. Official challenge is on the Robust Reading Competition portal. Dataset redistribution and licensing terms are not clearly specified in the team repo; its MIT license explicitly licenses that team's code, not necessarily the receipt images or annotations. Treat image reuse as rights-unclear pending organizer terms. [SROIE team repository](https://github.com/zzzDavid/ICDAR-2019-SROIE); [official ICDAR challenge](https://rrc.cvc.uab.es/?ch=13&com=introduction)
- EPHOIE contains 1,494 images (1,183 train, 311 test) cropped from real scanned Chinese examination-paper heads, with printed and handwritten Chinese. All text has quadrilateral boxes and transcriptions, and key-value entity labels, so it supports scene/document OCR and VIE, but is not a receipt/invoice corpus. [EPHOIE repository](https://github.com/HCIILAB/EPHOIE)
- EPHOIE has a research-only non-commercial use condition for SCUT-EnsText; training data are encrypted. Access steps: download and complete the application form; obtain institutional signature/stamp; provide 1–2 recent relevant publications; submit documents through the lab portal; await manual review (stated typical 1–5 business days); approved applicants receive download link and decompression password by email. Commercial use requires contacting the lab for a commercial license. [EPHOIE repository and access instructions](https://github.com/HCIILAB/EPHOIE)
- XFUND is seven-language form-understanding data (Chinese, Japanese, Spanish, French, Italian, German, Portuguese), not receipt/invoice data. Its image/annotation release provides K/V forms and token-level entities; the README’s per-language tables count entity tokens rather than documents/images. It is useful for form KIE and multilingual layout-aware understanding, not a standalone OCR recognition benchmark unless using its word transcripts as auxiliary recognition data. [XFUND repository](https://github.com/doc-analysis/XFUND)
- XFUND official release is GitHub release v1.0 linked from its README. Its stated license is CC BY-NC-SA 4.0: noncommercial and share-alike conditions matter for downstream use. The linked release is the download route; no application process is documented in the README. [XFUND repository](https://github.com/doc-analysis/XFUND); [v1.0 release](https://github.com/doc-analysis/XFUND/releases/tag/v1.0)
- DocILE covers 106,680 business documents with KILE/LIR labels (6,680 annotated and 100,000 synthetic), plus nearly 1 million unlabeled documents for pretraining; real-image/PDF documents are provided. Its purpose is field localization/extraction and line-item recognition, not OCR character recognition; precomputed DocTR OCR words are included, and document images can be rendered from supplied PDFs. [DocILE official site](https://docile.rossum.ai/); [DocILE repository](https://github.com/rossumai/docile)
- DocILE access process requires submitting its Dataset Access Request Google Form to obtain a secret token, then running the repository download script with the token and split name (`annotated-trainval`, `test`, `synthetic`, `unlabeled`; options include chunks and OCR-only unlabeled data). Docs characterize it as access for research purposes; the site links a legal-information notice on personal data. Do not treat the software repository's MIT license as a blanket data license; dataset access terms apply. [DocILE official site](https://docile.rossum.ai/); [download instructions](https://github.com/rossumai/docile)
- DocILE annotation format is field instances with page, normalized bbox, field type and optional text; LIR additionally groups fields with line-item ids. It supplies precomputed OCR word boxes/text and evaluation tracks KILE and LIR. Its language is not prominently declared on the landing page; the corpus is semi-structured business documents, with English-language examples/labels in materials, but do not infer that every document is English. [DocILE repository](https://github.com/rossumai/docile); [DocILE paper](https://arxiv.org/abs/2302.05658)
- RVL-CDIP/IIT-CDIP is 400,000 grayscale document images across 16 document classes, derived from the IIT-CDIP collection; receipt is one class among many. It is a document image classification dataset with no word transcripts or OCR box labels, and thus is not suitable for supervised OCR recognition or receipt KIE. [Harley’s RVL-CDIP page and HF integration](https://www.cs.cmu.edu/~aharley/rvl-cdip); [Hugging Face dataset](https://huggingface.co/datasets/aharley/rvl_cdip)
- RVL-CDIP images can be obtained through the linked dataset resources/Hugging Face; access and source rights are not equivalent to an unrestricted license. The source collection is government-produced scanned documents, and reuse restrictions should be checked with original IIT-CDIP / dataset terms. Publicly accessible images do not by themselves establish commercial redistribution or model-training rights. [RVL-CDIP page](https://www.cs.cmu.edu/~aharley/rvl-cdip)
- A useful additional real-image English receipt KIE benchmark is SROIE itself; CORD remains the accessible image-plus-transcription dataset with the clearest permissive license among those reviewed. For invoice KIE at scale, DocILE is more directly relevant but gated and its labels/OCR do not constitute ground-truth full-page OCR transcripts. [CORD](https://github.com/clovaai/cord); [DocILE](https://docile.rossum.ai/)

### Inferences
- If the objective is training/evaluating OCR recognition on real receipt images, prioritize CORD and the labeled SROIE trainval portion; SROIE has a 400-image held-out test portion, but the mirrored materials do not establish public ground-truth availability for every test image.
- If the objective is KIE from real business invoices, DocILE is the most task-aligned benchmark here; CORD and SROIE offer smaller receipt-focused KIE alternatives. XFUND/EPHOIE support transfer/pretraining in forms/documents, not Czech receipt domain matching.
- Licenses and access apply independently to repository code and underlying image data. In particular, SROIE mirror MIT, DocILE tool MIT, or XFUND project code license should not be construed to grant broader image rights beyond explicit dataset terms.

### Gaps
- Official SROIE challenge page was not retrievable during this pass; exact official dataset terms, test-set annotation access, and any challenge registration steps remain to be verified with the organizers. The participant mirror's Google Drive link works as a published pointer, but is not an authoritative license statement.
- DocILE landing page does not state a simple standard open data license or full language distribution; request and read the current access agreement before production/commercial use.
- RVL-CDIP/IIT-CDIP exact current access procedure and redistribution license were not reliably established from the current university page; treat access and reuse rights as unresolved.
- No particular community Kaggle/Hugging Face upload is recommended as a rights-cleared source: community copies frequently omit provenance/license and may be reshared from restricted originals. Verify uploader provenance and original terms before use.

## What are the exact download routes, access requirements and legal cautions?

### Takeaway
CORD v2 is the clearest low-friction download, XFUND is a public release with noncommercial share-alike restrictions, and EPHOIE/DocILE require formal access workflows. SROIE has working published mirrors but unclear dataset-specific rights; RVL-CDIP should be used as classification-only data and its source terms checked.

### Cited Findings
- CORD: choose v2 on Hugging Face (1,000 examples; 800/100/100 split) or v0 sample Drive folders from the project README; license stated by project is CC BY 4.0. [CORD README](https://github.com/clovaai/cord); [CORD v2 dataset card](https://huggingface.co/datasets/naver-clova-ix/cord-v2)
- SROIE: the participant repository's README links Google Drive and Baidu Netdisk copies of the 1,000-image dataset; repository itself also contains a corrected data folder. The MIT text displayed is for the repository contribution; it does not clearly grant rights in challenge source scans. [SROIE README](https://github.com/zzzDavid/ICDAR-2019-SROIE)
- EPHOIE: download the form, secure institutional endorsement and qualifying publications, submit in the SCUT portal, and after approval use emailed link/password; noncommercial research only absent a separately obtained commercial license. [EPHOIE README](https://github.com/HCIILAB/EPHOIE)
- XFUND: download the v1.0 GitHub release; project terms state CC BY-NC-SA 4.0. [XFUND README](https://github.com/doc-analysis/XFUND)
- DocILE: submit the Google Form, obtain token, use `download_dataset.sh TOKEN SPLIT DEST --unzip`; access supports annotated-trainval, test, synthetic and unlabeled packages. [DocILE site](https://docile.rossum.ai/); [DocILE repository](https://github.com/rossumai/docile)
- RVL-CDIP: owner page links RVL-CDIP assets and its Hugging Face integration. It is a 400k image, 16-class classification corpus, without OCR labels. [RVL-CDIP page](https://www.cs.cmu.edu/~aharley/rvl-cdip)

### Inferences
- Rights-cleared commercial OCR training is not established by download availability alone. CORD's explicit CC BY 4.0 is comparatively clear; EPHOIE prohibits commercial use absent license; XFUND prohibits commercial use under NC-SA; SROIE/DocILE/RVL require checking source-specific terms before commercial deployment or redistribution.
- For a Czech receipt project, these datasets are best used as OCR/KIE method benchmarks or pretraining resources, not as Czech-language representative evaluation sets; none of the named datasets is Czech.

### Gaps
- The request portal's exact legal terms for current DocILE access were not available on the landing page itself; inspect terms delivered with token or contact organizers.
- A dataset-specific license statement for SROIE images and current RVL-CDIP/IIT-CDIP redistribution permissions was not confirmed.

## Practical suitability summary: OCR recognition versus KIE

### Takeaway
CORD and SROIE have direct text transcription supervision and are the best fits for receipt OCR recognition. CORD/SROIE/DocILE are relevant to receipt or invoice KIE; XFUND and EPHOIE are form/education document understanding resources, and RVL-CDIP is only classification data.

### Cited Findings
- CORD explicitly supplies receipt images, OCR text boxes/transcripts, semantic labels, and hierarchical receipt parse. [CORD README](https://github.com/clovaai/cord)
- SROIE explicitly defines OCR localization/recognition and KIE tasks and documents both bbox transcript text files and key-field JSON. [SROIE README](https://github.com/zzzDavid/ICDAR-2019-SROIE)
- EPHOIE supplies all-text boxes/content and entity key-value pairs for Chinese exam papers. [EPHOIE README](https://github.com/HCIILAB/EPHOIE)
- XFUND is a human-labeled multilingual form understanding dataset focused on K/V forms, SER and relation extraction. [XFUND README](https://github.com/doc-analysis/XFUND)
- DocILE has KILE/LIR annotations and precomputed OCR predictions rather than complete human ground-truth OCR transcripts. [DocILE repository](https://github.com/rossumai/docile)
- RVL-CDIP classifies document images into 16 types and supplies no OCR/KIE ground truth. [RVL-CDIP page](https://www.cs.cmu.edu/~aharley/rvl-cdip)

### Inferences
- Direct OCR recognition benchmarking: CORD strongest practical balance of image transcription labels and stated license; SROIE useful, subject to dataset rights/test annotations.
- Receipt KIE: CORD and SROIE provide receipt-domain fields; DocILE scales to invoices and line items but is gated and should not be mistaken for OCR ground truth.
- Cross-lingual/form KIE transfer: XFUND; handwritten/printed Chinese document OCR/VIE: EPHOIE, under its research access terms.
- RVL-CDIP can support document-type classification experiments only, not OCR model fine-tuning with supervised text labels.

### Gaps
- This scan did not audit every Kaggle, Roboflow, or Hugging Face community receipt collection. Such copies need individual provenance, image count, annotation-schema, deduplication and licensing checks before use; no general license can be assigned to “community data.”

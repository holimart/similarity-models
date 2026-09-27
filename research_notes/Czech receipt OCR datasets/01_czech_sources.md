# Czech Receipt and Invoice OCR Datasets

## Public Czech-specific datasets with receipt/invoice images and OCR annotations

### Takeaway
The searches and direct catalog checks made for these notes did not verify a publicly downloadable Czech-specific receipts/účtenky or invoice corpus that combines actual images with OCR transcriptions. Search results include Czech receipt-processing software repositories, but these are applications rather than evidence of released annotated datasets. Treat this as a bounded negative finding, not proof that no private, access-controlled, or differently named academic corpus exists.

### Cited Findings
- A direct Hugging Face Hub API search for datasets matching “czech receipt” returned an empty list; a separate “uctenka” search also returned an empty list. [Hugging Face dataset search: czech receipt](https://huggingface.co/api/datasets?search=czech%20receipt); [Hugging Face dataset search: uctenka](https://huggingface.co/api/datasets?search=uctenka)
- A direct GitHub repository search for “czech receipt OCR dataset” returned zero repositories. [GitHub repository search](https://api.github.com/search/repositories?q=czech+receipt+OCR+dataset)
- GitHub search for “uctenka OCR” returned two repositories: `aykoooo/uctenka`, described as a receipt ingestion/OCR parsing/spending visualization application, and `kubiq/uctenkomat`, described as a Czech-store-receipt photo ingestion application using a vision API. Neither search result identifies a dataset release, corpus size, or transcriptions. [GitHub search results](https://api.github.com/search/repositories?q=uctenka+OCR); [aykoooo/uctenka](https://github.com/aykoooo/uctenka); [kubiq/uctenkomat](https://github.com/kubiq/uctenkomat)
- GitHub repository searches for Czech invoices and invoice dataset/OCR returned zero repositories in the API at the time checked. [Czech invoice dataset/OCR search](https://api.github.com/search/repositories?q=Czech+invoice+dataset+OCR+images); [Czech-language invoices search](https://api.github.com/search/repositories?q=%C4%8Desk%C3%A9+faktury+dataset+OCR)
- `kubiq/uctenkomat` has a public MIT license for the software repository; that is not a license for any receipt photos or dataset, and the repository search result does not establish that a dataset is included. [Repository metadata](https://api.github.com/repos/kubiq/uctenkomat)
- `aykoooo/uctenka` has no repository license listed in the GitHub API metadata. Its description characterizes it as an application, not a dataset. [Repository metadata](https://api.github.com/repos/aykoooo/uctenka)

### Inferences
- Publicly indexed Hub/GitHub records found here are insufficient to claim availability of Czech receipt/invoice image-plus-transcription training data; the two Czech receipt projects should not be cited as dataset sources without independent evidence of bundled or linked sample corpora.
- Repository/software licensing and dataset/image licensing must be checked separately before any reuse.

### Gaps
- A complete census of Czech university repositories, theses, national research infrastructure, and competition archives could not be established from search endpoints available in this research pass.
- The Google search endpoint returned a JavaScript/consent response instead of usable result listings, limiting broad web discovery. Queries included Czech receipt OCR datasets, Czech invoices, Czech OCR competition data, and Hugging Face/Kaggle/GitHub scopes.
- No dataset-level download was attempted, in keeping with the instruction not to download data. Thus no file-level validation of images, transcription contents, corpus size, or format was possible.
- No verified Czech OCR competition dataset was located. An organizer/competition landing page or archived competition terms would be needed to establish whether data exists, whether image assets remain accessible, and whether redistribution/reuse is permitted.

## Candidate records and whether they qualify

### Takeaway
The only Czech-specific public records surfaced with “receipt/účtenka” relevance were software repositories. They do not meet the requested image-plus-OCR-transcription dataset criteria based on the available metadata.

### Cited Findings
- `kubiq/uctenkomat` describes taking a photograph of a Czech store receipt and filing it as an expense, with on-device app behavior and an OpenAI vision backend. Its repository metadata reports MIT software licensing; metadata contains no dataset size, annotation scheme, language coverage statement for a corpus, or dataset license. [Project page](https://github.com/kubiq/uctenkomat); [GitHub API metadata](https://api.github.com/repos/kubiq/uctenkomat)
- `aykoooo/uctenka` describes an n8n receipt-ingestion/OCR-parsing project and is publicly visible on GitHub; metadata provides no dataset release, image count, OCR label format, or license. [Project page](https://github.com/aykoooo/uctenka); [GitHub API metadata](https://api.github.com/repos/aykoooo/uctenka)
- The GitHub search endpoints used expose repository metadata and returned no qualifying Czech invoice/receipt dataset repositories for the specific queries; search results are not a universal index of GitHub content. [Receipt query](https://api.github.com/search/repositories?q=czech+receipt+OCR+dataset); [invoice query](https://api.github.com/search/repositories?q=Czech+invoice+dataset+OCR+images)

### Inferences
- These projects demonstrate Czech receipt-processing use cases, not availability of their user-submitted receipt images or annotations. App functionality should not be confused with an openly licensed benchmark.
- No reliable values can be reported for dataset size, image modality (phone photos versus scans), annotation granularity, or data terms for a qualifying Czech-specific corpus because no qualifying corpus was verified.

### Gaps
- Repository contents were not downloaded or examined file-by-file; direct project pages and metadata are the basis for classification.
- Kaggle results were not verifiable through the available search endpoint; no claim that Kaggle has zero matching datasets is warranted.
- Czech-language academic publications may refer to internal/private data or name the corpus without indexing “Czech receipt” in English. Those cases remain unresolved.

## Research scope and interpretation

### Takeaway
A usable candidate needs evidence for all three elements: Czech or Czech-relevant receipts/invoices, actual image files (photographs or scans), and paired OCR text or structured labels, plus a verifiable access route and applicable terms. No source checked here demonstrated all of them together.

### Cited Findings
- Hugging Face’s public datasets API search returned no results for the exact Czech-receipt and Czech-language term checks made during this research. [API: czech receipt](https://huggingface.co/api/datasets?search=czech%20receipt); [API: uctenka](https://huggingface.co/api/datasets?search=uctenka); [API: invoice Czech](https://huggingface.co/api/datasets?search=invoice%20Czech)
- GitHub’s repository search returned no matching records for the dataset-oriented Czech receipt and invoice phrases checked; the distinct “uctenka OCR” result set contained software projects. [Dataset-oriented query](https://api.github.com/search/repositories?q=czech+receipt+OCR+dataset); [Invoice query](https://api.github.com/search/repositories?q=Czech+invoice+dataset+OCR+images); [Uctenka OCR query](https://api.github.com/search/repositories?q=uctenka+OCR)

### Inferences
- International receipt datasets that do not document Czech-language content should not be counted as Czech data merely because OCR text or receipt images are available.
- Any claimed competition corpus needs separate checks for competition access restrictions, participant-only access, retention of hosted files, and redistribution rights; none can be inferred from a competition name alone.

### Gaps
- This note does not assess general multilingual receipt datasets as substitutes because Czech language coverage and Czech receipt provenance were not established by the queried sources.
- Dataset pages may use Czech terms such as “doklad,” “faktura,” “pokladní doklad,” or institution-specific names not captured by the API phrase checks. Broader institution-level and Czech scholarly catalogue searches remain necessary for a definitive inventory.

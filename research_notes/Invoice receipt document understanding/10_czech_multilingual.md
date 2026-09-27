# Czech and multilingual invoice/receipt extraction

## Language coverage and evidence for leading systems/models

### Takeaway
Published language checklists are evidence of whether a text recognizer claims support, not of Czech receipt extraction quality. Czech-specific end-to-end accuracy evidence is sparse in the sources reviewed; evaluate recognition of Czech diacritics and field extraction on local receipts separately.

### Cited Findings
- AWS Textract lists text detection support for English, French, German, Italian, Portuguese and Spanish; Czech is absent. Its character inventory includes several accented Latin characters (such as á/é/í/ó/ú/ü, ñ, ç, and umlauts), but it omits Czech-specific characters such as č, ď, ě, ň, ř, š, ť, ů, ž. The character list is therefore especially relevant to Czech, and does not support assuming that generic Central European language coverage exists. [AWS Textract document limits](https://docs.aws.amazon.com/textract/latest/dg/limits-document.html)
- Textract documents AnalyzeExpense for invoices and receipts, but its language limitations apply to its supported text detection; it is not a Czech-specialized receipt model. [What is Amazon Textract?](https://docs.aws.amazon.com/textract/latest/dg/what-is.html); [language and character limits](https://docs.aws.amazon.com/textract/latest/dg/limits-document.html)
- EasyOCR advertises 80+ languages and exposes language selection at OCR runtime. Its project documentation says a language needs a character set and dictionary, and notes languages sharing character sets are often compatible. This establishes configurable multilingual OCR availability, not Czech invoice field accuracy; its advertised scope and current language list should be checked against model/version before deployment. [EasyOCR repository](https://github.com/JaidedAI/EasyOCR)
- Google Document AI’s pretrained Invoice Parser extracts up to 46 generic invoice entities (including invoice number, supplier, invoice/tax amounts, invoice date and due date); the overview does not establish Czech language support or Czech accuracy. [Google Document AI pretrained overview](https://docs.cloud.google.com/document-ai/docs/pretrained-overview)
- EU eInvoicing is based on structured data exchange and the European Standard EN 16931, not OCR. For conforming machine-readable invoices, parsing the structured syntax is preferable to visual OCR, while scans and paper receipts still need recognition. [European Commission eInvoicing](https://ec.europa.eu/digital-building-blocks/sites/display/DIGITAL/eInvoicing)

### Inferences
- “Supports Latin” or “supports European languages” is insufficient evidence for Czech: a robust system must preserve the full Czech character repertoire, including carons and ring, through OCR, normalization, search, and export.
- Separate OCR quality from semantic extraction: the text engine may read a receipt accurately while an invoice parser fails on receipt-specific concepts (cashier, item lines, VAT groupings, total/paid/change) or unfamiliar Czech labels.
- Treat vendor language matrices as a procurement shortlist only. Benchmark Czech thermal-paper receipts, photographed crumpled/faded receipts, PDFs, and formal invoices with field-level exact match and confidence calibration.

### Gaps
- No directly comparable public benchmark or primary study was found in this research pass that reports Czech receipt/invoice field-level extraction metrics across commercial systems.
- Publicly accessible vendor material reviewed did not establish current Czech support/accuracy for Google Invoice Parser or a Czech-specific performance guarantee for EasyOCR. Verify against versioned language documentation and a local test corpus.

## Czech účtenky, OCR and local document characteristics

### Takeaway
Czech “účtenka” is a receipt, commonly a narrow thermal-paper document, while “faktura” is an invoice; the extraction target should reflect receipt-level commercial evidence as well as formal invoice fields. Czech diacritics and dense receipt typography make an explicit Czech OCR capability check essential.

### Cited Findings
- The Czech VAT Act (Act No. 235/2004 Coll.) is the national legal framework implementing relevant EU VAT rules; its current consolidated text is published in Czech. It provides context for Czech VAT terminology and requirements, but is not an OCR specification. [Czech VAT Act No. 235/2004 Coll.](https://www.zakonyprolidi.cz/cs/2004-235)
- Textract’s published character repertoire does not include several letters intrinsic to Czech orthography (č, ď, ě, ň, ř, š, ť, ů, ž); the documented text languages also exclude Czech. [AWS Textract document limits](https://docs.aws.amazon.com/textract/latest/dg/limits-document.html)
- EasyOCR’s maintainers describe language-specific character files and dictionaries as part of adding language support, with dictionary sizes typically around 30,000 entries or more. This highlights that character coverage alone and lexicon/language modeling are separate concerns. [EasyOCR language request guidance](https://github.com/JaidedAI/EasyOCR)
- Czech VAT identifiers are commonly presented with the country prefix “CZ” and a numeric identifier; official definitions and edge cases should be validated against the current Czech VAT legislation and tax administration guidance rather than inferred from OCR token shape. [Czech VAT Act](https://www.zakonyprolidi.cz/cs/2004-235)

### Inferences
- Keep OCR text in Unicode and never silently strip diacritics. A folded, accent-insensitive form can be generated as a secondary search key, but the canonical extracted value should preserve the source spelling.
- Include Czech item descriptions and merchant names in OCR evaluation: dictionary correction can improve ordinary prose but can also “correct” brand names, abbreviations, product codes, and tax labels incorrectly.
- For receipts, model layout and line-item association (quantity × unit price, discounts, VAT rate/base/tax, total, payment method) in addition to key-value pairs. Receipt line wrapping and columns may be ambiguous in narrow, low-resolution thermal prints.

### Gaps
- No authoritative Czech national public dataset of photographed účtenky with field-level ground truth was identified in the sources reviewed. Privacy and commercial sensitivity may limit open datasets.
- No official exhaustive taxonomy of Czech receipt layouts, thermal-printer failure modes, or standard receipt field labels was located. Collect representative documents with consent and expert annotation.
- The reviewed legal text is extensive; exact receipt/invoice mandatory-field distinctions depend on transaction type and statutory exceptions and should be checked with Czech tax counsel or the tax authority for production compliance.

## EU invoice formats and locale ambiguities (VAT, IBAN, dates, numbers)

### Takeaway
EU standardization improves structured e-invoice interoperability but does not make scanned documents visually uniform. Locale-aware parsing plus validation is necessary: Czech numeric formatting and European date conventions can be confused with other locales, while VAT IDs and IBANs require checksum/registry validation rather than OCR confidence alone.

### Cited Findings
- The European Commission defines eInvoicing as structured invoice data that can be automatically processed; it identifies EN 16931-1 semantic rules and the CEN syntax specifications as the EU standard framework. This is distinct from a PDF image of an invoice. [European Commission eInvoicing](https://ec.europa.eu/digital-building-blocks/sites/display/DIGITAL/eInvoicing)
- EU VAT Directive 2006/112/EC Article 226 specifies invoice particulars including issue date, sequential number, supplier and customer VAT identification numbers where applicable, transaction description/quantity, taxable amount, VAT rate and VAT amount. Applicability and exceptions depend on the transaction and national implementation. [Council Directive 2006/112/EC](https://eur-lex.europa.eu/eli/dir/2006/112/oj)
- Czech Act No. 235/2004 Coll. defines Czech VAT law and includes rules for converting foreign currency amounts, allowing specified Czech National Bank or European Central Bank exchange rates subject to the statutory conditions. [Czech VAT Act, §4(8)](https://www.zakonyprolidi.cz/cs/2004-235)
- The European Commission describes EN 16931 e-invoicing as a standard and provides code lists and validation artefacts, reinforcing that structured format validation can be deterministic rather than OCR-based. [European Commission eInvoicing](https://ec.europa.eu/digital-building-blocks/sites/display/DIGITAL/eInvoicing)

### Inferences
- Czech numeric conventions normally use comma as decimal separator and spacing (often a nonbreaking space) for digit grouping, while other EU locales may use period or comma differently. A string such as `1.234,56` should not be normalized without a document-country/locale hypothesis; preserve the raw token and record the chosen parse.
- Dates such as `03.04.2025` are day-month-year in Czech usage but can be interpreted month-day-year in US-centric systems. Infer locale from document language, issuer address, currency/VAT prefix and neighboring dates, then retain raw and normalized forms with ambiguity flags.
- Validate Czech VAT IDs using country-specific structure and, when appropriate, an authoritative VAT validation service such as VIES; format checks alone do not prove registration or transaction eligibility.
- Validate IBAN length/country structure and mod-97 checksum, and keep it distinct from domestic account-number notation and bank codes. OCR substitutions such as O/0, I/1 and misplaced spaces are common candidates for checksum-guided review, but checksums cannot prove that the account belongs to the named supplier.
- Prefer direct XML/UBL/CII or other EN 16931-conformant input when available; use OCR only for raster/PDF inputs and reconcile extracted totals, tax arithmetic, and VAT breakdowns as independent consistency checks.

### Gaps
- This research pass did not retrieve a reliable official Czech National Bank IBAN-format page or an authoritative locale specification for Czech date/number formatting. Implementations should verify Czech IBAN length/check digits against current SWIFT/ISO registry data and locale behavior against Unicode CLDR or equivalent primary data.
- EU VAT invoice rules have many exceptions (simplified invoices, reverse charge, exempt supplies, cross-border cases); the high-level Article 226 list is not a complete compliance checklist.
- This source set does not establish comparative numeric accuracy or Czech date/IBAN/VAT error rates for leading OCR/extraction vendors. Such claims require reproducible Czech-specific evaluation.

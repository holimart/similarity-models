# Non-receipt dataset scope note

Neither dataset is in scope for the receipt-field schema. Do not manually label their 8,746 TextZoom word crops or 350 XFUND forms as receipts; do not create receipt records for them.

- **TextZoom test export:** The official local metadata describes low-/high-resolution scene-text word crops and text labels, not receipts. It provides OCR/transcription text at word-crop level, but no receipt categories, totals or other amounts, tax, tip, currency, or person-assigned items. There is no receipt-level context for merchant, transaction purpose, or line items.
- **XFUND validation:** The official local metadata describes multilingual form-understanding data, not receipts. The source annotations contain OCR text and generic form/layout labels (`header`, `question`, `answer`, `other`); these do not encode receipt semantics. No receipt categories, totals or other amounts, tax, tip, currency, or person-assigned items are annotated. Merchant, transaction purpose, and receipt line-item fields are not applicable.

Accordingly, receipt-schema fields `merchant`, `purpose`, `total`, `taxes`/`tax_status`, `tip`, `service_charge`, and `line_items_status` are not applicable to these datasets. Neither source provides person-to-item assignments (and the schema explicitly treats allocation as a later UI action rather than an image field). OCR/transcription coverage alone does not make either corpus receipt data.

Scope checked against `data/textzoom/test/DATASET_INFO.md`, `data/xfund-val/DATASET_INFO.md`, and the available XFUND validation source annotations. Source datasets were not modified.

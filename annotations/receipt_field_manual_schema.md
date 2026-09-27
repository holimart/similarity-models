# Manual receipt-field annotation schema

These annotations are an additive local layer. Never overwrite CORD/SROIE source labels. Preserve receipt strings exactly as shown; keep uncertain or missing values explicit rather than guessing. These files may contain financial/merchant information and remain under `$DATASETS_ROOT/manual/receipt_annotations/`, outside version control.

One JSON object per receipt:

```json
{
  "dataset": "cord-v2 | sroie-mirror",
  "split": "validation | test | mirror_subset",
  "row_id": "dataset record id",
  "image": "workspace-relative path, e.g. source/sroie-mirror/img/001.jpg",
  "merchant": {"value": "visible merchant text or null", "status": "present | absent | unreadable", "evidence": "verbatim image text or null"},
  "purpose": {"category": "food_dining | groceries | fuel | transport | lodging | healthcare | office_supplies | utilities | entertainment | retail_other | unknown", "status": "clear | uncertain | unknown", "evidence": "verbatim visible text or null"},
  "total": {"amount_raw": "verbatim total payable amount or null", "currency_code": "ISO 4217 code or null", "currency_raw": "verbatim symbol/code or null", "status": "present | absent | unreadable | ambiguous", "evidence": "verbatim label/value text"},
  "taxes": [{"amount_raw": "verbatim tax amount", "rate_raw": "verbatim rate or null", "currency_raw": "visible symbol/code or null", "evidence": "verbatim label/value text"}],
  "tax_status": "present | absent | unreadable | ambiguous",
  "tip": {"amount_raw": "verbatim tip/gratuity or null", "currency_raw": "visible symbol/code or null", "status": "present | absent | unreadable | ambiguous", "evidence": "verbatim label/value text or null"},
  "service_charge": {"amount_raw": "verbatim service fee or null", "currency_raw": "visible symbol/code or null", "status": "present | absent | unreadable | ambiguous", "evidence": "verbatim label/value text or null"},
  "line_items_status": "visible_not_individually_annotated | not_present | unreadable",
  "confidence": "high | medium | low",
  "notes": "brief reason for uncertainty or special layout"
}
```

Interpret the target total as the final receipt/invoice amount due (normally inclusive of tax), not subtotal, tax alone, cash tendered, or change. Keep `tip` separate from `service_charge`. Do not infer a currency from a country alone; if there is no visible marker/code, set it to null and explain any contextual inference in `notes`. `purpose` describes the transaction category, not a payer/person assignment. Line-item person allocation is a later UI action, not a field to guess from the image. Image paths in the merged manifest are relative to `$DATASETS_ROOT`.

For CORD and SROIE, annotate the current downloaded images only. The OCR benchmark corpora TextZoom (word crops) and XFUND (forms) do not have receipt-level semantics; mark them out of scope rather than fabricating receipt labels. Review source dataset licenses separately; this local annotation layer must not be redistributed with source images absent clear rights.

"""Schema, prompt and scoring helpers for LLM receipt/invoice extraction.

The extraction contract is intentionally engine-neutral: the same JSON can be
produced from an image, an OCR transcript, or both.  It is also the payload the
mobile app would receive, so it aims to be useful without a second model call.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

PROMPT_VERSION = "receipt-extraction-v1"
SCHEMA_PATH = Path(__file__).with_name("receipt_extraction_schema.json")

# USD per 1,000,000 tokens.  OpenRouter reports the authoritative cost in the
# response; this table is only a fallback and for offline planning.
DEFAULT_PRICING: dict[str, dict[str, float]] = {
    "deepseek/deepseek-v4.1-flash": {"input": 0.30, "output": 1.20, "cache_read": 0.006},
    "z-ai/glm-5.3-flash": {"input": 0.0107, "output": 0.1707, "cache_read": 0.0107},
}

COMPACT_SHAPE = """{
  "document_type": "receipt|invoice|credit_note|refund|other|unknown",
  "document": {"number": null, "date": "YYYY-MM-DD|null", "time": "HH:MM|null",
               "due_date": null, "payment_terms": null,
               "currency": "ISO4217|null", "country": "ISO3166-1|null", "language": "ISO639-1|null"},
  "merchant": {"name": null, "legal_name": null, "address": null, "phone": null,
               "email": null, "website": null,
               "tax_ids": [{"type": null, "value": null}],
               "store_id": null, "cashier": null, "table": null},
  "customer": {"name": null, "address": null, "tax_id": null, "account_id": null},
  "amounts": {"subtotal": null, "discount_total": null, "tax_total": null,
              "tip": null, "service_charge": null, "delivery_fee": null,
              "shipping": null, "rounding": null, "total": null,
              "amount_paid": null, "change": null, "amount_due": null,
              "prior_balance": null,
              "taxes": [{"label": null, "rate_percent": null, "base": null,
                         "amount": null, "jurisdiction": null, "included_in_price": null}]},
  "payment": {"method": null, "card_brand": null, "card_last4": null,
              "transaction_id": null, "auth_code": null},
  "line_items": [{"description": null, "sku": null, "quantity": null, "unit": null,
                  "unit_price": null, "gross_amount": null, "discount": null,
                  "net_amount": null, "tax_rate_percent": null,
                  "category": null, "notes": null}],
  "classification": {"category": "food_dining|groceries|fuel|transport|lodging|healthcare|office_supplies|utilities|entertainment|travel|retail|services|other|unknown",
                     "subcategory": null, "purpose_summary": null,
                     "is_business_expense": null, "tags": []},
  "quality": {"legibility": "high|medium|low|null", "handwritten": null, "blur": null,
              "glare": null, "cropped": null, "arithmetic_ok": null,
              "duplicate_suspected": null, "confidence": null, "warnings": []}
}"""

AUDIT_SHAPE = """Add an "evidence" object with verbatim source strings for
"merchant", "date", "total", "tax" and "tip". Do not quote invented text."""

RULES = """Rules:
- Return exactly one JSON object and no markdown or commentary.
- Read visible text; never guess. Missing or unreadable values must be null.
- Monetary values are decimal numbers in major currency units, using a dot as
  decimal separator (e.g. "1 234,56 Kč" -> 1234.56). Do not include symbols.
- total is the final amount paid or due, including tax, tip, service charge,
  delivery/shipping, and after discounts. Never use subtotal, tax alone, cash
  tendered, or change as total.
- Keep tip separate from service_charge and from tax_total. US sales tax and EU
  VAT both go in amounts.taxes and amounts.tax_total.
- Use the printed order for line_items. Keep modifiers with their parent item.
  If the document shows a subtotal but no itemised lines, return an empty list.
- document.currency only when a currency symbol/code or unambiguous locale
  evidence is visible. Do not infer currency from the merchant name alone.
- classification.category must be from the fixed list. purpose_summary is a
  short English phrase answering what was bought and why.
- quality.arithmetic_ok: check subtotal + tax + tip + fees - discounts = total
  within normal rounding. quality.confidence is 0..1 for the extraction overall.
"""


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def build_prompt(
    input_mode: str,
    ocr_text: str | None = None,
    audit: bool = False,
    locale_hint: str | None = None,
) -> str:
    """Build a compact extraction prompt for image, OCR, or both inputs."""
    if input_mode not in {"image", "ocr", "both"}:
        raise ValueError("input_mode must be image, ocr or both")
    if input_mode in {"ocr", "both"} and not (ocr_text or "").strip():
        raise ValueError(f"input_mode={input_mode!r} requires OCR text")
    if input_mode == "image":
        source = "The receipt or invoice image is attached."
    elif input_mode == "ocr":
        source = (
            "Only an OCR transcript is available. It may contain recognition errors; "
            "use null rather than inventing a value that is not in the transcript."
        )
    else:
        source = (
            "The image is attached and an OCR transcript is provided. Use the image "
            "to resolve OCR errors; the transcript is a reading aid, not a second source of truth."
        )

    parts = [
        "You are a receipt and invoice extraction engine for an expense app.",
        source,
        RULES,
        "Return this JSON shape (all keys present; fill unknown values with null):",
        COMPACT_SHAPE,
    ]
    if audit:
        parts.append(AUDIT_SHAPE)
    if locale_hint:
        parts.append(f"Locale hint from the app (verify against the document): {locale_hint}")
    if input_mode in {"ocr", "both"}:
        parts.append("OCR TRANSCRIPT START\n" + ocr_text.strip() + "\nOCR TRANSCRIPT END")
    return "\n\n".join(parts)


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a model response that should be one JSON object.

    Tolerates markdown fences and leading/trailing prose, but rejects arrays and
    scalar responses so a schema-shaped object is always required.
    """
    if not text or not text.strip():
        raise ValueError("empty model response")
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("response does not contain a JSON object")
        value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("response JSON is not an object")
    return value


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace("\u00a0", "").replace(" ", "")
        if not text:
            return None
        text = re.sub(r"[^0-9,.\-]", "", text)
        if "," in text and "." in text:
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        elif "," in text:
            text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip().casefold()
    return text or None


def _get(extraction: dict[str, Any], path: str) -> Any:
    current: Any = extraction
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


CRITICAL_FIELDS: tuple[tuple[str, str], ...] = (
    ("document_type", "text"),
    ("document.date", "text"),
    ("document.currency", "text"),
    ("merchant.name", "text"),
    ("amounts.total", "number"),
    ("amounts.tax_total", "number"),
    ("amounts.tip", "number"),
    ("amounts.service_charge", "number"),
    ("classification.category", "text"),
    ("classification.purpose_summary", "text"),
)


def critical_values(extraction: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for path, kind in CRITICAL_FIELDS:
        raw = _get(extraction, path)
        values[path] = _number(raw) if kind == "number" else _text(raw)
    return values


def _same(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    if isinstance(left, float) or isinstance(right, float):
        return abs(float(left) - float(right)) <= 0.011
    return left == right


def build_consensus(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group extraction rows by image and flag critical-field disagreements.

    This is not a truth oracle.  It produces a review queue: fields on which all
    successful engines agree can be promoted; disagreements stay explicit.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("error") or not row.get("json_valid"):
            continue
        groups.setdefault(str(row.get("id") or row.get("image")), []).append(row)

    output: list[dict[str, Any]] = []
    for image_id, group in sorted(groups.items()):
        values_by_path: dict[str, list[Any]] = {path: [] for path, _ in CRITICAL_FIELDS}
        for row in group:
            values = critical_values(row.get("extraction") or {})
            for path, value in values.items():
                if value is not None:
                    values_by_path[path].append(value)
        fields: dict[str, Any] = {}
        needs_review = False
        for path, values in values_by_path.items():
            distinct: list[Any] = []
            for value in values:
                if not any(_same(value, seen) for seen in distinct):
                    distinct.append(value)
            agree = len(distinct) <= 1
            needs_review = needs_review or not agree
            fields[path] = {
                "agree": agree,
                "values": values,
                "chosen": values[0] if agree and values else None,
            }
        line_counts = [len((row.get("extraction") or {}).get("line_items") or []) for row in group]
        line_count_agree = len(set(line_counts)) <= 1
        needs_review = needs_review or not line_count_agree
        output.append(
            {
                "id": image_id,
                "image": group[0].get("image"),
                "models": sorted({str(row.get("model")) for row in group}),
                "modes": sorted({str(row.get("input_mode")) for row in group}),
                "n_extractions": len(group),
                "needs_review": needs_review,
                "fields": fields,
                "line_item_count": {
                    "agree": line_count_agree,
                    "values": line_counts,
                    "chosen": line_counts[0] if line_count_agree and line_counts else None,
                },
            }
        )
    return output


def cost_from_usage(usage: dict[str, Any], pricing: dict[str, float] | None) -> float:
    """Fallback cost calculation when the provider does not report a cost."""
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    cached = int(usage.get("cached_tokens") or 0)
    if not pricing:
        return 0.0
    uncached = max(0, prompt - cached)
    input_rate = float(pricing.get("input", 0.0)) / 1_000_000
    cache_rate = float(pricing.get("cache_read", pricing.get("input", 0.0))) / 1_000_000
    output_rate = float(pricing.get("output", 0.0)) / 1_000_000
    return uncached * input_rate + cached * cache_rate + completion * output_rate


def normalize_usage(raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = raw or {}
    details = raw.get("completion_tokens_details") or {}
    prompt_details = raw.get("prompt_tokens_details") or {}
    return {
        "prompt_tokens": int(raw.get("prompt_tokens") or 0),
        "completion_tokens": int(raw.get("completion_tokens") or 0),
        "total_tokens": int(raw.get("total_tokens") or 0),
        "reasoning_tokens": int(details.get("reasoning_tokens") or 0),
        "cached_tokens": int(prompt_details.get("cached_tokens") or 0),
        "image_tokens": int(details.get("image_tokens") or 0),
        "cost_usd": float(raw.get("cost") or 0.0),
    }

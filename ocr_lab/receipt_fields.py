"""Receipt-oriented fields layered over normalized OCR detections."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

from PIL import Image

from .amounts import AmountCandidate, amount_methods, normalize_amount, ranker_score


@dataclass
class LineItemAssignment:
    """Future UI-ready shape; no automatic line-item parsing is done yet."""

    description: str | None = None
    quantity: str | None = None
    amount_raw: str | None = None
    assigned_person_id: str | None = None
    assignment_status: str = "unassigned"


PURPOSE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("food_dining", ("restaurant", "restaurace", "cafe", "kavarna", "bistro", "coffee", "starbucks", "mcdonald", "kfc", "morganfield", "meal", "food", "pizza", "nasi", "ayam", "mie", "teh", "jidlo", "obcerstveni")),
    ("groceries", ("supermarket", "grocery", "potraviny", "market", "tesco", "aldi", "lidl", "carrefour")),
    ("fuel", ("fuel", "petrol", "gas station", "diesel", "unleaded", "benzin", "palivo")),
    ("transport", ("taxi", "uber", "bolt", "bus", "train", "metro", "tramvaj", "vlak", "jizdne", "parking")),
    ("lodging", ("hotel", "hostel", "lodging", "room charge")),
    ("healthcare", ("pharmacy", "lekarna", "drugstore", "clinic", "medical", "hospital")),
    ("office_supplies", ("stationery", "office supply", "printer", "toner", "paper")),
    ("utilities", ("electricity", "water bill", "internet", "utility", "gas bill")),
    ("entertainment", ("cinema", "movie", "theatre", "concert", "ticket")),
)

CURRENCY_MARKERS = {
    "czk": ("CZK", "CZK"), "kč": ("CZK", "Kč"), "kc": ("CZK", "Kc"),
    "eur": ("EUR", "EUR"), "€": ("EUR", "€"),
    "usd": ("USD", "USD"), "gbp": ("GBP", "GBP"), "£": ("GBP", "£"),
    "pln": ("PLN", "PLN"), "huf": ("HUF", "HUF"),
    "rm": ("MYR", "RM"), "myr": ("MYR", "MYR"),
    "rp": ("IDR", "Rp"), "idr": ("IDR", "IDR"),
}


def _center_y(record: dict[str, Any]) -> float:
    polygon = record.get("polygon") or []
    return sum(float(point[1]) for point in polygon) / len(polygon) if polygon else 0.0


def _fold_for_search(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(char))


def _labelled_amount(
    records: list[dict[str, Any]],
    candidates: list[AmountCandidate],
    keywords: tuple[str, ...],
    dataset: str,
    image_height: int,
) -> dict[str, Any] | None:
    tolerance = max(20.0, image_height * 0.045)
    matches: list[tuple[float, float, dict[str, Any]]] = []
    for record in records:
        text = str(record.get("text", ""))
        lower = text.casefold()
        if not any(re.search(pattern, lower) for pattern in keywords):
            continue
        if any(x in lower for x in ("subtotal", "sub total")) and "total" in keywords:
            continue
        anchor_y = _center_y(record)
        rate = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
        nearby = [
            candidate for candidate in candidates
            if abs(candidate.y - anchor_y) <= tolerance
            and not any(
                match.group(0) == candidate.raw and re.match(r"\s*%", text[match.end():])
                for match in re.finditer(re.escape(candidate.raw), text)
            )
        ]
        if not nearby:
            continue
        candidate = min(nearby, key=lambda c: (abs(c.y - anchor_y), -c.confidence))
        matches.append((abs(candidate.y - anchor_y), anchor_y, {
            "amount_raw": candidate.raw,
            "normalized_value": candidate.normalized_value,
            "rate_percent_raw": rate.group(1) if rate else None,
            "label_evidence": text,
            "amount_evidence": candidate.source_text,
            "confidence": candidate.confidence,
        }))
    if not matches:
        return None
    return min(matches, key=lambda item: (item[0], -item[1]))[2]


def infer_currency(records: list[dict[str, Any]]) -> dict[str, Any]:
    text = " \n ".join(str(record.get("text", "")) for record in records)
    lower = "".join(char for char in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(char))
    found = []
    for marker, (code, raw) in CURRENCY_MARKERS.items():
        pattern = re.escape(marker) if len(marker) == 1 else rf"\b{re.escape(marker)}\b"
        if re.search(pattern, lower):
            found.append((code, raw))
    distinct = sorted({code for code, _ in found})
    if len(distinct) == 1:
        code = distinct[0]
        marker = next(raw for found_code, raw in found if found_code == code)
        return {"code": code, "raw_marker": marker, "status": "inferred_from_receipt_text", "evidence": marker}
    if len(distinct) > 1:
        return {"code": None, "raw_marker": None, "status": "ambiguous", "evidence": sorted({raw for _, raw in found})}
    if "$" in text:
        return {"code": None, "raw_marker": "$", "status": "ambiguous_symbol_only", "evidence": "$"}
    return {"code": None, "raw_marker": None, "status": "not_found", "evidence": None}


def infer_purpose(records: list[dict[str, Any]], image_height: int) -> dict[str, Any]:
    text = " \n ".join(str(record.get("text", "")) for record in records)
    lower = _fold_for_search(text)
    for category, terms in PURPOSE_RULES:
        for term in terms:
            folded_term = _fold_for_search(term)
            if folded_term in lower:
                evidence = next(str(record.get("text", "")) for record in records if folded_term in _fold_for_search(str(record.get("text", ""))))
                return {"category": category, "summary": evidence, "method": "keyword_rule", "status": "inferred"}
    return {"category": "unknown", "summary": None, "method": "keyword_rule", "status": "not_found"}


def infer_merchant(records: list[dict[str, Any]], image_height: int) -> dict[str, Any]:
    candidates = []
    ignored = ("receipt", "invoice", "tax invoice", "guest check", "total", "date", "cashier", "www.")
    for record in records:
        text = str(record.get("text", "")).strip()
        y = _center_y(record)
        if not text or y > image_height * 0.28 or not re.search(r"[A-Za-zÀ-ž]", text):
            continue
        if any(word in text.casefold() for word in ignored):
            continue
        if sum(char.isdigit() for char in text) > len(text) * 0.45:
            continue
        candidates.append((y, -float(record.get("confidence") or 0.0), text, record.get("confidence")))
    if not candidates:
        return {"name": None, "status": "not_found", "evidence": None}
    _, _, name, confidence = min(candidates)
    return {"name": name, "status": "ocr_top_header_candidate", "evidence": name, "confidence": confidence}


def extract_receipt_fields(
    records: list[dict[str, Any]],
    image_height: int,
    dataset: str,
    mode: str = "naive",
    ranker_weights: list[float] | None = None,
) -> dict[str, Any]:
    """Return consistent receipt fields using rule or CORD-trained total selection."""
    if mode not in {"naive", "tuned"}:
        raise ValueError("mode must be naive or tuned")
    candidates, heuristics, features = amount_methods(records, dataset, image_height)
    if mode == "tuned":
        if not ranker_weights:
            raise ValueError("tuned mode requires candidate-ranker weights trained with scripts/evaluate_total_amount.py")
        total_candidate = max(zip(candidates, features), key=lambda pair: ranker_score(ranker_weights, pair[1]))[0] if candidates else None
        total_method = "cord_trained_candidate_ranker"
    else:
        total_candidate = heuristics["keyword_nearby"]
        total_method = "keyword_nearby_rule"

    currency = infer_currency(records)
    total = None if total_candidate is None else {
        "amount_raw": total_candidate.raw,
        "amount_normalized": normalize_amount(total_candidate.raw, dataset),
        "currency_code": currency["code"],
        "currency_status": currency["status"],
        "candidate_confidence": total_candidate.confidence,
        "evidence": total_candidate.source_text,
        "method": total_method,
    }
    taxes = []
    tax_field = _labelled_amount(records, candidates, (r"\btax\b", r"\bvat\b", r"\bgst\b", r"\bdph\b", r"\bdaň\b", r"\bdan\b"), dataset, image_height)
    if tax_field:
        taxes.append(tax_field)
    tip = _labelled_amount(records, candidates, (r"\btip\b", r"\bgratuity\b", r"\bpropina\b", r"spropitn[eé]"), dataset, image_height)
    service_charge = _labelled_amount(records, candidates, (r"service charge", r"serv\. charge", r"service fee"), dataset, image_height)

    return {
        "schema_version": 1,
        "mode": mode,
        "merchant": infer_merchant(records, image_height),
        "purpose": infer_purpose(records, image_height),
        "total": total,
        "currency": currency,
        "taxes": taxes,
        "tip": tip,
        "service_charge": service_charge,
        "line_items": {
            "status": "not_extracted_yet",
            "items": [],
            "item_schema": asdict(LineItemAssignment()),
        },
        "amount_candidate_count": len(candidates),
    }

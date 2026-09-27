"""Receipt-total amount candidate extraction and field-level scoring."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

from PIL import Image


AMOUNT_RE = re.compile(r"(?<![A-Za-z0-9/])(?:\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,]\d{1,2})?(?![A-Za-z0-9/])")
NON_DIGIT_RE = re.compile(r"[^0-9,.-]+")


@dataclass(frozen=True)
class AmountCandidate:
    raw: str
    normalized_value: str
    x: float
    y: float
    confidence: float
    source_text: str


def normalize_amount(value: str, dataset: str) -> str:
    """Canonicalize a receipt amount without applying general OCR ASCII-folding.

    CORD amounts use Indonesian-style group punctuation inconsistently, so use
    their digit sequence. SROIE values are parsed as decimal currency units and
    compared as integer cents. Preserve raw predictions separately for review.
    """
    if dataset == "cord":
        digits = "".join(char for char in value if char.isdigit())
        return digits.lstrip("0") or ("0" if digits else "")
    cleaned = NON_DIGIT_RE.sub("", value)
    if not cleaned or not any(char.isdigit() for char in cleaned):
        return ""
    # SROIE is an English-language receipt benchmark using dot decimals and
    # optional comma grouping; a bare integer is interpreted as whole currency.
    cleaned = cleaned.replace(",", "")
    try:
        amount = Decimal(cleaned).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return ""
    return str(int(amount * 100))


def _center(record: dict[str, Any]) -> tuple[float, float]:
    polygon = record.get("polygon") or []
    if not polygon:
        return 0.0, 0.0
    return (
        sum(float(point[0]) for point in polygon) / len(polygon),
        sum(float(point[1]) for point in polygon) / len(polygon),
    )


def _anchor_weight(text: str) -> float:
    value = "".join(char for char in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(char))
    if re.search(r"\b(subtotal|sub total)\b", value):
        return 0.0
    if re.search(r"\b(grand total|amount due|amount payable|total due|total payable|total incl(?:usive)?|total amount|celkova castka|castka k uhrade|k uhrade)\b", value):
        return 9.0
    if re.search(r"\b(total|jumlah|celkem)\b", value):
        return 7.0
    if re.search(r"\bamount\b", value):
        return 3.0
    return 0.0


def amount_methods(records: list[dict[str, Any]], dataset: str, image_height: int) -> tuple[list[AmountCandidate], dict[str, AmountCandidate | None], list[list[float]]]:
    candidates = []
    anchors: list[tuple[float, float, float]] = []
    for record in records:
        text = str(record.get("text", ""))
        x, y = _center(record)
        weight = _anchor_weight(text)
        if weight:
            anchors.append((x, y, weight))
        for match in AMOUNT_RE.finditer(text):
            if re.match(r"\s*%", text[match.end():]):
                continue
            raw = match.group(0)
            digit_count = sum(char.isdigit() for char in raw)
            normalized = normalize_amount(raw, dataset)
            if digit_count < 2 or digit_count > 10 or not normalized:
                continue
            candidates.append(AmountCandidate(raw, normalized, x, y, float(record.get("confidence") or 0.0), text))

    tolerance = max(18.0, image_height * 0.035)
    def features(candidate: AmountCandidate) -> list[float]:
        anchors_nearby = [weight * math.exp(-abs(candidate.y - anchor_y) / tolerance) for _, anchor_y, weight in anchors]
        anchor_score = max(anchors_nearby, default=0.0)
        anchor_distance = min((abs(candidate.y - anchor_y) / max(1, image_height) for _, anchor_y, _ in anchors), default=1.0)
        own_anchor = _anchor_weight(candidate.source_text) / 9.0
        excluded_context = bool(re.search(r"\b(cash|change|subtotal|tax|vat|gst|discount|rounding|paid|received)\b", candidate.source_text.casefold()))
        magnitude = math.log1p(max(0, int(candidate.normalized_value))) / 20.0
        has_separator = float(any(char in candidate.raw for char in ".,"))
        return [
            1.0,
            anchor_score / 9.0,
            min(1.0, anchor_distance),
            min(1.0, max(0.0, candidate.y / max(1, image_height))),
            own_anchor,
            min(1.0, len(candidate.normalized_value) / 10.0),
            min(1.0, magnitude),
            candidate.confidence,
            has_separator,
            float(excluded_context),
        ]

    method_scores = {
        "keyword_nearby": lambda item: (
            max((weight * math.exp(-abs(item.y - anchor_y) / tolerance) for _, anchor_y, weight in anchors), default=0.0)
            + 0.5 * min(1.0, max(0.0, item.y / max(1, image_height)))
        ),
        "bottommost": lambda item: (item.y, item.confidence),
        "largest_amount": lambda item: (int(item.normalized_value), item.y),
    }
    methods: dict[str, AmountCandidate | None] = {
        name: max(candidates, key=score, default=None) for name, score in method_scores.items()
    }
    return candidates, methods, [features(candidate) for candidate in candidates]


def fit_linear_ranker(examples: Iterable[tuple[list[float], int, float]], epochs: int = 600, learning_rate: float = 0.15, l2: float = 0.001) -> list[float]:
    """Fit a compact weighted logistic candidate scorer using only stdlib math."""
    examples = list(examples)
    if not examples:
        raise ValueError("No labeled amount candidates available to train the ranker")
    weights = [0.0] * len(examples[0][0])
    total_weight = max(1e-9, sum(sample_weight for _, _, sample_weight in examples))
    for _ in range(epochs):
        gradient = [0.0] * len(weights)
        for vector, label, sample_weight in examples:
            logit = max(-30.0, min(30.0, sum(w * x for w, x in zip(weights, vector))))
            probability = 1.0 / (1.0 + math.exp(-logit))
            residual = (probability - label) * sample_weight / total_weight
            for index, feature in enumerate(vector):
                gradient[index] += residual * feature
        for index in range(1, len(weights)):
            gradient[index] += l2 * weights[index]
        for index in range(len(weights)):
            weights[index] -= learning_rate * gradient[index]
    return weights


def ranker_score(weights: list[float], features: list[float]) -> float:
    logit = max(-30.0, min(30.0, sum(w * x for w, x in zip(weights, features))))
    return 1.0 / (1.0 + math.exp(-logit))


def train_candidate_ranker(
    prediction_path: Path,
    dataset_root: Path,
    dataset: str,
    rows: list[dict[str, Any]],
    split: str = "validation",
) -> tuple[list[float], dict[str, int]]:
    """Train a candidate scorer from image-level total labels and OCR candidates.

    Documents are weighted equally; within each document, positive candidates
    and negatives each receive half the document's sample weight.
    """
    totals = sroie_totals(dataset_root) if dataset == "sroie" else {}
    image_by_key = (
        {int(row.get("row_id", -1)): row for row in rows}
        if dataset == "sroie"
        else {(str(row.get("split", "")), int(row.get("row_id", -1))): row for row in rows}
    )
    examples: list[tuple[list[float], int, float]] = []
    documents = no_positive = 0
    for prediction in (json.loads(line) for line in prediction_path.read_text(encoding="utf-8").splitlines() if line.strip()):
        if dataset == "cord" and prediction.get("split") != split:
            continue
        key = int(prediction.get("row_id", -1)) if dataset == "sroie" else (str(prediction.get("split", "")), int(prediction.get("row_id", -1)))
        manifest_row = image_by_key.get(key)
        if manifest_row is None:
            continue
        raw_target = totals.get(int(prediction["row_id"])) if dataset == "sroie" else cord_total(manifest_row)
        if raw_target is None:
            continue
        target = normalize_amount(raw_target, dataset)
        image_path = dataset_root / prediction["image"]
        with Image.open(image_path) as image:
            image_height = image.height
        candidates, _, feature_rows = amount_methods(prediction.get("text_instances", []), dataset, image_height)
        labels = [int(candidate.normalized_value == target) for candidate in candidates]
        positive_count, negative_count = sum(labels), len(labels) - sum(labels)
        if positive_count == 0 or negative_count == 0:
            no_positive += int(positive_count == 0)
            continue
        documents += 1
        for features, label in zip(feature_rows, labels):
            sample_weight = (0.5 / positive_count) if label else (0.5 / negative_count)
            examples.append((features, label, sample_weight))
    weights = fit_linear_ranker(examples)
    return weights, {"documents_used": documents, "documents_without_positive_candidate": no_positive, "labeled_candidates": len(examples)}


def cord_total(row: dict[str, Any]) -> str | None:
    try:
        ground_truth = json.loads(row["ground_truth"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
    value = ground_truth.get("gt_parse", {}).get("total", {}).get("total_price")
    return str(value) if value is not None and str(value).strip() else None


def sroie_totals(root: Path) -> dict[int, str]:
    values = {}
    for path in (root / "key").glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if item.get("total") is not None and str(item["total"]).strip():
            values[int(path.stem)] = str(item["total"]).strip()
    return values


def score_predictions(
    prediction_path: Path,
    dataset_root: Path,
    dataset: str,
    rows: list[dict[str, Any]],
    ranker_weights: list[float] | None = None,
    split: str | None = None,
) -> dict[str, Any]:
    targets = sroie_totals(dataset_root) if dataset == "sroie" else {}
    image_by_key = (
        {int(row.get("row_id", -1)): row for row in rows}
        if dataset == "sroie"
        else {(str(row.get("split", "")), int(row.get("row_id", -1))): row for row in rows}
    )
    method_names = ("oracle_any", "keyword_nearby", "bottommost", "largest_amount") + (("learned_ranker",) if ranker_weights else ())
    stats = {method: {"correct": 0, "selected": 0} for method in method_names}
    no_gt = no_candidates = 0
    details = []
    predictions = [json.loads(line) for line in prediction_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for prediction in predictions:
        if split is not None and prediction.get("split") != split:
            continue
        key = int(prediction.get("row_id", -1)) if dataset == "sroie" else (str(prediction.get("split", "")), int(prediction.get("row_id", -1)))
        manifest_row = image_by_key.get(key)
        if manifest_row is None:
            continue
        raw_target = targets.get(int(prediction["row_id"])) if dataset == "sroie" else cord_total(manifest_row)
        if raw_target is None:
            no_gt += 1
            continue
        target = normalize_amount(raw_target, dataset)
        image_path = dataset_root / prediction["image"]
        with Image.open(image_path) as image:
            image_height = image.height
        candidates, methods, feature_rows = amount_methods(prediction.get("text_instances", []), dataset, image_height)
        if ranker_weights and candidates:
            methods["learned_ranker"] = max(
                zip(candidates, feature_rows),
                key=lambda pair: ranker_score(ranker_weights, pair[1]),
            )[0]
        exact_any = any(candidate.normalized_value == target for candidate in candidates)
        stats["oracle_any"]["selected"] += 1
        stats["oracle_any"]["correct"] += int(exact_any)
        if not candidates:
            no_candidates += 1
        doc = {
            "image": prediction["image"],
            "ground_truth_raw": raw_target,
            "ground_truth_normalized": target,
            "candidate_count": len(candidates),
            "any_candidate_exact": exact_any,
        }
        for method, selected in methods.items():
            stats[method]["selected"] += int(selected is not None)
            correct = selected is not None and selected.normalized_value == target
            stats[method]["correct"] += int(correct)
            doc[method] = None if selected is None else {
                "raw": selected.raw,
                "normalized": selected.normalized_value,
                "source_text": selected.source_text,
                "confidence": selected.confidence,
                "x": selected.x,
                "y": selected.y,
                "correct": bool(correct),
            }
        details.append(doc)

    n = len(details)
    results = {}
    for method, values in stats.items():
        results[method] = {
            "exact_accuracy_over_labeled": values["correct"] / max(1, n),
            "exact_accuracy_when_selected": values["correct"] / max(1, values["selected"]),
            "selection_coverage": values["selected"] / max(1, n),
            "correct": values["correct"],
            "labeled_documents": n,
        }
    return {
        "dataset": dataset,
        "prediction_file": str(prediction_path),
        "labeled_documents_evaluated": n,
        "missing_ground_truth_documents": no_gt,
        "documents_with_no_amount_candidates": no_candidates,
        "normalization": "CORD=digits-only signature; SROIE=integer cents (comma grouping, decimal to 2 places)",
        "split_filter": split,
        "methods": results,
        "per_document": details,
    }

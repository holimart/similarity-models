"""Evaluate receipt-field baselines against the local manual annotation layer."""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocr_lab.amounts import amount_methods, normalize_amount, ranker_score
from ocr_lab.data_paths import manual_annotations_dir, source_dataset
from ocr_lab.receipt_fields import extract_receipt_fields


def _canonical_text(value: str | None) -> str:
    if not value:
        return ""
    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in folded if not unicodedata.combining(char) and char.isalnum())


def _percentage(correct: int, total: int) -> float | None:
    return correct / total if total else None


def _status_stats(gold: list[bool], predicted: list[bool]) -> dict[str, Any]:
    tp = sum(actual and guess for actual, guess in zip(gold, predicted))
    tn = sum(not actual and not guess for actual, guess in zip(gold, predicted))
    fp = sum(not actual and guess for actual, guess in zip(gold, predicted))
    fn = sum(actual and not guess for actual, guess in zip(gold, predicted))
    return {
        "labeled": len(gold),
        "accuracy": _percentage(tp + tn, len(gold)),
        "precision_present": _percentage(tp, tp + fp),
        "recall_present": _percentage(tp, tp + fn),
        "true_present": tp,
        "true_absent": tn,
        "false_present": fp,
        "missed_present": fn,
    }


def _numeric_stats(matches: int, selected: int, positive_labels: int) -> dict[str, Any]:
    return {
        "positive_labels": positive_labels,
        "selected": selected,
        "exact_matches": matches,
        "exact_accuracy_over_positive_labels": _percentage(matches, positive_labels),
        "selection_coverage_on_positive_labels": _percentage(selected, positive_labels),
        "exact_accuracy_when_selected": _percentage(matches, selected),
    }


def _identity(row: dict[str, Any], dataset_name: str) -> tuple[str, str, str]:
    split = "mirror_subset" if dataset_name == "sroie-mirror" else str(row.get("split", ""))
    return dataset_name, split, str(row["row_id"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("cord", "sroie"), required=True)
    parser.add_argument("--predictions", type=Path, required=True, help="Saved raw OCR prediction JSONL")
    parser.add_argument("--manual-labels", type=Path, default=manual_annotations_dir() / "receipt_field_annotations.jsonl")
    parser.add_argument("--ranker", type=Path, default=Path("runs/total-amount/cord-paddle-ranker.json"))
    parser.add_argument("--split", help="Split filter; defaults to test for CORD, all predictions for SROIE")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON report")
    args = parser.parse_args()

    dataset_name = "cord-v2" if args.dataset == "cord" else "sroie-mirror"
    root = source_dataset(dataset_name)
    split_filter = args.split or ("test" if args.dataset == "cord" else None)
    ranker_weights = json.loads(args.ranker.read_text(encoding="utf-8"))["weights"]
    labels = {
        _identity(row, dataset_name): row
        for row in (json.loads(line) for line in args.manual_labels.read_text(encoding="utf-8").splitlines() if line.strip())
        if row["dataset"] == dataset_name
    }

    totals = {
        method: {"matches": 0, "selected": 0, "positive_labels": 0}
        for method in ("keyword_nearby", "bottommost", "largest_amount", "learned_ranker")
    }
    auxiliary: dict[str, dict[str, Any]] = {
        field: {"positive_matches": 0, "positive_selected": 0, "positive_labels": 0, "status_gold": [], "status_predicted": []}
        for field in ("tax", "tip", "service_charge")
    }
    purpose = {"matches": 0, "selected": 0, "labeled": 0}
    currency = {"matches": 0, "selected": 0, "labeled": 0}
    merchant = {"matches": 0, "selected": 0, "labeled": 0}
    evaluated: list[dict[str, Any]] = []
    unmatched: list[tuple[str, str, str]] = []
    predictions = [json.loads(line) for line in args.predictions.read_text(encoding="utf-8").splitlines() if line.strip()]

    for prediction in predictions:
        key = _identity(prediction, dataset_name)
        if split_filter and key[1] != split_filter:
            continue
        label = labels.get(key)
        if label is None:
            unmatched.append(key)
            continue
        image_path = root / prediction["image"]
        with Image.open(image_path) as image:
            image_height = image.height
        records = prediction.get("text_instances", [])
        candidates, methods, feature_rows = amount_methods(records, args.dataset, image_height)
        if candidates:
            methods["learned_ranker"] = max(
                zip(candidates, feature_rows), key=lambda pair: ranker_score(ranker_weights, pair[1])
            )[0]

        total = label["total"]
        if total.get("status") == "present" and total.get("amount_raw"):
            target = normalize_amount(total["amount_raw"], args.dataset)
            for method, method_stats in totals.items():
                candidate = methods.get(method)
                method_stats["positive_labels"] += 1
                method_stats["selected"] += int(candidate is not None)
                method_stats["matches"] += int(candidate is not None and candidate.normalized_value == target)

        naive = extract_receipt_fields(records, image_height, args.dataset, mode="naive")
        tuned = extract_receipt_fields(records, image_height, args.dataset, mode="tuned", ranker_weights=ranker_weights)
        fields = {"naive": naive, "tuned": tuned}

        for field, manual_status, predicted_value in (
            ("tax", label["tax_status"], naive["taxes"][0] if naive["taxes"] else None),
            ("tip", label["tip"]["status"], naive["tip"]),
            ("service_charge", label["service_charge"]["status"], naive["service_charge"]),
        ):
            stats = auxiliary[field]
            if manual_status in {"present", "absent"}:
                stats["status_gold"].append(manual_status == "present")
                stats["status_predicted"].append(predicted_value is not None)
            if manual_status == "present":
                targets = label["taxes"] if field == "tax" else [label[field]]
                target_amounts = {
                    normalize_amount(item["amount_raw"], args.dataset)
                    for item in targets
                    if item.get("amount_raw")
                }
                stats["positive_labels"] += 1
                stats["positive_selected"] += int(predicted_value is not None)
                predicted_amount = predicted_value.get("normalized_value") if predicted_value else None
                stats["positive_matches"] += int(predicted_amount in target_amounts)

        purpose_label = label["purpose"]
        if purpose_label["status"] == "clear":
            purpose["labeled"] += 1
            guess = naive["purpose"]["category"]
            purpose["selected"] += int(guess != "unknown")
            purpose["matches"] += int(guess == purpose_label["category"])

        expected_currency = total.get("currency_code")
        if expected_currency:
            currency["labeled"] += 1
            guess = naive["currency"].get("code")
            currency["selected"] += int(guess is not None)
            currency["matches"] += int(guess == expected_currency)

        merchant_label = label["merchant"]
        if merchant_label["status"] == "present" and merchant_label.get("value"):
            merchant["labeled"] += 1
            guess = naive["merchant"].get("name")
            merchant["selected"] += int(guess is not None)
            merchant["matches"] += int(_canonical_text(guess) == _canonical_text(merchant_label["value"]))

        evaluated.append({"split": key[1], "row_id": key[2], "image": prediction["image"], "manual": label, "fields": fields})

    result: dict[str, Any] = {
        "dataset": dataset_name,
        "prediction_file": str(args.predictions),
        "manual_labels": str(args.manual_labels),
        "split_filter": split_filter,
        "documents_evaluated": len(evaluated),
        "unmatched_predictions": len(unmatched),
        "total_methods": {
            method: _numeric_stats(value["matches"], value["selected"], value["positive_labels"])
            for method, value in totals.items()
        },
        "tax": {
            "status": _status_stats(auxiliary["tax"]["status_gold"], auxiliary["tax"]["status_predicted"]),
            "amount": _numeric_stats(auxiliary["tax"]["positive_matches"], auxiliary["tax"]["positive_selected"], auxiliary["tax"]["positive_labels"]),
        },
        "tip": {
            "status": _status_stats(auxiliary["tip"]["status_gold"], auxiliary["tip"]["status_predicted"]),
            "amount": _numeric_stats(auxiliary["tip"]["positive_matches"], auxiliary["tip"]["positive_selected"], auxiliary["tip"]["positive_labels"]),
        },
        "service_charge": {
            "status": _status_stats(auxiliary["service_charge"]["status_gold"], auxiliary["service_charge"]["status_predicted"]),
            "amount": _numeric_stats(auxiliary["service_charge"]["positive_matches"], auxiliary["service_charge"]["positive_selected"], auxiliary["service_charge"]["positive_labels"]),
        },
        "purpose": _numeric_stats(purpose["matches"], purpose["selected"], purpose["labeled"]),
        "currency_code": _numeric_stats(currency["matches"], currency["selected"], currency["labeled"]),
        "merchant_exact": _numeric_stats(merchant["matches"], merchant["selected"], merchant["labeled"]),
        "note": "Auxiliary fields use the same OCR text in naive/tuned modes; only total selection changes. Purpose is scored on clear manual labels, currencies only where a visible ISO currency was annotated, and merchant strings by case/punctuation-insensitive exact match. Unreadable and ambiguous targets are excluded from field-value denominators.",
        "per_document": evaluated,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "per_document"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

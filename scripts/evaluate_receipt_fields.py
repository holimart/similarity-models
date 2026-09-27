"""Run the shared receipt field schema in naive or CORD-tuned mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocr_lab.amounts import cord_total, normalize_amount, sroie_totals
from ocr_lab.receipt_fields import extract_receipt_fields
from ocr_lab.data_paths import source_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("cord", "sroie"), required=True)
    parser.add_argument("--mode", choices=("naive", "tuned"), default="naive")
    parser.add_argument("--predictions", type=Path, required=True, help="Raw OCR evaluator JSONL")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--ranker", type=Path, help="Candidate-ranker JSON file (required for tuned mode)")
    parser.add_argument("--split", help="Optional output split filter, e.g. test")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root or source_dataset("cord-v2" if args.dataset == "cord" else "sroie-mirror")
    labels_path = args.labels or root / "labels.jsonl"
    manifest = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    labels_by_key = (
        {int(row["row_id"]): row for row in manifest}
        if args.dataset == "sroie"
        else {(str(row.get("split", "")), int(row["row_id"])): row for row in manifest}
    )
    sroie_gt = sroie_totals(root) if args.dataset == "sroie" else {}

    ranker_weights = None
    if args.mode == "tuned":
        if not args.ranker:
            parser.error("--ranker is required in tuned mode")
        ranker_weights = json.loads(args.ranker.read_text(encoding="utf-8"))["weights"]

    predictions = [json.loads(line) for line in args.predictions.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.split:
        predictions = [row for row in predictions if row.get("split") == args.split]
    if args.limit:
        predictions = predictions[:args.limit]

    outputs: list[dict[str, Any]] = []
    total_labeled = total_correct = total_selected = 0
    tax_labeled = tax_correct = tax_selected = 0
    service_labeled = service_correct = service_selected = 0
    for prediction in predictions:
        key = int(prediction["row_id"]) if args.dataset == "sroie" else (str(prediction.get("split", "")), int(prediction["row_id"]))
        label = labels_by_key.get(key)
        if label is None:
            continue
        image_path = root / prediction["image"]
        with Image.open(image_path) as image:
            fields = extract_receipt_fields(
                prediction.get("text_instances", []), image.height, args.dataset,
                mode=args.mode, ranker_weights=ranker_weights,
            )

        if args.dataset == "sroie":
            total_gt = sroie_gt.get(int(prediction["row_id"]))
            tax_gt = None  # SROIE's key-field annotations do not label tax.
            service_gt = None
        else:
            gt_parse = json.loads(label["ground_truth"]).get("gt_parse", {})
            total_gt = cord_total(label)
            subtotal = gt_parse.get("sub_total", gt_parse.get("subtotal", {}))
            tax_value = subtotal.get("tax_price")
            tax_gt = str(tax_value) if tax_value is not None and str(tax_value).strip() else None
            service_value = subtotal.get("service_price")
            service_gt = str(service_value) if service_value is not None and str(service_value).strip() else None

        total_target = normalize_amount(total_gt, args.dataset) if total_gt else None
        total_pred = fields["total"]["amount_normalized"] if fields.get("total") else None
        total_is_correct = total_target is not None and total_pred == total_target
        if total_target is not None:
            total_labeled += 1
            total_correct += int(total_is_correct)
            total_selected += int(total_pred is not None)

        tax_pred = fields["taxes"][0]["normalized_value"] if fields.get("taxes") else None
        tax_target = normalize_amount(tax_gt, args.dataset) if tax_gt else None
        tax_is_correct = tax_target is not None and tax_pred == tax_target
        if tax_target is not None:
            tax_labeled += 1
            tax_correct += int(tax_is_correct)
            tax_selected += int(tax_pred is not None)

        service_pred = fields["service_charge"]["normalized_value"] if fields.get("service_charge") else None
        service_target = normalize_amount(service_gt, args.dataset) if service_gt else None
        service_is_correct = service_target is not None and service_pred == service_target
        if service_target is not None:
            service_labeled += 1
            service_correct += int(service_is_correct)
            service_selected += int(service_pred is not None)

        outputs.append({
            "dataset": args.dataset,
            "mode": args.mode,
            "split": prediction.get("split", "unspecified"),
            "row_id": prediction["row_id"],
            "image": prediction["image"],
            "total_ground_truth_raw": total_gt,
            "total_correct": bool(total_is_correct) if total_target is not None else None,
            "tax_ground_truth_raw": tax_gt,
            "tax_correct": bool(tax_is_correct) if tax_target is not None else None,
            "service_charge_ground_truth_raw": service_gt,
            "service_charge_correct": bool(service_is_correct) if service_target is not None else None,
            "fields": fields,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in outputs), encoding="utf-8")
    print(json.dumps({
        "dataset": args.dataset,
        "mode": args.mode,
        "documents": len(outputs),
        "total_labeled": total_labeled,
        "total_exact_accuracy": total_correct / max(1, total_labeled),
        "total_selection_coverage": total_selected / max(1, total_labeled),
        "total_exact_accuracy_when_selected": total_correct / max(1, total_selected),
        "tax_labeled": tax_labeled,
        "tax_exact_accuracy_on_labeled": tax_correct / tax_labeled if tax_labeled else None,
        "tax_selection_coverage_on_labeled": tax_selected / tax_labeled if tax_labeled else None,
        "tax_exact_accuracy_when_selected": tax_correct / tax_selected if tax_selected else None,
        "service_charge_labeled": service_labeled,
        "service_charge_exact_accuracy_on_labeled": service_correct / service_labeled if service_labeled else None,
        "service_charge_selection_coverage_on_labeled": service_selected / service_labeled if service_labeled else None,
        "service_charge_exact_accuracy_when_selected": service_correct / service_selected if service_selected else None,
        "currency_and_purpose_have_no_ground_truth_in_these_benchmarks": True,
        "line_items_status": "schema placeholder only; not extracted",
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Score OCR-to-total-field extraction methods against receipt labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocr_lab.amounts import score_predictions, train_candidate_ranker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("cord", "sroie"), required=True)
    parser.add_argument("--predictions", type=Path, required=True, help="Raw evaluator per-image JSONL (not ASCII-folded rescoring output)")
    parser.add_argument("--root", type=Path, help="Dataset root; defaults to data/cord-v2 or data/sroie-mirror")
    parser.add_argument("--labels", type=Path, help="Label manifest; defaults to the dataset root's labels.jsonl")
    parser.add_argument("--output", type=Path, help="Optional detailed JSON output")
    parser.add_argument("--split", help="Optional prediction split filter, e.g. test")
    parser.add_argument("--train-predictions", type=Path, help="Optional OCR JSONL used to train the candidate ranker")
    parser.add_argument("--train-labels", type=Path, help="Training label manifest; defaults to --labels")
    parser.add_argument("--train-root", type=Path, help="Training dataset root; defaults to --root")
    parser.add_argument("--train-dataset", choices=("cord", "sroie"), help="Training dataset type; defaults to --dataset")
    parser.add_argument("--train-split", default="validation")
    parser.add_argument("--ranker-output", type=Path, help="Optional trained ranker JSON artifact")
    args = parser.parse_args()

    root = args.root or Path("data/cord-v2" if args.dataset == "cord" else "data/sroie-mirror")
    labels_path = args.labels or root / "labels.jsonl"
    manifest: list[dict[str, Any]] = [
        json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    weights = None
    training_info = None
    if args.train_predictions:
        train_root = args.train_root or root
        train_labels_path = args.train_labels or labels_path
        train_manifest = [
            json.loads(line) for line in train_labels_path.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        train_dataset = args.train_dataset or args.dataset
        weights, training_info = train_candidate_ranker(
            args.train_predictions,
            train_root,
            train_dataset,
            train_manifest,
            split=args.train_split,
        )
        if args.ranker_output:
            args.ranker_output.parent.mkdir(parents=True, exist_ok=True)
            args.ranker_output.write_text(json.dumps({
                "feature_names": ["bias", "near_total_anchor", "anchor_distance", "vertical_position", "line_has_total", "digit_length", "log_amount", "ocr_confidence", "has_separator", "excluded_context"],
                "weights": weights,
                "training": training_info,
                "training_dataset": train_dataset,
                "training_split": args.train_split,
                "score_normalization": "dataset-specific amount normalization; not OCR ASCII-fold",
            }, indent=2) + "\n", encoding="utf-8")

    results = score_predictions(args.predictions, root, args.dataset, manifest, ranker_weights=weights, split=args.split)
    if training_info is not None:
        results["ranker_training"] = training_info
    serialized = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    summary = {key: value for key, value in results.items() if key != "per_document"}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

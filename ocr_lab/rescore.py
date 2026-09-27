"""Rescore saved OCR outputs without rerunning inference."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from .evaluate import edit_distance, normalize, normalize_for_scoring


MODES = ("case-sensitive", "case-insensitive", "ascii-fold")


def metric_pair(reference: str, prediction: str, mode: str) -> tuple[int, int, int, int]:
    ref = normalize_for_scoring(reference, mode)
    pred = normalize_for_scoring(prediction, mode)
    char_edits = edit_distance(ref, pred)
    word_edits = edit_distance(ref.split(), pred.split())
    return char_edits, len(ref), word_edits, len(ref.split())


def rescore_file(source: Path, destination: Path, mode: str = "ascii-fold") -> dict[str, Any]:
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    totals = {name: [0, 0, 0, 0] for name in (*MODES, mode)}
    latencies: list[float] = []
    updated: list[dict[str, Any]] = []
    for row in rows:
        truth = normalize(row["ground_truth_text"])
        prediction = normalize(row["predicted_text"])
        row["ground_truth_text"] = truth
        row["predicted_text"] = prediction
        scores = {name: metric_pair(truth, prediction, name) for name in set((*MODES, mode))}
        for name, (char_edits, char_count, word_edits, word_count) in scores.items():
            aggregate = totals[name]
            aggregate[0] += char_edits
            aggregate[1] += char_count
            aggregate[2] += word_edits
            aggregate[3] += word_count
            row[f"cer_{name.replace('-', '_')}"] = char_edits / max(1, char_count)
            row[f"wer_{name.replace('-', '_')}"] = word_edits / max(1, word_count)

        primary = scores[mode]
        row["cer"] = primary[0] / max(1, primary[1])
        row["wer"] = primary[2] / max(1, primary[3])
        row["score_normalization"] = mode
        if row.get("latency_seconds") is not None:
            latencies.append(float(row["latency_seconds"]))
        updated.append(row)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in updated), encoding="utf-8")

    def aggregate_score(name: str) -> dict[str, float]:
        values = totals[name]
        return {"cer": values[0] / max(1, values[1]), "wer": values[2] / max(1, values[3])}

    summary: dict[str, Any] = {
        "source": str(source),
        "predictions_normalized": str(destination),
        "num_images": len(rows),
        "score_normalization": mode,
        **aggregate_score(mode),
        "case_sensitive": aggregate_score("case-sensitive"),
        "case_insensitive": aggregate_score("case-insensitive"),
        "ascii_fold": aggregate_score("ascii-fold"),
        "wall_seconds_per_image_p50": statistics.median(latencies) if latencies else None,
        "note": "Re-scored saved OCR outputs; inference was not rerun. ASCII-fold ignores case, punctuation/symbols, and decomposable Latin diacritics; other scripts remain.",
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", nargs="+", type=Path, help="Saved per-image OCR JSONL prediction files")
    parser.add_argument("--normalization", choices=MODES, default="ascii-fold")
    parser.add_argument("--output-dir", type=Path, default=Path("runs/ascii-fold"))
    parser.add_argument("--summary", type=Path, default=Path("runs/ascii-fold/summary.json"))
    args = parser.parse_args()
    summaries = []
    for source in args.predictions:
        destination = args.output_dir / f"{source.stem}-{args.normalization}.jsonl"
        summaries.append(rescore_file(source, destination, args.normalization))
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

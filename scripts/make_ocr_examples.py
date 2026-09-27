"""Create best/median/worst side-by-side OCR examples from CORD runs."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocr_lab.evaluate import ascii_fold


def load_results(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows[(str(row.get("split", "")), int(row.get("row_id", -1)))] = row
    return rows


def color_diff(reference: str, prediction: str) -> str:
    """Highlight only differences scored by the ASCII-fold normalization."""
    def units(text: str) -> list[tuple[str, int, str]]:
        output: list[tuple[str, int, str]] = []
        for source_index, char in enumerate(text):
            folded = " " if char.isspace() else ascii_fold(char)
            output.extend((folded_char, source_index, char) for folded_char in folded)
        return output

    ref_units, pred_units = units(reference), units(prediction)
    n, m = len(ref_units), len(pred_units)
    distance = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        distance[i][0] = i
    for j in range(m + 1):
        distance[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            distance[i][j] = min(
                distance[i - 1][j] + 1,
                distance[i][j - 1] + 1,
                distance[i - 1][j - 1] + (ref_units[i - 1][0] != pred_units[j - 1][0]),
            )

    wrong_prediction_indices: set[int] = set()
    missing_before: dict[int, list[str]] = {}
    i, j = n, m
    while i or j:
        if i and j and ref_units[i - 1][0] == pred_units[j - 1][0] and distance[i][j] == distance[i - 1][j - 1]:
            i -= 1
            j -= 1
        elif i and j and distance[i][j] == distance[i - 1][j - 1] + 1:
            wrong_prediction_indices.add(pred_units[j - 1][1])
            i -= 1
            j -= 1
        elif j and distance[i][j] == distance[i][j - 1] + 1:
            wrong_prediction_indices.add(pred_units[j - 1][1])
            j -= 1
        else:
            ref_char = ref_units[i - 1][2]
            cursor = pred_units[j][1] if j < m else len(prediction)
            missing_before.setdefault(cursor, []).append(ref_char)
            i -= 1
    red_style = ' style="background-color:#ffb3b3;color:#7f0000;padding:0 1px;border-radius:2px"'
    rendered = []
    for source_index, char in enumerate(prediction):
        for missing_char in missing_before.get(source_index, []):
            escaped_missing = html.escape(missing_char)
            rendered.append(f"<span{red_style} title=\"missing reference character: {escaped_missing}\">∅</span>")
        escaped = html.escape(char)
        if source_index in wrong_prediction_indices:
            rendered.append(f"<span{red_style}>{escaped}</span>")
        else:
            rendered.append(escaped)
    for missing_char in missing_before.get(len(prediction), []):
        escaped_missing = html.escape(missing_char)
        rendered.append(f"<span{red_style} title=\"missing reference character: {escaped_missing}\">∅</span>")
    return "<pre>" + "".join(rendered) + "</pre>"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paddle", type=Path, default=Path("runs/cord-paddleocr.jsonl"))
    parser.add_argument("--rapid", type=Path, default=Path("runs/cord-rapidocr-no-orientation.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("reports/OCR example comparisons.md"))
    parser.add_argument("--dataset-root", type=Path, default=Path("data/cord-v2"))
    parser.add_argument("--dataset-name", default="CORD")
    args = parser.parse_args()
    paddle = load_results(args.paddle)
    rapid = load_results(args.rapid)
    common = sorted(set(paddle) & set(rapid))
    if not common:
        raise SystemExit("No common image keys in the two prediction files")

    def rank_key(key: tuple[str, int]) -> tuple[float, int]:
        return (float(paddle[key].get("cer", 1.0)), -len(paddle[key].get("ground_truth_text", "")))

    ranked = sorted(common, key=rank_key)
    eligible = [key for key in ranked if len(paddle[key].get("ground_truth_text", "")) >= 40]
    if len(eligible) >= 3:
        ranked_for_examples = sorted(eligible, key=rank_key)
    else:
        ranked_for_examples = ranked
    selections = {
        "Best (lowest PaddleOCR CER; ties prefer longer text)": ranked_for_examples[0],
        "Median (nearest the median PaddleOCR per-image CER)": ranked_for_examples[(len(ranked_for_examples) - 1) // 2],
        "Worst (highest PaddleOCR CER; ties prefer longer text)": ranked_for_examples[-1],
    }
    lines = [
        "# OCR example comparisons",
        "",
        f"Examples are drawn from shared `{args.dataset_name}` predictions. Best/median/worst rank is based on per-image ASCII-fold PaddleOCR CER (for ties, longer references are preferred). Red backgrounds mark substitutions and extra predicted characters after case/punctuation/diacritic normalization; a red `∅` marks a missing character. The OCR run configs and environment are recorded in the matching `runs/` outputs. These examples are pipeline diagnostics—not Czech receipts.",
        "",
    ]
    for title, key in selections.items():
        p, r = paddle[key], rapid[key]
        image = args.dataset_root / p["image"]
        image_from_report = Path("..") / image
        lines.extend([
            f"## {title}",
            "",
            f"- Image: `{image}`",
            f"\n![Receipt image]({image_from_report.as_posix()})\n",
            f"- Split / record: `{key[0]} / {key[1]}`",
            f"- PaddleOCR: CER `{p['cer']:.3f}`, WER `{p['wer']:.3f}`",
            f"- RapidOCR: CER `{r['cer']:.3f}`, WER `{r['wer']:.3f}`",
            "",
            "**Ground truth**",
            "```text",
            p["ground_truth_text"],
            "```",
            "**PaddleOCR**",
            color_diff(p["ground_truth_text"], p["predicted_text"]),
            "**RapidOCR**",
            color_diff(r["ground_truth_text"], r["predicted_text"]),
            "",
        ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote examples to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

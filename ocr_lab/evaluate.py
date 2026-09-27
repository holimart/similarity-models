"""Evaluate a chosen OCR harness on the downloaded CORD label manifest."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import time
import unicodedata
from pathlib import Path
from typing import Any

from .core import LocalOCRHarness, OCRConfig, config_dict, installed_versions


def flatten_cord_text(ground_truth: str) -> tuple[str, list[tuple[float, float, str]]]:
    parsed = json.loads(ground_truth)
    positioned: list[tuple[float, float, str]] = []
    for line in parsed.get("valid_line", []):
        for word in line.get("words", []):
            text = word.get("text")
            quad = word.get("quad", {})
            if not text:
                continue
            xs = [float(quad[k]) for k in ("x1", "x2", "x3", "x4") if k in quad]
            ys = [float(quad[k]) for k in ("y1", "y2", "y3", "y4") if k in quad]
            positioned.append((sum(ys) / len(ys) if ys else 0.0, min(xs) if xs else 0.0, str(text)))
    positioned.sort(key=lambda item: (round(item[0] / 12) * 12, item[1]))
    return " ".join(item[2] for item in positioned), positioned


def ground_truth_text(value: str) -> str:
    """Accept CORD's JSON payload or a plain transcription (e.g. TextZoom)."""
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return str(value)
    if isinstance(parsed, dict) and "valid_line" in parsed:
        return flatten_cord_text(value)[0]
    return str(value)


def prediction_text(records: list[dict[str, Any]]) -> str:
    positioned: list[tuple[float, float, str]] = []
    for record in records:
        polygon = record.get("polygon") or []
        if polygon:
            ys = [point[1] for point in polygon]
            xs = [point[0] for point in polygon]
            y, x = sum(ys) / len(ys), min(xs)
        else:
            y, x = 0.0, 0.0
        positioned.append((y, x, record["text"]))
    positioned.sort(key=lambda item: (round(item[0] / 12) * 12, item[1]))
    return " ".join(item[2] for item in positioned)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", text).strip()


def ascii_fold(text: str) -> str:
    """Ignore case, decomposable Latin diacritics, punctuation, and symbols."""
    special = {"ø": "o", "ł": "l", "đ": "d", "ð": "d", "þ": "th", "æ": "ae", "œ": "oe", "ħ": "h", "ŋ": "n"}
    output: list[str] = []
    for char in unicodedata.normalize("NFKD", text.casefold()):
        if unicodedata.combining(char) or unicodedata.category(char)[0] in {"P", "S"}:
            continue
        output.append(special.get(char, char))
    return normalize("".join(output))


def normalize_for_scoring(text: str, mode: str) -> str:
    text = normalize(text)
    if mode == "case-sensitive":
        return text
    if mode == "case-insensitive":
        return text.casefold()
    if mode == "ascii-fold":
        return ascii_fold(text)
    raise ValueError(f"Unknown normalization mode: {mode}")


def edit_distance(left: str, right: str) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (left_char != right_char)))
        previous = current
    return previous[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=Path("data/cord-v2/labels.jsonl"))
    parser.add_argument("--harness", choices=("paddleocr", "rapidocr"), default=None)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path, default=Path("runs/cord-predictions.jsonl"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--resolution", choices=("lr", "hr"), help="Optional TextZoom subset filter")
    parser.add_argument("--normalization", choices=("ascii-fold", "case-insensitive", "case-sensitive"), default="ascii-fold", help="Scoring normalization; default ignores case, punctuation, symbols, and decomposable diacritics")
    args = parser.parse_args()
    config = OCRConfig.from_json(args.config) if args.config else OCRConfig()
    if args.harness:
        config.harness = args.harness
    harness = LocalOCRHarness(config)
    rows = [json.loads(line) for line in args.labels.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.resolution:
        rows = [row for row in rows if row.get("resolution") == args.resolution]
    if args.limit:
        rows = rows[:args.limit]
    if not rows:
        raise SystemExit("No samples found in labels manifest")

    for _ in range(max(args.warmup, 0)):
        harness(args.labels.parent / rows[0]["image"])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    total_char_errors = total_chars = total_word_errors = total_words = 0
    strict_char_errors = strict_word_errors = strict_chars_total = strict_words_total = 0
    insensitive_char_errors = insensitive_word_errors = insensitive_chars_total = insensitive_words_total = 0
    ascii_char_errors = ascii_word_errors = ascii_chars_total = ascii_words_total = 0
    latencies: list[float] = []
    with args.output.open("w", encoding="utf-8") as out:
        for row in rows:
            image_path = args.labels.parent / row["image"]
            started = time.perf_counter()
            records, backend = harness(image_path)
            latency = time.perf_counter() - started
            latencies.append(latency)
            truth = normalize(ground_truth_text(row["ground_truth"]))
            predicted = normalize(prediction_text(records))
            strict_truth, strict_prediction = normalize_for_scoring(truth, "case-sensitive"), normalize_for_scoring(predicted, "case-sensitive")
            insensitive_truth, insensitive_prediction = normalize_for_scoring(truth, "case-insensitive"), normalize_for_scoring(predicted, "case-insensitive")
            ascii_truth, ascii_prediction = normalize_for_scoring(truth, "ascii-fold"), normalize_for_scoring(predicted, "ascii-fold")
            scored_truth = normalize_for_scoring(truth, args.normalization)
            scored_prediction = normalize_for_scoring(predicted, args.normalization)
            strict_truth_words, strict_prediction_words = strict_truth.split(), strict_prediction.split()
            insensitive_truth_words, insensitive_prediction_words = insensitive_truth.split(), insensitive_prediction.split()
            ascii_truth_words, ascii_prediction_words = ascii_truth.split(), ascii_prediction.split()
            strict_chars = edit_distance(strict_truth, strict_prediction)
            strict_words = edit_distance(strict_truth_words, strict_prediction_words)
            insensitive_chars = edit_distance(insensitive_truth, insensitive_prediction)
            insensitive_words = edit_distance(insensitive_truth_words, insensitive_prediction_words)
            ascii_chars = edit_distance(ascii_truth, ascii_prediction)
            ascii_words = edit_distance(ascii_truth_words, ascii_prediction_words)
            char_errors = edit_distance(scored_truth, scored_prediction)
            word_errors = edit_distance(scored_truth.split(), scored_prediction.split())
            total_char_errors += char_errors
            total_chars += len(scored_truth)
            total_word_errors += word_errors
            total_words += len(scored_truth.split())
            strict_char_errors += strict_chars
            strict_word_errors += strict_words
            strict_chars_total += len(strict_truth)
            strict_words_total += len(strict_truth_words)
            insensitive_char_errors += insensitive_chars
            insensitive_word_errors += insensitive_words
            insensitive_chars_total += len(insensitive_truth)
            insensitive_words_total += len(insensitive_truth_words)
            ascii_char_errors += ascii_chars
            ascii_word_errors += ascii_words
            ascii_chars_total += len(ascii_truth)
            ascii_words_total += len(ascii_truth_words)
            out.write(json.dumps({
                "split": row.get("split", row.get("difficulty", "unspecified")),
                "row_id": row.get("row_id", row.get("index")), "image": row["image"],
                "ground_truth_text": truth, "predicted_text": predicted,
                "cer": char_errors / max(1, len(scored_truth)),
                "wer": word_errors / max(1, len(scored_truth.split())),
                "score_normalization": args.normalization,
                "cer_case_sensitive": strict_chars / max(1, len(truth)),
                "wer_case_sensitive": strict_words / max(1, len(strict_truth_words)),
                "cer_case_insensitive": insensitive_chars / max(1, len(insensitive_truth)),
                "wer_case_insensitive": insensitive_words / max(1, len(insensitive_truth_words)),
                "cer_ascii_fold": ascii_chars / max(1, len(ascii_truth)),
                "wer_ascii_fold": ascii_words / max(1, len(ascii_truth_words)),
                "latency_seconds": latency, "text_instances": records, "runtime": backend,
            }, ensure_ascii=False) + "\n")

    print(json.dumps({
        "harness": config.harness,
        "config": config_dict(config),
        "packages": installed_versions(),
        "num_images": len(rows),
        "score_normalization": args.normalization,
        "character_error_rate": total_char_errors / max(1, total_chars),
        "word_error_rate": total_word_errors / max(1, total_words),
        "character_error_rate_case_sensitive": strict_char_errors / max(1, strict_chars_total),
        "word_error_rate_case_sensitive": strict_word_errors / max(1, strict_words_total),
        "character_error_rate_case_insensitive": insensitive_char_errors / max(1, insensitive_chars_total),
        "word_error_rate_case_insensitive": insensitive_word_errors / max(1, insensitive_words_total),
        "character_error_rate_ascii_fold": ascii_char_errors / max(1, ascii_chars_total),
        "word_error_rate_ascii_fold": ascii_word_errors / max(1, ascii_words_total),
        "wall_seconds_per_image_p50": statistics.median(latencies),
        "wall_seconds_total": sum(latencies),
        "predictions": str(args.output),
        "note": "ASCII-fold scoring is default and ignores case, punctuation/symbols, and decomposable diacritics; strict and case-insensitive scores are also reported. Non-Latin letters are retained.",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

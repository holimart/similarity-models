"""Evaluate a local Ollama text LLM for selecting a receipt total from OCR text."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
import statistics
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocr_lab.amounts import amount_methods, cord_total, normalize_amount, sroie_totals


OLLAMA_CHAT = "http://localhost:11434/api/chat"
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "selected_candidate_id": {"type": ["string", "null"]},
    },
    "required": ["selected_candidate_id"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = "Choose final amount due including tax, not subtotal, tax, items, cash tender, or change. Select a supplied candidate ID only, or null. Never calculate/invent."


def load_dataset(dataset: str, root: Path) -> tuple[list[dict[str, Any]], dict[int, str]]:
    manifest = root / "labels.jsonl"
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    targets = sroie_totals(root) if dataset == "sroie" else {}
    return rows, targets


def get_target(dataset: str, row: dict[str, Any], sroie_values: dict[int, str]) -> str | None:
    if dataset == "sroie":
        value = sroie_values.get(int(row.get("row_id", -1)))
        return value if value and value.strip() else None
    return cord_total(row)


def make_prompt(records: list[dict[str, Any]], dataset: str) -> tuple[str, dict[str, dict[str, Any]]]:
    candidates: list[str] = []
    candidate_map: dict[str, dict[str, Any]] = {}
    label_lines: list[dict[str, Any]] = []
    from ocr_lab.amounts import AMOUNT_RE, normalize_amount

    positioned: list[tuple[int, dict[str, Any], str, float | None, list[Any]]] = []
    for line_id, record in enumerate(records, start=1):
        text = str(record.get("text", ""))
        polygon = record.get("polygon") or []
        y = round(sum(float(point[1]) for point in polygon) / len(polygon), 1) if polygon else None
        matches = list(AMOUNT_RE.finditer(text))
        positioned.append((line_id, record, text, y, matches))

    max_y = max((line[3] or 0 for line in positioned), default=1.0) or 1.0
    anchor_words = ("total", "payable", "due", "subtotal", "cash", "change", "gst", "tax", "tender")
    for line_id, record, text, y, matches in positioned:
        lowered = text.casefold()
        if any(word in lowered for word in anchor_words):
            label_lines.append({"line_id": line_id, "y": round((y or 0.0) / max_y, 2), "text": text[:64]})
        for match in matches:
            raw = match.group(0)
            digit_count = sum(char.isdigit() for char in raw)
            if digit_count < 2 or digit_count > 10:
                continue
            normalized = normalize_amount(raw, dataset)
            if not normalized:
                continue
            candidate_id = f"C{len(candidates) + 1}"
            item = {
                "candidate_id": candidate_id,
                "raw_amount_text": raw,
                "ocr_line_id": line_id,
                "y": round((y or 0.0) / max_y, 3),
                "ocr_line_text": text,
                "ocr_confidence": record.get("confidence"),
                "normalized_value_internal": normalized,
            }
            candidates.append(f"{candidate_id}={raw}@L{line_id},y{round((y or 0.0) / max_y, 2)}")
            candidate_map[candidate_id] = item

    label_text = "; ".join(f"L{line['line_id']}@{line['y']} {line['text']}" for line in label_lines)
    prompt = (
        f"Labels at page positions: {label_text}\nCandidates: {'; '.join(candidates)}\n"
        "Return JSON with selected_candidate_id. Prefer the amount aligned with the final total label."
    )
    return prompt, candidate_map


def call_ollama(model: str, prompt: str, timeout: int, think: bool | str, threads: int, num_predict: int) -> tuple[dict[str, Any], dict[str, Any]]:
    response = requests.post(
        OLLAMA_CHAT,
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "format": OUTPUT_SCHEMA,
            "stream": False,
            "think": think,
            "keep_alive": "10m",
            "options": {"temperature": 0, "num_ctx": 1024, "num_predict": num_predict, "num_thread": threads, "seed": 42},
        },
        timeout=timeout,
    )
    response.raise_for_status()
    body = response.json()
    message = body.get("message", {})
    content = message.get("content", "")
    parsed = json.loads(content)
    metadata = {
        "total_duration_ns": body.get("total_duration"),
        "load_duration_ns": body.get("load_duration"),
        "prompt_eval_count": body.get("prompt_eval_count"),
        "prompt_eval_duration_ns": body.get("prompt_eval_duration"),
        "eval_count": body.get("eval_count"),
        "eval_duration_ns": body.get("eval_duration"),
        "thinking_chars": len(message.get("thinking") or ""),
    }
    return parsed, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Ollama model tag, e.g. gpt-oss:20b or qwen3:4b")
    parser.add_argument("--dataset", choices=("cord", "sroie"), required=True)
    parser.add_argument("--predictions", type=Path, required=True, help="Raw OCR run JSONL (not case-folded rescoring output)")
    parser.add_argument("--root", type=Path, help="Dataset root; defaults to local CORD/SROIE path")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--row-ids", nargs="+", type=int, help="Optional stable dataset row IDs for a reproducible small pilot")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--threads", type=int, default=12, help="CPU inference threads; tune for this host")
    parser.add_argument("--num-predict", type=int, help="Maximum generated tokens; defaults to 128 for GPT-OSS and 40 for Qwen3")
    parser.add_argument("--think", choices=("off", "low", "medium", "high"), help="Reasoning effort; defaults to low for GPT-OSS and off for Qwen3")
    parser.add_argument("--resume", action="store_true", help="Skip image IDs already present in the output JSONL")
    args = parser.parse_args()
    think_mode = args.think or ("low" if args.model.startswith("gpt-oss") else "off")
    think_value: bool | str = False if think_mode == "off" else think_mode
    num_predict = args.num_predict or (128 if args.model.startswith("gpt-oss") else 40)

    root = args.root or Path("data/cord-v2" if args.dataset == "cord" else "data/sroie-mirror")
    manifest_rows, target_map = load_dataset(args.dataset, root)
    row_lookup = (
        {int(row.get("row_id", -1)): row for row in manifest_rows}
        if args.dataset == "sroie"
        else {(str(row.get("split", "")), int(row.get("row_id", -1))): row for row in manifest_rows}
    )
    predictions = [json.loads(line) for line in args.predictions.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.dataset == "cord":
        predictions = [row for row in predictions if row.get("split") == "test"]
    if args.row_ids:
        wanted = set(args.row_ids)
        predictions = [row for row in predictions if int(row.get("row_id", -1)) in wanted]
    if args.limit:
        predictions = predictions[:args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    existing_ids: set[str] = set()
    if args.resume and args.output.exists():
        for line in args.output.read_text(encoding="utf-8").splitlines():
            if line.strip():
                saved_row = json.loads(line)
                if not saved_row.get("error"):
                    existing_ids.add(str(saved_row.get("document_id")))

    output_mode = "a" if args.resume else "w"
    totals = {"labeled": 0, "correct": 0, "selected": 0, "oracle_correct": 0, "valid_json": 0, "unsupported_id": 0}
    latencies: list[float] = []
    with args.output.open(output_mode, encoding="utf-8") as output:
        for index, prediction in enumerate(predictions, start=1):
            document_id = f"{prediction.get('split', 'sroie')}:{prediction.get('row_id')}"
            if document_id in existing_ids:
                continue
            key = int(prediction.get("row_id", -1)) if args.dataset == "sroie" else (str(prediction.get("split", "")), int(prediction.get("row_id", -1)))
            source_row = row_lookup.get(key)
            if source_row is None:
                continue
            target_raw = target_map.get(int(prediction.get("row_id", -1))) if args.dataset == "sroie" else get_target(args.dataset, source_row, target_map)
            if target_raw is None:
                continue
            target_normalized = normalize_amount(target_raw, args.dataset)
            records = prediction.get("text_instances", [])
            prompt, candidate_map = make_prompt(records, args.dataset)
            started = time.perf_counter()
            error = None
            try:
                parsed, llm_meta = call_ollama(args.model, prompt, args.timeout, think_value, args.threads, num_predict)
            except Exception as exc:
                parsed, llm_meta, error = {"selected_candidate_id": None, "evidence_line_ids": []}, {}, f"{type(exc).__name__}: {exc}"
            latency = time.perf_counter() - started
            latencies.append(latency)
            selected_id = parsed.get("selected_candidate_id")
            selected = candidate_map.get(selected_id) if selected_id is not None else None
            unsupported = selected_id is not None and selected is None
            selected_norm = selected.get("normalized_value_internal") if selected else None
            exact = selected_norm == target_normalized
            oracle_correct = any(item["normalized_value_internal"] == target_normalized for item in candidate_map.values())
            totals["labeled"] += 1
            totals["correct"] += int(exact)
            totals["selected"] += int(selected is not None)
            totals["oracle_correct"] += int(oracle_correct)
            totals["valid_json"] += int(error is None)
            totals["unsupported_id"] += int(unsupported)
            output.write(json.dumps({
                "document_id": document_id,
                "image": prediction["image"],
                "ground_truth_raw": target_raw,
                "ground_truth_normalized": target_normalized,
                "status": "found" if selected is not None else ("error" if error else "abstain"),
                "selected_candidate_id": selected_id,
                "selected_candidate_raw": selected.get("raw_amount_text") if selected else None,
                "selected_candidate_normalized": selected_norm,
                "selected_candidate_line_id": selected.get("ocr_line_id") if selected else None,
                "selected_candidate_line": selected.get("ocr_line_text") if selected else None,
                "evidence_line_ids": parsed.get("evidence_line_ids", []),
                "correct": exact,
                "ocr_oracle_contains_total": oracle_correct,
                "unsupported_candidate_id": unsupported,
                "latency_seconds": latency,
                "llm_metadata": llm_meta,
                "error": error,
            }, ensure_ascii=False) + "\n")
            output.flush()
            if index % 10 == 0 or index == len(predictions):
                print(f"{args.model} {args.dataset}: processed {index}/{len(predictions)}", file=sys.stderr)

    saved_by_id: dict[str, dict[str, Any]] = {}
    for line in args.output.read_text(encoding="utf-8").splitlines():
        if line.strip():
            saved_row = json.loads(line)
            saved_by_id[str(saved_row.get("document_id"))] = saved_row
    saved_rows = list(saved_by_id.values())
    # Resume attempts can append a prior failed attempt and a later success for
    # the same receipt. Keep only the latest record in the final result file.
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in saved_rows), encoding="utf-8")
    saved_count = len(saved_rows)
    latencies = [float(row["latency_seconds"]) for row in saved_rows if row.get("latency_seconds") is not None]
    summary = {
        "model": args.model,
        "dataset": args.dataset,
        "ocr_input": str(args.predictions),
        "output": str(args.output),
        "labeled_documents": saved_count,
        "exact_total_accuracy": sum(bool(row.get("correct")) for row in saved_rows) / max(1, saved_count),
        "selection_coverage": sum(row.get("selected_candidate_raw") is not None for row in saved_rows) / max(1, saved_count),
        "oracle_ocr_amount_recall": sum(bool(row.get("ocr_oracle_contains_total")) for row in saved_rows) / max(1, saved_count),
        "valid_json_rate": sum(not row.get("error") for row in saved_rows) / max(1, saved_count),
        "unsupported_candidate_rate": sum(bool(row.get("unsupported_candidate_id")) for row in saved_rows) / max(1, saved_count),
        "latency_seconds_p50": statistics.median(latencies) if latencies else None,
        "think_mode": think_mode,
        "note": "This is extraction from OCR text; it does not read the receipt image. Amount equality uses dataset-specific amount normalization.",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    args.output.with_suffix(".summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate and merge the manually reviewed CORD and SROIE annotation batches."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocr_lab.data_paths import datasets_root, manual_annotations_dir


def normalized_image(dataset: str, image: str) -> str:
    value = image.replace("\\", "/")
    if value.startswith("data/"):
        value = value.removeprefix("data/")
    if value.startswith("images/") and dataset == "cord-v2":
        value = f"cord-v2/{value}"
    if value.startswith("cord-v2/") or value.startswith("sroie-mirror/"):
        value = f"source/{value}"
    return value


def main() -> int:
    manual_dir = manual_annotations_dir()
    batches = sorted(
        path for path in manual_dir.glob("*.jsonl")
        if path.name.startswith(("cord_", "sroie_"))
    )
    rows = [
        json.loads(line)
        for path in batches
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    expected = {
        ("cord-v2", split, str(row_id))
        for split in ("validation", "test")
        for row_id in range(100)
    } | {("sroie-mirror", "mirror_subset", str(row_id)) for row_id in range(626)}

    normalized: list[dict[str, object]] = []
    seen: Counter[tuple[str, str, str]] = Counter()
    for row in rows:
        dataset = str(row.get("dataset", ""))
        if dataset == "naver-clova-ix/cord-v2":
            dataset = "cord-v2"
        row_id = str(row.get("row_id", ""))
        if dataset == "sroie-mirror":
            row_id = str(int(row_id))
        split = str(row.get("split", ""))
        key = (dataset, split, row_id)
        seen[key] += 1
        row["dataset"] = dataset
        row["row_id"] = row_id
        row["image"] = normalized_image(dataset, str(row.get("image", "")))
        total = row.get("total", {})
        if isinstance(total, dict) and total.get("currency_code") and not total.get("currency_raw"):
            total["currency_code"] = None
        image_path = datasets_root() / str(row["image"])
        if not image_path.is_file():
            raise SystemExit(f"Missing source image for {key}: {image_path}")
        normalized.append(row)

    actual = set(seen)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    duplicates = sorted(key for key, count in seen.items() if count != 1)
    if missing or extra or duplicates:
        raise SystemExit(
            f"Annotation identity validation failed: missing={missing[:10]}, "
            f"extra={extra[:10]}, duplicates={duplicates[:10]}"
        )

    normalized.sort(key=lambda row: (str(row["dataset"]), str(row["split"]), int(str(row["row_id"]))))
    normalized_by_key = {
        (str(row["dataset"]), str(row["split"]), str(row["row_id"])): row
        for row in normalized
    }
    for batch in batches:
        batch_keys = []
        for line in batch.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            dataset = "cord-v2" if raw.get("dataset") == "naver-clova-ix/cord-v2" else str(raw.get("dataset", ""))
            row_id = str(raw.get("row_id", ""))
            if dataset == "sroie-mirror":
                row_id = str(int(row_id))
            batch_keys.append((dataset, str(raw.get("split", "")), row_id))
        batch_rows = [normalized_by_key[key] for key in batch_keys]
        batch.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in batch_rows),
            encoding="utf-8",
        )

    output = manual_dir / "receipt_field_annotations.jsonl"
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in normalized),
        encoding="utf-8",
    )
    summary = (
        "# Manual receipt-field annotation coverage\n\n"
        f"Merged manifest: `{output.name}`\n\n"
        f"- CORD-v2 validation: 100 receipts\n"
        f"- CORD-v2 test: 100 receipts\n"
        f"- SROIE corrected mirror subset: 626 receipts\n"
        f"- Total manually reviewed receipt records: {len(normalized)}\n"
        "- TextZoom and XFUND are documented as out of scope because they are not receipt datasets.\n"
    )
    (manual_dir / "COVERAGE.md").write_text(summary, encoding="utf-8")
    print(f"Validated {len(normalized)} unique annotations; wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

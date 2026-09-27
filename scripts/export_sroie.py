"""Create an OCR-harness manifest from the mirrored SROIE CSV box labels."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocr_lab.data_paths import source_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=source_dataset("sroie-mirror"))
    args = parser.parse_args()
    rows = []
    for image_path in sorted((args.root / "img").glob("*.jpg")):
        label_path = args.root / "box" / f"{image_path.stem}.csv"
        positioned: list[tuple[float, float, str, list[list[int]]]] = []
        with label_path.open(encoding="utf-8-sig", newline="") as file:
            for fields in csv.reader(file):
                if len(fields) < 9:
                    continue
                coordinates = [int(value.strip()) for value in fields[:8]]
                text = ",".join(fields[8:]).strip()
                points = [[coordinates[i], coordinates[i + 1]] for i in range(0, 8, 2)]
                ys = [point[1] for point in points]
                xs = [point[0] for point in points]
                positioned.append((sum(ys) / len(ys), min(xs), text, points))
        positioned.sort(key=lambda item: (round(item[0] / 12) * 12, item[1]))
        rows.append({
            "dataset": "SROIE corrected mirror subset",
            "row_id": int(image_path.stem),
            "image": f"img/{image_path.name}",
            "ground_truth": " ".join(item[2] for item in positioned),
            "ground_truth_instances": [
                {"text": item[2], "polygon": item[3]} for item in positioned
            ],
        })
    if not rows:
        raise SystemExit(f"No images found under {args.root / 'img'}")
    destination = args.root / "labels.jsonl"
    destination.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(f"Exported {len(rows)} OCR labels to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

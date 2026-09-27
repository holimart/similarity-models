"""Create a text-manifest for XFUND validation documents across its 7 languages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/xfund-val"))
    args = parser.parse_args()
    records: list[dict[str, Any]] = []
    for language in ("de", "es", "fr", "it", "ja", "pt", "zh"):
        source = args.root / f"{language}.val.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        for document in payload["documents"]:
            positioned = []
            for entity in document.get("document", []):
                text = str(entity.get("text", "")).strip()
                box = entity.get("box") or [0, 0, 0, 0]
                if text:
                    positioned.append((float(box[1]), float(box[0]), text, entity))
            positioned.sort(key=lambda item: (round(item[0] / 12) * 12, item[1]))
            image_rel = Path(language) / f"{document['id']}.jpg"
            records.append({
                "dataset": "XFUND-v1-validation",
                "language": language,
                "row_id": document["id"],
                "image": image_rel.as_posix(),
                "ground_truth": " ".join(item[2] for item in positioned),
                "ground_truth_instances": [
                    {"text": item[2], "box": item[3].get("box"), "label": item[3].get("label")}
                    for item in positioned
                ],
            })
    output = args.root / "labels.jsonl"
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")
    print(f"Exported {len(records)} XFUND validation records to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

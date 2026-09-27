"""Export TextZoom test LMDB word crops to ordinary image files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import lmdb
from PIL import Image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/textzoom/test"))
    parser.add_argument("--dest", type=Path, default=Path("data/textzoom/test_export"))
    parser.add_argument("--resolution", choices=("lr", "hr", "both"), default="lr")
    args = parser.parse_args()
    args.dest.mkdir(parents=True, exist_ok=True)
    labels: list[dict[str, object]] = []
    for difficulty in ("easy", "medium", "hard"):
        database_path = args.source / f"{difficulty}.mdb"
        if not database_path.is_file():
            raise SystemExit(f"Missing {database_path}; run scripts/download_textzoom_test.py first")
        env = lmdb.open(str(database_path), readonly=True, lock=False, readahead=False, meminit=False, subdir=False)
        with env.begin(write=False) as txn:
            sample_count = int(txn.get(b"num-samples"))
            for index in range(1, sample_count + 1):
                suffix = f"{index:09d}".encode()
                label = txn.get(b"label-" + suffix)
                if label is None:
                    continue
                for resolution in (("lr", "hr") if args.resolution == "both" else (args.resolution,)):
                    raw = txn.get(f"image_{resolution}-".encode() + suffix)
                    if raw is None:
                        continue
                    relative = Path(difficulty) / f"{index:06d}_{resolution}.jpg"
                    image_path = args.dest / relative
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    with image_path.open("wb") as output:
                        output.write(raw)
                    with Image.open(image_path) as image:
                        width, height = image.size
                    labels.append({
                        "dataset": "TextZoom",
                        "difficulty": difficulty,
                        "index": index,
                        "resolution": resolution,
                        "image": relative.as_posix(),
                        "ground_truth": label.decode("utf-8"),
                        "width": width,
                        "height": height,
                    })
        env.close()
        print(f"exported {difficulty}: {sample_count} source samples")
    manifest = args.dest / "labels.jsonl"
    manifest.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in labels), encoding="utf-8")
    print(f"saved {len(labels)} image labels to {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

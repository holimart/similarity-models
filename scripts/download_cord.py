"""Download CORD-v2 validation/test receipt images and preserve OCR labels.

Only a local evaluation copy is created. Review the dataset's terms before
redistributing downloaded images or labels.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
from pathlib import Path
from typing import Any

import requests

DATASET = "naver-clova-ix/cord-v2"
ROWS_API = "https://datasets-server.huggingface.co/rows"
DEFAULT_DEST = Path("data/cord-v2")


def fetch_rows(split: str, limit: int | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    session = requests.Session()
    while limit is None or len(rows) < limit:
        length = min(100, limit - len(rows)) if limit is not None else 100
        response = session.get(
            ROWS_API,
            params={"dataset": DATASET, "config": "default", "split": split, "offset": offset, "length": length},
            timeout=90,
        )
        response.raise_for_status()
        payload = response.json()
        batch = payload.get("rows", [])
        if not batch:
            break
        rows.extend(batch)
        offset += len(batch)
        print(f"{split}: retrieved {len(rows)} rows", file=sys.stderr)
        if len(batch) < length:
            break
    return rows


def download_one(item: tuple[Path, str]) -> tuple[Path, int]:
    destination, url = item
    if destination.exists() and destination.stat().st_size:
        return destination, destination.stat().st_size
    response = requests.get(url, timeout=(20, 120), stream=True)
    response.raise_for_status()
    temporary = destination.with_suffix(destination.suffix + ".part")
    total = 0
    with temporary.open("wb") as stream:
        for chunk in response.iter_content(chunk_size=1024 * 512):
            if chunk:
                stream.write(chunk)
                total += len(chunk)
    if total < 4:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Downloaded response was unexpectedly small for {destination.name}")
    with temporary.open("rb") as stream:
        if stream.read(3) != b"\xff\xd8\xff":
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"Response is not a JPEG image: {destination.name}")
    temporary.replace(destination)
    return destination, total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--splits", nargs="+", choices=("validation", "test"), default=("validation", "test"))
    parser.add_argument("--limit-per-split", type=int, default=None, help="Optional small smoke-test subset")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if args.limit_per_split is not None and args.limit_per_split < 1:
        parser.error("--limit-per-split must be positive")

    args.dest.mkdir(parents=True, exist_ok=True)
    all_labels: list[dict[str, Any]] = []
    download_jobs: list[tuple[Path, str]] = []
    for split in args.splits:
        rows = fetch_rows(split, args.limit_per_split)
        for entry in rows:
            row = entry["row"]
            image = row.get("image") or {}
            source_url = image.get("src")
            if not source_url:
                continue
            row_id = int(entry.get("row_idx", len(all_labels)))
            image_rel = Path("images") / split / f"{row_id:04d}.jpg"
            image_path = args.dest / image_rel
            image_path.parent.mkdir(parents=True, exist_ok=True)
            download_jobs.append((image_path, source_url))
            all_labels.append({
                "dataset": DATASET,
                "split": split,
                "row_id": row_id,
                "image": image_rel.as_posix(),
                "width": image.get("width"),
                "height": image.get("height"),
                "ground_truth": row.get("ground_truth"),
            })

    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download_one, job): job[0] for job in download_jobs}
        for future in concurrent.futures.as_completed(futures):
            path = futures[future]
            try:
                _, size = future.result()
                print(f"downloaded {path} ({size:,} bytes)", file=sys.stderr)
            except Exception as exc:  # report all failures after useful work completes
                failures.append(f"{path}: {exc}")

    labels_path = args.dest / "labels.jsonl"
    labels_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in all_labels), encoding="utf-8")
    if failures:
        (args.dest / "download_errors.txt").write_text("\n".join(failures) + "\n", encoding="utf-8")
        raise SystemExit(f"Downloaded with {len(failures)} failures; see {args.dest / 'download_errors.txt'}")
    (args.dest / "DATASET_INFO.md").write_text(
        "# CORD-v2 local evaluation copy\n\n"
        "Source: https://huggingface.co/datasets/naver-clova-ix/cord-v2\n\n"
        "Dataset project states CC BY 4.0: https://github.com/clovaai/cord/blob/master/LICENSE-CC-BY\n\n"
        "This local copy contains only the selected validation/test image files and the original `ground_truth` strings. "
        "CORD consists of Indonesian receipts and is not a Czech benchmark. Do not redistribute this local image copy "
        "without checking the dataset and underlying image rights. Cite the CORD paper and dataset project when reporting results.\n",
        encoding="utf-8",
    )
    print(f"Saved {len(all_labels)} labels to {labels_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

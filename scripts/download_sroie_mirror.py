"""Download the publicly mirrored SROIE receipt OCR annotations and images.

The upstream mirror is an academic team's corrected 626-record subset, not the
full 1,000-image official challenge release. Keep this local and review source
image terms before redistribution.
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path, PurePosixPath

import requests

ARCHIVE_URL = "https://codeload.github.com/zzzDavid/ICDAR-2019-SROIE/zip/refs/heads/master"
SOURCE_URL = "https://github.com/zzzDavid/ICDAR-2019-SROIE"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=Path("data/sroie-mirror"))
    args = parser.parse_args()
    args.dest.mkdir(parents=True, exist_ok=True)
    response = requests.get(ARCHIVE_URL, timeout=(30, 300))
    response.raise_for_status()
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    selected = [
        item for item in archive.infolist()
        if any(f"/data/{kind}/" in item.filename for kind in ("img", "box", "key"))
        and not item.is_dir()
    ]
    if not selected:
        raise RuntimeError("The source archive did not contain the expected data/img, data/box, data/key files")
    expected_prefix = "ICDAR-2019-SROIE-master/data/"
    for item in selected:
        relative = PurePosixPath(item.filename).relative_to(expected_prefix)
        destination = args.dest / Path(relative.as_posix())
        destination.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(item) as src, destination.open("wb") as dst:
            while chunk := src.read(1024 * 1024):
                dst.write(chunk)

    counts = {name: sum(1 for _ in (args.dest / name).glob("*")) for name in ("img", "box", "key")}
    if len(set(counts.values())) != 1 or counts["img"] == 0:
        raise RuntimeError(f"The downloaded image/annotation counts do not match: {counts}")
    (args.dest / "DATASET_INFO.md").write_text(
        "# SROIE corrected mirror subset\n\n"
        f"Source: {SOURCE_URL}\n\n"
        f"Downloaded files: {json.dumps(counts, sort_keys=True)}. The mirror README states the official challenge has 1,000 images; this repository's corrected `data/` tree contains a smaller 626-image subset. "
        "Files include receipt JPEGs, OCR text-box CSVs, and key-field JSON. The upstream repository publishes an MIT license for its software; that does not conclusively establish a license for the receipt scans or grant broader image rights. "
        "This copy is held locally for the requested nonprofit research evaluation; do not redistribute it unless dataset/image terms are verified with the challenge organizers.\n",
        encoding="utf-8",
    )
    print(f"Downloaded SROIE mirror subset to {args.dest}: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

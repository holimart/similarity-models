"""Download the publicly linked TextZoom real-image test LMDB files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocr_lab.data_paths import source_dataset

FILES = {
    "easy": ("1PHaoh-VdLBk1NgjsNag21rSpQeJKpurr", 12_600_000),
    "hard": ("1751l97_mFPf0G-C9PeNiVlzNttUrsCUD", 11_100_000),
    "medium": ("1KOAisCLPcw4cuar7d2GHNJQpfYijjcFB", 5_500_000),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=source_dataset("textzoom/test"))
    args = parser.parse_args()
    args.dest.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    for difficulty, (file_id, expected_approx) in FILES.items():
        target = args.dest / f"{difficulty}.mdb"
        if target.exists() and target.stat().st_size > 1024:
            print(f"already present: {target} ({target.stat().st_size:,} bytes)")
            continue
        response = session.get(
            "https://drive.google.com/uc",
            params={"export": "download", "id": file_id},
            stream=True,
            timeout=(20, 120),
        )
        response.raise_for_status()
        if "text/html" in response.headers.get("Content-Type", ""):
            page = response.text
            action = re.search(r'<form[^>]+action="([^"]+)"', page)
            fields = dict(re.findall(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"', page))
            response.close()
            if not action or "confirm" not in fields:
                raise RuntimeError(f"Google Drive returned an unrecognized confirmation page for {difficulty}")
            response = session.get(action.group(1), params=fields, stream=True, timeout=(20, 180))
            response.raise_for_status()
            if "text/html" in response.headers.get("Content-Type", ""):
                response.close()
                raise RuntimeError(f"Google Drive confirmation did not yield the {difficulty} dataset")
        temporary = target.with_suffix(".mdb.part")
        size = 0
        with temporary.open("wb") as output:
            for chunk in response.iter_content(1024 * 512):
                if chunk:
                    size += len(chunk)
                    output.write(chunk)
        response.close()
        if size < expected_approx * 0.5:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"{difficulty} download too small ({size:,} bytes), expected roughly {expected_approx:,}")
        temporary.replace(target)
        print(f"downloaded {target} ({size:,} bytes)")

    (args.dest / "DATASET_INFO.md").write_text(
        "# TextZoom test set (LMDB)\n\n"
        "Official project: https://github.com/WenjiaWang0312/TextZoom\n"
        "Official data link: https://drive.google.com/drive/folders/1WRVy-fC_KrembPkaI68uqQ9wyaptibMh\n\n"
        "This folder contains the public test split's easy/medium/hard LMDBs (low-resolution and high-resolution word crops with text labels). "
        "The source repository links the data but does not provide a clear dataset-specific redistribution license. This local copy is for the requested private evaluation workspace; do not redistribute it without confirming the terms. "
        "It is scene-text data, not a receipt dataset.\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

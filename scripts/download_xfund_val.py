"""Download official XFUND v1.0 validation images/labels for noncommercial research."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocr_lab.data_paths import source_dataset

LANGUAGES = ("de", "es", "fr", "it", "ja", "pt", "zh")
# Official release tag (immutable by convention). Verify the tag and file
# checksums when a reproducible re-download matters.
TAG = "v1.0"
RELEASE = f"https://github.com/doc-analysis/XFUND/releases/download/{TAG}"


def safe_destination(name: str, root: Path) -> Path | None:
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    return root.joinpath(*relative.parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=source_dataset("xfund-val"))
    args = parser.parse_args()
    args.dest.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    for language in LANGUAGES:
        zip_path = args.dest / f".{language}.val.zip.part"
        json_path = args.dest / f"{language}.val.json"
        if not json_path.exists():
            response = session.get(f"{RELEASE}/{language}.val.json", timeout=(30, 120))
            response.raise_for_status()
            json_path.write_bytes(response.content)
        language_dir = args.dest / language
        if not language_dir.is_dir() or not any(language_dir.rglob("*.jpg")):
            response = session.get(f"{RELEASE}/{language}.val.zip", timeout=(30, 240), stream=True)
            response.raise_for_status()
            with zip_path.open("wb") as output:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        output.write(chunk)
            response.close()
            with zipfile.ZipFile(zip_path) as archive:
                for item in archive.infolist():
                    if item.is_dir():
                        continue
                    target = safe_destination(item.filename, args.dest / language)
                    if target is None:
                        raise RuntimeError(f"Unsafe path in XFUND archive: {item.filename}")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as source, target.open("wb") as dest:
                        while chunk := source.read(1024 * 1024):
                            dest.write(chunk)
            zip_path.unlink(missing_ok=True)
        print(f"prepared XFUND {language}.val")

    info = args.dest / "DATASET_INFO.md"
    info.write_text(
        "# XFUND v1.0 validation images\n\n"
        "Source: https://github.com/doc-analysis/XFUND/releases/tag/v1.0\n"
        "License stated by the project: CC BY-NC-SA 4.0. Preserve attribution and share-alike terms; noncommercial use only. "
        "This validation subset covers seven languages (German, Spanish, French, Italian, Japanese, Portuguese, Chinese), "
        "not Czech or English receipts. It is a multilingual form-understanding dataset and a supplemental OCR/layout test, not receipt data.\n",
        encoding="utf-8",
    )
    print(f"XFUND validation data saved under {args.dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

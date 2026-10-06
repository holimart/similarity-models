"""Download every dataset this repository can fetch, then print next steps.

This is a convenience wrapper around the per-dataset downloaders so a fresh
checkout can be made reproducible in one command. Datasets are written under
``$DATASETS_ROOT/source`` (configurable via ``--datasets-root``). Datasets that
require manual access (COCO, the RAM++ checkpoint) are reported, not fetched.

Example::

    set -a; . ./.env; set +a
    python scripts/download_datasets.py

After downloading, verify the workspace against the committed manifest::

    python scripts/generate_manifest.py --check datasets.manifest.json --base "$DATASETS_ROOT"
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
sys.path.insert(0, str(REPO_ROOT))

from ocr_lab.data_paths import datasets_root  # noqa: E402

STEPS: list[tuple[str, list[str]]] = [
    ("CORD-v2 receipts (CC BY 4.0 project terms)", ["download_cord.py"]),
    ("SROIE corrected mirror subset (local-only images)", ["download_sroie_mirror.py"]),
    ("TextZoom test LMDBs (scene text, no clear data license)", ["download_textzoom_test.py"]),
    ("XFUND v1.0 validation (CC BY-NC-SA 4.0)", ["download_xfund_val.py"]),
]

MANUAL_STEPS = [
    "COCO 2017: download val2017/ and annotations_trainval2017.zip from "
    "https://cocodataset.org/#download and extract under $COCO_ROOT.",
    "RAM++ checkpoint: clone https://github.com/xinyu1205/recognize-anything and "
    "download ram_plus_swin_large_14m.pth; set RAM_REPO and RAM_CHECKPOINT in .env.",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--datasets-root", type=Path, default=datasets_root(), help="Workspace root for downloaded data")
    parser.add_argument("--only", nargs="*", help="Subset of script names to run, e.g. download_cord.py")
    args = parser.parse_args()
    root = args.datasets_root.expanduser()
    print(f"Datasets root: {root}\n")

    failures: list[str] = []
    for label, command in STEPS:
        script_name = command[0]
        if args.only and script_name not in args.only:
            continue
        print(f"==> {label}")
        result = subprocess.run([sys.executable, str(SCRIPTS / script_name), *command[1:]], check=False)
        if result.returncode != 0:
            failures.append(script_name)
        print()

    print("Manual steps (network/registration required, not automated):")
    for item in MANUAL_STEPS:
        print(f"  - {item}")

    if failures:
        print(f"\nCompleted with failures: {', '.join(failures)}")
        return 1
    print("\nAll automated downloads finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

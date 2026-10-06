"""Generate or verify a SHA-256 manifest for local dataset/model workspaces.

The datasets and model weights used by this repository live outside version
control (see README). This script records a stable, reviewable fingerprint of
whatever is present so a run can be reproduced or checked without publishing
the bytes. It both writes a manifest and (with ``--check``) verifies that a
workspace still matches a committed manifest.

Examples
--------
Record the receipt datasets under the shared workspace::

    python scripts/generate_manifest.py \
        --root "$DATASETS_ROOT/source" \
        --output datasets.manifest.json \
        --base "$DATASETS_ROOT"

Verify the same tree later::

    python scripts/generate_manifest.py --check datasets.manifest.json \
        --base "$DATASETS_ROOT"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterator

CHUNK = 1024 * 1024


def load_env() -> None:
    """Load .env so shell runs can resolve $DATASETS_ROOT like the code does."""
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


EXCLUDE_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "__pycache__"}


def iter_files(root: Path, exclude: set[str]) -> Iterator[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.is_symlink():
            continue
        if path.name in exclude or path.name.startswith(".env"):
            continue
        if EXCLUDE_DIRS.intersection(path.relative_to(root).parts):
            continue
        yield path


def build_manifest(root: Path, base: Path | None, exclude: set[str]) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for path in iter_files(root, exclude):
        relative = path.relative_to(base) if base else path.relative_to(root)
        files[relative.as_posix()] = {
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return {
        "root": str(root),
        "base": str(base) if base else None,
        "file_count": len(files),
        "total_bytes": sum(item["size"] for item in files.values()),
        "files": files,
    }


def verify_manifest(manifest_path: Path, base: Path | None) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    missing: list[str] = []
    changed: list[str] = []
    for relative, expected in manifest["files"].items():
        path = (base / relative) if base else Path(relative)
        if not path.is_file():
            missing.append(relative)
            continue
        if path.stat().st_size != expected["size"] or sha256_file(path) != expected["sha256"]:
            changed.append(relative)
    if missing:
        print(f"missing ({len(missing)}):")
        for name in missing[:20]:
            print(f"  {name}")
    if changed:
        print(f"changed ({len(changed)}):")
        for name in changed[:20]:
            print(f"  {name}")
    if missing or changed:
        print(f"Manifest check FAILED: {len(missing)} missing, {len(changed)} changed")
        return 1
    print(f"Manifest OK: {manifest['file_count']} files match {manifest_path}")
    return 0


def main() -> int:
    load_env()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, help="Directory to fingerprint (write mode)")
    parser.add_argument("--output", type=Path, help="Manifest path to write (write mode)")
    parser.add_argument("--check", type=Path, help="Existing manifest to verify (read mode)")
    parser.add_argument("--base", type=Path, help="Base for relative paths; defaults to --root for writing, or the manifest's recorded base when checking")
    parser.add_argument("--exclude", nargs="*", default=[".DS_Store", "Thumbs.db"], help="File names to skip")
    args = parser.parse_args()
    exclude = set(args.exclude)

    if args.check:
        base = args.base
        if base is None:
            recorded = json.loads(args.check.read_text(encoding="utf-8")).get("base")
            base = Path(recorded) if recorded else None
        return verify_manifest(args.check, base)

    if not args.root or not args.output:
        parser.error("write mode requires --root and --output")
    base = args.base or args.root
    manifest = build_manifest(args.root, base, exclude)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}: {manifest['file_count']} files, {manifest['total_bytes']:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

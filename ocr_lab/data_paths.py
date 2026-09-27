"""Resolve local dataset locations from the shared workspace configuration."""

from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _configured_value(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    env_file = REPO_ROOT / ".env"
    if not env_file.is_file():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, candidate = stripped.split("=", 1)
        if key.strip() == name:
            return candidate.strip().strip("\"'") or None
    return None


def datasets_root() -> Path:
    """Return the shared dataset workspace, preserving the legacy local fallback."""
    configured = _configured_value("DATASETS_ROOT")
    if configured:
        return Path(configured).expanduser()
    coco_root = _configured_value("COCO_ROOT")
    if coco_root:
        return Path(coco_root).expanduser().parent
    return REPO_ROOT / "data"


def source_dataset(name: str) -> Path:
    """Resolve a source dataset, supporting the pre-migration repository layout."""
    source = datasets_root() / "source" / name
    if source.exists() or datasets_root() != REPO_ROOT / "data":
        return source
    return REPO_ROOT / "data" / name


def derived_dataset(name: str) -> Path:
    """Resolve a generated dataset export."""
    derived = datasets_root() / "derived" / name
    if derived.exists() or datasets_root() != REPO_ROOT / "data":
        return derived
    return REPO_ROOT / "data" / name


def manual_annotations_dir() -> Path:
    """Resolve the local manual annotation directory."""
    manual = datasets_root() / "manual" / "receipt_annotations"
    if manual.exists() or datasets_root() != REPO_ROOT / "data":
        return manual
    return REPO_ROOT / "data" / "manual_receipt_annotations"

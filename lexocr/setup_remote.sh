#!/usr/bin/env bash
# Install a self-contained OCR virtualenv for lexocr.
#
# Usage:
#   setup_remote.sh WORKSPACE [PYTHON] [--cpu]
#
#   WORKSPACE   target directory (or set $LEXOCR_WORKSPACE); venv at $WORKSPACE/venv-ocr
#   PYTHON      interpreter to build the venv with (default: python3)
#   --cpu       install CPU onnxruntime instead of onnxruntime-gpu
#
# Extra environment:
#   LEXOCR_SRC    if set, `pip install "$LEXOCR_SRC"` (a path/URL to this package)
#   OCR_CPU_THREADS  forwarded at runtime (not used here)
#
# Everything (venv, uv cache, pip cache) lives under WORKSPACE — never $HOME.
# Idempotent: safe to re-run.

set -euo pipefail

WORKSPACE="${1:-${LEXOCR_WORKSPACE:-}}"
if [ -z "$WORKSPACE" ]; then
    echo "usage: setup_remote.sh WORKSPACE [PYTHON] [--cpu]" >&2
    exit 2
fi
shift || true

PYTHON="python3"
DEVICE="gpu"
for arg in "$@"; do
    case "$arg" in
        --cpu) DEVICE="cpu" ;;
        --*) echo "unknown option: $arg" >&2; exit 2 ;;
        *) PYTHON="$arg" ;;
    esac
done

mkdir -p "$WORKSPACE"
WORKSPACE="$(cd "$WORKSPACE" && pwd)"
VENV="$WORKSPACE/venv-ocr"

# Keep all caches inside the workspace so nothing is written to $HOME.
export UV_CACHE_DIR="$WORKSPACE/.uv-cache"
export PIP_CACHE_DIR="$WORKSPACE/.pip-cache"
export XDG_CACHE_HOME="$WORKSPACE/.cache"
export XDG_CONFIG_HOME="$WORKSPACE/.config"
export XDG_DATA_HOME="$WORKSPACE/.local/share"
mkdir -p "$UV_CACHE_DIR" "$PIP_CACHE_DIR" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME"

echo "workspace: $WORKSPACE"
echo "venv:      $VENV"
echo "device:    $DEVICE"

# --- create venv (uv preferred, else stdlib venv) ---
if [ -x "$VENV/bin/python" ]; then
    echo "venv already exists; reusing"
elif command -v uv >/dev/null 2>&1; then
    uv venv --python "$PYTHON" "$VENV"
else
    "$PYTHON" -m venv "$VENV"
fi

VPY="$VENV/bin/python"

# --- install deps (uv preferred, else pip) ---
case "$DEVICE" in
    cpu) ORT_PKG="onnxruntime>=1.18" ;;
    *)   ORT_PKG="onnxruntime-gpu>=1.18" ;;
esac
DEPS=("rapidocr>=3.9,<4" "$ORT_PKG" "pymupdf>=1.24")

install_pkgs() {
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "$VPY" "$@"
    else
        "$VPY" -m pip install --upgrade pip
        "$VPY" -m pip install "$@"
    fi
}

echo "installing deps: ${DEPS[*]}"
install_pkgs "${DEPS[@]}"

if [ -n "${LEXOCR_SRC:-}" ]; then
    echo "installing lexocr from: $LEXOCR_SRC"
    install_pkgs "$LEXOCR_SRC"
fi

echo
echo "done. activate with:"
echo "    source \"$VENV/bin/activate\""
echo "probe with:"
echo "    \"$VPY\" -m lexocr probe"

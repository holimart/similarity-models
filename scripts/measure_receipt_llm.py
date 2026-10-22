r"""Measure token usage and cost of receipt/invoice extraction engines.

The script sends each document to a vision LLM (image, OCR text, or both),
records the provider-reported token usage, and writes a comparable summary.
It also materialises per-document extraction JSON so a corpus can be turned
into an "as good as the LLM can do" ground-truth layer.

Examples
--------
Measure image-only extraction for both default models::

    python3 scripts/measure_receipt_llm.py --images /path/to/receipts \
        --input-mode image --models deepseek/deepseek-v4.1-flash z-ai/glm-5.3-flash

Measure the incremental cost of adding OCR text to the image::

    python3 scripts/measure_receipt_llm.py --images /path/to/receipts \
        --input-mode image both --out-dir runs/llm-extraction

Use the local opencode CLI instead of a direct OpenRouter call::

    python3 scripts/measure_receipt_llm.py --images /path/to/receipts \
        --backend opencode --models openrouter/deepseek/deepseek-v4.1-flash

No image or OCR text is uploaded until the script is run; OCR is performed
locally and cached under the output directory.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocr_lab.receipt_extraction import (  # noqa: E402
    DEFAULT_PRICING,
    PROMPT_VERSION,
    build_consensus,
    build_prompt,
    cost_from_usage,
    critical_values,
    normalize_usage,
    parse_json_object,
)

DEFAULT_MODELS = ("deepseek/deepseek-v4.1-flash", "z-ai/glm-5.3-flash")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".pdf"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "model"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def collect_manifest(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.manifest:
        rows = read_jsonl(args.manifest)
        base = args.manifest.parent
    elif args.images:
        base = args.images
        rows = []
        for path in sorted(args.images.rglob("*")):
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                relative = path.relative_to(args.images)
                rows.append(
                    {
                        "id": relative.with_suffix("").as_posix().replace("/", "-"),
                        "image": path.as_posix(),
                        "split": "unspecified",
                    }
                )
    else:
        raise SystemExit("Provide --images or --manifest")

    prepared: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        image = Path(row.get("image") or "")
        if not image.is_absolute():
            candidate = base / image
            image = candidate if candidate.exists() else image
        if not image.is_file():
            print(f"warning: missing image {image}", file=sys.stderr)
            continue
        prepared.append(
            {
                "id": str(row.get("id") or row.get("row_id") or image.stem or index),
                "image": image.resolve().as_posix(),
                "split": row.get("split") or "unspecified",
                "ground_truth": row.get("ground_truth"),
            }
        )
    if args.offset:
        prepared = prepared[args.offset :]
    if args.limit:
        prepared = prepared[: args.limit]
    if not prepared:
        raise SystemExit("No documents selected")
    return prepared


def prepare_image(
    source: Path,
    cache_dir: Path,
    max_side: int,
    quality: int,
) -> dict[str, Any]:
    """Return a normalized JPEG path and reproducible image metadata."""
    source_bytes = source.read_bytes()
    source_hash = sha256_bytes(source_bytes)
    key = sha256_bytes(
        f"{source_hash}|{max_side}|{quality}".encode("ascii")
    )
    processed_dir = cache_dir / "images"
    processed_dir.mkdir(parents=True, exist_ok=True)
    output = processed_dir / f"{key[:24]}.jpg"
    original_width = original_height = None

    if output.is_file() and output.stat().st_size:
        try:
            with Image.open(output) as existing:
                width, height = existing.size
            return {
                "path": output.as_posix(),
                "source": source.as_posix(),
                "source_sha256": source_hash,
                "sha256": sha256_bytes(output.read_bytes()),
                "width": width,
                "height": height,
                "bytes": output.stat().st_size,
                "source_bytes": len(source_bytes),
                "source_width": None,
                "source_height": None,
                "source_type": "pdf" if source.suffix.lower() == ".pdf" else "image",
            }
        except OSError:
            output.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory(prefix="receipt-image-") as temporary:
        image_path = source
        if source.suffix.lower() == ".pdf":
            if not shutil.which("pdftoppm"):
                raise RuntimeError("PDF input requires pdftoppm (poppler-utils)")
            prefix = Path(temporary) / "page"
            subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    "1",
                    "-l",
                    "1",
                    "-r",
                    "200",
                    "-png",
                    "-singlefile",
                    source.as_posix(),
                    prefix.as_posix(),
                ],
                check=True,
                capture_output=True,
            )
            image_path = prefix.with_suffix(".png")
        with Image.open(image_path) as opened:
            original_width, original_height = opened.size
            image = ImageOps.exif_transpose(opened).convert("RGB")
            if max_side and max(image.size) > max_side:
                image.thumbnail((max_side, max_side), Image.LANCZOS)
            image.save(output, format="JPEG", quality=quality, optimize=True)
            width, height = image.size

    return {
        "path": output.as_posix(),
        "source": source.as_posix(),
        "source_sha256": source_hash,
        "sha256": sha256_bytes(output.read_bytes()),
        "width": width,
        "height": height,
        "bytes": output.stat().st_size,
        "source_bytes": len(source_bytes),
        "source_width": original_width,
        "source_height": original_height,
        "source_type": "pdf" if source.suffix.lower() == ".pdf" else "image",
    }


def _tesseract_version() -> str:
    try:
        result = subprocess.run(
            ["tesseract", "--version"], capture_output=True, text=True, timeout=30
        )
        return (result.stdout or result.stderr).splitlines()[0] if result.stdout or result.stderr else "unknown"
    except Exception:
        return "unknown"


def run_tesseract(image: Path, lang: str, psm: int) -> dict[str, Any]:
    if not shutil.which("tesseract"):
        raise RuntimeError("tesseract is not installed")
    started = time.perf_counter()
    result = subprocess.run(
        ["tesseract", image.as_posix(), "stdout", "-l", lang, "--psm", str(psm)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"tesseract failed: {result.stderr.strip()[:500]}")
    text = "\n".join(line.strip() for line in result.stdout.splitlines() if line.strip())
    return {
        "text": text,
        "seconds": time.perf_counter() - started,
        "backend": "tesseract",
        "version": _tesseract_version(),
        "lang": lang,
        "psm": psm,
    }


def run_rapidocr(image: Path, lang: str) -> dict[str, Any]:
    try:
        from ocr_lab.core import LocalOCRHarness, OCRConfig
    except ImportError as exc:
        raise RuntimeError("RapidOCR backend is not installed; see requirements-ocr.txt") from exc
    config = OCRConfig(harness="rapidocr", lang=lang, use_orientation=True)
    harness = LocalOCRHarness(config)
    started = time.perf_counter()
    records, metadata = harness(image)
    seconds = time.perf_counter() - started
    positioned = []
    for record in records:
        polygon = record.get("polygon") or []
        y = sum(point[1] for point in polygon) / len(polygon) if polygon else 0.0
        x = min((point[0] for point in polygon), default=0.0)
        positioned.append((round(y / 10) * 10, x, str(record.get("text") or "")))
    positioned.sort()
    text = "\n".join(item[2] for item in positioned if item[2].strip())
    return {
        "text": text,
        "seconds": seconds,
        "backend": "rapidocr",
        "version": "rapidocr",
        "lang": lang,
        "metadata": metadata,
    }


def load_precomputed_ocr(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in read_jsonl(path):
        text = row.get("text") or row.get("ocr_text") or row.get("ground_truth_text")
        if text is None:
            continue
        for key in ("id", "row_id", "image"):
            value = row.get(key)
            if value is not None:
                mapping[str(value)] = str(text)
    return mapping


def ocr_document(
    document: dict[str, Any],
    processed: dict[str, Any],
    args: argparse.Namespace,
    cache_dir: Path,
) -> dict[str, Any]:
    if args.precomputed_ocr:
        text = args.precomputed_ocr.get(document["id"]) or args.precomputed_ocr.get(
            document["image"]
        )
        if text is None:
            stem = Path(document["image"]).stem
            text = args.precomputed_ocr.get(stem)
        if text is None:
            raise RuntimeError(f"no precomputed OCR text for {document['id']}")
        return {"text": text, "seconds": 0.0, "backend": "precomputed", "version": None, "cached": True}

    if args.ocr_backend == "none":
        raise RuntimeError("OCR is required for this input mode but --ocr-backend is none")

    key_material = (
        f"{processed['sha256']}|{args.ocr_backend}|{args.ocr_lang}|{args.ocr_psm}"
    )
    key = sha256_bytes(key_material.encode("ascii"))
    cache_path = cache_dir / "ocr" / f"{key[:24]}.json"
    if cache_path.is_file() and not args.force:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        cached["cached"] = True
        return cached

    if args.ocr_backend == "tesseract":
        result = run_tesseract(Path(processed["path"]), args.ocr_lang, args.ocr_psm)
    elif args.ocr_backend == "rapidocr":
        result = run_rapidocr(Path(processed["path"]), args.ocr_lang)
    else:
        raise RuntimeError(f"unknown OCR backend {args.ocr_backend!r}")
    result["cached"] = False
    result["key"] = key
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def data_url(path: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def resolve_api_key(args: argparse.Namespace) -> str:
    if args.api_key:
        return args.api_key
    value = os.environ.get(args.api_key_env)
    if value:
        return value.strip()
    if args.no_auth_from_opencode:
        raise SystemExit(
            f"Set {args.api_key_env} or pass --api-key (OpenCode credential lookup is disabled)"
        )
    for auth_path in (
        Path.home() / ".local" / "share" / "opencode" / "auth.json",
        Path.home() / "Library" / "Application Support" / "opencode" / "auth.json",
    ):
        if not auth_path.is_file():
            continue
        try:
            auth = json.loads(auth_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        entry = auth.get(args.auth_provider) or {}
        key = entry.get("key") if isinstance(entry, dict) else None
        if key:
            print(
                f"using {args.auth_provider} credential from {auth_path} "
                f"(key not printed)",
                file=sys.stderr,
            )
            return key
    raise SystemExit(
        f"No API key found. Set {args.api_key_env} or pass --api-key; "
        f"checked OpenCode auth at ~/.local/share/opencode/auth.json"
    )


def request_openrouter(
    model: str,
    prompt: str,
    image_path: Path | None,
    args: argparse.Namespace,
) -> dict[str, Any]:
    key = args.api_key_value
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    if image_path:
        content.append({"type": "image_url", "image_url": {"url": data_url(image_path)}})
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    if args.reasoning != "auto":
        body["reasoning"] = (
            {"enabled": False} if args.reasoning == "disabled" else {"effort": args.reasoning}
        )
    if args.structured_output:
        body["response_format"] = {"type": "json_object"}
    if args.provider_order:
        body["provider"] = {
            "order": list(args.provider_order),
            "allow_fallbacks": args.allow_fallbacks,
        }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if "openrouter.ai" in args.base_url:
        headers["HTTP-Referer"] = args.referer
        headers["X-Title"] = args.title

    attempts: list[dict[str, Any]] = []
    last_error: str | None = None
    attempt = 0
    while attempt <= args.max_retries:
        attempt += 1
        started = time.perf_counter()
        request = urllib.request.Request(
            args.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=args.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            latency = time.perf_counter() - started
            choice = (payload.get("choices") or [{}])[0] or {}
            message = choice.get("message") or {}
            text = message.get("content") or ""
            usage = normalize_usage(payload.get("usage"))
            usage["list_cost_usd"] = cost_from_usage(usage, args.pricing.get(model))
            if not usage["cost_usd"]:
                usage["cost_usd"] = usage["list_cost_usd"]
            attempts.append(
                {
                    "attempt": attempt,
                    "latency_seconds": latency,
                    "usage": usage,
                    "finish_reason": choice.get("finish_reason"),
                }
            )
            last_error = None
            return {
                "text": text,
                "usage": usage,
                "attempts": attempts,
                "finish_reason": choice.get("finish_reason"),
                "provider_name": payload.get("provider"),
                "response_model": payload.get("model"),
                "reasoning_forced": "reasoning" not in body and args.reasoning == "disabled",
            }
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", "replace")
            latency = time.perf_counter() - started
            attempts.append(
                {
                    "attempt": attempt,
                    "latency_seconds": latency,
                    "usage": normalize_usage(None),
                    "http_status": exc.code,
                    "error": body_text[:1000],
                }
            )
            last_error = f"HTTP {exc.code}: {body_text[:500]}"
            mandatory_reasoning = (
                exc.code == 400
                and "reasoning" in body_text.casefold()
                and "mandatory" in body_text.casefold()
                and "reasoning" in body
            )
            if mandatory_reasoning:
                if body.get("reasoning") != {"effort": "low"}:
                    body["reasoning"] = {"effort": "low"}
                    print(
                        f"{model}: provider requires reasoning; retrying with low effort",
                        file=sys.stderr,
                    )
                else:
                    body.pop("reasoning", None)
                    print(
                        f"{model}: low reasoning rejected; retrying with model default",
                        file=sys.stderr,
                    )
                continue
            if exc.code in {408, 409, 429, 500, 502, 503, 504} and attempt <= args.max_retries:
                time.sleep(min(2**attempt + random.random(), 30))
                continue
            break
        except Exception as exc:  # network errors, timeouts, JSON decode
            latency = time.perf_counter() - started
            attempts.append(
                {
                    "attempt": attempt,
                    "latency_seconds": latency,
                    "usage": normalize_usage(None),
                    "error": str(exc)[:1000],
                }
            )
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt <= args.max_retries:
                time.sleep(min(2**attempt + random.random(), 30))
                continue
            break

    total_usage = _sum_usage(attempts)
    return {
        "text": "",
        "usage": total_usage,
        "attempts": attempts,
        "finish_reason": None,
        "error": last_error,
    }


def _sum_usage(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    total = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "reasoning_tokens": 0,
        "cached_tokens": 0,
        "image_tokens": 0,
        "cost_usd": 0.0,
        "list_cost_usd": 0.0,
    }
    for attempt in attempts:
        usage = attempt.get("usage") or {}
        for key in total:
            total[key] += usage.get(key) or 0
    return total


def _opencode_version() -> str:
    try:
        result = subprocess.run(
            ["opencode", "--version"], capture_output=True, text=True, timeout=30
        )
        return (result.stdout or result.stderr).strip()
    except Exception:
        return "unknown"


def _parse_opencode_events(stdout: str) -> dict[str, Any]:
    text_parts: list[str] = []
    usages: list[dict[str, Any]] = []
    errors: list[str] = []
    steps = 0
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "text":
            part = event.get("part") or {}
            if part.get("text"):
                text_parts.append(str(part["text"]))
        elif event.get("type") == "step_finish":
            steps += 1
            part = event.get("part") or {}
            tokens = part.get("tokens") or {}
            cache = tokens.get("cache") or {}
            usages.append(
                {
                    "prompt_tokens": int(tokens.get("input") or 0),
                    "completion_tokens": int(tokens.get("output") or 0),
                    "total_tokens": int(tokens.get("total") or 0),
                    "reasoning_tokens": int(tokens.get("reasoning") or 0),
                    "cached_tokens": int(cache.get("read") or 0),
                    "image_tokens": 0,
                    "cost_usd": float(part.get("cost") or 0.0),
                }
            )
        elif event.get("type") == "error":
            errors.append(json.dumps(event.get("error") or {}))
    return {
        "text": "".join(text_parts),
        "usage": _sum_usage([{"usage": usage} for usage in usages]),
        "steps": steps,
        "errors": errors,
    }


def opencode_baseline(
    model: str, args: argparse.Namespace, cache_dir: Path
) -> dict[str, Any] | None:
    if not args.calibrate_opencode:
        return None
    cache_path = cache_dir / "opencode_baseline.json"
    cache = {}
    if cache_path.is_file():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}
    key = f"{model}|{_opencode_version()}"
    if key in cache:
        return cache[key]
    cmd = [
        "opencode",
        "run",
        "-m",
        model,
        "--format",
        "json",
        "--dir",
        args.workdir,
        "Reply with OK. Do not call tools.",
    ]
    started = time.perf_counter()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=args.timeout, cwd=args.workdir
        )
        parsed = _parse_opencode_events(result.stdout)
        baseline = {
            "usage": parsed["usage"],
            "seconds": time.perf_counter() - started,
            "version": _opencode_version(),
        }
        cache[key] = baseline
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        return baseline
    except Exception as exc:
        print(f"warning: opencode baseline failed for {model}: {exc}", file=sys.stderr)
        return None


def request_opencode(
    model: str,
    prompt: str,
    image_path: Path | None,
    args: argparse.Namespace,
    cache_dir: Path,
) -> dict[str, Any]:
    baseline = opencode_baseline(model, args, cache_dir)
    cmd = [
        "opencode",
        "run",
        "-m",
        model,
        "--format",
        "json",
        "--dir",
        args.workdir,
    ]
    cmd.append(prompt)
    if image_path:
        cmd.extend(["-f", image_path.as_posix()])
    attempts: list[dict[str, Any]] = []
    last_error: str | None = None
    for attempt in range(1, args.max_retries + 2):
        started = time.perf_counter()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=args.timeout, cwd=args.workdir
            )
            latency = time.perf_counter() - started
            parsed = _parse_opencode_events(result.stdout)
            usage = parsed["usage"]
            if parsed["errors"]:
                last_error = "; ".join(parsed["errors"])[:1000]
            elif not parsed["steps"]:
                stderr_tail = (result.stderr or "").strip().splitlines()[-3:]
                last_error = "opencode produced no steps" + (
                    ": " + " | ".join(stderr_tail) if stderr_tail else ""
                )
            if baseline:
                for key in (
                    "prompt_tokens",
                    "completion_tokens",
                    "total_tokens",
                    "reasoning_tokens",
                    "cached_tokens",
                    "cost_usd",
                ):
                    usage[key] = max(0.0, usage[key] - baseline["usage"].get(key, 0))
            usage["list_cost_usd"] = cost_from_usage(usage, args.pricing.get(model))
            attempts.append(
                {
                    "attempt": attempt,
                    "latency_seconds": latency,
                    "usage": usage,
                    "steps": parsed["steps"],
                    "error": last_error,
                }
            )
            return {
                "text": parsed["text"],
                "usage": usage,
                "attempts": attempts,
                "steps": parsed["steps"],
                "baseline": baseline,
                "error": last_error,
            }
        except Exception as exc:
            latency = time.perf_counter() - started
            attempts.append(
                {
                    "attempt": attempt,
                    "latency_seconds": latency,
                    "usage": normalize_usage(None),
                    "error": str(exc)[:1000],
                }
            )
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt <= args.max_retries:
                time.sleep(min(2**attempt + random.random(), 30))
    return {
        "text": "",
        "usage": _sum_usage(attempts),
        "attempts": attempts,
        "baseline": baseline,
        "error": last_error,
    }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = min(len(ordered) - 1, max(0, int(round(fraction * (len(ordered) - 1)))))
    return ordered[position]


def deduplicate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one row per model/mode/document, preferring a later success."""
    latest: dict[tuple[str, str, str, str, bool], dict[str, Any]] = {}
    for row in rows:
        key = (
            str(row.get("model")),
            str(row.get("input_mode")),
            str(row.get("id")),
            str(row.get("prompt_version")),
            bool(row.get("audit")),
        )
        previous = latest.get(key)
        if previous is None:
            latest[key] = row
        elif previous.get("error") and not row.get("error"):
            latest[key] = row
        elif not previous.get("error") and row.get("error"):
            continue
        else:
            latest[key] = row
    return list(latest.values())


def summarize(rows: list[dict[str, Any]], pricing: dict[str, dict[str, float]]) -> dict[str, Any]:
    raw_rows = rows
    rows = deduplicate_rows(rows)
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(
            (
                str(row.get("model")),
                str(row.get("input_mode")),
                str(row.get("provider_name") or row.get("provider") or "unknown"),
            ),
            [],
        ).append(row)

    summary: dict[str, Any] = {
        "generated_at": now_iso(),
        "prompt_version": PROMPT_VERSION,
        "n_rows_raw": len(raw_rows),
        "n_rows": len(rows),
        "n_errors": sum(1 for row in rows if row.get("error")),
        "total_cost_all_attempts_usd": sum(
            float((row.get("usage") or {}).get("cost_usd") or 0.0) for row in raw_rows
        ),
        "error_counts": {},
        "models": {},
    }
    for row in rows:
        if row.get("error"):
            key = f"{row.get('model')}::{row.get('input_mode')}"
            summary["error_counts"][key] = summary["error_counts"].get(key, 0) + 1
    for (model, mode, provider_name), group in sorted(groups.items()):
        successful = [row for row in group if not row.get("error")]
        if not successful:
            continue
        costs = [float(row["usage"]["cost_usd"]) for row in successful]
        list_costs = [float(row["usage"].get("list_cost_usd") or 0.0) for row in successful]
        prompt = [int(row["usage"]["prompt_tokens"]) for row in successful]
        completion = [int(row["usage"]["completion_tokens"]) for row in successful]
        reasoning = [int(row["usage"]["reasoning_tokens"]) for row in successful]
        attempts = [int(row.get("attempts_count") or 1) for row in group]
        avg_cost = statistics.mean(costs) if costs else 0.0
        avg_list_cost = statistics.mean(list_costs) if list_costs else 0.0
        model_summary = summary["models"].setdefault(model, {"modes": {}})
        key = f"{provider_name}::{mode}"
        model_summary["modes"][key] = {
            "provider": provider_name,
            "n": len(group),
            "n_success": len(successful),
            "json_valid_rate": (
                sum(1 for row in group if row.get("json_valid")) / len(group) if group else 0.0
            ),
            "avg_attempts": statistics.mean(attempts) if attempts else 0.0,
            "avg_prompt_tokens": statistics.mean(prompt) if prompt else 0.0,
            "p50_prompt_tokens": statistics.median(prompt) if prompt else 0.0,
            "p95_prompt_tokens": percentile([float(v) for v in prompt], 0.95),
            "avg_completion_tokens": statistics.mean(completion) if completion else 0.0,
            "p50_completion_tokens": statistics.median(completion) if completion else 0.0,
            "p95_completion_tokens": percentile([float(v) for v in completion], 0.95),
            "avg_reasoning_tokens": statistics.mean(reasoning) if reasoning else 0.0,
            "avg_cost_usd": avg_cost,
            "avg_list_cost_usd": avg_list_cost,
            "p50_cost_usd": statistics.median(costs) if costs else 0.0,
            "p95_cost_usd": percentile(costs, 0.95),
            "total_cost_usd": sum(float(row["usage"]["cost_usd"]) for row in group),
            "cost_per_1k_usd": avg_cost * 1_000,
            "cost_per_100k_usd": avg_cost * 100_000,
            "cost_per_1m_usd": avg_cost * 1_000_000,
            "list_cost_per_1k_usd": avg_list_cost * 1_000,
            "list_cost_per_100k_usd": avg_list_cost * 100_000,
            "list_cost_per_1m_usd": avg_list_cost * 1_000_000,
            "pricing": pricing.get(model),
        }
    # Paired incremental cost: compare modes on the same document, so image
    # difficulty and output-length variance do not masquerade as modality cost.
    paired: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = {}
    for row in rows:
        if row.get("error"):
            continue
        key = (
            str(row.get("model")),
            str(row.get("provider_name") or "unknown"),
            str(row.get("id")),
        )
        paired.setdefault(key, {})[str(row.get("input_mode"))] = row

    pair_defs = {
        "ocr_added_to_image": ("image", "both"),
        "image_added_to_ocr": ("ocr", "both"),
        "image_minus_ocr": ("ocr", "image"),
    }
    for model, model_summary in summary["models"].items():
        by_provider: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for (row_model, provider, _), modes in paired.items():
            if row_model != model:
                continue
            bucket = by_provider.setdefault(provider, {name: [] for name in pair_defs})
            for name, (left_mode, right_mode) in pair_defs.items():
                left = modes.get(left_mode)
                right = modes.get(right_mode)
                if not left or not right:
                    continue
                bucket[name].append(
                    {
                        "list_cost": float(right["usage"].get("list_cost_usd") or 0.0)
                        - float(left["usage"].get("list_cost_usd") or 0.0),
                        "cost": float(right["usage"].get("cost_usd") or 0.0)
                        - float(left["usage"].get("cost_usd") or 0.0),
                        "prompt": int(right["usage"]["prompt_tokens"])
                        - int(left["usage"]["prompt_tokens"]),
                        "completion": int(right["usage"]["completion_tokens"])
                        - int(left["usage"]["completion_tokens"]),
                        "reasoning": int(right["usage"]["reasoning_tokens"])
                        - int(left["usage"]["reasoning_tokens"]),
                    }
                )
        paired_summary: dict[str, Any] = {}
        for provider, buckets in by_provider.items():
            for name, diffs in buckets.items():
                if not diffs:
                    continue
                paired_summary[f"{provider}: {name}"] = {
                    "n_pairs": len(diffs),
                    "avg_list_cost_delta_usd": statistics.mean(d["list_cost"] for d in diffs),
                    "avg_cost_delta_usd": statistics.mean(d["cost"] for d in diffs),
                    "avg_prompt_delta": statistics.mean(d["prompt"] for d in diffs),
                    "avg_completion_delta": statistics.mean(d["completion"] for d in diffs),
                    "avg_reasoning_delta": statistics.mean(d["reasoning"] for d in diffs),
                }
        model_summary["paired_incremental"] = paired_summary
    return summary


def write_summary_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# LLM receipt extraction cost measurement",
        "",
        f"Generated: {summary['generated_at']}  ",
        f"Prompt version: `{summary['prompt_version']}`  ",
        f"Rows: {summary['n_rows']} unique documents/model/mode "
        f"({summary['n_rows_raw']} attempt rows, {summary['n_errors']} unresolved errors)",
        (
            "Error counts: "
            + ", ".join(f"`{k}` {v}" for k, v in summary.get("error_counts", {}).items())
            if summary.get("error_counts")
            else ""
        ),
        "",
        "| model | input | n | in tok | out tok | reasoning | billed $/receipt | "
        "list $/receipt | list $/1k | list $/100k | list $/1M | JSON ok |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, model_summary in summary["models"].items():
        for key, data in model_summary["modes"].items():
            provider, mode = key.split("::", 1)
            lines.append(
                "| {model} | {provider} / {mode} | {n} | {inp:.0f} | {out:.0f} | {reason:.0f} | "
                "${cost:.6f} | ${list_cost:.6f} | ${k:.2f} | ${k100:.0f} | ${k1m:.0f} | {valid:.0%} |".format(
                    model=model,
                    provider=provider,
                    mode=mode,
                    n=data["n_success"],
                    inp=data["avg_prompt_tokens"],
                    out=data["avg_completion_tokens"],
                    reason=data["avg_reasoning_tokens"],
                    cost=data["avg_cost_usd"],
                    list_cost=data["avg_list_cost_usd"],
                    k=data["list_cost_per_1k_usd"],
                    k100=data["list_cost_per_100k_usd"],
                    k1m=data["list_cost_per_1m_usd"],
                    valid=data["json_valid_rate"],
                )
            )
    lines.extend(["", "## Paired incremental cost", ""])
    lines.append(
        "Differences are computed per document, then averaged. Cost deltas use stable "
        "list prices; actual billed deltas are also in `summary.json`."
    )
    lines.append("")
    lines.append(
        "| model | provider / comparison | pairs | list $ delta | actual $ delta | "
        "prompt tok delta | out+reasoning tok delta |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for model, model_summary in summary["models"].items():
        for name, value in model_summary.get("paired_incremental", {}).items():
            provider, comparison = name.split(": ", 1)
            lines.append(
                "| {model} | {provider} / {comparison} | {n} | ${list_cost:+.6f} | "
                "${cost:+.6f} | {prompt:+.0f} | {out:+.0f} |".format(
                    model=model,
                    provider=provider,
                    comparison=comparison,
                    n=value["n_pairs"],
                    list_cost=value["avg_list_cost_delta_usd"],
                    cost=value["avg_cost_delta_usd"],
                    prompt=value["avg_prompt_delta"],
                    out=value["avg_completion_delta"] + value["avg_reasoning_delta"],
                )
            )
    lines.extend(
        [
            "",
            "## Method notes",
            "",
            "- Billed cost is provider-reported by OpenRouter; list cost is computed from the pricing table (USD per 1M tokens) for stable planning and cross-provider comparison.",
            "- Token counts include the extraction prompt and schema. For `--backend opencode`, a per-model trivial-prompt baseline is subtracted to remove the CLI agent system prompt.",
            "- Reasoning tokens are provider output tokens and are included in cost. Use `--reasoning disabled` where the provider supports it.",
            "- OCR runs locally and is cached; its compute cost is not included in the token totals.",
            "- Compare engines on the same image size: `--max-image-side` and JPEG quality change image-token counts.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_ground_truth(
    rows: list[dict[str, Any]],
    directory: Path,
    models: list[str] | None = None,
    modes: list[str] | None = None,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    index_path = directory / "ground_truth.jsonl"
    index_rows = []
    for row in rows:
        if row.get("error") or not row.get("json_valid"):
            continue
        if models and row.get("model") not in models:
            continue
        if modes and row.get("input_mode") not in modes:
            continue
        target = directory / slug(str(row["model"])) / str(row["input_mode"])
        target.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "prompt_version": row.get("prompt_version"),
            "source": {
                "id": row.get("id"),
                "image": row.get("image"),
                "image_sha256": row.get("image_sha256"),
                "split": row.get("split"),
                "model": row.get("model"),
                "input_mode": row.get("input_mode"),
                "backend": row.get("backend"),
                "created_at": row.get("timestamp"),
            },
            "usage": row.get("usage"),
            "cost_usd": row.get("cost_usd"),
            "extraction": row.get("extraction"),
        }
        (target / f"{slug(str(row.get('id')))}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        index_rows.append(payload)
    write_jsonl(index_path, index_rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--images", type=Path, help="Directory of receipts/invoices (recursive)")
    parser.add_argument("--manifest", type=Path, help="JSONL with image/id/split/ground_truth")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument(
        "--input-mode",
        nargs="+",
        choices=("image", "ocr", "both"),
        default=("image",),
        help="Input modalities to measure; pass several to compare incremental cost",
    )
    parser.add_argument("--backend", choices=("openrouter", "opencode"), default="openrouter")
    parser.add_argument(
        "--provider-order",
        nargs="+",
        help="OpenRouter upstream provider order, e.g. OpenInference, to pin tokenization",
    )
    parser.add_argument("--no-allow-fallbacks", dest="allow_fallbacks", action="store_false")
    parser.add_argument("--base-url", default="https://openrouter.ai/api/v1")
    parser.add_argument("--api-key")
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--auth-provider", default="openrouter")
    parser.add_argument("--no-auth-from-opencode", action="store_true")
    parser.add_argument("--referer", default="https://localhost")
    parser.add_argument("--title", default="receipt-extraction-cost")
    parser.add_argument("--workdir", default=str(Path.cwd()))
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument(
        "--reasoning",
        choices=("auto", "disabled", "low", "medium", "high"),
        default="disabled",
        help="Provider reasoning control; mandatory-reasoning models fall back to auto",
    )
    parser.add_argument("--structured-output", action="store_true")
    parser.add_argument("--audit", action="store_true", help="Request verbatim evidence snippets")
    parser.add_argument("--locale-hint")
    parser.add_argument("--ocr-backend", choices=("tesseract", "rapidocr", "none"), default="tesseract")
    parser.add_argument("--ocr-lang", default="eng+ces")
    parser.add_argument("--ocr-psm", type=int, default=6)
    parser.add_argument("--precomputed-ocr", type=Path)
    parser.add_argument("--max-image-side", type=int, default=1600)
    parser.add_argument("--jpeg-quality", type=int, default=90)
    parser.add_argument("--out-dir", type=Path, default=Path("runs/llm-extraction"))
    parser.add_argument("--ground-truth-dir", type=Path)
    parser.add_argument(
        "--ground-truth-models",
        nargs="+",
        help="Only write these models into the ground-truth directory",
    )
    parser.add_argument(
        "--ground-truth-modes",
        nargs="+",
        choices=("image", "ocr", "both"),
        help="Only write these input modes into the ground-truth directory",
    )
    parser.add_argument("--consensus", action="store_true")
    parser.add_argument("--pricing", type=Path, help="JSON model -> {input,output,cache_read} USD/M")
    parser.add_argument("--force", action="store_true", help="Ignore cached results and OCR")
    parser.add_argument("--save-raw", action="store_true")
    parser.add_argument("--allow-fallbacks", dest="allow_fallbacks", action="store_true", default=True)
    parser.add_argument("--calibrate-opencode", action="store_true", default=True)
    parser.add_argument("--no-calibrate-opencode", dest="calibrate_opencode", action="store_false")
    args = parser.parse_args()

    if args.max_retries < 0:
        parser.error("--max-retries must be nonnegative")
    if args.backend == "openrouter":
        args.api_key_value = resolve_api_key(args)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = args.out_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    pricing = dict(DEFAULT_PRICING)
    if args.pricing:
        pricing.update(json.loads(args.pricing.read_text(encoding="utf-8")))
    args.pricing = pricing
    if args.precomputed_ocr:
        args.precomputed_ocr = load_precomputed_ocr(args.precomputed_ocr)

    documents = collect_manifest(args)
    results_path = args.out_dir / "results.jsonl"
    if args.force and results_path.exists():
        results_path.unlink()
    existing_rows = [] if args.force else read_jsonl(results_path)
    done = {
        (
            str(row.get("model")),
            str(row.get("input_mode")),
            str(row.get("id")),
            str(row.get("prompt_version")),
            bool(row.get("audit")),
        )
        for row in existing_rows
        if not row.get("error")
    }
    rows = list(existing_rows)
    print(
        f"measuring {len(documents)} documents x {len(args.models)} models x "
        f"{len(args.input_mode)} modes ({len(rows)} existing rows)",
        file=sys.stderr,
    )

    for document in documents:
        processed = prepare_image(
            Path(document["image"]), cache_dir, args.max_image_side, args.jpeg_quality
        )
        ocr_cache: dict[str, dict[str, Any]] = {}
        ocr_key = "ocr"
        for model in args.models:
            for mode in args.input_mode:
                key = (model, mode, document["id"], PROMPT_VERSION, args.audit)
                if key in done:
                    print(f"skip {document['id']} {model} {mode}", file=sys.stderr)
                    continue
                ocr_result = None
                if mode in {"ocr", "both"}:
                    try:
                        if ocr_key not in ocr_cache:
                            ocr_cache[ocr_key] = ocr_document(
                                document, processed, args, cache_dir
                            )
                        ocr_result = ocr_cache[ocr_key]
                    except Exception as exc:
                        row = {
                            "timestamp": now_iso(),
                            "prompt_version": PROMPT_VERSION,
                            "backend": args.backend,
                            "provider": args.base_url,
                            "model": model,
                            "id": document["id"],
                            "image": document["image"],
                            "split": document["split"],
                            "input_mode": mode,
                            "audit": args.audit,
                            "error": f"OCR failed: {exc}",
                            "json_valid": False,
                            "attempts_count": 0,
                            "usage": normalize_usage(None),
                            "cost_usd": 0.0,
                        }
                        rows.append(row)
                        append_jsonl(results_path, row)
                        print(f"ERROR {document['id']} {model} {mode}: {exc}", file=sys.stderr)
                        continue

                try:
                    prompt = build_prompt(
                        mode,
                        ocr_text=(ocr_result or {}).get("text"),
                        audit=args.audit,
                        locale_hint=args.locale_hint,
                    )
                    image_path = Path(processed["path"]) if mode in {"image", "both"} else None
                    if args.backend == "openrouter":
                        raw = request_openrouter(model, prompt, image_path, args)
                    else:
                        raw = request_opencode(model, prompt, image_path, args, cache_dir)
                    usage = raw.get("usage") or normalize_usage(None)
                    if not usage.get("cost_usd"):
                        usage["cost_usd"] = cost_from_usage(usage, pricing.get(model))
                    extraction = None
                    json_valid = False
                    parse_error = None
                    if raw.get("text"):
                        try:
                            extraction = parse_json_object(raw["text"])
                            json_valid = True
                        except Exception as exc:
                            parse_error = str(exc)
                    if not raw.get("error") and not json_valid:
                        raw["error"] = f"invalid JSON: {parse_error}"
                    row = {
                        "timestamp": now_iso(),
                        "prompt_version": PROMPT_VERSION,
                        "backend": args.backend,
                        "provider": args.base_url if args.backend == "openrouter" else "opencode",
                        "provider_name": raw.get("provider_name"),
                        "response_model": raw.get("response_model"),
                        "model": model,
                        "id": document["id"],
                        "image": document["image"],
                        "image_sha256": processed["sha256"],
                        "split": document["split"],
                        "input_mode": mode,
                        "audit": args.audit,
                        "ocr_backend": (ocr_result or {}).get("backend"),
                        "ocr_chars": len((ocr_result or {}).get("text") or ""),
                        "ocr_seconds": (ocr_result or {}).get("seconds"),
                        "ocr_cached": (ocr_result or {}).get("cached"),
                        "image_meta": processed,
                        "usage": usage,
                        "cost_usd": float(usage.get("cost_usd") or 0.0),
                        "attempts": raw.get("attempts") or [],
                        "attempts_count": len(raw.get("attempts") or []),
                        "latency_seconds": sum(
                            float(item.get("latency_seconds") or 0)
                            for item in (raw.get("attempts") or [])
                        ),
                        "json_valid": json_valid,
                        "extraction": extraction,
                        "finish_reason": raw.get("finish_reason"),
                        "error": raw.get("error"),
                        "reasoning": args.reasoning,
                        "raw_response": raw.get("text") if args.save_raw else None,
                    }
                    rows.append(row)
                    append_jsonl(results_path, row)
                    print(
                        f"{document['id']} {model} {mode}: "
                        f"{usage['prompt_tokens']} in / {usage['completion_tokens']} out / "
                        f"{usage['reasoning_tokens']} reasoning / ${usage['cost_usd']:.6f}"
                        + (f" [{row['error']}]" if row.get("error") else ""),
                        file=sys.stderr,
                    )
                except Exception as exc:
                    row = {
                        "timestamp": now_iso(),
                        "prompt_version": PROMPT_VERSION,
                        "backend": args.backend,
                        "provider": args.base_url,
                        "model": model,
                        "id": document["id"],
                        "image": document["image"],
                        "split": document["split"],
                        "input_mode": mode,
                        "audit": args.audit,
                        "error": f"{type(exc).__name__}: {exc}",
                        "json_valid": False,
                        "attempts_count": 0,
                        "usage": normalize_usage(None),
                        "cost_usd": 0.0,
                    }
                    rows.append(row)
                    append_jsonl(results_path, row)
                    print(f"ERROR {document['id']} {model} {mode}: {exc}", file=sys.stderr)

    summary = summarize(rows, pricing)
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_summary_markdown(summary, args.out_dir / "summary.md")
    if args.ground_truth_dir:
        write_ground_truth(
            rows,
            args.ground_truth_dir,
            models=args.ground_truth_models,
            modes=args.ground_truth_modes,
        )
    if args.consensus:
        consensus = build_consensus(deduplicate_rows(rows))
        write_jsonl(args.out_dir / "consensus.jsonl", consensus)
        review = sum(1 for item in consensus if item["needs_review"])
        print(
            f"consensus: {len(consensus)} documents, {review} need review",
            file=sys.stderr,
        )
    print(f"wrote {results_path} and {args.out_dir / 'summary.md'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

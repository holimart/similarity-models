"""Tests for the lexocr package (network-free; OCR engine mocked)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lexocr import engine  # noqa: E402
from lexocr.batch import run_batch  # noqa: E402
from lexocr.engine import is_readable, pdf_to_text  # noqa: E402

pytest.importorskip("pymupdf")

_GOOD_TEXT = (
    "The quick brown fox jumps over the lazy dog near the river bank. "
    "Legal reasoning requires careful attention to the facts and the law. "
) * 8


def _make_pdf(text: str) -> bytes:
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page()
    if text:
        page.insert_textbox(pymupdf.Rect(36, 36, 560, 800), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


# --- readability heuristic -------------------------------------------------


def test_is_readable_accepts_real_text():
    report = is_readable(_GOOD_TEXT)
    assert report.readable is True
    assert report.chars >= 200
    assert report.letter_ratio >= 0.5
    assert report.word_ratio >= 0.5
    assert report.reason == "ok"


def test_is_readable_rejects_short_and_garbage():
    short = is_readable("too short")
    assert short.readable is False
    assert "too short" in short.reason

    garbage = is_readable("###$$$%%%^^^&&&***((()))___+++===|||~~~:::;;;<<<>>>???" * 20)
    assert garbage.readable is False


# --- text layer ------------------------------------------------------------


def test_pdf_to_text_uses_text_layer_without_ocr(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("OCR must not be called for a good text layer")

    monkeypatch.setattr(engine, "_ocr_image", _boom)
    result = pdf_to_text(_make_pdf(_GOOD_TEXT), ocr=True, device="cpu")

    assert result.used_ocr is False
    assert result.ocr_pages == 0
    assert result.pages == 1
    assert result.readability.readable is True
    assert "quick brown fox" in result.text


# --- OCR fallback ----------------------------------------------------------


def test_image_only_pdf_triggers_ocr(monkeypatch):
    ocr_text = _GOOD_TEXT
    seen = {"calls": 0}

    def fake_ocr(image_bytes, device="cpu"):
        seen["calls"] += 1
        assert image_bytes[:4] == b"\x89PNG"
        return ocr_text

    monkeypatch.setattr(engine, "ocr_available", lambda: True)
    monkeypatch.setattr(engine, "_ocr_image", fake_ocr)

    result = pdf_to_text(_make_pdf(""), ocr=True, device="cpu")

    assert seen["calls"] >= 1
    assert result.used_ocr is True
    assert result.ocr_pages == 1
    assert result.dpi == 200
    assert result.readability.readable is True


def test_ocr_disabled_keeps_text_layer(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("OCR must not run when ocr=False")

    monkeypatch.setattr(engine, "_ocr_image", _boom)
    result = pdf_to_text(_make_pdf(""), ocr=False)

    assert result.used_ocr is False
    assert result.ocr_pages == 0
    assert result.meta.get("note") == "ocr disabled"


# --- non-PDF / unreadable content ------------------------------------------


def test_non_pdf_returns_skip(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("OCR must not run for a non-PDF")

    monkeypatch.setattr(engine, "_ocr_image", _boom)
    result = pdf_to_text(b"this is definitely not a pdf", ocr=True)

    assert result.pages == 0
    assert result.used_ocr is False
    assert result.ocr_pages == 0
    assert result.readability.readable is False
    assert "open failed" in result.readability.reason


# --- batch -----------------------------------------------------------------


def test_run_batch_writes_jsonl(tmp_path, monkeypatch):
    batch_dir = tmp_path / "pdfs"
    batch_dir.mkdir()
    (batch_dir / "aaa.pdf").write_bytes(_make_pdf(_GOOD_TEXT))
    (batch_dir / "bbb.pdf").write_bytes(_make_pdf(_GOOD_TEXT))
    (batch_dir / "ignore.txt").write_text("not a pdf")

    def _boom(*_a, **_k):
        raise AssertionError("good text layers should not require OCR")

    monkeypatch.setattr(engine, "_ocr_image", _boom)

    out = tmp_path / "out.jsonl"
    stats = run_batch(batch_dir, out, device="cpu", workers=1)

    assert stats == {"documents": 2, "readable": 2, "ocr_pages": 0}

    import json

    lines = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
    assert [ln["source_id"] for ln in lines] == ["aaa", "bbb"]
    assert all(ln["readable"] for ln in lines)

import json

import pytest

from ocr_lab.receipt_extraction import (
    build_consensus,
    build_prompt,
    cost_from_usage,
    critical_values,
    load_schema,
    normalize_usage,
    parse_json_object,
)


def test_schema_has_app_contract():
    schema = load_schema()
    assert schema["required"] == [
        "document_type",
        "document",
        "merchant",
        "customer",
        "amounts",
        "payment",
        "line_items",
        "classification",
        "quality",
    ]
    assert "taxes" in schema["properties"]["amounts"]["properties"]
    assert "purpose_summary" in schema["properties"]["classification"]["properties"]


def test_prompt_modes():
    image_only = build_prompt("image")
    assert "OCR TRANSCRIPT" not in image_only
    assert "Return this JSON shape" in image_only

    with_ocr = build_prompt("both", ocr_text="RESTAURANT\nTotal 12.50")
    assert "RESTAURANT" in with_ocr
    assert "OCR TRANSCRIPT START" in with_ocr

    with pytest.raises(ValueError):
        build_prompt("ocr")
    with pytest.raises(ValueError):
        build_prompt("image+ocr")


def test_audit_prompt_adds_evidence_instruction():
    prompt = build_prompt("image", audit=True)
    assert '"evidence"' in prompt
    assert "Do not quote invented text" in prompt


def test_parse_json_fenced_and_with_prose():
    fenced = parse_json_object('```json\n{"document_type": "receipt"}\n```')
    assert fenced["document_type"] == "receipt"
    prose = parse_json_object('Here is the result:\n{"a": 1}\nDone.')
    assert prose["a"] == 1
    with pytest.raises(ValueError):
        parse_json_object("[1, 2, 3]")
    with pytest.raises(ValueError):
        parse_json_object("")


def test_cost_from_usage_uses_cache_and_output_rates():
    usage = {
        "prompt_tokens": 1_000,
        "completion_tokens": 500,
        "cached_tokens": 200,
    }
    cost = cost_from_usage(
        usage, {"input": 0.30, "output": 1.20, "cache_read": 0.006}
    )
    expected = (800 * 0.30 + 200 * 0.006 + 500 * 1.20) / 1_000_000
    assert cost == pytest.approx(expected)


def test_normalize_usage_reads_reasoning_and_image_tokens():
    usage = normalize_usage(
        {
            "prompt_tokens": 700,
            "completion_tokens": 300,
            "total_tokens": 1000,
            "cost": 0.001,
            "prompt_tokens_details": {"cached_tokens": 100},
            "completion_tokens_details": {"reasoning_tokens": 120, "image_tokens": 600},
        }
    )
    assert usage["reasoning_tokens"] == 120
    assert usage["cached_tokens"] == 100
    assert usage["image_tokens"] == 600
    assert usage["cost_usd"] == 0.001


def test_critical_values_normalizes_amounts_and_text():
    extraction = {
        "document_type": "receipt",
        "document": {"date": "2026-10-20", "currency": "CZK"},
        "merchant": {"name": "  Restaurant   Na Rynku "},
        "amounts": {"total": "1 234,56", "tax_total": 210.0, "tip": None},
        "classification": {"category": "food_dining", "purpose_summary": "Lunch"},
    }
    values = critical_values(extraction)
    assert values["amounts.total"] == pytest.approx(1234.56)
    assert values["merchant.name"] == "restaurant na rynku"
    assert values["document.currency"] == "czk"


def test_deduplicate_rows_prefers_success():
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "scripts" / "measure_receipt_llm.py"
    spec = importlib.util.spec_from_file_location("measure_receipt_llm", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = {
        "model": "m",
        "input_mode": "image",
        "id": "r1",
        "prompt_version": "v1",
        "audit": False,
        "usage": {"cost_usd": 0.0},
    }
    rows = [
        {**base, "error": "HTTP 429"},
        {**base, "error": None, "usage": {"cost_usd": 0.1}},
    ]
    assert len(module.deduplicate_rows(rows)) == 1
    assert module.deduplicate_rows(rows)[0]["error"] is None


def test_consensus_flags_disagreement():
    rows = [
        {
            "id": "r1",
            "image": "r1.jpg",
            "model": "a",
            "input_mode": "image",
            "json_valid": True,
            "extraction": {
                "amounts": {"total": 10.0},
                "merchant": {"name": "Cafe"},
            },
        },
        {
            "id": "r1",
            "image": "r1.jpg",
            "model": "b",
            "input_mode": "image",
            "json_valid": True,
            "extraction": {
                "amounts": {"total": 10.5},
                "merchant": {"name": "Cafe"},
            },
        },
    ]
    result = build_consensus(rows)
    assert len(result) == 1
    assert result[0]["needs_review"] is True
    assert result[0]["fields"]["amounts.total"]["agree"] is False
    assert result[0]["fields"]["merchant.name"]["agree"] is True

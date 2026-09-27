"""Shared config and result normalization for local OCR harnesses."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


@dataclass
class OCRConfig:
    harness: str = "rapidocr"
    device: str = "cpu"
    lang: str = "en"
    model_family: str = "PP-OCRv6"
    model_size: str = "small"
    engine: str = "onnxruntime"
    det_limit_side_len: int = 1280
    det_limit_type: str = "max"
    det_thresh: float = 0.3
    box_thresh: float = 0.5
    unclip_ratio: float = 1.6
    rec_score_thresh: float = 0.0
    use_orientation: bool = True
    det_model_path: str | None = None
    rec_model_path: str | None = None
    cls_model_path: str | None = None
    rec_keys_path: str | None = None

    @classmethod
    def from_json(cls, path: str | Path) -> "OCRConfig":
        import json

        values = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**values)


def normalized_result(boxes: Any, texts: Any, scores: Any) -> list[dict[str, Any]]:
    """Normalize package output to polygon/text/confidence records."""
    if boxes is None or texts is None:
        return []
    result: list[dict[str, Any]] = []
    for index, text in enumerate(texts):
        if text is None or not str(text).strip():
            continue
        box = boxes[index] if index < len(boxes) else None
        score = scores[index] if scores is not None and index < len(scores) else None
        polygon = None
        if box is not None:
            try:
                polygon = [[float(point[0]), float(point[1])] for point in box]
            except (TypeError, ValueError, IndexError):
                polygon = None
        try:
            score = float(score) if score is not None else None
        except (TypeError, ValueError):
            score = None
        result.append({"polygon": polygon, "text": str(text), "confidence": score})
    return result


def create_rapidocr(config: OCRConfig) -> Any:
    try:
        from rapidocr import EngineType, LangDet, LangRec, ModelType, OCRVersion, RapidOCR
    except ImportError as exc:
        raise RuntimeError("RapidOCR is not installed. See requirements-ocr.txt and README-ocr.md.") from exc

    try:
        engine_type = getattr(EngineType, config.engine.upper())
        model_type = getattr(ModelType, config.model_size.upper())
        ocr_version = getattr(OCRVersion, config.model_family.replace("-", "").upper())
        det_lang = LangDet.CH
        if config.model_family == "PP-OCRv6":
            rec_lang = LangRec.CH
        elif config.lang.lower() in {"cs", "en", "latin"}:
            rec_lang = LangRec.LATIN if config.lang.lower() != "en" else LangRec.EN
        else:
            rec_lang = getattr(LangRec, config.lang.upper())
        cls_version = OCRVersion.PPOCRV4
        cls_size = ModelType.MOBILE
    except AttributeError as exc:
        raise ValueError(f"Unsupported RapidOCR model/backend/language option: {exc}") from exc
    rapid_config: dict[str, Any] = {
        "Det.engine_type": engine_type,
        "Det.lang_type": det_lang,
        "Det.model_type": model_type,
        "Det.ocr_version": ocr_version,
        "Det.limit_side_len": config.det_limit_side_len,
        "Det.limit_type": config.det_limit_type,
        "Det.thresh": config.det_thresh,
        "Det.box_thresh": config.box_thresh,
        "Det.unclip_ratio": config.unclip_ratio,
        "Cls.engine_type": engine_type,
        "Cls.lang_type": LangDet.CH,
        "Cls.model_type": cls_size,
        "Cls.ocr_version": cls_version,
        "Rec.engine_type": engine_type,
        "Rec.lang_type": rec_lang,
        "Rec.model_type": model_type,
        "Rec.ocr_version": ocr_version,
        "Global.text_score": config.rec_score_thresh,
        "Global.use_cls": config.use_orientation,
        "Global.log_level": "error",
    }
    if config.det_model_path:
        rapid_config["Det.model_path"] = config.det_model_path
    if config.rec_model_path:
        rapid_config["Rec.model_path"] = config.rec_model_path
    if config.cls_model_path:
        rapid_config["Cls.model_path"] = config.cls_model_path
    if config.rec_keys_path:
        rapid_config["Rec.rec_keys_path"] = config.rec_keys_path
    if config.engine == "onnxruntime":
        rapid_config["EngineConfig.onnxruntime.use_cuda"] = config.device.startswith("cuda")
        if config.device.startswith("cuda:"):
            rapid_config["EngineConfig.onnxruntime.cuda_ep_cfg.device_id"] = int(config.device.split(":", 1)[1])
    elif config.engine in {"paddle", "torch"}:
        rapid_config[f"EngineConfig.{config.engine}.use_cuda"] = config.device.startswith("cuda")

    return RapidOCR(params=rapid_config)


def predict_rapidocr(engine: Any, image_path: str | Path, config: OCRConfig) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output = engine(str(image_path))
    records = normalized_result(output.boxes, output.txts, output.scores)
    metadata = {
        "elapsed": getattr(output, "elapse", None),
        "elapsed_by_stage": getattr(output, "elapse_list", None),
        "engine": config.engine,
        "model_family": config.model_family,
        "model_size": config.model_size,
    }
    return records, metadata


def create_paddleocr(config: OCRConfig) -> Any:
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError("PaddleOCR is not installed. See requirements-ocr.txt and README-ocr.md.") from exc

    kwargs: dict[str, Any] = {
        "lang": config.lang,
        "device": config.device,
        "engine": config.engine,
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": config.use_orientation,
        "text_det_limit_side_len": config.det_limit_side_len,
        "text_det_limit_type": config.det_limit_type,
        "text_det_thresh": config.det_thresh,
        "text_det_box_thresh": config.box_thresh,
        "text_det_unclip_ratio": config.unclip_ratio,
        "text_rec_score_thresh": config.rec_score_thresh,
    }
    family = config.model_family.upper().replace("-", "")
    size = config.model_size.lower()
    if family == "PPOCRV6":
        kwargs["text_detection_model_name"] = f"PP-OCRv6_{size}_det"
        kwargs["text_recognition_model_name"] = f"PP-OCRv6_{size}_rec"
    elif family in {"PPOCRV4", "PPOCRV5"}:
        kwargs["ocr_version"] = config.model_family
        paddle_size = "server" if size == "server" else "mobile"
        kwargs["text_detection_model_name"] = f"{config.model_family}_{paddle_size}_det"
        if config.lang.lower() in {"cs", "latin"} and family == "PPOCRV5":
            kwargs["text_recognition_model_name"] = f"latin_{config.model_family}_{paddle_size}_rec"
        else:
            kwargs["text_recognition_model_name"] = f"{config.model_family}_{paddle_size}_rec"
    if config.det_model_path:
        kwargs["text_detection_model_dir"] = config.det_model_path
    if config.rec_model_path:
        kwargs["text_recognition_model_dir"] = config.rec_model_path
    return PaddleOCR(**kwargs)


def predict_paddleocr(engine: Any, image_path: str | Path, config: OCRConfig) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    predictions = engine.predict(str(image_path))
    if not predictions:
        return [], {"elapsed": None}

    payload = getattr(predictions[0], "json", {})
    if callable(payload):
        payload = payload()
    if isinstance(payload, dict) and "res" in payload:
        payload = payload["res"]
    boxes = payload.get("rec_polys", payload.get("dt_polys", [])) if isinstance(payload, dict) else []
    texts = payload.get("rec_texts", []) if isinstance(payload, dict) else []
    scores = payload.get("rec_scores", payload.get("dt_scores", [])) if isinstance(payload, dict) else []
    records = normalized_result(boxes, texts, scores)
    return records, {
        "elapsed": None,
        "engine": "paddle",
        "model_family": config.model_family,
        "model_size": config.model_size,
        "effective_params": payload.get("text_det_params") if isinstance(payload, dict) else None,
    }


class LocalOCRHarness:
    """Loaded backend reusable across images to avoid model-init bias."""

    def __init__(self, config: OCRConfig):
        self.config = config
        if config.harness == "rapidocr":
            self.engine = create_rapidocr(config)
            self.predict = predict_rapidocr
        elif config.harness == "paddleocr":
            self.engine = create_paddleocr(config)
            self.predict = predict_paddleocr
        else:
            raise ValueError(f"Unknown harness {config.harness!r}; choose paddleocr or rapidocr")

    def __call__(self, image_path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        return self.predict(self.engine, image_path, self.config)


def run_ocr(image_path: str | Path, config: OCRConfig) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return LocalOCRHarness(config)(image_path)


def config_dict(config: OCRConfig) -> dict[str, Any]:
    return asdict(config)


def installed_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in ("paddleocr", "paddlepaddle", "rapidocr", "onnxruntime"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = None
    return versions

#!/usr/bin/env python3
"""Inference-only image tagging baselines evaluated against COCO instance labels."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Sequence


def load_project_env():
    """Load simple KEY=VALUE entries from the repository .env without dependencies."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        if key:
            os.environ.setdefault(key, value)


def load_coco(annotations_path: Path, image_dir: Path, limit: int | None = None):
    """Return existing images and 80-way image-level labels from COCO instances JSON."""
    data = json.loads(annotations_path.read_text(encoding="utf-8"))
    categories = sorted(data["categories"], key=lambda item: item["id"])
    cat_id_to_idx = {item["id"]: i for i, item in enumerate(categories)}
    by_image: Dict[int, set] = defaultdict(set)
    for ann in data["annotations"]:
        # Crowd regions are excluded from this simple image-presence target.
        if ann.get("iscrowd", 0):
            continue
        by_image[ann["image_id"]].add(cat_id_to_idx[ann["category_id"]])

    rows = []
    for image in sorted(data["images"], key=lambda item: item["id"]):
        path = image_dir / image["file_name"]
        if not path.is_file():
            continue
        labels = [0] * len(categories)
        for index in by_image[image["id"]]:
            labels[index] = 1
        rows.append({"id": image["id"], "path": path, "labels": labels})
        if limit is not None and len(rows) >= limit:
            break
    if not rows:
        raise ValueError(f"No COCO images found under {image_dir}; check the annotation/image paths")
    return categories, rows


def average_precision(y_true: Sequence[int], y_score: Sequence[float]) -> float | None:
    positives = sum(y_true)
    if positives == 0:
        return None
    order = sorted(range(len(y_score)), key=lambda i: y_score[i], reverse=True)
    found = 0
    total = 0.0
    for rank, index in enumerate(order, start=1):
        if y_true[index]:
            found += 1
            total += found / rank
    return total / positives


def compute_metrics(targets, scores, threshold: float, top_k: int = 5):
    """Compute per-class AP and pooled / macro threshold metrics."""
    n_images, n_classes = len(targets), len(targets[0])
    aps, class_values = [], []
    tp_all = fp_all = fn_all = 0
    image_precisions = []
    for c in range(n_classes):
        truth = [int(targets[i][c]) for i in range(n_images)]
        pred_scores = [float(scores[i][c]) for i in range(n_images)]
        ap = average_precision(truth, pred_scores)
        if ap is not None:
            aps.append(ap)
        tp = fp = fn = 0
        for y, score in zip(truth, pred_scores):
            predicted = score >= threshold
            tp += int(predicted and bool(y))
            fp += int(predicted and not y)
            fn += int(not predicted and bool(y))
        if tp + fp + fn:
            p = tp / (tp + fp) if tp + fp else 0.0
            r = tp / (tp + fn) if tp + fn else 0.0
            f = (2 * p * r / (p + r)) if p + r else 0.0
            class_values.append((p, r, f))
        tp_all += tp
        fp_all += fp
        fn_all += fn

    for truth, row_scores in zip(targets, scores):
        indices = sorted(range(n_classes), key=lambda c: row_scores[c], reverse=True)[:top_k]
        image_precisions.append(sum(truth[c] for c in indices) / max(1, len(indices)))

    micro_p = tp_all / (tp_all + fp_all) if tp_all + fp_all else 0.0
    micro_r = tp_all / (tp_all + fn_all) if tp_all + fn_all else 0.0
    micro_f = 2 * micro_p * micro_r / (micro_p + micro_r) if micro_p + micro_r else 0.0
    macro = [sum(values[i] for values in class_values) / len(class_values) for i in range(3)]
    return {
        "macro_map": sum(aps) / len(aps) if aps else None,
        "evaluated_classes_with_positives": len(aps),
        "macro_precision_at_threshold": macro[0],
        "macro_recall_at_threshold": macro[1],
        "macro_f1_at_threshold": macro[2],
        "micro_precision_at_threshold": micro_p,
        "micro_recall_at_threshold": micro_r,
        "micro_f1_at_threshold": micro_f,
        f"precision_at_{top_k}": sum(image_precisions) / len(image_precisions),
    }


def load_model(model_name: str, categories, device: str):
    import torch

    if model_name == "clip":
        import open_clip

        model, _, preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai", device=device
        )
        tokenizer = open_clip.get_tokenizer("ViT-B-32")
        prompts = [f"a photo of {item['name']}" for item in categories]
        with torch.inference_mode():
            text = model.encode_text(tokenizer(prompts).to(device))
            text = text / text.norm(dim=-1, keepdim=True)

        def predict(image_path):
            from PIL import Image

            image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
            with torch.inference_mode():
                image_features = model.encode_image(image)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                return (image_features @ text.T).squeeze(0).float().cpu().tolist()

        return predict

    if model_name == "siglip2":
        from PIL import Image
        from transformers import AutoModel, AutoProcessor

        checkpoint = "google/siglip2-base-patch16-224"
        processor = AutoProcessor.from_pretrained(checkpoint)
        model = AutoModel.from_pretrained(checkpoint).to(device).eval()
        prompts = [f"This is a photo of {item['name']}." for item in categories]
        tokens = processor.tokenizer(
            prompts, padding="max_length", max_length=64, return_tensors="pt"
        ).to(device)
        with torch.inference_mode():
            text_features = model.get_text_features(**tokens).pooler_output
            text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)

        def predict(image_path):
            image = Image.open(image_path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt").to(device)
            with torch.inference_mode():
                image_features = model.get_image_features(**inputs).pooler_output
                image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
                logits = model.logit_scale.exp() * (image_features @ text_features.T)
                logits = logits + model.logit_bias
                logits = logits.squeeze(0)
            return torch.sigmoid(logits).float().cpu().tolist()

        return predict

    if model_name == "ram_plus":
        import sys
        from PIL import Image

        repo = os.environ.get("RAM_REPO")
        checkpoint = os.environ.get("RAM_CHECKPOINT")
        if not repo or not Path(repo).is_dir():
            raise RuntimeError("Set RAM_REPO in .env to the cloned recognize-anything repository")
        if not checkpoint or not Path(checkpoint).is_file():
            raise RuntimeError("Set RAM_CHECKPOINT in .env to the downloaded RAM++ checkpoint")
        sys.path.insert(0, repo)
        from ram import get_transform
        from ram.models import ram_plus

        image_size = 384
        model = ram_plus(pretrained=checkpoint, image_size=image_size, vit="swin_l").to(device).eval()
        transform = get_transform(image_size=image_size)
        tag_indices = {str(tag).strip().casefold(): i for i, tag in enumerate(model.tag_list)}
        aliases = {
            "airplane": ("airplane", "aeroplane", "plane"),
            "couch": ("couch", "sofa"),
            "tv": ("tv", "television"),
            "cell phone": ("cell phone", "cellphone", "mobile phone", "smartphone"),
            "hair drier": ("hair drier", "hair dryer"),
            "motorcycle": ("motorcycle", "motorbike"),
            "potted plant": ("potted plant", "houseplant", "plant"),
            "fire hydrant": ("fire hydrant", "hydrant"),
            "suitcase": ("suitcase", "luggage"),
            "skis": ("skis", "ski", "ski equipment"),
            "dining table": ("dining table", "dinning table", "kitchen table", "table"),
            "toilet": ("toilet", "toilet bowl", "toilet seat"),
            "refrigerator": ("refrigerator", "fridge"),
            "teddy bear": ("teddy bear", "teddy", "stuffed animal", "stuffed toy"),
        }
        category_tag_indices = []
        for item in categories:
            options = aliases.get(item["name"].casefold(), (item["name"].casefold(),))
            category_tag_indices.append([tag_indices[name] for name in options if name in tag_indices])

        def predict(image_path):
            image = transform(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
            with torch.inference_mode():
                image_embeds = model.image_proj(model.visual_encoder(image))
                image_atts = torch.ones(image_embeds.size()[:-1], dtype=torch.long, device=image.device)
                image_cls = image_embeds[:, 0, :]
                image_cls = image_cls / image_cls.norm(dim=-1, keepdim=True)
                descriptions_per_tag = model.label_embed.shape[0] // model.num_class
                logits = model.reweight_scale.exp() * image_cls @ model.label_embed.t()
                logits = logits.view(1, -1, descriptions_per_tag)
                weights = torch.nn.functional.softmax(logits, dim=2)
                tag_embeddings = model.label_embed.view(-1, descriptions_per_tag, 512)
                tag_embeddings = (weights.unsqueeze(-1) * tag_embeddings).sum(dim=2)
                tag_embeddings = torch.nn.functional.relu(model.wordvec_proj(tag_embeddings))
                tag_features = model.tagging_head(
                    encoder_embeds=tag_embeddings,
                    encoder_hidden_states=image_embeds,
                    encoder_attention_mask=image_atts,
                    return_dict=False,
                    mode="tagging",
                )[0]
                tag_scores = torch.sigmoid(model.fc(tag_features).squeeze(-1))[0]
            output = []
            for indices in category_tag_indices:
                output.append(max((float(tag_scores[index]) for index in indices), default=0.0))
            return output

        return predict

    if model_name == "fasterrcnn":
        from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights, fasterrcnn_resnet50_fpn
        from torchvision.transforms.functional import pil_to_tensor
        from PIL import Image

        weights = FasterRCNN_ResNet50_FPN_Weights.DEFAULT
        model = fasterrcnn_resnet50_fpn(weights=weights).to(device).eval()
        model_categories = weights.meta["categories"]
        target_lookup = {item["name"].lower(): idx for idx, item in enumerate(categories)}
        model_to_target = {}
        for idx, name in enumerate(model_categories):
            if idx and name.lower() in target_lookup:
                model_to_target[idx] = target_lookup[name.lower()]

        def predict(image_path):
            image = Image.open(image_path).convert("RGB")
            tensor = pil_to_tensor(image).float().div_(255).to(device)
            with torch.inference_mode():
                result = model([tensor])[0]
            output = [0.0] * len(categories)
            for label, score in zip(result["labels"].tolist(), result["scores"].tolist()):
                target_idx = model_to_target.get(label)
                if target_idx is not None:
                    output[target_idx] = max(output[target_idx], float(score))
            return output

        return predict
    raise ValueError(f"Unknown model: {model_name}")


def benchmark_one(model_name, categories, rows, device, threshold):
    import torch

    predict = load_model(model_name, categories, device)
    scores, elapsed, targets, image_ids = [], [], [], []
    if device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
    for row in rows:
        start = time.perf_counter()
        scores.append(predict(row["path"]))
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        elapsed.append(time.perf_counter() - start)
        targets.append(row["labels"])
        image_ids.append(row["id"])
    return {
        "model": model_name,
        "device": device,
        "images": len(rows),
        "image_ids": image_ids,
        "seconds_per_image_mean": statistics.mean(elapsed),
        "seconds_per_image_median": statistics.median(elapsed),
        "images_per_second": len(elapsed) / sum(elapsed),
        "peak_cuda_memory_mb": torch.cuda.max_memory_allocated() / (1024 * 1024) if device.startswith("cuda") else None,
        "metrics": compute_metrics(targets, scores, threshold),
    }


def parse_args():
    load_project_env()
    coco_root = Path(os.environ["COCO_ROOT"]) if os.environ.get("COCO_ROOT") else None
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, default=coco_root / "val2017" if coco_root else None, help="COCO val2017 image directory (defaults from COCO_ROOT)")
    parser.add_argument("--annotations", type=Path, default=coco_root / "annotations/instances_val2017.json" if coco_root else None, help="instances_val2017.json (defaults from COCO_ROOT)")
    parser.add_argument("--model", choices=("clip", "fasterrcnn", "siglip2", "ram_plus", "all"), default="clip")
    parser.add_argument("--device", default="auto", help="auto, cpu, or a torch device such as cuda:0")
    parser.add_argument("--limit", type=int, help="Evaluate first N images by COCO image ID")
    parser.add_argument("--threshold", type=float, default=0.25, help="Fixed threshold for P/R/F1; mAP uses raw scores")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    import torch

    if args.images is None or args.annotations is None:
        raise SystemExit("Set COCO_ROOT in .env or pass --images and --annotations")
    device = ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    categories, rows = load_coco(args.annotations, args.images, args.limit)
    selected = ("clip", "fasterrcnn", "siglip2", "ram_plus") if args.model == "all" else (args.model,)
    results = {
        "benchmark": "COCO 2017 val image-level instance-category presence",
        "threshold": args.threshold,
        "categories": [item["name"] for item in categories],
        "results": [benchmark_one(name, categories, rows, device, args.threshold) for name in selected],
    }
    rendered = json.dumps(results, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

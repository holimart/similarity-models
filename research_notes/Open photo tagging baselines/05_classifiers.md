# Open pretrained image classifiers for photo-tagging baselines

## Which pretrained classifiers make practical CPU/GPU baselines, and what do their size and speed imply?

### Takeaway
For a low-friction baseline, start with TorchVision ImageNet-1K weights: MobileNet V3 Small/Large or EfficientNet-B0 are compact choices; ResNet-50 is a familiar, higher-compute reference. TorchVision publishes parameter count, checkpoint file size, FLOPs and ImageNet accuracy, but those are not device-specific latency measurements—benchmark on the target CPU/GPU and workload.

### Cited Findings
- TorchVision provides pretrained image-classification models including ResNet, EfficientNet, MobileNet V2/V3, RegNet and many others; the available weights and their ImageNet top-1/top-5, parameter and GFLOP statistics are listed in its model documentation. [TorchVision model and weights catalog](https://docs.pytorch.org/vision/stable/models.html)
- Representative tradeoffs at the documented evaluation size: MobileNet V3 Small has 2.5M parameters and 0.06 GFLOPs (67.668% ImageNet-1K top-1); MobileNet V3 Large V2 has 5.5M parameters and 0.22 GFLOPs (75.274%); EfficientNet-B0 has 5.3M parameters and 0.39 GFLOPs (77.692%); ResNet-50 V2 has 25.6M parameters and 4.09 GFLOPs (80.858%). These are published model statistics/benchmark accuracy, not latency guarantees. [TorchVision model catalog](https://docs.pytorch.org/vision/stable/models.html); [MobileNet V3 Large details](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_large.html); [EfficientNet-B0 details](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html); [ResNet-50 details](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet50.html)
- The corresponding documented checkpoint sizes are 21.1 MB for MobileNet V3 Large and 20.5 MB for EfficientNet-B0, and 97.8 MB for ResNet-50. (The model catalog gives parameter count and GFLOPs for MobileNet V3 Small; consult the individual weight metadata for checkpoint file size.) [MobileNet V3 Large details](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_large.html); [EfficientNet-B0 details](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html); [ResNet-50 details](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet50.html)
- Practical expectation (inference, not a published wall-clock result): small MobileNet/EfficientNet models are reasonable first CPU candidates for interactive or batch tagging; ResNet-50 is more compute-heavy and typically better suited to GPU or lower-throughput CPU use. Actual seconds/image depend on hardware, threading, batch size, preprocessing and precision; GFLOPs alone cannot determine them. [TorchVision model catalog](https://docs.pytorch.org/vision/stable/models.html)

### Inferences
- A useful three-point baseline set is MobileNet V3 Small (minimum compute), EfficientNet-B0 or MobileNet V3 Large (compact balance), and ResNet-50 V2 (common stronger reference). Keep the chosen model/weights version fixed when comparing.
- Run a warm-up and measure end-to-end and model-only latency separately on representative images, batch sizes and target hardware. Include image decode and transforms in the end-to-end figure.

### Gaps
- Official TorchVision model pages do not provide a directly comparable CPU/GPU latency table across representative consumer devices; local benchmarking is necessary.

## Licensing and setup: what can be used, and how do you load it?

### Takeaway
TorchVision's code repository is BSD-3-Clause licensed, but that alone does not establish the license/terms for pretrained weights or training data. The official docs explicitly warn that weights can have their own licenses or dataset-derived terms, so review the exact selected weights and dataset terms for the intended use.

### Cited Findings
- The TorchVision repository LICENSE is BSD 3-Clause. [TorchVision LICENSE](https://github.com/pytorch/vision/blob/main/LICENSE)
- TorchVision warns that pretrained models may have their own licenses or terms and conditions derived from the training dataset and assigns responsibility for confirming permission to the user. [TorchVision model and weights documentation](https://docs.pytorch.org/vision/stable/models.html)
- Weights download on model instantiation and are cached; `TORCH_HOME` can select the cache location. [TorchVision model and weights documentation](https://docs.pytorch.org/vision/stable/models.html)
- The current multi-weight API uses a weights enum, for example `ResNet50_Weights.DEFAULT`; `DEFAULT` can alias a particular weight version and may change over time. Pin the explicit enum (such as `IMAGENET1K_V2`) for reproducibility. [TorchVision model and weights documentation](https://docs.pytorch.org/vision/stable/models.html); [ResNet-50 weight details](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet50.html)
- Official setup/inference example (install a compatible PyTorch and TorchVision build for the host from the PyTorch install selector):

```python
import torch
from PIL import Image
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
weights = EfficientNet_B0_Weights.IMAGENET1K_V1  # explicit version
model = efficientnet_b0(weights=weights).to(device).eval()
preprocess = weights.transforms()

image = Image.open("photo.jpg").convert("RGB")
batch = preprocess(image).unsqueeze(0).to(device)
with torch.inference_mode():
    probabilities = model(batch).softmax(dim=1)[0]
values, indices = probabilities.topk(5)
for score, index in zip(values.tolist(), indices.tolist()):
    print(weights.meta["categories"][index], score)
```

- The bundled `weights.transforms()` is the supported preprocessing route; operations, resize/crop size and normalization vary by weight version/model. Use `model.eval()` at inference. [TorchVision model and weights documentation](https://docs.pytorch.org/vision/stable/models.html); [EfficientNet-B0 details](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html)

### Inferences
- Package installation and checkpoint download are separate operational concerns: choose the PyTorch wheel matching the machine/accelerator, and expect the first weight-enabled construction to download the checkpoint unless it is already cached.
- Keep package versions and explicit weights identifiers in deployment metadata; `DEFAULT` is convenient for experiments but can shift with library releases.

### Gaps
- A definitive commercial-use determination cannot be made from the library BSD license alone. Evaluate current terms associated with the precise pretrained weights and ImageNet dataset and seek legal review where needed.

## What do the outputs mean, and what are the main photo-tagging caveats?

### Takeaway
These standard pretrained heads produce scores over 1,000 ImageNet-1K categories, not arbitrary natural-language tags or a calibrated, multi-label description of everything present. Top-k classes can be used as candidate tags, but thresholds and usefulness need validation on the target photo collection.

### Cited Findings
- TorchVision exposes the class names through `weights.meta["categories"]`; its example applies softmax, chooses the highest score and maps the index to a category. [TorchVision model and weights documentation](https://docs.pytorch.org/vision/stable/models.html)
- The documented accuracies are ImageNet-1K single-crop classification metrics, and the weight pages show examples such as `tench`, `goldfish`, and `great white shark` among the 1,000 categories. [TorchVision model catalog](https://docs.pytorch.org/vision/stable/models.html); [ResNet-50 details](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet50.html)
- TorchVision notes that the correct model-specific preprocessing is critical and may vary across architecture, variant and weight version; its bundled transform API carries the prescribed preprocessing. [TorchVision model and weights documentation](https://docs.pytorch.org/vision/stable/models.html)

### Inferences
- A top-5 list is a useful baseline interface, but these single-label-trained classifiers do not directly answer “which multiple objects are present?” Treat softmax values as relative class probabilities over the fixed candidate set, not as calibrated confidence that a tag is true; evaluate thresholds against labeled target-domain examples.
- ImageNet taxonomy includes fine-grained and sometimes non-user-friendly labels. A production tagging layer may need category filtering, synonym/parent-category mapping, and a policy for suppressing low-value classes.
- Center-crop evaluation may omit peripheral content; test crop behavior on full-frame, landscape and portrait user photos. Preserve orientation and convert inputs to RGB before applying the weight transforms.

### Gaps
- The official classification documentation does not claim open-vocabulary tagging, exhaustive multi-object detection, calibrated confidence, or performance guarantees on private/photo-library distributions. Those properties require separate models or empirical target-domain evaluation.

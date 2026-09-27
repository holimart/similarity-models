# GPU economics for invoice and receipt understanding

## What VRAM should be budgeted for small open VLMs, quantization, and document images?

### Takeaway

For a single-GPU deployment, a 3B-class VLM in 4-bit should fit comfortably on a 16 GB GPU for one invoice at a time; 7B-class 4-bit is a practical fit on 16 GB at controlled image resolution and batch 1, while 7B 8-bit is a better fit for 24 GB and batching. The important variable beyond weight storage is how many visual tokens an image processor creates: Qwen2.5-VL documents a range from 4 to 16,384 visual tokens per image and explicitly exposes resolution limits, so unrestricted high-resolution inputs can overwhelm otherwise adequate memory and compute.

### Cited Findings

- Qwen2.5-VL is offered in nominal 3B, 7B, and 72B variants; Hugging Face cards report the 3B card as 4B parameters and the 7B card as 8B parameters, indicating that “B” labels are rounded/model-family labels rather than precise resident parameter counts. [3B model card](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct); [7B model card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)
- Qwen2.5-VL model guidance says default visual token counts span 4–16,384/image. It gives a practical `max_pixels=1280*28*28` example, described as roughly 256–1280 tokens, to balance performance and cost. [Qwen2.5-VL model card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)
- Transformers documents 8-bit loading as approximately halving model memory and 4-bit loading as reducing it approximately 4x; non-linear modules can remain in the original/default precision, so actual memory exceeds the raw bit-per-parameter arithmetic. [Hugging Face bitsandbytes documentation](https://huggingface.co/docs/transformers/main/en/quantization/bitsandbytes)
- Qwen2.5-VL documentation includes an int4 weight-only quantization example and says image resolution can be capped with `min_pixels`/`max_pixels`. [Transformers Qwen2.5-VL docs](https://huggingface.co/docs/transformers/main/en/model_doc/qwen2_5_vl)

### Inferences

Raw weight memory calculations use decimal model parameters and decimal GB (1 billion bytes); GPU vendors/cloud pages generally advertise GB/GiB imprecisely. Practical ranges below include quantization metadata, unquantized modules, runtime/context and vision working space, and reserve headroom; they are sizing estimates, not guaranteed peak measurements.

| Nominal model | Precision | Raw weight lower bound | Practical single-request VRAM budget | Practical implication |
|---|---:|---:|---:|---|
| 3B | BF16/FP16 | ~6 GB | ~9–13 GB | 12–16 GB device; batch 1, moderate resolution |
| 3B | 8-bit | ~3 GB | ~6–10 GB | 8–12 GB device; extra room for larger images/batch |
| 3B | 4-bit | ~1.5 GB | ~5–8 GB | 8 GB may work at batch 1; 12 GB more comfortable |
| 7B | BF16/FP16 | ~14 GB | ~19–26 GB | 24 GB tight at large images/batch; 32 GB safer |
| 7B | 8-bit | ~7 GB | ~11–16 GB | 16 GB batch 1; 24 GB preferable for batching |
| 7B | 4-bit | ~3.5 GB | ~8–12 GB | 12–16 GB batch 1; 16 GB has useful headroom |

The “practical” column includes an estimated 2–4 GB runtime/vision/temporary buffer allowance at batch 1, with additional context/KV cache and per-image activations varying by model implementation, image resolution, and batch size. The 7B labels map to roughly 8B on the model card, so use actual checkpoint parameter count and measured `torch.cuda.max_memory_allocated()` for final procurement. At 4-bit, quantizing only linear layers does not make the entire model exactly 0.5 bytes/parameter: scales/metadata, embeddings, norms, vision modules, and kernels consume additional memory.

Vision token count is a more useful operational control than input JPEG size: raise/lower `max_pixels` and sample actual `image_grid_thw` or processor outputs, especially for long thermal-paper receipts, multi-page PDFs, and double-page scans. A page split into two crops is approximately two images’ vision compute and activation burden. Batch memory scales roughly with the sum of per-request image tokens (plus padding/cache), not simply batch count; group similarly sized pages or use a token-budgeted dynamic batch.

## What are plausible throughput and cost per page on one rented GPU, including 4-bit/8-bit and batching?

### Takeaway

For a cost model, a 3B VLM at 4-bit on an L4-class GPU is a plausible low-cost baseline; a 7B 4-bit model on 16–24 GB is a quality-oriented candidate. Public hourly rates cited here range from $0.49/hr for Runpod L4 Secure Cloud to $0.74/hr for RTX 4090 Secure Cloud; at 2–10 seconds/page, GPU-only compute is roughly $0.00027–$0.00206/page before utilization, preprocessing, storage, retries, and engineering. There are no cited apples-to-apples public benchmarks for this exact invoice workload in this note: throughput numbers are planning scenarios to validate by replaying the actual document set.

### Cited Findings

- Runpod currently lists L4 24 GB at $0.49/hour Secure Cloud and RTX 4090 24 GB at $0.74/hour Secure Cloud (Community Cloud prices are lower); A40 48 GB is $0.49/hour Secure Cloud. The page distinguishes Pods (dedicated GPU hourly) from Serverless. [Runpod GPU pricing](https://www.runpod.io/gpu-instance/pricing)
- Lambda lists one-GPU instances by minute, including A6000 48 GB at $1.09/GPU-hour, A100 40 GB at $1.99/hour and H100 80 GB at $4.29/hour in its 1-GPU table. Its page notes applicable sales taxes. [Lambda GPU instances and rates](https://lambda.ai/service/gpu-cloud)
- Hugging Face provides a batch-inference example for Qwen2.5-VL, establishing that multi-input batch operation is supported; it does not promise a specific speedup. [Qwen2.5-VL model card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)

### Inferences

**Reproducible planning assumptions (not benchmark claims).** One “page” means one invoice/receipt image, one VLM pass, one structured JSON response, no second-pass validation, no OCR fallback, no network wait, and no model startup/load time. Use an image cap around 1,280 visual tokens/page as the starting point; cap output at 200–400 tokens (central case 300); use an optimized inference server with mixed-precision compute and batch 1. Proposed end-to-end GPU service-time scenarios, to replace with a measured benchmark: 3B 4-bit, 2–5 sec/page; 3B 8-bit, 2–5 sec/page; 7B 4-bit, 4–10 sec/page; 7B 8-bit, 4–10 sec/page. These wide brackets deliberately overlap because hardware/kernel/model details dominate and quantization can trade memory for speed without a universal direction. High-resolution/crop-expanded pages, long outputs, or Transformers eager inference may take materially longer.

**GPU-only cost formula:** `hourly GPU price × seconds per page / 3,600`. At $0.49/hr, 2 sec = $0.000272/page, 5 sec = $0.000681, 10 sec = $0.001361. At $0.74/hr, the respective costs are $0.000411, $0.001028, and $0.002056. At Lambda A6000 $1.09/hr, they are $0.000606, $0.001514, and $0.003028. If a second pass doubles inference time, compute cost/page doubles. For throughput `pages/sec=1/service_seconds`; 2–5 seconds means 0.2–0.5 pages/sec (720–1,800/hr) for a single non-batched stream; 4–10 seconds means 0.1–0.25 pages/sec (360–900/hr).

**Illustrative table at central 5-sec 3B / 8-sec 7B scenario, GPU-only.**

| GPU/rate | 3B at 5 sec | 7B at 8 sec | Hourly throughput (same assumed service time) |
|---|---:|---:|---:|
| Runpod L4 Secure, $0.49/hr | $0.000681/page | $0.001089/page | 720 pages/hr (3B); 450 (7B) |
| Runpod RTX 4090 Secure, $0.74/hr | $0.001028/page | $0.001644/page | 720 (3B); 450 (7B) |
| Lambda A6000, $1.09/hr | $0.001514/page | $0.002422/page | 720 (3B); 450 (7B) |

The throughput table holds inference time constant to isolate rate effects; a faster GPU may improve throughput, but does not necessarily reduce cost/page if hourly price rises proportionately. For an unknown workload, planning uncertainty is at least 2–4x around the central cost estimate because service time can vary with pages’ visual-token count, handwriting/legibility, batch size, kernel support, and generation length. Rates are snapshots and should be checked at deployment; Community Cloud versus Secure Cloud price/availability/security terms may not be comparable.

**Batching.** There is no dependable universal multiplier: larger batches improve GPU occupancy, but vision prefill, decode, padding, memory pressure, and output generation interact. For rough capacity planning only, test batch sizes 1, 2, 4, and 8 with matched resolution and token caps. A provisional 1.3–2.5x aggregate throughput uplift at batch 4 over batch 1 is an explicit hypothesis, not sourced benchmark evidence; it must be replaced by measured pages/sec and p95 latency. If 5-sec/page serial becomes 2.5–3.8 effective GPU-seconds/page after that uplift, $0.49/hr compute is about $0.00034–$0.00052/page. Cost per page falls only to the extent GPU busy time/page falls; with a per-page execution time unchanged it does not. Batch latency can increase, and synchronous batch completion waits for the slowest page. Bucket receipts by resolution/token size and use a max-token budget so one giant scan does not set batch memory for all items.

**4-bit vs 8-bit recommendation.** Start with 4-bit for 7B when VRAM is constrained and benchmark invoice-field exact match, JSON validity, and totals/line-item accuracy against 8-bit on a human-reviewed sample. If 8-bit fits, its lower quantization severity can be a safer accuracy/engineering choice, but no general accuracy delta is asserted here. The cost/page difference is primarily the observed seconds/page and achievable batching, not “4-bit is half the price.” On 24 GB GPUs, 7B 8-bit should generally have enough room for moderate batch, subject to image token and framework overhead. On 16 GB, 7B 4-bit is the more robust setup; keep batch modest and cap image tokens.

## What uncertainty and reproducible validation are needed before choosing self-hosting?

### Takeaway

Public cloud rates make raw GPU compute pennies per thousand invoice pages under the assumed service times, but the estimate is dominated by unmeasured application throughput and billable idle/startup time rather than arithmetic. The meaningful decision is workload-specific: document quality/accuracy, arrival pattern and GPU utilization, not just a single nominal cost/page.

### Cited Findings

- Runpod lists storage separately, including container/volume pricing, and has separate serverless and pod billing models; this means the displayed GPU hourly rate is not a complete deployment TCO. [Runpod pricing](https://www.runpod.io/gpu-instance/pricing)
- Lambda describes instance billing by the minute and says no egress fees; advertised rates exclude applicable taxes. [Lambda GPU cloud](https://lambda.ai/service/gpu-cloud)
- Qwen model docs recommend adjusting max pixel count as a performance/memory tradeoff and support mixed batches; these are knobs that should be included in workload benchmarks. [Qwen2.5-VL model card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct); [Transformers docs](https://huggingface.co/docs/transformers/main/en/model_doc/qwen2_5_vl)

### Inferences

Reproduce/replace the estimate with a controlled test: record the checkpoint revision, quantization backend/type (e.g., NF4 or int8), GPU SKU and provider price, serving stack/version, attention/kernel settings, image processor `min_pixels`/`max_pixels`, actual visual tokens/page, max output tokens, batch size/token budget, and warm/cold state. Use a representative stratified set (scanned invoices, photographed receipts, long receipts, multi-page documents, language/quality variations) and report median/p90/p95 latency, completed pages/sec, peak GPU memory, JSON-valid rate, field-level accuracy, and cost per correct page. Separate preprocessing and PDF rasterization time from GPU time; include retries and fallback rates in production costs. Run each batch size repeatedly after warm-up and quote a confidence interval/range rather than one best run.

At low utilization, continuously rented GPU cost can exceed the compute-only figure substantially: e.g., a $0.49/hour instance running at 10% useful utilization makes effective cost per successfully processed page about 10x the fully utilized compute cost (before fixed setup and storage). Scale-to-zero/serverless can avoid that idle cost but may add cold starts and different rates; compare actual billable duration and service-level latency. Local owned GPU economics require amortized hardware purchase, power, cooling, maintenance, and operator time; no such inputs were specified, so cloud rates are the reproducible baseline rather than an ownership break-even claim.

### Gaps

- No public, reproducible benchmark was located here giving Qwen2.5-VL 3B/7B invoice-page throughput across both 4-bit and 8-bit on the same single GPU at a stated resolution/batch. Throughput scenarios above are estimates that require workload benchmarking.
- Actual invoices’ visual-token distribution, field extraction accuracy requirements, receipt length, concurrency/arrival pattern, and monthly volume were not provided; those could alter recommended GPU, batching, and effective unit economics.
- Quantization support and performance vary by framework and checkpoint/module. Confirm the selected VLM implementation supports the chosen 4/8-bit backend for both language and vision components; measure memory and accuracy rather than assuming every submodule is quantized.

## References and calculation notes

Rates checked 2026-09-26; listed prices are USD per GPU-hour and exclude taxes and any storage/add-on charges unless stated. Prefer Secure Cloud/paid-provider rates for the primary table; Runpod Community Cloud offers lower but separate market pricing and should not be mixed into apples-to-apples comparisons. The per-page tables are derived arithmetically from stated prices and assumed service seconds; they are not provider quotes or independently measured benchmarks.

Primary sources: [Qwen2.5-VL-3B card](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct), [Qwen2.5-VL-7B card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct), [Hugging Face bitsandbytes quantization guide](https://huggingface.co/docs/transformers/main/en/quantization/bitsandbytes), [Transformers Qwen2.5-VL guide](https://huggingface.co/docs/transformers/main/en/model_doc/qwen2_5_vl), [Runpod rates](https://www.runpod.io/gpu-instance/pricing), [Lambda rates](https://lambda.ai/service/gpu-cloud).

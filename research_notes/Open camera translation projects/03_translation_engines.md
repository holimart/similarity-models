# Open translation engines for live on-device camera translation

## Which candidates best fit Czech–English and multilingual offline translation?

### Takeaway
For an embedded live-camera product, benchmark **Bergamot/Marian small CPU-optimized models** and **direct Czech↔English OPUS-MT models** first: these have the best demonstrated consumer-device/browser deployment orientation, and pair-specific models avoid loading a very large multilingual checkpoint. **Argos Translate** is the simplest packaged offline route with Czech in its language catalog, while NLLB-200 and M2M100 bring much broader language coverage at substantially greater model/runtime cost; NLLB also has a non-commercial-only model license.

### Cited Findings
- Argos Translate is a Python offline translation library based on OpenNMT; it installs `.argosmodel` packages, supports language models and can pivot through intermediary languages when no direct pair is installed (with a quality cost). Its project lists Czech and English among supported languages. [Argos Translate](https://github.com/argosopentech/argos-translate)
- The Argos package index is the official catalog/download entry point. The web catalog did not expose reliable package byte sizes or package-level license terms during this review; verify each Czech↔English model's metadata/download and bundled notices before distribution. [Argos package index](https://www.argosopentech.com/argospm/index/); [index repository](https://github.com/argosopentech/argospm-index)
- Marian is an efficient pure-C++ neural machine translation framework, supports CPU and GPU inference, and is MIT-licensed. Bergamot wraps Marian with an API specifically optimized for consumer-grade devices and can build native or WebAssembly versions. [Marian](https://github.com/marian-nmt/marian-dev); [Bergamot Translator](https://github.com/browsermt/bergamot-translator)
- Mozilla's Firefox Translations extension supported Czech in its production set and used Bergamot WASM locally; the extension is archived and its README says translation development moved into Firefox from version 108. It is evidence of practical offline/browser architecture, not a maintained standalone camera SDK. [Firefox Translations (archived)](https://github.com/mozilla/firefox-translations)
- Mozilla's model project describes `tiny` models as fastest/smallest but lower quality, `base` as better quality but slower/larger, and `base-memory` as lower-memory with somewhat lower quality. Model hosting moved from the archived repository to Mozilla's current translations project/storage; check the model registry for current pair availability. [Firefox Translations models (archived; migration notice and configuration descriptions)](https://github.com/mozilla/firefox-translations-models); [current model registry](https://mozilla.github.io/translations/model-registry/)
- Helsinki-NLP publishes separate Marian/OPUS-MT Czech→English and English→Czech checkpoints. Their cards identify the language directions, normalization plus SentencePiece preprocessing, and Apache-2.0 model license. They report test-set metrics and link original downloadable model archives, but not a standardized on-device latency result. [cs→en model card](https://huggingface.co/Helsinki-NLP/opus-mt-cs-en); [en→cs model card](https://huggingface.co/Helsinki-NLP/opus-mt-en-cs)
- The OPUS-MT model cards identify separate directional checkpoints, so supporting both directions means distributing/loading two models (or a suitable combined alternative), and the tokenization/preprocessing must match the model. [cs→en](https://huggingface.co/Helsinki-NLP/opus-mt-cs-en); [en→cs](https://huggingface.co/Helsinki-NLP/opus-mt-en-cs)
- NLLB-200 distilled 600M is a multilingual model carded for 196 languages and single-sentence translation; its license is CC-BY-NC-4.0 and its authors explicitly state it is a research model, not released for production deployment. It is therefore a poor fit where commercial use is intended without separate permission. [NLLB-200 distilled 600M model card](https://huggingface.co/facebook/nllb-200-distilled-600M)
- M2M100 418M is a many-to-many multilingual encoder-decoder covering 100 languages and 9,900 language directions, including Czech and English; its Hugging Face model card lists MIT. Translation requires setting the source language and forcing the target-language token. [M2M100 418M model card](https://huggingface.co/facebook/m2m100_418M)
- As a rough lower bound from parameter count only, dense 600M and 418M checkpoints require about 1.2 GB and 0.84 GB respectively for FP16 weights (about twice that in FP32), before tokenizer, runtime, temporary activations, and app overhead. This is a calculation, not a published model-package size. OPUS pair models and Bergamot model variants may be much smaller, but their exact deployed sizes depend on checkpoint/quantization; retrieve current artifacts and measure rather than assuming a fixed value.
- No comparable, current benchmark in tokens/second or camera-text latency across these candidates and target phones was found in the reviewed primary documentation. OCR, crop/line segmentation, repeated recognition, and rendering are additional latency costs outside the MT model.

### Inferences
- For **Czech↔English only**, two compact directional models (OPUS-MT or Bergamot pair models) are likely to use less storage/RAM than a 418M/600M all-language model and may yield better pair quality, but that expectation requires device benchmarking and task-specific evaluation.
- For **many languages**, M2M100 is commercially more plausible from the stated model license than NLLB, but its 418M parameters make it a significant mobile footprint. NLLB offers even broader language coverage but has a material usage restriction and research-only caveat.
- Bergamot's WASM and CPU optimization make it the clearest architectural precedent for offline, incremental consumer-device MT. An app can reuse its engine/models only after checking model pair coverage, platform integration, runtime compatibility, and all transitive/model terms.
- OCR output typically consists of short phrases or fragmented lines rather than well-formed sentences. Sentence context and batching may materially affect MT quality; camera translation should preserve line/region grouping where practical and evaluate signage/menu samples, not rely only on published news-domain benchmarks.

### Gaps
- Exact current disk sizes, peak RAM, warm/cold-start latency, and energy use on specific Android/iOS devices were not published in the reviewed primary sources. Benchmark representative mid-range and low-end target devices, including OCR-to-overlay end-to-end latency.
- Exact current Argos Czech↔English package availability, byte size, provenance and model license need confirmation from the live package metadata/artifacts; the engine's software license does not itself settle model terms.
- Current Firefox/Bergamot model-registry pair availability and licensing for redistribution should be checked artifact by artifact; the legacy repositories are archived and point to migrated storage.

## How do software licenses differ from model licenses, and what are the practical deployment constraints?

### Takeaway
Treat the **engine/software**, **model weights**, **tokenizer/vocabulary**, and sometimes training data as distinct assets with potentially distinct terms. A permissively licensed runtime does not make a checkpoint commercially usable: NLLB's CC-BY-NC-4.0 restriction is the clearest example, while OPUS-MT and M2M100 cards state Apache-2.0 and MIT respectively.

### Cited Findings
- Argos Translate itself is dual-licensed MIT or CC0. This license statement covers the project software; Argos separately distributes model packages, so inspect their included model-specific licensing/metadata. [Argos Translate license](https://github.com/argosopentech/argos-translate)
- LibreTranslate is an AGPL-3.0 self-hosted API powered by Argos Translate. It is a server/API application layer, not a model or translation engine checkpoint; running it locally can provide an offline service but is not necessary for embedding Argos directly in an app. [LibreTranslate](https://github.com/LibreTranslate/LibreTranslate)
- Marian's framework license is MIT; Bergamot's repository is MPL-2.0. Those are software licenses and do not automatically establish the license for a Marian-format model distributed separately. [Marian](https://github.com/marian-nmt/marian-dev); [Bergamot](https://github.com/browsermt/bergamot-translator)
- The OPUS-MT Czech↔English model cards explicitly state Apache-2.0 for the model repositories. [cs→en](https://huggingface.co/Helsinki-NLP/opus-mt-cs-en); [en→cs](https://huggingface.co/Helsinki-NLP/opus-mt-en-cs)
- The M2M100 418M model card explicitly lists MIT. [M2M100 418M](https://huggingface.co/facebook/m2m100_418M)
- The NLLB-200 distilled 600M model card lists CC-BY-NC-4.0 and says the model is intended for research, not production deployment. [NLLB-200 distilled 600M](https://huggingface.co/facebook/nllb-200-distilled-600M)
- LibreTranslate's AGPL applies to that server software. Argos and LibreTranslate are not interchangeable licenses: embedding the Argos library and deploying/modifying the LibreTranslate network service are different software choices. [Argos Translate](https://github.com/argosopentech/argos-translate); [LibreTranslate](https://github.com/LibreTranslate/LibreTranslate)

### Inferences
- Before shipping, create an asset inventory per supported direction: engine binaries/source and dependency licenses; model checkpoint and tokenizer licenses; any quantized/converted derivatives; and OCR/model assets. Preserve required notices and assess attribution/share-alike/non-commercial obligations with counsel for the intended distribution and business model.
- For strict offline operation, fetch and package/cache models in advance, load them locally, and ensure camera frames/text are not sent to any remote service. Argos and LibreTranslate both support self-host/offline workflows, but using LibreTranslate as an API entails operating a local service and does not remove model-download/setup requirements.
- LibreTranslate is usually excessive as an in-process mobile dependency: it is designed as an API/web service around Argos. For a mobile camera app, integrate a native/local translation runtime directly unless an independently hosted local API architecture is specifically desired.

### Gaps
- The reviewed sources do not establish the license for every Argos `.argosmodel`, every current Firefox model artifact, or every transitive dependency and model conversion. Check the actual downloaded artifact and repository notices before redistribution.
- This is a technical research note, not a legal interpretation. License compatibility depends on the product's deployment, distribution, and commercial circumstances.

## What should be shortlisted and tested for live camera translation?

### Takeaway
Use a staged shortlist: (1) Bergamot tiny/base Czech↔English models for the most relevant mobile-oriented baseline, (2) OPUS-MT cs→en and en→cs as pair-specific quality/storage baselines, (3) Argos packages for fastest offline integration, and (4) M2M100 only when broad multilingual coverage justifies a larger model. Exclude NLLB from commercial production planning unless its terms/use restrictions are resolved.

### Cited Findings
- Bergamot explicitly targets optimized translation on consumer-grade devices and provides both native and WebAssembly builds, unlike a research-only large checkpoint path. [Bergamot Translator](https://github.com/browsermt/bergamot-translator)
- Mozilla's deployed client-side Firefox translation architecture was based on Bergamot WASM, included Czech among production languages, and model metadata differentiates speed/size/quality tiers (`tiny`, `base`, `base-memory`). Its extension and model repositories are now archived, making current maintenance/model availability a verification item. [Firefox Translations](https://github.com/mozilla/firefox-translations); [model archive and migration links](https://github.com/mozilla/firefox-translations-models)
- OPUS-MT supplies Czech-English checkpoints in both directions, with model cards and published benchmark metrics. [cs→en](https://huggingface.co/Helsinki-NLP/opus-mt-cs-en); [en→cs](https://huggingface.co/Helsinki-NLP/opus-mt-en-cs)
- Argos packages can be installed locally and translated without a remote API; missing direct directions can pivot through an installed intermediary, at the cost of quality. [Argos Translate](https://github.com/argosopentech/argos-translate)
- M2M100 directly supports many-to-many translation across 100 languages and includes Czech; model card code demonstrates explicit source/target language control. [M2M100](https://huggingface.co/facebook/m2m100_418M)
- NLLB supports 196 languages but carries CC-BY-NC-4.0 and its model card disclaims production deployment. [NLLB](https://huggingface.co/facebook/nllb-200-distilled-600M)

### Inferences
- Measure at least: app/model download size per language configuration; peak resident RAM and load time; latency per OCR region and per full camera frame; sustained throughput/thermal throttling; battery draw; and translation quality on photographed signs, menus, labels, glare, perspective, mixed scripts, and OCR errors.
- Compare model variants at identical OCR text, decoding settings, and hardware; report warm and cold model startup separately. Use BLEU/chrF only as supplementary measures and add human adequacy checks for short, context-poor text.
- A robust product may select a small fast model by default and permit optional downloads for additional language pairs; camera-overlay latency benefits from incremental region updates, while avoiding excessive repeated inference on unchanged text.

### Gaps
- No primary source reviewed offered apples-to-apples phone speed or memory data for all named projects. The recommendation is a shortlist based on documented architecture, language coverage and model scale, not a claim of measured winner.
- OCR engine and overlay implementation are outside these translation-project sources; full camera performance cannot be inferred from MT model benchmarks alone.

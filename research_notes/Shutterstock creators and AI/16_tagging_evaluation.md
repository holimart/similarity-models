# Evaluating AI-Generated Image Captions and Keywords

## What existing evaluations reveal about caption accuracy, hallucination, and coverage

### Takeaway
Standard caption similarity scores are not sufficient evidence that captions are visually correct: models can produce fluent, benchmark-like descriptions while inventing objects or omitting useful details. Evaluate factual grounding separately from coverage and language quality, using both reference-based benchmarks and image-conditioned checks.

### Cited Findings
- Rohrbach et al. introduce CHAIR (Caption Hallucination Assessment with Image Relevance), evaluating mentioned objects against human-annotated visual labels on MS COCO. They report that stronger scores on standard sentence metrics do not always correspond to less object hallucination, and associate more hallucination with language-prior-driven errors. [Object Hallucination in Image Captioning, EMNLP 2018](https://arxiv.org/abs/1809.02156)
- CHAIR distinguishes hallucinated object mentions from total object mentions and from captions containing at least one hallucination. It is useful for object-level precision, but does not by itself measure whether the caption captures all salient content, nor validate subjective attributes or fine-grained relations. [Paper](https://arxiv.org/abs/1809.02156)
- The nocaps benchmark was designed to test novel-object captioning beyond the restricted concepts in common caption training data. It contains 166,100 human captions for 15,100 Open Images validation/test images; nearly 400 test-image object classes have no or few associated training captions. This is a useful stress test for long-tail vocabulary and out-of-distribution subjects, though its benchmark captions do not directly measure commercial search success. [nocaps benchmark](https://nocaps.org/)
- Hessel et al. find CLIPScore, an image-text compatibility metric, correlates with human caption judgments better than the evaluated reference-based metrics across several corpora; combining it with reference-based similarity as RefCLIPScore further improves correlation. They also report weaker performance for news captions requiring richer context. Similarity scores are proxies, not proof of factuality or completeness. [CLIPScore, EMNLP 2021](https://arxiv.org/abs/2104.08718)
- Conventional metrics such as CIDEr and SPICE compare generated text with human references. Reference captions describe only a subset of valid image content; consequently, paraphrases or useful tags missing from references can be penalized, while a plausible phrase shared with references may still fail to verify every asserted detail. [CLIPScore paper](https://arxiv.org/abs/2104.08718); [Object Hallucination paper](https://arxiv.org/abs/1809.02156)

### Inferences
- For stock metadata, report object precision (unsupported entity mentions / all entity mentions) and recall (relevant visible entities or concepts recovered / annotated relevant concepts) separately. A single aggregate caption score conceals the practical trade-off: false tags can harm trust and relevance, while omissions reduce discovery.
- Build evaluation sets with both common and uncommon subjects, multiple styles (isolated product, editorial, lifestyle, illustration), and difficult distinctions such as breed/species, exact setting, age, emotion, and inferred activity. The nocaps design supports the importance of long-tail testing; the category list and adjudication rules need to be adapted to the actual catalogue.

### Gaps
- The cited caption benchmarks do not directly establish how model-generated stock keywords affect Shutterstock search ranking, conversion, or contributor earnings.
- Available benchmark findings are not a universal current-model error rate; results depend on model, prompt, image domain, and annotation policy.

## How to test keyword relevance, precision/recall, and search utility in practice

### Takeaway
Treat keywords as ranked retrieval metadata, not simply as a list of words similar to a reference caption. Measure whether each proposed keyword is visually defensible, whether important concepts are missed, and whether the metadata retrieves useful assets for real buyer queries.

### Cited Findings
- The MS COCO captioning and object-label setting gives a repeatable basis for checking recognized objects; CHAIR demonstrates why visually grounded label comparison should supplement text-to-text metrics. However, object labels alone are not a complete vocabulary for stock search (e.g., mood, composition, use case, color, and abstract concepts). [CHAIR paper](https://arxiv.org/abs/1809.02156)
- nocaps deliberately evaluates concepts underrepresented in caption training data, providing a practical model for a separate long-tail slice rather than relying only on random samples dominated by frequent objects. [nocaps](https://nocaps.org/)
- CLIPScore evaluates image-text compatibility without requiring a reference caption, and can complement reference-based measures. It evaluates a caption as a whole; a high score should not be interpreted as validation of every individual keyword in a long list. [CLIPScore](https://arxiv.org/abs/2104.08718)
- Shutterstock’s contributor keyword guidance is the platform-specific primary source to consult when operationalizing keyword policy; its guidance should be applied alongside factual checks, since platform metadata rules and model-evaluation metrics answer different questions. [Shutterstock contributor resources](https://submit.shutterstock.com/help/en/)

### Inferences
- A practical offline protocol: (1) sample a stratified set of real portfolio images; (2) have two reviewers independently mark visible facts and useful search concepts, with adjudication; (3) generate captions/tags blind to the reference; (4) classify each output term as supported, unsupported, ambiguous, or irrelevant; (5) score precision, recall, F1, and unsupported-claim rate, with results split by concept type and image category.
- For multi-label keywords, compute per-image precision and recall against an adjudicated set, plus micro- and macro-averages across images/categories. Report recall at a fixed keyword budget and precision among top-ranked suggestions: these make the cost of a limited keyword allowance explicit. Do not treat every absent reference keyword as a definite false positive—reviewers may omit valid synonyms and concepts.
- Add a query-based retrieval test: create realistic buyer queries, compare search results from human metadata, AI metadata, and AI-plus-human-edited metadata, and have blinded reviewers grade relevance in top-k results. Track nDCG@k or precision@k and query success, plus search/business outcomes only in a controlled live experiment. Offline keyword correctness and online retrieval performance are related but not interchangeable.
- Audit taxonomy separately: exact object/name, broader category, attributes, scene/context, activity/relationships, style/medium, and conceptual/use-case terms. Require direct visual evidence for factual claims; mark inferred or contextual concepts separately and permit removal. Measure unsupported terms especially for brands, locations, identities, and sensitive attributes.

### Gaps
- I did not find a public, controlled study isolating the effect of AI-generated stock-photo keywords on Shutterstock buyer retrieval or sales. Platform ranking signals and commercial query logs are generally not public.
- There is no single accepted ground-truth list of all useful keywords for an image. Annotation instructions and human agreement should be published with any precision/recall result.

## Human review and implications for stock search workflows

### Takeaway
Use AI as a candidate generator and human review as the quality-control step, especially for specific claims and nuanced metadata. The strongest evaluation combines automated screening with blinded human relevance judgments and eventual search testing, because each catches a different failure mode.

### Cited Findings
- Caption-model hallucination persists even when standard text metrics look strong, motivating explicit image-grounded review rather than accepting fluent output at face value. [Rohrbach et al.](https://arxiv.org/abs/1809.02156)
- CLIPScore is designed to align with human judgments of image-caption compatibility and is complementary to reference-based scores, but its reported weakness on context-heavy news descriptions cautions against treating one automated metric as universally reliable. [Hessel et al.](https://arxiv.org/abs/2104.08718)
- nocaps demonstrates that performance on familiar object concepts does not ensure performance on novel or sparse-training concepts. Human reviewers should therefore be especially attentive to rare subjects, specialized terminology, and visually ambiguous details. [nocaps](https://nocaps.org/)
- Shutterstock publishes contributor-facing help and metadata information; operational keyword review should be aligned with the current platform rules rather than assuming benchmark labels define acceptable commercial metadata. [Shutterstock Contributor Help](https://submit.shutterstock.com/help/en/)

### Inferences
- A human review interface should show the image beside each suggested keyword, distinguish high-confidence visible objects from speculative context terms, and make accept/edit/delete actions quick. Reviewers should be able to flag an unsupported claim, not just rewrite the caption.
- Use automated scores to triage rather than auto-approve: send low image-text compatibility, rare entities, identity/location/brand claims, and disagreements between independent systems to human review. Audit a random sample of high-scoring outputs too, so systematic overconfidence is visible.
- For stock search, optimize for a balanced metadata set: accurate central subject terms first, then supported attributes and useful contextual/search-intent terms. Avoid padding with loosely associated or trending terms; irrelevant keywords can make retrieval less precise even when they increase nominal tag count.
- Run periodic blinded reviewer calibration and report agreement. Resolve policy ambiguity in the annotation guide, because measured precision is only meaningful relative to a consistent definition of “relevant” and “visible.”

### Gaps
- Public papers establish evaluation methods and known captioning limitations, but provide little direct evidence about the ideal human-review rate or the return on investment of human editing in commercial stock catalogues.
- Publicly accessible platform documentation does not reveal the full search-ranking algorithm, so metadata evaluation cannot infer exact ranking weights from contributor rules alone.

# Privacy, security, and compliance for invoice/receipt visual extraction

## What sensitive data is present, and what does GDPR require?

### Takeaway
Invoices and receipts should be treated as confidential business records that commonly contain personal data and financial/business-sensitive details; the image, OCR text, normalized fields, and logs can each remain sensitive. GDPR does not classify ordinary financial data as a special category by itself, but identifiers, sole-trader details, payment data, and contextual purchases can be personal data; minimize what is captured and define a lawful, purpose-limited processing path.

### Cited Findings
- GDPR personal data includes information relating to an identified or identifiable natural person; the definition is not limited to directly identifying fields (Article 4(1)). Processing includes collection, storage, consultation, disclosure, and erasure (Article 4(2)). [GDPR, Articles 4(1)–(2)](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)
- Common invoice/receipt content—names, home/business addresses of sole traders, email/phone, tax identifiers, bank account/payment references, items purchased, dates, locations, and totals—can identify or profile a natural person. Whether a field is personal data is context-dependent under GDPR’s identifiability definition. [GDPR, Article 4(1)](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)
- GDPR special categories are specifically enumerated (racial/ethnic origin, political opinions, religion, trade-union membership, genetic/biometric data used for unique identification, health, sex life/sexual orientation); financial information is not separately enumerated. A receipt can nevertheless incidentally disclose a special category, such as health-related purchases, depending on what it reveals and context. [GDPR, Article 9](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)
- Controllers must establish a lawful basis, purpose limitation, data minimization, accuracy, storage limitation, integrity/confidentiality, and accountability; the controller must be able to demonstrate compliance. [GDPR, Article 5](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng); [GDPR, Article 6](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)
- Where a processor handles documents for a customer, Article 28 requires a binding processing contract covering documented instructions, confidentiality, security, subprocessor authorization, assistance with rights/compliance, deletion or return, and audit information. [GDPR, Article 28](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng); [EDPB Guidelines 07/2020 on controller and processor](https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-072020-concepts-controller-and-processor-gdpr_en)
- GDPR requires risk-appropriate technical and organizational measures, including as appropriate encryption/pseudonymisation, resilience, restoration, and regular testing (Article 32). A personal data breach must be notified to the supervisory authority within 72 hours where the Article 33 threshold is met; processor-to-controller notice must be without undue delay. [GDPR, Articles 32–33](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)

### Inferences
- Treat source images and extracted output as the same sensitivity tier by default: removing the image while keeping vendor/person, item, timestamp, and payment data may not meaningfully anonymize the record.
- Prefer field allowlists (e.g., vendor, date, total, tax) over full-page OCR when the task does not need line-item descriptions, contact details, or payment fragments. Redact before external processing when those fields are not needed.
- If receipts may reveal health, religious, or other Article 9 information, perform the special-category assessment for the real workflow; do not assume that “receipt processing” makes these data irrelevant.

### Gaps
- This note does not determine the lawful basis, controller/processor role, or whether a DPIA is required for any particular product; those depend on purpose, scale, context, and deployment.

## Cloud vendors: residency, retention, training use, and controls

### Takeaway
Cloud document AI can provide managed infrastructure, regional choices, encryption, and access controls, but the product’s exact endpoint, region, settings, logs, and contractual terms determine whether the arrangement meets requirements. “Not used for training” does not mean “not retained”; verify image/input retention, derived output, logs, support access, subprocessors, and deletion separately.

### Cited Findings
- Amazon Textract communicates through HTTPS endpoints in supported Regions. AWS places responsibility for content configuration and access on the customer under its shared-responsibility model, and recommends IAM least privilege, MFA, TLS, CloudTrail, and encryption. AWS warns that free-form text fields can enter diagnostic logs. [AWS Textract data protection](https://docs.aws.amazon.com/textract/latest/dg/data-protection.html)
- AWS states that customers choose the Region(s) where customer content is stored and that AWS will not move or replicate that content outside chosen Regions without agreement; customers can select encryption/key controls. [AWS Data Privacy FAQs](https://aws.amazon.com/compliance/data-privacy-faq/)
- Textract Custom Queries adapter training content is processed in the training Region, encrypted in transit/at rest, and deleted when training completes; AWS says training images, prelabeling results, and annotations are not logged or retained for debugging in that workflow. This is a feature-specific commitment, not a blanket description of all Textract processing. [AWS Textract data protection](https://docs.aws.amazon.com/textract/latest/dg/data-protection.html)
- Azure Document Intelligence provides prebuilt invoice and receipt models and operates as a cloud service; it offers custom models trained from labeled datasets. Region availability and the configured Azure resource region should be confirmed against the current product-region and data-residency documentation for the chosen API/feature. [Microsoft Azure Document Intelligence overview](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview?view=doc-intel-4.0.0)
- Microsoft documents that requests can be configured to analyze page ranges and that custom training datasets are uploaded to train custom models; training is distinct from ordinary inference and needs its own data handling decision. [Document Intelligence quotas and limits](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/service-limits?view=doc-intel-4.0.0)
- OpenAI states that API data is not used to train or improve models unless the customer explicitly opts in. By default, abuse-monitoring logs may include customer content and are retained up to 30 days, subject to stated exceptions; Zero Data Retention and Modified Abuse Monitoring require eligibility/approval and endpoint limitations. [OpenAI API data controls](https://platform.openai.com/docs/guides/your-data)
- OpenAI’s data-residency controls are project- and endpoint/model-dependent. The documentation distinguishes storage residency from regional processing; system data is outside the customer-content residency promise, regional processing is available only for listed supported combinations, and some non-US regions require approved retention controls. [OpenAI API data controls—data residency](https://platform.openai.com/docs/guides/your-data#data-residency-controls)
- Google Document AI publishes product documentation for security/compliance, customer-managed encryption keys, audit logging, and regional/multi-regional support; check the selected processor and location rather than assuming every processor has identical location behavior. [Google Document AI security and compliance](https://cloud.google.com/document-ai/docs/security); [Google Document AI regional and multi-regional support](https://cloud.google.com/document-ai/docs/regions)

### Inferences
- A cloud vendor comparison should be made at the API-feature level, not brand level. For each candidate record: ingress region, inference region, result storage, support/diagnostic logging, custom training path, subprocessor list, deletion SLA, and contractual commitments.
- Cloud is practical when throughput and managed controls matter and the organization can accept a processor relationship and documented transfers. Configure resources in approved regions, avoid content in filenames/tags/free text, restrict console access, encrypt storage, and keep application logs free of document contents.
- Ask vendors to confirm contractually how backups, transient buffers, abuse/safety logs, diagnostic logs, and legal holds behave after deletion. Public product documentation may describe standard behavior but may not settle account-specific settings or service terms.

### Gaps
- Product-specific terms and regional processing change frequently. The citations are primary documentation, but procurement should revalidate the current DPA, subprocessor list, region matrix, retention controls, and selected SKU/API before launch.
- The Google security URL was available, but details can vary by processor/location; the documentation should be checked for the selected processor and current service terms.

## On-premises/open-weight models versus managed cloud

### Takeaway
Self-hosting can keep images and outputs inside an organization-controlled network and avoid routine third-party inference transfer, but it transfers security, availability, model-quality, patching, logging, and deletion responsibilities to the operator. “Open model” does not by itself mean open source, unrestricted commercial use, or compliant processing: review model-specific licenses and dependencies.

### Cited Findings
- Ollama documents a local API endpoint (`localhost:11434`) compatible with the OpenAI Chat Completions API, demonstrating a local inference deployment pattern. That compatibility page describes API usage, not a guarantee that every model or workflow is offline or that host logs/telemetry are absent. [Ollama OpenAI compatibility](https://ollama.com/blog/openai-compatibility)
- AWS’s shared-responsibility description illustrates the general operational distinction: cloud customers still configure content access/security while the provider protects underlying infrastructure. In a fully self-hosted deployment, the organization additionally operates that infrastructure and its controls. [AWS Textract data protection](https://docs.aws.amazon.com/textract/latest/dg/data-protection.html)
- GDPR security/accountability duties apply regardless of whether processing runs on-premises or in a cloud service; controllers remain responsible for lawful purpose, minimization, retention, security, and demonstrable compliance. [GDPR, Articles 5, 24, 25, 32](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)

### Inferences
- On-prem is strongest where no external processor transfer is acceptable, connectivity is restricted, or customized control over retention is essential. Budget for GPU capacity, secure model artifact provenance, vulnerability updates, access control, encrypted disks/backups, monitoring, disaster recovery, and quality evaluation.
- Managed cloud tends to reduce infrastructure burden and offers mature operational controls, but requires vendor due diligence and confidence in region/retention settings. Hybrid can route low-risk documents to cloud and sensitive classes to local models, provided classification itself does not leak content.
- Open-weight OCR/vision-language models may produce hallucinated or inconsistent normalized fields. Use deterministic validation (totals, VAT arithmetic, schema checks), confidence thresholds, and human review for exceptions; these controls protect financial integrity as well as privacy.

### Gaps
- No specific open-weight model was selected, so its license, security history, training-data terms, telemetry behavior, and invoice/receipt accuracy cannot be assessed here. Check the model card and license for the exact version and quantization being deployed.

## EU GDPR transfers, retention, and practical deployment controls

### Takeaway
EU residency is helpful but not a complete GDPR answer: assess where processing occurs, who can access data, support/subprocessor access, and whether a Chapter V transfer is involved. A defensible design maps the full lifecycle and applies a retention schedule, privacy-by-design minimization, processor terms, and transfer safeguards where needed.

### Cited Findings
- GDPR Chapter V restricts transfers of personal data to third countries; transfers may rely on an adequacy decision or appropriate safeguards such as standard contractual clauses, subject to applicable conditions. [GDPR, Articles 44–46](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)
- EDPB guidance explains that Chapter V applies when a controller or processor subject to GDPR transfers personal data to a separate controller/processor in a third country; the transfer analysis is separate from the territorial-scope test in Article 3. [EDPB Guidelines 05/2021, Article 3 and Chapter V](https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-052021-interplay-between-article-3-and-chapter-v-gdpr_en)
- GDPR requires personal data to be kept in identifiable form no longer than necessary for the processing purposes, with appropriate safeguards for longer retention in specified cases (Article 5(1)(e)); data protection by design/default requires limiting amount, extent, storage period, and accessibility (Article 25). [GDPR, Articles 5(1)(e), 25](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)
- GDPR requires a record of processing activities for many organizations, including purposes, categories, recipients, transfers, and envisaged erasure periods (Article 30); where processing is likely to result in high risk, a DPIA is required before processing (Article 35). [GDPR, Articles 30, 35](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)
- GDPR permits longer retention when necessary to comply with a legal obligation, but purpose and storage limitation still apply; therefore accounting/tax record retention is not a blanket reason to keep temporary extraction copies, duplicate uploads, or debug logs for the same period. [GDPR, Articles 5(1)(b), 5(1)(e), 6(1)(c)](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)

### Inferences
- Create a data-flow inventory covering mobile capture/cache, upload, queue, vendor, extraction response, retry/dead-letter queue, application database, analytics, observability, backups, and human-review UI. Set retention/deletion independently at each stage.
- Keep original documents only as long as required by the business/accounting purpose; make transient processing objects expire quickly; avoid logging image payloads, OCR text, prompt contents, identifiers, or extracted line items. Use opaque request IDs and redact error traces.
- Prefer EU-region processing and storage when required by policy, but separately verify inference-region behavior, global support access, subprocessors, and contractually applicable transfer mechanism. A region selector alone does not establish GDPR compliance.
- Conduct a DPIA screening and maintain the processing record; document purpose/lawful basis, data categories, necessity, risks, safeguards, human review, retention, and processor instructions. Implement access by role, encryption in transit/at rest, secrets management, audit trails, tested deletion, incident response, and a breach-notification path.

### Gaps
- National accounting/tax rules and sector-specific financial secrecy or payment-card requirements vary. The appropriate retention period, legal basis, and whether a particular deployment needs a DPIA require jurisdiction- and use-case-specific review.
- This note is operational research, not legal advice; EU transfer analysis and processor contractual terms should be reviewed against the actual data flows and vendor agreement.

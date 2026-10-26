# DocGuard: assessment delivery plan

## Status — Phase 6 application ready for feedback

UI revision after feedback: navy/blue visual design, stronger typography and document canvas. Added language context and Hindi/Marathi/Tamil/Bengali examples; language-specific model accuracy remains unvalidated. Interface switching now offers English, Hindi, Marathi, Tamil and Bengali, independently of document language. PDF reports remain English. Phase 7 has not started.

Phases 1–5 reviewed and continuation authorized. Phase 6 local Streamlit application connects trained models to image/PDF upload, page selection, overlays and PDF/ZIP exports. Browser verification covered real uploads, both models, result invalidation, downloads and mobile. See docs/PHASE_6.md. Model quality remains weak with high false-positive rates. The 20-epoch GPU notebooks are prepared but have not run in the user's Colab session. The UI follows the user's restrained document-review preference. Phase 7 submission materials remain behind the Phase 6 feedback gate.

Deadline: 28 October 2026. Team college assessment.
Hardware: ASUS Vivobook Go E1504FA, approximately 15 GB usable RAM, AMD Radeon integrated graphics. Local Python: 3.14.2.

## Deliverable

A local web application that accepts a document image or PDF, renders suspicious text-region overlays from a trained segmentation model, and exports a result report. Predictions indicate visual anomalies, not proof of fraud or authenticity. Any untrained preview must be explicitly labeled.

## Priority

1. Required: reproducible data preparation, trained CNN baseline, pretrained Transformer segmentation fine-tuning, held-out F1/IoU evaluation, image upload, heatmap, downloadable result, README and assessment report.
2. Next: bounded PDF page processing, JPEG/resizing robustness comparison, inference timing and failure examples.
3. If time permits: Hindi document examples and additional export polish. Hindi performance must be measured before making language-support claims.
4. Deferred: login/accounts, cloud deployment, OCR-based fraud reasoning and comprehensive multilingual validation. These require separate approval if promoted into the deadline scope.

## Execution constraints

Use a compatible isolated Python environment for the application. Prepare a GPU notebook for training; hosted GPU availability is not guaranteed. First establish dataset access, license, download size and annotation format. If original data is inaccessible, disclose any fallback synthetic dataset and its limitations. Split by source document before generating variants to prevent leakage. Keep authentic held-out documents for false-positive evaluation. Report measured results only.

## Feedback gates

1. Scope and architecture: this plan.
2. Dataset: inspect genuine/tampered examples, masks and split report.
3. CNN: review predictions and held-out metrics.
4. Transformer: review comparison with CNN.
5. Robustness: review degradation results and failure cases.
6. Application: review the complete upload-to-export flow.
7. Submission: review final report, slides and demo instructions.

Stop after each phase for user feedback. Apply requested changes before proceeding.

## Proposed schedule (India time)

- 26 October: scope, dataset preparation and baseline training setup.
- 27 October: training, evaluation, robustness experiments and application.
- 28 October: final verification, report, presentation and demo rehearsal; reserve submission buffer.

Actual feasibility depends on prompt feedback, dataset access and GPU training availability. A full-scale benchmark is outside this two-day scope.

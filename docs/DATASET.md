# Phase 2: dataset preparation

## Official dataset access

Source: https://github.com/qcf-568/DocTamper (checked 26 October 2026).
The official README restricts use to noncommercial research and describes an institutional application and password request. No access approval, archive size, or successful download has been verified here. Do not bypass that process. A faculty member can review the application requirements. No application or email has been sent.

## Available pilot

Run `python scripts/prepare_pilot.py` with Pillow installed. This produces 120 fictional receipt sources, each with an original and a changed-total version (240 images). Masks mark the edited text rectangle; originals have empty masks. Outputs include a CSV manifest, split counts and visual previews.

Source documents are split deterministically 70/15/15 before pairing. Both variants remain in the same split. Future JPEG/resize variants must inherit the same source split. This prevents source leakage but does not make the single-layout pilot representative of real-world documents.

The pilot is for validating loading, masks, training and UI. It is not DocTamper and must not be described as a real-document benchmark. It uses a single layout family and only total-value replacement. Strong pilot scores would not establish generalization.

## Gate before model training

Review previews (original, edited, red mask outline), approve the synthetic pilot or obtain approved DocTamper access, and decide the final dataset scope. For stronger synthetic evaluation, add varied layouts, fonts, edit locations, rendering and source-disjoint templates before training. Reserve genuine real-document negatives for a separate, explicitly reported false-positive check if available with permission.

## Expanded synthetic v2 (user-approved direction)

Generate with `python scripts/prepare_dataset.py`, then check with `python scripts/validate_dataset.py data/synthetic_v2`.

Default: 600 sources, 1,200 images. Train/validation/test contain 840/180/180 images with balanced original/edited labels. Twenty layout configurations are partitioned 14/3/3, so neither source IDs nor layout configuration IDs cross splits. Shared layout primitives remain; this is not a comprehensive unseen-document benchmark.

Variation includes four font families on Windows, randomized font sizes and paper tones, six editable fields, one or two replaced fields per edited image, matched-font replacement, font mismatch, and slight patch-tone mismatch. Both labels receive matched JPEG and blur processing. Windows/Colab font fallback can differ; preserve the generated images for reproducibility.

Matched-font, cleanly rerendered text may be visually indistinguishable from authentic text. No model can reliably recover edit history absent evidence. Report per-edit-type results as well as aggregate results. The changed-region masks are ground truth, not model predictions.

Known generation artifact: digit substitution can produce invalid dates. This can introduce semantic shortcuts; assess date edits separately and exclude them from any claim about purely visual forensic generalization. Other numeric fields are not guaranteed to remain arithmetically consistent.

User approved the expanded dataset direction and authorized Phase 3 baseline implementation. Training status and measured results belong in the Phase 3 records.

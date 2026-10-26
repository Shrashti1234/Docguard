# Phase 3 — CNN baseline

Architecture: small two-level U-Net, RGB input, one-channel edit logits. Native default inference/training size is 320×400, preserving the generated document aspect ratio. Images use bilinear resize, masks use nearest-neighbor. Small text details can still be lost at this resolution.

Loss: weighted BCE-with-logits plus soft Dice on positive documents. Positive weight is estimated using training masks only, capped at 30. Negative documents contribute BCE; they are not assigned a misleading perfect empty-mask Dice score. Metric convention: zero F1/IoU when both foreground counts are zero. Aggregate scores use global pixel counts.

The best epoch is selected using validation F1 at threshold 0.5. Final foreground threshold is selected from 0.1–0.9 using validation F1; ties favor the higher threshold. Test evaluation runs separately. The operational image flag is predicted foreground fraction >=0.001; it is a fixed heuristic, not a calibrated probability. Per-edit-type metrics are also exported. Authentic rows' foreground F1 is zero by definition; use false-positive rate to interpret authentic performance.

## Colab steps

1. Open `notebooks/Phase_3_CNN_Colab.ipynb` in Google Colab and select a GPU runtime.
2. Run cells in order; upload `deliverables/docguard_colab.zip` when prompted.
3. Complete 20-epoch training, test evaluation and result download.
4. Preserve the downloaded `docguard_cnn_results.zip` for review.

Run cells use checked subprocess calls for training/evaluation so failures stop execution. GPU access is supplied by the user's Colab session. This workspace does not have authenticated access to that session.

## Local commands

Install dependencies in an isolated environment with `python -m pip install -r requirements-train.txt`. Then:

```
python -m unittest discover -s tests -v
python -m docguard.baseline train --output runs/cnn_baseline
python -m docguard.baseline test --output runs/cnn_baseline
```

Outputs: `best.pt`, `config.json`, `history.json`, `validation.json`, `test_metrics.json`, individual test predictions and labeled prediction previews. Configuration records manifest SHA-256, framework version, resolution and seed. Exact GPU determinism is not guaranteed.

Reference for stable weighted BCE formulation: https://docs.pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html

Synthetic-only results cannot support claims of deployment-ready forgery detection. Inspect failure cases, especially matched-font edits without forensic evidence. No Transformer or user interface is implemented in this phase.

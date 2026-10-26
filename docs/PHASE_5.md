# Phase 5 — robustness protocol

Models: trained preliminary CNN and fully fine-tuned MiT-B0/custom decoder. Frozen-encoder diagnostics remain in Phase 4 and are not included in this main robustness comparison.

Both models are evaluated on the same test split under clean, additional JPEG quality 70 and 40, bilinear 50% and 25% down/up resizing, and a screenshot proxy (80% down/up resize, blur radius 0.4, JPEG quality 75). This is not a real screenshot capture study. Conditions are fixed before evaluation.

Perturbations occur before the normal model input resize. Native image dimensions are restored, so ground-truth coordinates remain unchanged. Binary masks use nearest-neighbor model resizing only. No threshold, checkpoint or hyperparameter is retuned. The runner verifies weight/threshold SHA-256 hashes before and after evaluation and checks whether clean pixel counts reproduce the previous test evaluation.

```
python -m docguard.robustness --cpu
python scripts/report_robustness.py
```

For GPU-trained outputs, pass `--runs runs/cnn_phase4_colab runs/transformer_phase4_colab` and a fresh output directory. Run the report script with matching `--input`. Install `requirements-analysis.txt` for the complete evaluation and plotting environment.

Outputs: global and subgroup metrics, per-image counts, labeled previews, fixed-threshold F1 changes, model-only forward timing, checkpoint hashes, report, CSV and standalone PNG/SVG charts. Evaluation wall time includes data loading and metric calculation; it is not inference latency. The separate forward benchmark uses one already-prepared image, batch size one, three warmups and 20 measured repeats, and excludes application overhead.

No metric is claimed until the runner finishes. Synthetic-only limitations, existing source JPEG variation and visual evidence loss under resizing must accompany results.

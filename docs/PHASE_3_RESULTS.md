# Phase 3 — measured preliminary CNN results

## Run

This is an actual local CPU training run, not a simulated result. It used the approved synthetic_v2 dataset: 840 training, 180 validation and 180 held-out test images. Original/edited pairs and layout IDs do not cross splits.

- Architecture: 30,081-parameter small U-Net.
- Resolution: **160×200**, deliberately lower than the notebook's 320×400 default.
- Training: 3 epochs, batch size 8, AdamW, learning rate 0.001, seed 42.
- Framework: PyTorch 2.14.1+cpu.
- Best epoch: 3, selected by validation pixel F1 at threshold 0.5.
- Final foreground threshold: 0.9, selected using validation F1 only.
- Logged training plus per-epoch validation time: 308.4 seconds (excludes initial data scan and final threshold selection).

## Held-out results

| Metric | Measured value |
|---|---:|
| Global pixel precision | 0.1878 |
| Global pixel recall | 0.3565 |
| Global pixel F1 | 0.2460 |
| Global pixel IoU | 0.1403 |
| Original documents flagged by fixed pixel-fraction rule | 90 / 90 |
| Original-document false-positive rate | 100% |

The document rule flags an image when at least 0.1% of pixels exceed the segmentation threshold. These results show that this rule and baseline cannot be used for reliable document screening. It is not a calibrated confidence score.

| Edited-image subgroup | Pixel F1 |
|---|---:|
| Font mismatch | 0.5880 |
| Matched font | 0.2460 |
| Patch tone | 0.2631 |

Subgroups contain edited images only. Their metrics exclude false positives on original documents and must not replace the global result.

## Inspection

The saved predictions show that the model often marks multiple numeric fields when only one was edited. This explains the poor precision and false alarms. Small characters also lose detail at the reduced CPU resolution. Training loss fell from 1.4105 to 1.1076, but lower loss alone does not establish reliable detection.

## Deliverables and remaining work

`runs/cnn_local_preliminary/` contains the actual checkpoint, configuration, history, validation selection, test metrics, per-image results and eight unselected sequential test previews. `deliverables/docguard_cnn_local_preliminary.zip` is a portable copy of this run.

The Colab notebook and project bundle provide a separate planned **20-epoch, 320×400 GPU run**. That run has not been executed in the user's Google account. Its quality is unknown; more training does not guarantee improvement.

Do not tune settings using this already-inspected test result. Any subsequent model choices should use training/validation data only. Preserve the baseline for the Transformer comparison. All scores here are synthetic-only and provide no evidence of real-document performance.

## Verification

Three automated checks passed: metric arithmetic, model shape/finite gradients for positive and negative batches, and false-alarm counting. Real-data loading, checkpoint saving/loading, validation threshold selection and held-out evaluation completed successfully. Colab archive integrity and notebook Python syntax were checked; the notebook itself remains unexecuted in Colab.

Phase 4 remains pending user feedback. UI direction is recorded separately in `docs/UI_DIRECTION.md`.

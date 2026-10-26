# Phase 4 — actual Transformer results

## Conclusion

Neither tested Transformer run improved global pixel F1 over the preliminary CNN. Full fine-tuning reduced the fixed document-rule false-positive rate, but it remained unacceptably high. These are short, low-resolution synthetic experiments, not reliable document-screening models.

## Matched data and evaluation

All runs used the same approved manifest, 840 training / 180 validation / 180 test images, 160×200 input, batch size 8, 3 epochs and seed 42. Source/layout splits were unchanged. Each checkpoint and foreground threshold was selected using validation only. All evaluated variants are reported.

| Model | Pixel precision | Pixel recall | Pixel F1 | Pixel IoU | Original documents falsely flagged |
|---|---:|---:|---:|---:|---:|
| CNN U-Net | 0.1878 | 0.3565 | 0.2460 | 0.1403 | 90/90 (100%) |
| Frozen MiT-B0 + trained decoder | 0.1330 | 0.6283 | 0.2195 | 0.1233 | 90/90 (100%) |
| Fully fine-tuned MiT-B0 + decoder | 0.1691 | 0.3538 | 0.2288 | 0.1292 | 77/90 (85.6%) |

Foreground thresholds: CNN 0.9; both Transformer runs 0.8. The document flag uses the same fixed >=0.1% predicted-foreground rule. It is not calibrated confidence or document-classification accuracy.

Learning rates differ: CNN and frozen-decoder run 0.001; full fine-tuning 0.00006. Pretraining, capacities and training modes also differ. Matching data, resolution and epochs does not make this a controlled architecture-only experiment.

## Transformer details

The encoder is genuinely pretrained ImageNet MiT-B0, not a randomly initialized Transformer. Encoder loading rejected missing/mismatched weights. The original classification head was intentionally discarded; the four-scale segmentation decoder is custom and initialized for this task.

- Total parameters: 3,349,377.
- Frozen run trainable parameters: 29,985.
- Full fine-tuning trainable parameters: 3,349,377.
- Full fine-tuning model revision: `80983a413c30d36a39c20203974ae7807835e2b4`.
- PyTorch: 2.14.1+cpu; Transformers: 5.20.2.
- Full fine-tuning best epoch: 3, selected on validation F1 at 0.5 before threshold selection.

Both Transformer modes and the full fine-tuning learning rate were planned before the full fine-tuned model's test evaluation. No subsequent settings were chosen to optimize these inspected test results.

## Failure inspection

Sequential prediction previews show multiple numeric fields highlighted when only one or two fields were edited. Both models can confuse numeric text with tampering. Tiny character detail is also lost at this resolution. Matched-font clean replacements may provide no detectable visual edit history. Generated-date and layout artifacts further limit conclusions.

## Verification and artifacts

Five checks passed: CNN shape/gradient checks, metric arithmetic, original-document false-alarm counting, Transformer freeze/shape behavior, and full encoder gradients with offline checkpoint round-trip. Actual checkpoint save/load, training and evaluation also completed. Both notebook JSON/Python syntax and Colab bundle integrity were checked.

`deliverables/model_comparison.json` contains exact measured metrics and experiment settings. `deliverables/docguard_phase4_local_results.zip` contains the three runs, previews, comparison, report and upstream model license.

`notebooks/Phase_4_Transformer_Colab.ipynb` prepares separate 20-epoch, 320×400 CNN and full Transformer training. This GPU notebook has **not** run in the user's account, and improvement is not guaranteed. The matching project/data bundle is `deliverables/docguard_colab.zip`.

Retain the NVIDIA license with derived weights. Synthetic-only scores do not establish real-document reliability. Phase 5 robustness experiments remain pending feedback.

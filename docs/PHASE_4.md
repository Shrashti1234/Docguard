# Phase 4 — pretrained Transformer segmentation

Model: ImageNet-pretrained NVIDIA MiT-B0 encoder with a custom multiscale binary segmentation decoder. This uses the SegFormer encoder architecture, not an unchanged official SegFormer segmentation model. Four feature maps are projected to 32 channels, resized to the first feature scale, concatenated, fused, and upsampled to input resolution.

Sources:
- https://huggingface.co/nvidia/mit-b0
- https://huggingface.co/docs/transformers/model_doc/segformer
- https://github.com/NVlabs/SegFormer/blob/master/LICENSE

The upstream model card links a noncommercial research/evaluation license. Its complete text is preserved at `docs/third_party/SEGFORMER_LICENSE.txt`; retain it with derived weights. No model or result is published externally by these scripts.

## Preprocessing and reproducibility

Input remains RGB [0,1], resized by the same loader as the CNN, then normalized using the upstream ImageNet mean/std. Masks remain binary without label reduction. Missing pretrained encoder parameters cause an error, with no silent random fallback. Configuration records the pretrained model ID, resolved revision where available, framework versions and manifest hash. Checkpoints contain encoder configuration and all weights, allowing offline restoration without a second model download.

## Run modes

Local verification: same 160×200 resolution, 3 epochs and dataset manifest as the preliminary CNN. The pretrained encoder is frozen; only the custom decoder trains. This is feature extraction, **not full Transformer fine-tuning**.

```
python -m pip install -r requirements-transformer.txt
python -m docguard.baseline train --model transformer --freeze-encoder --height 200 --width 160 --epochs 3 --output runs/transformer_local_preliminary --cpu
python -m docguard.baseline test --output runs/transformer_local_preliminary --cpu
python scripts/compare_models.py runs/cnn_local_preliminary runs/transformer_local_preliminary
```

A second, preplanned local mode fine-tunes the full encoder for 3 epochs at 160×200 using learning rate 0.00006:

```
python -m docguard.baseline train --model transformer --height 200 --width 160 --epochs 3 --lr 0.00006 --output runs/transformer_finetuned_local --cpu
python -m docguard.baseline test --output runs/transformer_finetuned_local --cpu
```

Both Transformer modes are reported, not selected using the test score. The frozen-encoder run is diagnostic. The full fine-tuning mode and its learning rate were defined before its held-out evaluation.

Colab full fine-tuning: 320×400, 20 epochs, learning rate 0.00006, unfrozen encoder. Run both the CNN and Transformer notebook cells at matching resolution/epoch budget before evaluating comparison claims. Different pretraining and model capacities still prevent an architecture-only causal claim.

Threshold/epoch selection, segmentation loss, global metrics and fixed image-flag rule match Phase 3. The test split is evaluated only after validation selection. Report false positives even if foreground metrics improve. More training or a Transformer does not guarantee improved performance, especially on clean synthetic replacements with no forensic evidence.

## Feedback gate

Inspect measured results and prediction previews after verification. Phase 5 robustness work starts after user feedback on this phase.

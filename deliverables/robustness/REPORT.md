# Phase 5 — measured robustness results

Conditions use the same synthetic held-out split; sample counts per model/condition: [180]. Model input resolutions (width, height): [(160, 200)]. Perturbations are applied at native document size before model input resizing. Weights and validation-selected thresholds remain unchanged. No model was retrained or selected using these perturbation results.

| Model | Condition | Pixel F1 | Pixel IoU | Original-document false-positive rate |
|---|---|---:|---:|---:|
| CNN | clean | 0.2460 | 0.1403 | 100.0% |
| CNN | jpeg70 | 0.2461 | 0.1403 | 100.0% |
| CNN | jpeg40 | 0.2444 | 0.1392 | 100.0% |
| CNN | resize50 | 0.2513 | 0.1437 | 100.0% |
| CNN | resize25 | 0.2569 | 0.1474 | 100.0% |
| CNN | screenshot_proxy | 0.2472 | 0.1410 | 100.0% |
| Fine-tuned Transformer | clean | 0.2288 | 0.1292 | 85.6% |
| Fine-tuned Transformer | jpeg70 | 0.2269 | 0.1279 | 86.7% |
| Fine-tuned Transformer | jpeg40 | 0.2252 | 0.1269 | 88.9% |
| Fine-tuned Transformer | resize50 | 0.2352 | 0.1333 | 78.9% |
| Fine-tuned Transformer | resize25 | 0.2364 | 0.1341 | 47.8% |
| Fine-tuned Transformer | screenshot_proxy | 0.2333 | 0.1321 | 82.2% |

## Observed changes

- CNN: lowest perturbed F1 was 0.2444 under `jpeg40`, a change of -0.0016 from clean.
- CNN: model-only forward median 19.70 ms, batch size one, 3 warmups and 20 repeats on cpu with 4 threads. This excludes loading, preprocessing, transfer and postprocessing; it is not application latency.
- CNN: clean pixel counts reproduced previous evaluation: **True**; weights/threshold hashes unchanged: **True**.
- Fine-tuned Transformer: lowest perturbed F1 was 0.2252 under `jpeg40`, a change of -0.0036 from clean.
- Fine-tuned Transformer: model-only forward median 34.65 ms, batch size one, 3 warmups and 20 repeats on cpu with 4 threads. This excludes loading, preprocessing, transfer and postprocessing; it is not application latency.
- Fine-tuned Transformer: clean pixel counts reproduced previous evaluation: **True**; weights/threshold hashes unchanged: **True**.

## Limits and interpretation

The source dataset is generated and already contains JPEG/blur variation. Additional JPEG is recompression, not first-time compression. Down/up resizing preserves annotation coordinates; masks are never blurred or JPEG-encoded. The screenshot condition combines resizing, blur and JPEG and is a proxy, not evidence about actual browser/mobile screenshots.

A higher F1 after degradation can reflect smoothing of synthetic artifacts or threshold effects. It does not establish improved real-world generalization. Severe downscaling may remove forensic evidence; labels continue to describe where the edit occurred even when it becomes visually unrecoverable.

The baseline models have high false-positive rates. These experiments characterize failure modes; they do not validate a deployment-ready authenticity detector. Pixel F1 is not document-classification accuracy. The fixed document flag is not a calibrated probability.

Charts and CSV contain the same measured values. Per-image predictions, checkpoint hashes, validation hashes and full subgroup metrics are retained in the results archive. Higher-resolution Colab training remains unexecuted and its results are unknown.

Phase 6 application implementation is pending user feedback. The interface direction remains a restrained document-review workspace.

"""Create standalone charts, CSV and an evidence-based Markdown report."""
import argparse
import csv
import json
import shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--input', default='runs/robustness_local', type=Path)
parser.add_argument('--output', default='deliverables/robustness', type=Path)
args = parser.parse_args()
data = json.loads((args.input/'results.json').read_text())
args.output.mkdir(parents=True, exist_ok=True)
shutil.copyfile(args.input/'results.json', args.output/'results.json')
models = data['models']
conditions = list(models[0]['conditions'])
if any(list(m['conditions']) != conditions for m in models):
    raise ValueError('Models evaluated under different condition sets')
names = ['CNN' if m['model']=='cnn' else 'Fine-tuned Transformer' for m in models]
labels = dict(clean='Clean', jpeg70='JPEG 70', jpeg40='JPEG 40', resize50='Resize 50%', resize25='Resize 25%', screenshot_proxy='Screenshot\nproxy')
rows = []
for model, name in zip(models, names):
    for condition, result in model['conditions'].items():
        metric = result['metrics']
        rows.append(dict(model=name, condition=condition, precision=metric['precision'], recall=metric['recall'],
                         f1=metric['f1'], iou=metric['iou'], false_positive_rate=metric['authentic_false_positive_rate'],
                         f1_change_from_clean=result.get('f1_change_from_clean', 0), threshold=model['threshold']))
with (args.output/'metrics.csv').open('w', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
figure, axes = plt.subplots(1, 2, figsize=(14, 5), layout='constrained')
positions = np.arange(len(conditions))
width = .8/len(models)
palette = ['#333a45', '#39708e', '#a37544']
for i, (model, name) in enumerate(zip(models, names)):
    for axis, metric_key in zip(axes, ['f1', 'authentic_false_positive_rate']):
        values = [model['conditions'][c]['metrics'][metric_key] for c in conditions]
        bars = axis.bar(positions-.4+width/2+i*width, values, width, label=name, color=palette[i % len(palette)])
        axis.bar_label(bars, labels=[f'{v:.2f}' for v in values], fontsize=8, padding=3)
for axis, title in zip(axes, ['Pixel F1 (higher is better)', 'Original-document false-positive rate (lower is better)']):
    axis.set_title(title, loc='left', fontsize=11, pad=15)
    axis.set_xticks(positions, [labels[c] for c in conditions], rotation=20, ha='right')
    axis.set_ylim(0, 1.12)
    axis.set_yticks([0, .25, .5, .75, 1])
    axis.set_axisbelow(True)
    axis.grid(axis='y', alpha=.18)
axes[0].legend(loc='upper left', frameon=False)
figure.suptitle('DocGuard robustness — synthetic test data, fixed weights and thresholds', fontsize=13)
figure.savefig(args.output/'robustness.png', dpi=180)
figure.savefig(args.output/'robustness.svg')
plt.close(figure)

samples = sorted({result['samples'] for model in models for result in model['conditions'].values()})
resolutions = sorted({tuple(model['resolution']) for model in models})
lines = ['# Phase 5 — measured robustness results', '',
         f'Conditions use the same synthetic held-out split; sample counts per model/condition: {samples}. Model input resolutions (width, height): {resolutions}. Perturbations are applied at native document size before model input resizing. Weights and validation-selected thresholds remain unchanged. No model was retrained or selected using these perturbation results.', '',
         '| Model | Condition | Pixel F1 | Pixel IoU | Original-document false-positive rate |',
         '|---|---|---:|---:|---:|']
for row in rows:
    lines.append(f"| {row['model']} | {row['condition']} | {row['f1']:.4f} | {row['iou']:.4f} | {100*row['false_positive_rate']:.1f}% |")
lines += ['', '## Observed changes', '']
for model, name in zip(models, names):
    perturbed = [(c, r) for c, r in model['conditions'].items() if c != 'clean']
    worst, result = min(perturbed, key=lambda pair:pair[1]['metrics']['f1'])
    delta = result['f1_change_from_clean']
    lines.append(f"- {name}: lowest perturbed F1 was {result['metrics']['f1']:.4f} under `{worst}`, a change of {delta:+.4f} from clean.")
    source_folder = args.input/Path(model['run']).name/worst/'previews'
    previews = sorted(source_folder.glob('*tampered.png'))
    if previews:
        shutil.copyfile(previews[0], args.output/f"{model['model']}_lowest_f1_example.png")
    benchmark = model['forward_benchmark']
    lines.append(f"- {name}: model-only forward median {benchmark['median_ms']:.2f} ms, batch size one, 3 warmups and 20 repeats on {data['device']} with {data['threads']} threads. This excludes loading, preprocessing, transfer and postprocessing; it is not application latency.")
    lines.append(f"- {name}: clean pixel counts reproduced previous evaluation: **{model.get('clean_reproduces_saved_pixel_counts')}**; weights/threshold hashes unchanged: **{model['weights_and_threshold_unchanged']}**.")
lines += ['', '## Limits and interpretation', '',
          'The source dataset is generated and already contains JPEG/blur variation. Additional JPEG is recompression, not first-time compression. Down/up resizing preserves annotation coordinates; masks are never blurred or JPEG-encoded. The screenshot condition combines resizing, blur and JPEG and is a proxy, not evidence about actual browser/mobile screenshots.', '',
          'A higher F1 after degradation can reflect smoothing of synthetic artifacts or threshold effects. It does not establish improved real-world generalization. Severe downscaling may remove forensic evidence; labels continue to describe where the edit occurred even when it becomes visually unrecoverable.', '',
          'The baseline models have high false-positive rates. These experiments characterize failure modes; they do not validate a deployment-ready authenticity detector. Pixel F1 is not document-classification accuracy. The fixed document flag is not a calibrated probability.', '',
          'Charts and CSV contain the same measured values. Per-image predictions, checkpoint hashes, validation hashes and full subgroup metrics are retained in the results archive. Higher-resolution Colab training remains unexecuted and its results are unknown.', '',
          'Phase 6 application implementation is pending user feedback. The interface direction remains a restrained document-review workspace.']
(args.output/'REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print(f'Report, CSV, PNG and SVG saved to {args.output.resolve()}')

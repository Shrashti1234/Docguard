"""Summarize measured runs without assuming a Transformer improvement."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('runs', nargs='+', type=Path)
parser.add_argument('--output', default='deliverables/model_comparison.json', type=Path)
args = parser.parse_args()
rows = []
for run in args.runs:
    config = json.loads((run/'config.json').read_text())
    report = json.loads((run/'test_metrics.json').read_text())
    rows.append(dict(run=str(run), model=config.get('model', 'cnn'),
                     manifest_sha256=config['manifest_sha256'], resolution=[config['width'], config['height']],
                     epochs=config['epochs'], freeze_encoder=config.get('freeze_encoder', False),
                     seed=config['seed'], batch_size=config['batch_size'], learning_rate=config['lr'], metrics=report['metrics']))
if len({r['manifest_sha256'] for r in rows}) != 1:
    raise ValueError('Cannot compare runs with different manifests')
matching = len({tuple(r['resolution']) for r in rows}) == 1 and len({r['epochs'] for r in rows}) == 1
result = dict(runs=rows, matching_resolution_and_epoch_budget=matching,
              caveats=['Synthetic-only data; inspected test results must not drive hyperparameter tuning.',
                       'Pretraining, architecture and frozen-vs-finetuned encoders differ; no controlled architecture-only claim.',
                       'Pixel F1 and IoU are segmentation scores, not document classification accuracy.'])
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))

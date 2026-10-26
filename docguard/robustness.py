"""Fixed-weight, fixed-threshold robustness evaluation. No tuning or training."""
import argparse
import hashlib
import io
import json
import time
from pathlib import Path

from PIL import Image, ImageFilter
import torch
from torch.utils.data import DataLoader
from docguard.baseline import Documents, SmallUNet, counts_to_metrics, evaluate, save_previews


CONDITIONS = {
    'clean': 'Unchanged generated image',
    'jpeg70': 'Additional JPEG encoding, quality=70',
    'jpeg40': 'Additional JPEG encoding, quality=40',
    'resize50': 'Downscale to 50%, then restore original dimensions (bilinear)',
    'resize25': 'Downscale to 25%, then restore original dimensions (bilinear)',
    'screenshot_proxy': '80% down/up resize, Gaussian blur radius=0.4, JPEG quality=75; simulation only',
}


def jpeg(image, quality):
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=quality)
    with Image.open(io.BytesIO(buffer.getvalue())) as encoded:
        return encoded.convert('RGB')


def down_up(image, scale):
    reduced = image.resize((max(1, round(image.width*scale)), max(1, round(image.height*scale))), Image.Resampling.BILINEAR)
    return reduced.resize(image.size, Image.Resampling.BILINEAR)


def degrade(image, condition):
    if condition == 'clean':
        return image.copy()
    if condition in ('jpeg70', 'jpeg40'):
        return jpeg(image, int(condition[4:]))
    if condition in ('resize50', 'resize25'):
        return down_up(image, int(condition[6:])/100)
    if condition == 'screenshot_proxy':
        return jpeg(down_up(image, .8).filter(ImageFilter.GaussianBlur(.4)), 75)
    raise ValueError(f'Unknown condition: {condition}')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@torch.inference_mode()
def forward_benchmark(model, dataset, device):
    """Batch-size-one model forward only; exclude disk/decode, transfer and postprocessing."""
    x = dataset[0][0].unsqueeze(0).to(device)
    model.eval()
    for _ in range(3):
        model(x)
    if device.type == 'cuda':
        torch.cuda.synchronize()
    durations = []
    for _ in range(20):
        started = time.perf_counter()
        model(x)
        if device.type == 'cuda':
            torch.cuda.synchronize()
        durations.append((time.perf_counter()-started)*1000)
    durations.sort()
    return dict(batch_size=1, warmups=3, repeats=20, median_ms=(durations[9]+durations[10])/2,
                min_ms=durations[0], max_ms=durations[-1],
                scope='Model forward only on one fixed input; not end-to-end app latency')


def run(args):
    if len({Path(p).name for p in args.runs}) != len(args.runs):
        raise ValueError('Run directories must have unique names to prevent output collisions')
    output = Path(args.output)
    if (output/'results.json').exists():
        raise ValueError('Choose a fresh output directory to preserve prior results')
    output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(args.threads)
    device = torch.device('cuda' if torch.cuda.is_available() and not args.cpu else 'cpu')
    results = []
    for run_path in args.runs:
        run_path = Path(run_path)
        config = json.loads((run_path/'config.json').read_text())
        if sha(Path(args.data)/'manifest.csv') != config['manifest_sha256']:
            raise ValueError('Dataset manifest differs from model training manifest')
        weights_hash = sha(run_path/'best.pt')
        threshold_hash = sha(run_path/'validation.json')
        calibration = json.loads((run_path/'validation.json').read_text())
        threshold = calibration['threshold']
        checkpoint = torch.load(run_path/'best.pt', map_location=device, weights_only=True)
        kind = checkpoint.get('model', 'cnn')
        if kind == 'transformer':
            from docguard.transformer import from_checkpoint
            model = from_checkpoint(checkpoint).to(device)
        else:
            model = SmallUNet(checkpoint['channels']).to(device)
        model.load_state_dict(checkpoint['state_dict'])
        model.eval()
        report = dict(run=run_path.as_posix(), model=kind, threshold=threshold,
                      checkpoint_sha256=weights_hash, validation_sha256=threshold_hash,
                      manifest_sha256=config['manifest_sha256'],
                      resolution=[checkpoint['width'], checkpoint['height']], conditions={})
        for condition, description in CONDITIONS.items():
            dataset = Documents(args.data, 'test', checkpoint['height'], checkpoint['width'],
                                image_transform=lambda im, c=condition: degrade(im, c))
            loader = DataLoader(dataset, batch_size=args.batch_size, num_workers=0)
            started = time.perf_counter()
            metrics, records, samples = evaluate(model, loader, device, [threshold], collect=True)
            seconds = time.perf_counter()-started
            groups = {}
            for group in sorted({r['edit_type'] for r in records}):
                group_rows = [r for r in records if r['edit_type']==group]
                groups[group] = counts_to_metrics(*[sum(r[key] for r in group_rows) for key in ('tp', 'fp', 'fn')])
            entry = dict(description=description, samples=len(dataset), metrics=metrics[threshold],
                         by_edit_type=groups, evaluation_seconds=seconds)
            if condition == 'clean':
                report['forward_benchmark'] = forward_benchmark(model, dataset, device)
                saved = run_path/'test_metrics.json'
                if saved.exists():
                    old = json.loads(saved.read_text())['metrics']
                    report['clean_reproduces_saved_pixel_counts'] = all(old[k] == metrics[threshold][k] for k in ('tp', 'fp', 'fn'))
            else:
                entry['f1_change_from_clean'] = entry['metrics']['f1']-report['conditions']['clean']['metrics']['f1']
            report['conditions'][condition] = entry
            folder = output/run_path.name/condition
            folder.mkdir(parents=True, exist_ok=True)
            (folder/'per_image.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
            if condition in ('clean', 'jpeg40', 'resize25', 'screenshot_proxy'):
                save_previews(samples, folder/'previews', threshold, 'Transformer' if kind=='transformer' else 'CNN')
            print(json.dumps(dict(run=run_path.name, condition=condition, f1=entry['metrics']['f1'],
                                  false_positive_rate=entry['metrics']['authentic_false_positive_rate'])), flush=True)
        if sha(run_path/'best.pt') != weights_hash or sha(run_path/'validation.json') != threshold_hash:
            raise RuntimeError('Model weights or threshold changed during robustness evaluation')
        report['weights_and_threshold_unchanged'] = True
        results.append(report)
        # Preserve completed work even if a later model fails.
        (output/'results.json').write_text(json.dumps(dict(device=str(device), threads=args.threads,
            torch_version=str(torch.__version__), models=results,
            caveats=['Synthetic-only generated data.', 'Screenshot condition is a proxy, not a real screenshot test.',
                     'Perturbations occur at native document size before model input resize.',
                     'F1 may rise under degradation; smoothing artifacts is not proof of better generalization.',
                     'Thresholds and weights remain fixed; no robustness tuning is performed.']), indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', nargs='+', default=['runs/cnn_local_preliminary', 'runs/transformer_finetuned_local'])
    parser.add_argument('--data', default='data/synthetic_v2')
    parser.add_argument('--output', default='runs/robustness_local')
    parser.add_argument('--batch-size', type=int, default=8)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--cpu', action='store_true')
    args = parser.parse_args()
    if args.batch_size < 1 or args.threads < 1:
        parser.error('Batch size and thread count must be positive')
    run(args)


if __name__ == '__main__':
    main()

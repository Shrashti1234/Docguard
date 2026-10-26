"""Small U-Net baseline. Run: python -m docguard.baseline --help."""
import argparse
import csv
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


class Documents(Dataset):
    def __init__(self, root, split, height=400, width=320, image_transform=None):
        self.root = Path(root)
        with (self.root/'manifest.csv').open(encoding='utf-8') as manifest:
            self.rows = [r for r in csv.DictReader(manifest) if r['split'] == split]
        if not self.rows:
            raise ValueError(f'No rows for {split}')
        self.size = (width, height)
        self.image_transform = image_transform

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        with Image.open(self.root/row['image']) as im:
            im = im.convert('RGB')
            if self.image_transform is not None:
                im = self.image_transform(im)
            x = np.array(im.resize(self.size, Image.Resampling.BILINEAR), dtype=np.float32)/255
        with Image.open(self.root/row['mask']) as im:
            y = np.array(im.convert('L').resize(self.size, Image.Resampling.NEAREST), dtype=np.float32)/255
        return torch.from_numpy(x.transpose(2, 0, 1).copy()), torch.from_numpy(y[None].copy()), index


def block(cin, cout):
    return nn.Sequential(nn.Conv2d(cin, cout, 3, padding=1), nn.GroupNorm(4, cout), nn.ReLU(),
                         nn.Conv2d(cout, cout, 3, padding=1), nn.GroupNorm(4, cout), nn.ReLU())


class SmallUNet(nn.Module):
    def __init__(self, channels=8):
        super().__init__()
        self.e1 = block(3, channels)
        self.e2 = block(channels, channels*2)
        self.center = block(channels*2, channels*4)
        self.d2 = block(channels*6, channels*2)
        self.d1 = block(channels*3, channels)
        self.head = nn.Conv2d(channels, 1, 1)
        self.pool = nn.MaxPool2d(2)

    def forward(self, x):
        a = self.e1(x)
        b = self.e2(self.pool(a))
        c = self.center(self.pool(b))
        up = nn.functional.interpolate(c, size=b.shape[-2:], mode='bilinear', align_corners=False)
        d = self.d2(torch.cat([up, b], 1))
        up = nn.functional.interpolate(d, size=a.shape[-2:], mode='bilinear', align_corners=False)
        return self.head(self.d1(torch.cat([up, a], 1)))


def counts_to_metrics(tp, fp, fn):
    precision = tp/(tp+fp) if tp+fp else 0.0
    recall = tp/(tp+fn) if tp+fn else 0.0
    return dict(precision=precision, recall=recall,
                f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0,
                iou=tp/(tp+fp+fn) if tp+fp+fn else 0.0,
                tp=tp, fp=fp, fn=fn)


def segmentation_loss(logits, target, positive_weight):
    bce = nn.functional.binary_cross_entropy_with_logits(logits, target, pos_weight=positive_weight)
    positive = target.sum((1, 2, 3)) > 0
    if positive.any():
        p, y = logits.sigmoid()[positive], target[positive]
        dice = 1 - ((2*(p*y).sum((1, 2, 3))+1)/(p.sum((1, 2, 3))+y.sum((1, 2, 3))+1)).mean()
    else:
        dice = logits.sum()*0
    return bce + dice


@torch.inference_mode()
def evaluate(model, loader, device, thresholds, collect=False):
    model.eval()
    tallies = {t: [0, 0, 0, 0, 0] for t in thresholds}
    records, samples = [], []
    for x, y, indices in loader:
        probabilities = model(x.to(device)).sigmoid().cpu()
        truth = y.bool()
        for t in thresholds:
            pred = probabilities >= t
            tally = tallies[t]
            tally[0] += int((pred & truth).sum())
            tally[1] += int((pred & ~truth).sum())
            tally[2] += int((~pred & truth).sum())
            authentic = ~truth.flatten(1).any(1)
            # Operational heuristic, not a calibrated fraud probability.
            flags = pred.float().flatten(1).mean(1) >= .001
            tally[3] += int((authentic & flags).sum())
            tally[4] += int(authentic.sum())
        if collect:
            t = thresholds[0]
            for k, index in enumerate(indices.tolist()):
                pred = probabilities[k] >= t
                actual = truth[k]
                m = counts_to_metrics(int((pred & actual).sum()), int((pred & ~actual).sum()), int((~pred & actual).sum()))
                row = loader.dataset.rows[index]
                records.append(dict(image=row['image'], edit_type=row.get('edit_type', 'unknown'), label=int(row['label']), **m))
                if len(samples) < 8:
                    samples.append((x[k], y[k], probabilities[k], row['image']))
    results = {}
    for t, (tp, fp, fn, false_alarms, negatives) in tallies.items():
        results[t] = dict(**counts_to_metrics(tp, fp, fn), authentic_false_alarms=false_alarms,
                          authentic_documents=negatives, authentic_false_positive_rate=false_alarms/negatives if negatives else None)
    return results, records, samples


def save_previews(samples, output, threshold, model_label='CNN'):
    output.mkdir(parents=True, exist_ok=True)
    for i, (x, y, p, name) in enumerate(samples):
        array = (x.permute(1, 2, 0).numpy()*255).astype(np.uint8)
        height, width = array.shape[:2]
        overlay = array.copy()
        selected = p[0].numpy() >= threshold
        overlay[selected] = (.45*overlay[selected]+.55*np.array([230, 35, 35])).astype(np.uint8)
        sheet = Image.new('RGB', (width*3, height+40), 'white')
        ground = Image.fromarray((y[0].numpy()*255).astype(np.uint8)).convert('RGB')
        for col, (im, title) in enumerate([(Image.fromarray(array), 'Input'), (ground, 'True edit mask'), (Image.fromarray(overlay), f'{model_label} prediction')]):
            sheet.paste(im, (col*width, 40))
            ImageDraw.Draw(sheet).text((col*width+5, 10), title, fill='black')
        sheet.save(output/f'{i:02d}_{Path(name).stem}.png')


def train(args):
    output = Path(args.output)
    if (output/'best.pt').exists():
        raise ValueError('Use a fresh output directory to preserve prior results')
    output.mkdir(parents=True, exist_ok=True)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device = torch.device('cuda' if torch.cuda.is_available() and not args.cpu else 'cpu')
    training = Documents(args.data, 'train', args.height, args.width)
    validation = Documents(args.data, 'val', args.height, args.width)
    loader = DataLoader(training, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(validation, batch_size=args.batch_size, num_workers=0)
    # Compute class imbalance using training masks only, at actual training resolution.
    positive, total = 0, 0
    for _, masks, _ in DataLoader(training, batch_size=args.batch_size):
        positive += int(masks.sum())
        total += masks.numel()
    if not positive:
        raise ValueError('No positive training pixels')
    weight = min(30.0, (total-positive)/positive)
    if args.model == 'transformer':
        from docguard.transformer import TransformerSegmenter
        model = TransformerSegmenter(args.pretrained, freeze_encoder=args.freeze_encoder).to(device)
    else:
        model = SmallUNet(args.channels).to(device)
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.lr, weight_decay=1e-4)
    config = vars(args).copy()
    config.update(device=str(device), positive_weight=weight, parameters=sum(p.numel() for p in model.parameters()),
                  torch_version=str(torch.__version__), manifest_sha256=hashlib.sha256((Path(args.data)/'manifest.csv').read_bytes()).hexdigest(),
                  provenance='synthetic_v2; results do not establish real-document performance')
    if args.model == 'transformer':
        import transformers
        config.update(transformers_version=transformers.__version__,
                      encoder_config=model.encoder_config,
                      pretrained_revision=model.pretrained_revision,
                      trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad))
    (output/'config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    history, best = [], -1
    started = time.perf_counter()
    for epoch in range(args.epochs):
        model.train()
        running = 0.0
        for x, y, _ in loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = segmentation_loss(model(x), y, torch.tensor(weight, device=device))
            if not torch.isfinite(loss):
                raise RuntimeError('Non-finite training loss')
            loss.backward()
            optimizer.step()
            running += float(loss.detach())*len(x)
        metrics = evaluate(model, val_loader, device, [.5])[0][.5]
        row = dict(epoch=epoch+1, train_loss=running/len(training), val_f1=metrics['f1'], val_iou=metrics['iou'], seconds=time.perf_counter()-started)
        history.append(row)
        print(json.dumps(row), flush=True)
        if metrics['f1'] > best:
            best = metrics['f1']
            checkpoint = dict(state_dict=model.state_dict(), model=args.model, channels=args.channels,
                              height=args.height, width=args.width, epoch=epoch+1)
            if args.model == 'transformer':
                checkpoint.update(encoder_config=model.encoder_config, freeze_encoder=args.freeze_encoder)
            torch.save(checkpoint, output/'best.pt')
        (output/'history.json').write_text(json.dumps(history, indent=2), encoding='utf-8')
    checkpoint = torch.load(output/'best.pt', map_location=device, weights_only=True)
    model.load_state_dict(checkpoint['state_dict'])
    thresholds = [.1, .2, .3, .4, .5, .6, .7, .8, .9]
    validation_results = evaluate(model, val_loader, device, thresholds)[0]
    threshold = max(thresholds, key=lambda t: (validation_results[t]['f1'], t))
    calibration = dict(threshold=threshold, selected_using='validation pixel F1 only', epoch=checkpoint['epoch'], metrics=validation_results[threshold], image_flag_min_pixel_fraction=.001)
    (output/'validation.json').write_text(json.dumps(calibration, indent=2), encoding='utf-8')
    print(f'Training complete. Validation-selected threshold: {threshold}. Test set untouched.', flush=True)


def test(args):
    output = Path(args.output)
    config = json.loads((output/'config.json').read_text())
    calibration = json.loads((output/'validation.json').read_text())
    root = Path(args.data)
    if hashlib.sha256((root/'manifest.csv').read_bytes()).hexdigest() != config['manifest_sha256']:
        raise ValueError('Manifest differs from training dataset')
    torch.set_num_threads(args.threads)
    device = torch.device('cuda' if torch.cuda.is_available() and not args.cpu else 'cpu')
    checkpoint = torch.load(output/'best.pt', map_location=device, weights_only=True)
    if checkpoint.get('model', 'cnn') == 'transformer':
        from docguard.transformer import from_checkpoint
        model = from_checkpoint(checkpoint).to(device)
    else:
        model = SmallUNet(checkpoint['channels']).to(device)
    model.load_state_dict(checkpoint['state_dict'])
    dataset = Documents(root, 'test', checkpoint['height'], checkpoint['width'])
    loader = DataLoader(dataset, batch_size=args.batch_size)
    threshold = calibration['threshold']
    metrics, records, samples = evaluate(model, loader, device, [threshold], collect=True)
    grouped = {}
    for kind in sorted({r['edit_type'] for r in records}):
        group = [r for r in records if r['edit_type']==kind]
        grouped[kind] = counts_to_metrics(*[sum(r[k] for r in group) for k in ('tp','fp','fn')])
    report = dict(split='test', model=checkpoint.get('model', 'cnn'), samples=len(dataset), threshold=threshold, metrics=metrics[threshold], by_edit_type=grouped,
                  limitations='Synthetic generated data only. Image flags use >=0.1% predicted foreground, not calibrated confidence.')
    (output/'test_metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (output/'test_predictions.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    save_previews(samples, output/'predictions', threshold, 'Transformer' if checkpoint.get('model') == 'transformer' else 'CNN')
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['train', 'test'])
    parser.add_argument('--data', default='data/synthetic_v2')
    parser.add_argument('--output', default='runs/cnn_baseline')
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--batch-size', type=int, default=8)
    parser.add_argument('--height', type=int, default=400)
    parser.add_argument('--width', type=int, default=320)
    parser.add_argument('--channels', type=int, default=8)
    parser.add_argument('--lr', type=float, default=.001)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--cpu', action='store_true')
    parser.add_argument('--model', choices=['cnn', 'transformer'], default='cnn')
    parser.add_argument('--pretrained', default='nvidia/mit-b0')
    parser.add_argument('--freeze-encoder', action='store_true', help='Transformer feature extraction only; default fine-tunes the encoder')
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1 or min(args.width, args.height) < 16 or args.channels < 4 or args.channels % 4:
        parser.error('Positive epochs/batch, dimensions >=16 and channels divisible by 4 required')
    if args.action == 'train' and args.model == 'transformer' and min(args.width, args.height) < 32:
        parser.error('MiT-B0 requires input dimensions >=32')
    if args.action == 'train' and args.freeze_encoder and args.model != 'transformer':
        parser.error('--freeze-encoder requires --model transformer')
    (train if args.action=='train' else test)(args)


if __name__ == '__main__':
    main()

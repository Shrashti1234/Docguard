"""Generate fictional receipt pairs for pipeline development, not a real-data benchmark."""
import argparse
import csv
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='data/pilot')
    parser.add_argument('--sources', type=int, default=120)
    args = parser.parse_args()
    if args.sources < 20:
        parser.error('Use at least 20 source documents for three splits.')
    root = Path(args.output)
    if (root / 'manifest.csv').exists():
        parser.error('Output already contains a manifest; choose a fresh output directory.')
    for folder in ('images', 'masks', 'previews'):
        (root / folder).mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    # Split source IDs before creating original/edited variants.
    ids = list(range(args.sources))
    rng.shuffle(ids)
    split_for = {source: ('train' if i < int(.7 * args.sources) else
                         'val' if i < int(.85 * args.sources) else 'test')
                 for i, source in enumerate(ids)}
    font = ImageFont.load_default(size=23)
    title_font = ImageFont.load_default(size=31)
    rows = []
    preview_pairs = []
    for source in range(args.sources):
        bg = tuple([rng.randint(240, 255)] * 3)
        original = Image.new('RGB', (640, 800), bg)
        draw = ImageDraw.Draw(original)
        x = rng.randint(40, 70)
        draw.text((x, 40), 'DEMO STORE — FICTIONAL', font=title_font, fill='black')
        draw.text((x, 100), f'Receipt: SAMPLE-{source:05d}', font=font, fill='black')
        draw.text((x, 145), 'Synthetic research document', font=font, fill='black')
        total = 0
        for j in range(5):
            cost = rng.randint(10, 999)
            total += cost
            draw.text((x, 220 + j * 65), f'Item {j+1}                 INR {cost}',
                      font=font, fill='black')
        draw.line((x, 570, 580, 570), fill='black', width=2)
        draw.text((x, 610), 'TOTAL INR', font=font, fill='black')
        location = (360, 610)
        draw.text(location, str(total), font=font, fill='black')
        edited = original.copy()
        edit_draw = ImageDraw.Draw(edited)
        replacement = str(total + rng.randint(50, 1500))
        old_box = draw.textbbox(location, str(total), font=font)
        new_box = edit_draw.textbbox(location, replacement, font=font)
        box = (min(old_box[0], new_box[0])-2, min(old_box[1], new_box[1])-2,
               max(old_box[2], new_box[2])+2, max(old_box[3], new_box[3])+2)
        edit_draw.rectangle(box, fill=bg)
        edit_draw.text(location, replacement, font=font, fill='black')
        mask = Image.new('L', original.size, 0)
        ImageDraw.Draw(mask).rectangle(box, fill=255)
        for variant, im in [('authentic', original), ('tampered', edited)]:
            name = f'{source:05d}_{variant}.png'
            target = mask if variant == 'tampered' else Image.new('L', original.size, 0)
            im.save(root / 'images' / name)
            target.save(root / 'masks' / name)
            rows.append(dict(source_id=source, split=split_for[source],
                             image=f'images/{name}', mask=f'masks/{name}',
                             label=int(variant == 'tampered'), provenance='synthetic'))
        if source < 3:
            overlay = edited.copy()
            ImageDraw.Draw(overlay).rectangle(box, outline='red', width=4)
            sheet = Image.new('RGB', (1920, 800), 'white')
            sheet.paste(original, (0, 0))
            sheet.paste(edited, (640, 0))
            sheet.paste(overlay, (1280, 0))
            preview_pairs.append(sheet)
    with (root / 'manifest.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = {s: sum(r['split'] == s for r in rows) for s in ('train', 'val', 'test')}
    report = dict(seed=42, source_documents=args.sources, samples=len(rows), splits=counts,
                  provenance='synthetic fictional receipts', mask='edited text bounding rectangle',
                  limitations=['Single layout family; total field edits only.',
                               'Cannot establish performance on real documents.',
                               'Authentic means unedited synthetic source, not verified real document.'])
    (root / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    preview = Image.new('RGB', (1920, 2400), 'white')
    for i, sheet in enumerate(preview_pairs):
        preview.paste(sheet, (0, i * 800))
    preview.thumbnail((1200, 1500))
    preview.save(root / 'previews' / 'examples.png')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

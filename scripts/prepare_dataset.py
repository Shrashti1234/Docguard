"""Source- and template-disjoint synthetic document benchmark prototype."""
import argparse
import csv
import io
import json
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def font(size, family):
    candidates = [Path('C:/Windows/Fonts') / family,
                  Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='data/synthetic_v2')
    parser.add_argument('--sources', type=int, default=600)
    args = parser.parse_args()
    if args.sources < 60:
        parser.error('At least 60 sources required')
    root = Path(args.output)
    if (root / 'manifest.csv').exists():
        parser.error('Choose an output without an existing manifest')
    for directory in ('images', 'masks', 'previews'):
        (root / directory).mkdir(parents=True, exist_ok=True)
    rng = random.Random(2026)
    rows, previews = [], []
    # Twenty layout configurations; hold out complete configurations.
    layouts = list(range(20))
    rng.shuffle(layouts)
    partitions = {'train': layouts[:14], 'val': layouts[14:17], 'test': layouts[17:]}
    for source in range(args.sources):
        split = 'train' if source < int(.7*args.sources) else 'val' if source < int(.85*args.sources) else 'test'
        template = partitions[split][source % len(partitions[split])]
        family = ['arial.ttf', 'times.ttf', 'cour.ttf', 'calibri.ttf'][template % 4]
        size = rng.randint(19, 25)
        body = font(size, family)
        heading = font(29, family)
        paper = rng.randint(240, 255)
        bg = (paper, paper, max(230, paper-3))
        ink = tuple([rng.randint(0, 55)]*3)
        image = Image.new('RGB', (640, 800), bg)
        draw = ImageDraw.Draw(image)
        left = 30 + (template % 5)*9
        top = 160 + (template // 5)*18
        gap = 62 + template % 3 * 5
        value_x = 340 + template % 4 * 12
        draw.text((left, 30), 'FICTIONAL / RESEARCH ONLY', font=heading, fill=ink)
        draw.text((left, 85), ['SAMPLE INVOICE', 'SAMPLE RECEIPT', 'SAMPLE RECORD'][template % 3], font=body, fill=ink)
        fields = [('Reference', f'{rng.randint(10000,99999)}'),
                  ('Date', f'{rng.randint(1,28):02d}/10/2026'),
                  ('Quantity', str(rng.randint(1,90))),
                  ('Unit price', str(rng.randint(100,9999))),
                  ('Amount INR', str(rng.randint(1000,99999))),
                  ('Record code', f'R{rng.randint(1000,9999)}')]
        if template % 2:
            draw.rectangle((left-8, top-12, 605, top+gap*6), outline=ink, width=1)
        locations = []
        for index, (label, value) in enumerate(fields):
            y = top + index*gap
            draw.text((left, y), label, font=body, fill=ink)
            draw.text((value_x, y), value, font=body, fill=ink)
            locations.append((value_x, y))
        draw.text((left, 745), 'Generated sample - no real personal data', font=font(17, family), fill=ink)
        edited = image.copy()
        ed = ImageDraw.Draw(edited)
        mask = Image.new('L', image.size, 0)
        md = ImageDraw.Draw(mask)
        boxes = []
        method = rng.choice(['matched_font', 'font_mismatch', 'patch_tone'])
        selected = rng.sample(range(len(fields)), rng.randint(1, 2))
        for index in selected:
            old = fields[index][1]
            # Preserve string shape; no deterministic "larger amount" cue.
            replacement = ''.join(str((int(c)+rng.randint(1,9)) % 10) if c.isdigit() else c for c in old)
            new_font = font(size + rng.choice([-1, 1]), 'arial.ttf') if method == 'font_mismatch' else body
            loc = locations[index]
            a = draw.textbbox(loc, old, font=body)
            b = ed.textbbox(loc, replacement, font=new_font)
            box = (min(a[0], b[0])-2, min(a[1], b[1])-2, max(a[2], b[2])+2, max(a[3], b[3])+2)
            patch = tuple(max(0, min(255, c+rng.choice([-3, 3]))) for c in bg) if method == 'patch_tone' else bg
            ed.rectangle(box, fill=patch)
            ed.text(loc, replacement, font=new_font, fill=ink)
            md.rectangle(box, fill=255)
            boxes.append(box)
        # Apply identical acquisition degradation distributions to both labels.
        quality = rng.randint(65, 96)
        blur = rng.choice([0, 0, .3, .6])
        processed = []
        for variant, document in [('authentic', image), ('tampered', edited)]:
            if blur:
                document = document.filter(ImageFilter.GaussianBlur(blur))
            buffer = io.BytesIO()
            document.save(buffer, format='JPEG', quality=quality)
            document = Image.open(io.BytesIO(buffer.getvalue())).convert('RGB')
            name = f'{source:05d}_{variant}.png'
            document.save(root / 'images' / name)
            target = mask if variant == 'tampered' else Image.new('L', image.size, 0)
            target.save(root / 'masks' / name)
            rows.append(dict(source_id=source, template_id=template, split=split,
                             image=f'images/{name}', mask=f'masks/{name}',
                             label=int(variant=='tampered'), edit_type=method if variant=='tampered' else 'none',
                             provenance='synthetic', jpeg_quality=quality, blur_radius=blur))
            processed.append(document)
        if len(previews) < 4 and (not previews or template != previews[-1][0]):
            overlay = processed[1].copy()
            for box in boxes:
                ImageDraw.Draw(overlay).rectangle(box, outline='red', width=3)
            strip = Image.new('RGB', (1920, 840), 'white')
            for col, (doc, title) in enumerate(zip([*processed, overlay], ['Original', 'Edited', 'Ground truth (not prediction)'])):
                strip.paste(doc, (640*col, 40))
                ImageDraw.Draw(strip).text((640*col+20, 8), title, font=font(21, family), fill='black')
            previews.append((template, strip))
    with (root/'manifest.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = dict(seed=2026, sources=args.sources, samples=len(rows),
                  splits={s: sum(r['split']==s for r in rows) for s in partitions},
                  template_partitions=partitions, provenance='synthetic only',
                  limitations=['Generated layouts and simulated edits only; not representative of real forgery.',
                               'Masks describe edit rectangles, not exact glyph pixels.',
                               'Matched-font edits can lack detectable visual evidence.',
                               'Fonts may differ between Windows and Colab; preserve generated dataset.'])
    (root/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    sheet = Image.new('RGB', (1920, 840*len(previews)), 'white')
    for i, (_, strip) in enumerate(previews):
        sheet.paste(strip, (0, 840*i))
    sheet.thumbnail((1200, 2100))
    sheet.save(root/'previews/examples.png')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

"""Check segmentation data integrity and split leakage."""
import argparse
import csv
from collections import defaultdict
from pathlib import Path
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('root', type=Path)
args = parser.parse_args()
rows = list(csv.DictReader((args.root/'manifest.csv').open(encoding='utf-8')))
assert rows, 'Empty manifest'
sources, templates = defaultdict(set), defaultdict(set)
for row in rows:
    sources[row['source_id']].add(row['split'])
    if 'template_id' in row:
        templates[row['template_id']].add(row['split'])
    with Image.open(args.root/row['image']) as image, Image.open(args.root/row['mask']) as mask:
        assert image.size == mask.size, row
        assert mask.mode == 'L', row
        assert {value for _, value in mask.getcolors(257)} <= {0, 255}, row
        assert bool(mask.getbbox()) == bool(int(row['label'])), row
assert all(len(s)==1 for s in sources.values()), 'Source leakage'
assert all(len(s)==1 for s in templates.values()), 'Template leakage'
assert all(sum(r['source_id']==source for r in rows)==2 for source in sources), 'Missing pair'
print(f'PASS: {len(rows)} image/mask pairs; binary masks; labels; no source/template split leakage')

"""Create a bounded portable application bundle without virtualenv or user uploads."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
out = root/'deliverables/docguard_phase6_app.zip'
paths = [root/'app.py', root/'start_app.ps1', root/'README.md', root/'PROJECT_PLAN.md', *root.glob('requirements-*.txt')]
for folder in ('docguard', 'scripts', 'tests', 'docs', '.streamlit', 'notebooks', 'assets', 'deliverables/robustness'):
    paths.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for run in ('cnn_local_preliminary', 'transformer_finetuned_local'):
    paths.extend(p for p in (root/'runs'/run).glob('*') if p.is_file())
for source in ('00510', '00511'):
    for variant in ('authentic', 'tampered'):
        paths.append(root/'data/synthetic_v2/images'/f'{source}_{variant}.png')
out.parent.mkdir(exist_ok=True)
with ZipFile(out, 'w', compression=ZIP_DEFLATED) as archive:
    for path in sorted(set(paths)):
        archive.write(path, path.relative_to(root).as_posix())
with ZipFile(out) as archive:
    assert archive.testzip() is None
    assert 'app.py' in archive.namelist()
    assert 'runs/transformer_finetuned_local/best.pt' in archive.namelist()
print(f'App bundle verified: {out} ({out.stat().st_size/1024**2:.1f} MB)')

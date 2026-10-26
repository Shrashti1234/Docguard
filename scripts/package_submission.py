"""Package the complete source, generated main dataset and submission artifacts."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables/DocGuard_Complete_Team_Project.zip'
files=[p for p in ROOT.iterdir() if p.is_file() and p.suffix not in ('.zip',)]
for folder in ('.streamlit','docguard','scripts','tests','docs','assets','notebooks','data/synthetic_v2','runs','deliverables/submission','deliverables/robustness'):
    files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.zip'))
files.extend([ROOT/'deliverables/model_comparison.json',ROOT/'deliverables/model_comparison_preview.png'])
manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
with ZipFile(OUT,'w',compression=ZIP_DEFLATED) as z:
    for p in sorted(set(files)):z.write(p,'DocGuard/'+p.relative_to(ROOT).as_posix())
    z.writestr('DocGuard/PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
with ZipFile(OUT) as z:
    assert z.testzip() is None
    for required in ('app.py','runs/transformer_finetuned_local/best.pt','deliverables/submission/DocGuard_Report.pdf','deliverables/submission/DocGuard_Assessment.pptx'):
        assert 'DocGuard/'+required in z.namelist(),required
    assert len([n for n in z.namelist() if '/data/synthetic_v2/images/' in n])==1200
print(f'Verified {len(manifest)} files; {OUT.stat().st_size/1024**2:.1f} MB; {OUT}')

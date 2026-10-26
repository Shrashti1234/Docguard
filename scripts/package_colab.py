"""Package approved generated data and source; never include credentials or virtualenv."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
out = root/'deliverables'
out.mkdir(exist_ok=True)
notebooks = root/'notebooks'
notebooks.mkdir(exist_ok=True)


def markdown(text):
    return dict(cell_type='markdown', metadata={}, source=text.splitlines(keepends=True))


def code(text):
    return dict(cell_type='code', metadata={}, source=text.splitlines(keepends=True), execution_count=None, outputs=[])


cells = [
    markdown('# DocGuard — Phase 3 CNN baseline\n\nSynthetic-data research prototype. Select **Runtime → Change runtime type → GPU**, then run cells in order. Upload `docguard_colab.zip` when asked. No accuracy is assumed in advance. Preserve downloaded outputs. Training here is user initiated; this notebook has not been run in your Google account.'),
    code('from google.colab import files\nfrom pathlib import Path\nimport zipfile, os\nuploaded = files.upload()\nassert "docguard_colab.zip" in uploaded, "Upload docguard_colab.zip"\nwork = Path("/content/docguard")\nwork.mkdir(exist_ok=True)\nwith zipfile.ZipFile("docguard_colab.zip") as archive:\n    for name in archive.namelist():\n        assert (work/name).resolve().is_relative_to(work.resolve()), "Unsafe archive path"\n    archive.extractall(work)\nos.chdir(work)\nprint("Project extracted:", work)'),
    code('%pip install -q -r requirements-train.txt\nimport torch\nprint("PyTorch:", torch.__version__)\nprint("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Unavailable")\nassert torch.cuda.is_available(), "Enable a GPU runtime before full training"'),
    code('import subprocess, sys\nsubprocess.run([sys.executable, "scripts/validate_dataset.py", "data/synthetic_v2"], check=True)\nsubprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], check=True)'),
    markdown('## Train\nUses all approved training images. The best checkpoint is selected by validation F1 at threshold 0.5. Afterwards the output threshold is selected on validation only. Test data is not read by training. If rerunning, select a new output directory rather than overwriting a previous run.'),
    code('import subprocess, sys\nRUN = "runs/cnn_colab"\nsubprocess.run([sys.executable, "-m", "docguard.baseline", "train", "--epochs", "20", "--batch-size", "8", "--output", RUN], check=True)'),
    markdown('## Held-out evaluation\nRun after training finishes. Do not tune settings using test results. Authentic false alarms use a fixed rule: at least 0.1% of pixels predicted edited. This is not a calibrated document authenticity score.'),
    code('subprocess.run([sys.executable, "-m", "docguard.baseline", "test", "--output", RUN], check=True)\nimport json\nprint(json.dumps(json.loads(Path(RUN, "test_metrics.json").read_text()), indent=2))'),
    code('from IPython.display import display, Image\nfor path in sorted(Path(RUN, "predictions").glob("*.png"))[:4]:\n    display(Image(filename=str(path)))'),
    code('import shutil\narchive = shutil.make_archive("/content/docguard_cnn_results", "zip", RUN)\nfiles.download(archive)'),
    markdown('## Interpretation\nReport synthetic-only F1/IoU, authentic false alarms, and per-edit-type metrics. Clean matched-font replacements may contain no recoverable forensic evidence. Generated dates can be invalid and introduce shortcuts. A high synthetic score does not demonstrate real-document accuracy. Keep the dataset and manifest unchanged for the Transformer comparison.')
]
notebook = dict(nbformat=4, nbformat_minor=5, metadata=dict(kernelspec=dict(display_name='Python 3', language='python', name='python3'), language_info=dict(name='python')), cells=cells)
for i, cell in enumerate(cells):
    cell['id'] = f'docguard-{i:02d}'
path = notebooks/'Phase_3_CNN_Colab.ipynb'
path.write_text(json.dumps(notebook, indent=2), encoding='utf-8')
phase4 = [markdown('# DocGuard — Phase 4 Transformer comparison\n\nThis notebook fine-tunes a pretrained MiT-B0 encoder with a custom segmentation decoder and trains a matching-resolution CNN baseline. Synthetic-only data; results are unknown until executed. Select a GPU runtime. Retain the upstream research/evaluation license with derived weights.'),
          cells[1],
          code('%pip install -q -r requirements-transformer.txt\nimport torch\nassert torch.cuda.is_available(), "Enable a GPU runtime before training"\nprint(torch.cuda.get_device_name(0))'),
          cells[3],
          markdown('## Train both models before viewing test results\nBoth use 320×400 images and 20 epochs, but pretraining, learning rates and batch sizes differ. This is a practical baseline comparison, not an architecture-only experiment. Encoder fine-tuning is enabled for the Transformer.'),
          code('CNN = "runs/cnn_phase4_colab"\nTRANSFORMER = "runs/transformer_phase4_colab"\nsubprocess.run([sys.executable, "-m", "docguard.baseline", "train", "--output", CNN, "--epochs", "20"], check=True)'),
          code('subprocess.run([sys.executable, "-m", "docguard.baseline", "train", "--model", "transformer", "--output", TRANSFORMER, "--epochs", "20", "--batch-size", "4", "--lr", "0.00006"], check=True)'),
          code('for run in [CNN, TRANSFORMER]:\n    subprocess.run([sys.executable, "-m", "docguard.baseline", "test", "--output", run, "--batch-size", "4"], check=True)\nsubprocess.run([sys.executable, "scripts/compare_models.py", CNN, TRANSFORMER], check=True)'),
          code('from IPython.display import display, Image\nfor path in sorted(Path(TRANSFORMER, "predictions").glob("*.png"))[:4]:\n    display(Image(filename=str(path)))'),
          code('import shutil\nexport = Path("/content/docguard_phase4_export")\nexport.mkdir(exist_ok=True)\nfor run in [CNN, TRANSFORMER]:\n    shutil.copytree(run, export/Path(run).name, dirs_exist_ok=True)\nshutil.copy("deliverables/model_comparison.json", export)\nshutil.copy("docs/third_party/SEGFORMER_LICENSE.txt", export)\narchive = shutil.make_archive("/content/docguard_phase4_results", "zip", export)\nfiles.download(archive)'),
          markdown('## Review gate\nInspect global F1/IoU, original-document false alarms, subgroup metrics and prediction examples. Do not claim improvement unless measured. This notebook has not been executed in your Colab account. Clean synthetic edits may lack visual evidence; results do not establish real-document reliability.')]
phase4_notebook = dict(nbformat=4, nbformat_minor=5, metadata=notebook['metadata'], cells=phase4)
for i, cell in enumerate(phase4):
    cell['id'] = f'phase4-{i:02d}'
(notebooks/'Phase_4_Transformer_Colab.ipynb').write_text(json.dumps(phase4_notebook, indent=2), encoding='utf-8')
paths = [*root.glob('requirements-*.txt'), root/'README.md', root/'PROJECT_PLAN.md']
for directory in ('docguard', 'scripts', 'tests', 'docs', 'data/synthetic_v2'):
    paths.extend(p for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
with ZipFile(out/'docguard_colab.zip', 'w', compression=ZIP_DEFLATED, compresslevel=3) as archive:
    for item in paths:
        archive.write(item, item.relative_to(root).as_posix())
print(f'Notebook: {path}')
print(f'Bundle: {out / "docguard_colab.zip"} ({(out/"docguard_colab.zip").stat().st_size/1024**2:.1f} MB)')

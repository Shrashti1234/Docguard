# DocGuard

College team assessment prototype for document tampering localization. Current dataset is explicitly synthetic; real-document accuracy has not been established.

## Current phase

Phase 7: personalized assessment report, presentation and complete team handoff prepared for KIET Deemed to be University, B.Tech CS, Semester 5, Section D, Deep Learning and GenAI (CS312B).

Team: Shrashti Agarwal (2400290120240), Saumya Tiwari (2400240120230), Subrat Singh (2400290120250). Setup, demo and viva notes: [docs/TEAM_SETUP_AND_VIVA.md](docs/TEAM_SETUP_AND_VIVA.md). Submission files are in `deliverables/submission/`. Trained application checkpoints and English examples are included in Git. The full generated dataset is included in the complete team ZIP or can be regenerated with the dataset script.

## Run the application

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-app.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

If `.venv` is already set up, run `start_app.ps1`. Open http://127.0.0.1:8501. Select an example or upload JPG/PNG/PDF, choose a trained model, and click **Analyse page**. Download the overlay, PDF review or full review ZIP. See `docs/PHASE_6.md` for limits and verification.

The app bundle contains English and multilingual demo documents and trained weights, not the full training dataset. Its models remain preliminary research models; a working interface does not improve detection accuracy.

The revised UI includes synthetic Hindi, Marathi, Tamil and Bengali receipt examples and a document-language selector (also English, Telugu, Urdu and Other). Language is recorded in exports. This is visual analysis without OCR/translation; language-specific accuracy is unvalidated. Hindi PDF examples can be downloaded directly from the sidebar.

Use **Interface language / भाषा** to switch application text between English, हिन्दी, मराठी, தமிழ் and বাংলা. It is independent of document language and preserves the current review. PDF reports remain English; their JSON metadata records the selected interface language.

Actual preliminary CPU results: pixel F1 0.2460, IoU 0.1403; the current document flag rule falsely flagged all 90 original test documents. This is a weak baseline, not a reliable screening tool. See `docs/PHASE_3_RESULTS.md`. The planned higher-resolution Colab run is not yet executed.

Full fine-tuned Transformer results: F1 0.2288, IoU 0.1292, 77/90 original documents falsely flagged. It did not outperform CNN global F1. See `docs/PHASE_4_RESULTS.md` for both Transformer modes and limitations.

Robustness results: `deliverables/robustness/REPORT.md`, standalone charts and CSV cover six fixed conditions on both models. The screenshot condition is simulated, not a real capture study. Weights and thresholds were unchanged and clean counts reproduced earlier test results. High false-positive rates remain a limitation.

## Start training in Colab

1. Open [Google Colab](https://colab.research.google.com/) and upload `notebooks/Phase_3_CNN_Colab.ipynb`.
2. Choose a GPU runtime and run cells in order.
3. When prompted, upload `deliverables/docguard_colab.zip` (contains the generated dataset and source).
4. Train, evaluate, inspect predictions, and download `docguard_cnn_results.zip`.

For the planned full CNN/Transformer comparison, instead open `notebooks/Phase_4_Transformer_Colab.ipynb`, use the same upload bundle, and run its checked cells. It installs `requirements-transformer.txt`, trains both models at matching resolution/epochs, evaluates them and exports weights/results with the upstream license. No Colab run is claimed until executed.

The notebook requires the user's own Colab session. No authenticated runtime has been started by this project.

## Local use

Use a virtual environment. Install `requirements-train.txt`, then run:

```
python -m unittest discover -s tests -v
python -m docguard.baseline train --output runs/cnn_baseline
python -m docguard.baseline test --output runs/cnn_baseline
```

Default training uses 320×400 images for 20 epochs. CPU runs can be slow. Use fresh output names for new experiments. Only evaluate test data after settings have been selected with training and validation data.

## Data preparation

```
python -m pip install -r requirements-data.txt
python scripts/prepare_dataset.py
python scripts/validate_dataset.py data/synthetic_v2
python scripts/package_colab.py
```

The generator refuses an existing manifest to protect previous data. Font rendering can differ across operating systems; use the packaged dataset for consistent comparisons. Training configuration stores the manifest hash.

## Documentation

- `docs/DATASET.md`: access restrictions, generation and known biases.
- `docs/PHASE_3.md`: architecture, loss, metric definitions and outputs.
- `docs/UI_DIRECTION.md`: user's preference for a restrained document review interface.
- `docs/PHASE_5.md`: robustness protocol and reproducible evaluation/report commands.
- `PROJECT_PLAN.md`: scope and feedback gates.

## Limitations

Synthetic edit masks are annotations, not detector predictions. Clean rerendered text may leave no detectable edit evidence. Some generated numeric replacements are semantically invalid. Results must be labeled synthetic-only. Model outputs do not prove authenticity or fraud.

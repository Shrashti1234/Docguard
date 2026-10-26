# Phase 6 — local document review application

## Start

From the project folder:

```
.venv\Scripts\python.exe -m pip install -r requirements-app.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Or run `start_app.ps1` in PowerShell after installing dependencies. The default URL is http://127.0.0.1:8501. The app is local; no cloud deployment or login is configured. To set up a fresh environment, run `python -m venv .venv` first.

## Included workflow

- Use a fictional example or upload JPG, PNG or PDF (20 MB maximum).
- PDFs: 1–20 pages; choose one page to render/review. Rendering is capped at 1,600 pixels on the longer side. Encrypted PDFs require an unlocked copy.
- Choose the trained CNN or fully fine-tuned MiT-B0 model. No untrained fallback is used.
- Analyse the selected page, then view original, thresholded overlay, continuous heatmap or side-by-side comparison.
- Adjust overlay opacity without changing the model's validation-selected threshold.
- Download overlay PNG, single-page review PDF, or ZIP with JSON metadata, PDF, mask, heatmap and overlay.

Input images are EXIF-oriented and transparent pixels composited onto white. Images over 20 megapixels are rejected. Page/model/document changes invalidate prior predictions. Files are processed in memory; uploads are not written to a project dataset or sent to a model API. Uploaded document content is not globally cached. Trained models are cached locally across sessions.

## Presentation

Revised after user feedback: navy sidebar, blue controls, stronger sans-serif typography, a dotted document canvas, paper shadow and a compact review panel. No gradient hero, decorative metrics dashboard or animations. Mobile starts with the sidebar collapsed; the Analyse action remains above the document. Technical results live in a separate Evaluation & method tab.

## Languages and examples

The document-language selector records English, Hindi, Marathi, Tamil, Bengali, Telugu, Urdu or Other in review metadata/PDF. It does not select a language-trained model or run OCR/translation. Any supported JPG/PNG/PDF can contain these scripts, but language-specific detection accuracy has not been established.

Properly shaped synthetic Hindi, Marathi, Tamil and Bengali receipt examples are included under `assets/examples/`, with downloadable PDFs. Hindi includes original and edited versions; other new scripts include original examples. These are workflow demonstrations, not new training data or a multilingual benchmark.

The independent **Interface language / भाषा** control switches application labels, actions, review messages, validation errors and method explanations between English, Hindi, Marathi, Tamil and Bengali. Session choices and predictions are preserved across language switches. Document language remains independent and interface language is recorded in JSON exports. PDF reports, technical identifiers, chart image labels and native browser/Streamlit upload prompts remain English; the PDF export limitation is shown in the selected language. Interface translation does not alter model capability or translate document text.

Translations live in `docguard/i18n.py`. Catalog tests check complete keys, non-empty translations and matching dynamic placeholders. `python -m scripts.verify_languages` exercises switching every interface language, preserving a Hindi document and its existing result/view, exported locale metadata, returning to English and a narrow Tamil viewport.

Highlighted percentage means model-grid foreground fraction, not a fraud confidence score. The app labels itself a research prototype and includes measured high false-positive rates. Clear overlays do not certify authenticity. Arbitrary real PDFs and different aspect ratios are outside the validated synthetic domain.

## Verification

Unit checks cover decoding, transparency, empty/malformed input, PDF page selection/limits, password protection, byte/pixel limits, missing model discovery, overlay mapping and export contents. Existing model and robustness tests remain in the suite.

`scripts/verify_app.py` uses Playwright against a running server to exercise actual Transformer/CNN inference, PNG upload, two-page PDF navigation, stale-result invalidation, invalid-PDF handling, side-by-side display, browser PDF/ZIP downloads and 390px mobile inference. Browser tooling is optional: install `requirements-browser.txt`, then `python -m playwright install chromium`.

PDF export was rendered with Poppler and visually inspected. Downloaded PDF/ZIP metadata and archive integrity were checked. Preview screenshots and check logs live in `deliverables/app_preview/`.

Current automated suite: **14 tests passed**, including translation coverage/placeholders and actual Streamlit state preservation. The 14 main browser flows cover both models, uploads, multilingual examples and exports. Separate interface-language browser checks cover all five locales, unchanged prediction metadata, upload preservation and mobile layout. A fresh extraction of the initial portable app was tested with `HF_HUB_OFFLINE=1`: both included trained checkpoints restored and produced demo predictions using the installed environment. A fully fresh dependency installation on another machine has not been tested.

Automatic source watching is disabled to avoid Streamlit introspecting Transformers lazy modules. Restart the app after editing Python source; ordinary document/model/view controls still rerun normally.

## Portable bundle

`deliverables/docguard_phase6_app.zip` contains application source, requirements, trained CNN/Transformer checkpoints, English demo images, multilingual PNG/PDF examples, reference charts, documentation and launcher. It excludes the virtual environment and full training dataset. Use the existing Colab bundle for full generated training data.

## Remaining phase

Phase 7 submission report, slides, final packaging and demo guide require user feedback on this application first. Higher-resolution Colab training is still pending; neither app completion nor a working upload flow implies improved detection quality.

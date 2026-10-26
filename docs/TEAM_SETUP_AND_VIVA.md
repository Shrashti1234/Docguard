# DocGuard team handoff

KIET Deemed to be University · B.Tech CS · Semester 5 · Section D
Deep Learning and GenAI · CS312B

| Member | Roll number |
| --- | --- |
| Shrashti Agarwal | 2400290120240 |
| Saumya Tiwari | 2400240120230 |
| Subrat Singh | 2400290120250 |

## Start on a teammate laptop

Extract the complete ZIP first. Open a terminal in the extracted project folder. Python and an internet connection are required for the initial package installation; the trained models are included.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-app.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Linux or macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-app.txt
.venv/bin/python -m streamlit run app.py
```

Open http://127.0.0.1:8501. No API key is required. After dependencies are installed, local checkpoint inference can run offline. The virtual environment is deliberately excluded because installed environments are machine dependent. The supplied scripts regenerate the synthetic dataset; the full team ZIP also contains the generated dataset.

## Five minute presentation

1. Explain the problem: localize suspicious edits instead of returning only a page label.
2. Describe the 1,200 image synthetic dataset and source/layout disjoint split.
3. Compare the small CNN with MiT B0 plus a custom segmentation decoder.
4. Run an edited example, inspect both models and download a review.
5. Upload a Hindi PDF and switch the interface language.
6. Show actual F1 results and false positive rates. End with limitations and proposed improvements.

Suggested speaking allocation, to be agreed by the team: one member introduces data and problem; one explains models and evaluation; one demonstrates the app and limitations. This is a proposal, not a record of individual contributions.

## Viva questions with Hinglish explanations

**Why segmentation?** Page label se edit ki location nahi milti. Segmentation har model pixel par score deti hai, jisse overlay ban sakta hai.

**Why CNN and Transformer?** CNN local patterns seekhta hai. Transformer encoder broader context model karta hai. Same split par compare kiya; Transformer ka F1 CNN se better nahi tha.

**Did you use a GAN?** No. Implemented topic Transformer based document segmentation hai, CNN baseline ke saath. Synthetic data procedural image generation se bana hai, GAN se nahi.

**What was pretrained?** MiT B0 encoder ImageNet pretrained tha. Binary multiscale decoder project ka hai. Frozen and full fine tuning experiments alag hain.

**Why no accuracy headline?** Background pixels bahut zyada hain. Pixel accuracy misleading ho sakti hai. Precision, recall, F1 and IoU report karte hain.

**What is data leakage prevention?** Same receipt source aur layout configuration ko multiple splits mein nahi dala. Threshold validation par select hua, test par nahi.

**What does the highlighted percentage mean?** Model grid ka predicted positive area. Fraud probability nahi hai.

**Is Hindi supported?** Hindi PDF upload aur Hindi interface workflow supported hai. OCR/translation implement nahi hai; Hindi specific model accuracy measure nahi ki gayi.

**What are the results?** CNN F1 0.2460, full Transformer F1 0.2288. Authentic page false flags 90/90 and 77/90 respectively. Yeh weak research models hain.

**Why weak results?** Small synthetic domain, three CPU epochs, low resolution and ambiguous edits likely contributors hain. In causes ka separate ablation study nahi hua.

**What is future work?** Licensed real documents, better masks, longer training, higher resolution and independent calibration. In improvements ko achieved result mat bolna.

## Repository

https://github.com/Shrashti1234/Docguard

Git clone includes application source, trained application models and English demo images. The complete team ZIP additionally includes the full generated dataset. Do not commit personal uploaded documents, credentials, virtual environments or generated ZIP files.

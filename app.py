"""Run with: python -m streamlit run app.py"""
import hashlib
import html
import json
import logging
from pathlib import Path
import streamlit as st
from docguard.i18n import LANGUAGES, translate
from docguard.inference import (ROOT, LIMITATION, DocumentInputError, available_models,
    document_info, document_page, load_trained_model, predict, display_images,
    review_metadata, report_pdf, export_review, png_bytes)

st.set_page_config(page_title='DocGuard | Document review', layout='wide', initial_sidebar_state='auto')
st.markdown('''<style>
.stApp {font-family:"Segoe UI",Arial,sans-serif;background:#f2f5f9;}
.block-container {padding-top:2rem;padding-bottom:2rem;max-width:1530px;}
h1,h2,h3 {font-family:"Segoe UI",Arial,sans-serif;font-weight:650!important;letter-spacing:-.035em;}
h1{font-size:2.1rem!important}h3{font-size:1.22rem!important}
[data-testid="stSidebar"]{background:#142c3b;border-right:1px solid #203e51;color:#edf4fa;}
[data-testid="stAppDeployButton"] {display:none;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,[data-testid="stSidebar"] label p {color:#c3d5e4!important;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:#b1c6d8!important;}
[data-testid="stSidebar"] .stDownloadButton button{background:#24495e;border-color:#55778d;}
[data-testid="stSidebar"] .stDownloadButton button p{color:#f4f8fc!important;}
[data-testid="stSidebar"] [data-baseweb="select"]>div{background:#203f52;border-color:#3a5668;color:white;border-radius:7px;}
[data-testid="stSidebar"] [data-baseweb="select"] span,[data-testid="stSidebar"] [data-baseweb="select"] input{color:#f2f7fb!important;}
[data-testid="stSidebar"] [data-baseweb="select"] svg{fill:#bdcfde;}
[data-testid="stSidebar"] hr{border-color:#365063;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]{background:#203f52;border:1px dashed #637c8e;}
[data-testid="stSidebar"] .block-container{padding-top:1.8rem;}
.brand{display:flex;align-items:center;gap:12px;font-size:26px;font-weight:700;letter-spacing:-1px;margin-bottom:10px;color:#fff;}
.brand-mark{display:grid;place-items:center;width:37px;height:42px;border:1px solid #6489ad;border-radius:8px;color:#9ac5ff;font-size:20px;letter-spacing:-3px;}
.eyebrow{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#93b0c6;margin-bottom:32px;}
.workspace-head{display:flex;justify-content:space-between;align-items:center;padding-bottom:23px;margin-bottom:12px;}
.workspace-kicker{font-size:10px;letter-spacing:1.8px;color:#627b94;font-weight:650;margin-bottom:8px;}
.workspace-head .name{font-size:30px;font-weight:700;letter-spacing:-1.1px;color:#142c42;}
.workspace-description{font-size:13px;color:#728398;margin-top:6px;}
.status{display:flex;align-items:center;gap:7px;font-size:10px;font-weight:650;letter-spacing:.7px;color:#5c7084;border:1px solid #d6e0e9;background:#fff;padding:8px 11px;border-radius:30px;white-space:nowrap;}
.status:before{content:"";width:6px;height:6px;background:#c58437;border-radius:100%;}
.fileline{display:flex;align-items:center;gap:12px;font-size:12px;color:#667b90;margin:6px 0 15px;overflow-wrap:anywhere;}
.file-tag{font-size:9px;letter-spacing:1px;font-weight:700;color:#446984;background:#e1eaf2;padding:5px 7px;border-radius:4px;}
.result-label{font-size:10px;text-transform:uppercase;letter-spacing:1.3px;color:#74859b;margin-top:15px;}
.result-value{font-size:43px;font-weight:650;letter-spacing:-2px;line-height:1.4;color:#315fc3;}
.st-key-review_notes{padding:22px!important;background:white;border:1px solid #dfe6ef;border-top:3px solid #5377cc;border-radius:10px;box-shadow:0 4px 16px #203b5810;}
.canvas-bar{display:flex;justify-content:space-between;font-size:9px;font-weight:650;letter-spacing:1.3px;color:#5c7288;margin-bottom:14px;}
.st-key-document_canvas{background-color:#e0e7ef;background-image:radial-gradient(#afbed0 .65px,transparent .65px);background-size:13px 13px;border:1px solid #cbd6e2;padding:22px!important;border-radius:10px;min-height:520px;}
.st-key-document_canvas [data-testid="stImage"] {display:flex;justify-content:center;}
.st-key-document_canvas img{max-height:660px;object-fit:contain;box-shadow:0 12px 30px #293e5426;border:1px solid #fff;}
.stButton button,.stDownloadButton button{border-radius:7px!important;font-weight:600;}
.stButton button[kind="primary"]{background:#315fc3;border-color:#315fc3;box-shadow:0 4px 9px #315fc325;}
.stButton button[kind="primary"]:hover{background:#244ca3;border-color:#244ca3;}
[data-baseweb="tab-list"]{gap:26px;border-bottom:1px solid #dce4ee;margin-bottom:14px;}
[data-baseweb="tab"]{font-weight:600;font-size:13px;}
@media(max-width:760px){.block-container{padding-top:4.2rem;padding-left:1rem;padding-right:1rem}.workspace-head{align-items:flex-start;gap:10px}.workspace-head .name{font-size:23px}.workspace-description{font-size:12px}.status{font-size:8px;padding:7px}.st-key-document_canvas{padding:10px!important;min-height:250px}.st-key-review_notes{padding:18px!important}.fileline{gap:7px;font-size:11px}}
</style>''', unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def cached_model(path, fingerprint):
    return load_trained_model(path)


models = available_models()
interface_language = st.session_state.get('interface_language', 'en')
def t(message, **values):
    return translate(message, interface_language, **values)

def remember_choice(widget_key, stored_key):
    st.session_state[stored_key] = st.session_state[widget_key]

def choice(widget, label, options, name, default=None, scope='', **kwargs):
    options = list(options)
    stored_key = 'choice_'+name
    saved = st.session_state.get(stored_key, default if default is not None else options[0])
    if saved not in options:
        saved = options[0]
    widget_key = name+'_'+interface_language+'_'+scope
    result = widget(t(label), options, index=options.index(saved), key=widget_key,
                    on_change=remember_choice, args=(widget_key,stored_key), **kwargs)
    st.session_state[stored_key] = result
    return result

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">D/</span>DocGuard</div><div class="eyebrow">'+t('Document inspection workspace')+'</div>', unsafe_allow_html=True)
    st.selectbox('Interface language / भाषा', list(LANGUAGES), format_func=lambda code:LANGUAGES[code], key='interface_language')
    source_mode = choice(st.radio,'Document source', ['Example document', 'Upload document'],'document_source',format_func=t)
    if source_mode == 'Upload document':
        st.caption(t('Choose a document'))
        upload_version = st.session_state.get('upload_version', 0)
        upload = st.file_uploader('Document file', type=['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tif', 'tiff', 'pdf'], label_visibility='collapsed', key=f'document_upload_{upload_version}')
        st.caption(t('Up to 20 MB. PDFs: up to 20 pages, reviewed one page at a time.'))
        st.caption('JPG · PNG · WEBP · BMP · TIFF · PDF. Large photos are resized automatically. Export HEIC as JPG first.')
        data = upload.getvalue() if upload else None
        filename = upload.name if upload else None
        if upload is not None:
            st.caption(f'{upload.name} · {upload.size/1024:.0f} KB')
            if st.button('Clear upload / try another file', key='clear_upload'):
                st.session_state['upload_version'] = upload_version + 1
                for name in ('prediction', 'bundle', 'review_identity'):
                    st.session_state.pop(name, None)
                st.rerun()
    else:
        examples = {'Edited fictional receipt':ROOT/'data/synthetic_v2/images/00510_tampered.png',
                    'Original fictional receipt':ROOT/'data/synthetic_v2/images/00510_authentic.png',
                    'Hindi receipt · original':ROOT/'assets/examples/hindi_original.png',
                    'Hindi receipt · edited':ROOT/'assets/examples/hindi_edited.png',
                    'Marathi receipt · original':ROOT/'assets/examples/marathi_original.png',
                    'Tamil receipt · original':ROOT/'assets/examples/tamil_original.png',
                    'Bengali receipt · original':ROOT/'assets/examples/bengali_original.png'}
        example = choice(st.selectbox,'Example',list(examples),'example_document',format_func=t)
        sample = examples[example]
        data = sample.read_bytes() if sample.exists() else None
        filename = sample.name
        st.caption(t('Generated sample for demonstrating the workflow.'))
        if sample.with_suffix('.pdf').exists():
            example_language = example.split(' receipt')[0]
            st.download_button(t('Download {language} example PDF', language=example_language), sample.with_suffix('.pdf').read_bytes(), sample.with_suffix('.pdf').name, 'application/pdf', key='download_example')
    st.divider()
    native_names={'English':'English', 'Hindi':'Hindi · हिन्दी', 'Marathi':'Marathi · मराठी',
                  'Tamil':'Tamil · தமிழ்', 'Bengali':'Bengali · বাংলা', 'Telugu':'Telugu · తెలుగు', 'Urdu':'Urdu · اردو', 'Other':'Other language'}
    inferred_language = next((language for language in native_names if filename and filename.startswith(language.lower()+'_')), 'English')
    if st.session_state.get('document_language_source') != filename:
        st.session_state['choice_document_language_value'] = inferred_language
        st.session_state['document_language_source'] = filename
    document_language = choice(st.selectbox,'Document language',list(native_names),'document_language_value',default=inferred_language,
                                   scope=hashlib.sha256((filename or '').encode()).hexdigest()[:12],
                                   format_func=lambda name:t(native_names[name]),
                                   help=t('Language is recorded in the report. Analysis uses image pixels, without OCR or translation.'))
    st.caption(t('These scripts can be uploaded as images/PDFs. Language-specific detection accuracy has not been validated.'))
    st.divider()
    if not models:
        st.error(t('No trained checkpoint found. Complete training before reviewing documents.'))
        st.stop()
    selected = choice(st.selectbox,'Review model',range(len(models)),'review_model',format_func=lambda i:models[i]['title'])
    model_info = models[selected]
    st.caption(t('Trained weights available · local inference'))
    st.divider()
    st.markdown('**'+t('About this prototype')+'**')
    st.caption(t('Synthetic-data research model. Current false-positive rates are high. Highlights support manual review; they do not establish fraud or authenticity.'))

st.markdown('<div class="workspace-head"><div><div class="workspace-kicker">'+t('WORKSPACE / DOCUMENT INSPECTION')+'</div><div class="name">'+t('Document review')+'</div><div class="workspace-description">'+t('Inspect the source. Compare model-selected regions.')+'</div></div><span class="status">'+t('RESEARCH PROTOTYPE')+'</span></div>', unsafe_allow_html=True)
review_tab, research_tab = st.tabs([t('Review workspace'), t('Evaluation & method')])

with research_tab:
    st.subheader(t('What the models have measured'))
    st.write(t('Both models were trained on generated documents. These are preliminary 3-epoch runs at 160 × 200 resolution. Real-document accuracy has not been established.'))
    st.table([{t('Model'):'CNN U-Net', 'Pixel F1':.2460, 'Pixel IoU':.1403, t('Original-document false-positive rate'):'100%'},
              {t('Model'):'Fine-tuned MiT-B0', 'Pixel F1':.2288, 'Pixel IoU':.1292, t('Original-document false-positive rate'):'85.6%'}])
    st.caption(t('Reference results for the included preliminary checkpoints. The document flag rule used ≥0.1% predicted foreground. Pixel F1 is not document-classification accuracy.'))
    chart = ROOT/'deliverables/robustness/robustness.png'
    if chart.exists():
        st.image(str(chart), caption=t('Fixed-weight robustness experiments on synthetic test images.'))
    st.write(t('The Transformer uses a pretrained MiT-B0 encoder with a custom multiscale decoder. Epochs and thresholds were selected on validation data. The screenshot experiment is simulated. Higher-resolution Colab training is prepared but has not run.'))

with review_tab:
    if not data:
        st.subheader(t('Open a document to begin'))
        st.write(t('Upload a JPG, PNG or PDF from the left panel, or choose a fictional example.'))
        st.stop()
    try:
        info = document_info(data, filename)
        page_options = list(range(info['pages']))
        toolbar, page_control, action_control = st.columns([2.5, .8, .9])
        with toolbar:
            view = choice(st.radio,'Document view',['Original','Overlay','Heatmap','Side by side'],'document_view',default='Overlay',horizontal=True,format_func=t)
        with page_control:
            page_index = choice(st.selectbox,'Page',page_options,'document_page',format_func=lambda i:t('{current} of {total}',current=i+1,total=info['pages']))
        with action_control:
            st.caption(t('Review action'))
            analyse = st.button(t('Analyse page'), type='primary', width='stretch', key='analyse_page')
        image = document_page(data, filename, page_index)
    except DocumentInputError as exc:
        st.error(t(str(exc)))
        st.stop()
    identity = hashlib.sha256(data).hexdigest()+f':{page_index}:{model_info["path"]}:{model_info["fingerprint"]}'
    if st.session_state.get('review_identity') != identity:
        st.session_state['review_identity'] = identity
        st.session_state.pop('prediction', None)
        st.session_state.pop('bundle', None)
    st.markdown(f'<div class="fileline"><span class="file-tag">{info["kind"].upper()}</span><span>{html.escape(filename)}</span><span>{t("Page")} {page_index+1} · {image.width} × {image.height} px · {document_language}</span></div>', unsafe_allow_html=True)
    canvas_column, results_column = st.columns([3.1, 1], gap='large')
    with results_column, st.container(key='review_notes'):
        st.subheader(t('Review notes'))
        st.caption(model_info['title'])
        if analyse:
            try:
                with st.spinner(t('Reviewing selected page…')):
                    bundle = cached_model(model_info['path'], model_info['fingerprint'])
                    prediction = predict(bundle, image)
                st.session_state['prediction'] = prediction
                st.session_state['bundle'] = bundle
            except Exception as exc:
                logging.exception('DocGuard analysis failed for %s using %s', filename, model_info['path'])
                st.error(t('The page could not be analysed. Check that the trained checkpoint and app dependencies are available.'))
                st.warning('Try CNN U-Net in Review model, then click Analyse page again. In VS Code, use Run DocGuard so the correct Python environment is selected.')
                with st.expander(t('Technical error')):
                    st.code(f'{type(exc).__name__}: {exc}')
        prediction = st.session_state.get('prediction')
        bundle = st.session_state.get('bundle')
        opacity_key = 'overlay_opacity_'+interface_language
        opacity = st.slider(t('Overlay opacity'),20,90,st.session_state.get('choice_opacity',55),step=5,disabled=prediction is None,
                            key=opacity_key,on_change=remember_choice,args=(opacity_key,'choice_opacity'))/100
        st.session_state['choice_opacity'] = round(opacity*100)
        if prediction is None:
            st.markdown('**'+t('Ready for review')+'**')
            st.caption(t('Analyse this page to reveal the model overlay. The original is shown until then.'))
        else:
            fraction = prediction['highlighted_fraction']
            st.markdown('<div class="result-label">'+t('Highlighted area')+'</div>'+f'<div class="result-value">{fraction*100:.2f}%</div>', unsafe_allow_html=True)
            st.caption(t('Of the model input grid; not a probability of fraud.'))
            st.markdown('**'+t('Manual review required' if fraction else 'No regions above the model threshold')+'**')
            st.caption(t('Compare highlighted regions with the original. A clear overlay does not certify authenticity.'))
            st.divider()
            st.caption(t('Saved threshold {threshold} · Epoch {epoch} · {width} × {height} input',threshold=f"{bundle['threshold']:.2f}",epoch=bundle['epoch'],width=bundle['width'],height=bundle['height']))
            st.caption(t('Inference pipeline: {ms} ms · CPU',ms=f"{prediction['elapsed_ms']:.0f}"))
    rendered = None
    if prediction is not None:
        rendered = display_images(image, prediction['probability'], bundle['threshold'], opacity)
    with canvas_column:
        with st.container(key='document_canvas'):
            st.markdown(f'<div class="canvas-bar"><span>{t("DOCUMENT CANVAS")}</span><span>{t(view).upper()} / {t("Page")} {page_index+1:02d}</span></div>', unsafe_allow_html=True)
            if rendered is None or view == 'Original':
                st.image(image, caption=t('Original document'), width="stretch")
            elif view == 'Side by side':
                original_column, overlay_column = st.columns(2)
                original_column.image(image, caption=t('Original'), width="stretch")
                overlay_column.image(rendered['overlay'], caption=t('Model-selected regions'), width="stretch")
            else:
                st.image(rendered['overlay'] if view=='Overlay' else rendered['heatmap'],
                         caption=t('Red: model-selected pixels' if view=='Overlay' else 'Model output intensity; not calibrated confidence'), width="stretch")
    if rendered is not None:
        metadata = review_metadata(bundle, prediction, image, filename, data, page_index)
        metadata['document_language'] = document_language
        metadata['interface_language'] = interface_language
        metadata['language_validation'] = 'Not benchmarked by language. Visual analysis only; no OCR or translation.'
        pdf = report_pdf(metadata, rendered['overlay'])
        with results_column:
            st.caption(t('PDF reports are currently exported in English.'))
            st.download_button(t('Download overlay'), png_bytes(rendered['overlay']), 'docguard_overlay.png', 'image/png', width="stretch")
            st.download_button(t('Download PDF report'), pdf, 'docguard_review.pdf', 'application/pdf', width="stretch")
            st.download_button(t('Download review ZIP'), export_review(metadata, rendered, pdf), 'docguard_review.zip', 'application/zip', width="stretch")
        with st.expander(t('Review metadata')):
            st.json(metadata)
    st.caption(t('Local review · Uploaded files stay in this running session. Downloads are generated on demand.'))

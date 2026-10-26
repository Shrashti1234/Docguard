"""Local document decoding, trained inference and portable review exports."""
import hashlib
import io
import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
import pymupdf
import torch

MAX_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 20_000_000
MAX_PAGES = 20
ROOT = Path(__file__).resolve().parents[1]
LIMITATION = 'Research prototype trained on synthetic documents. High false-positive rates; highlights do not prove tampering or authenticity.'


class DocumentInputError(ValueError):
    pass


def validate_bytes(data):
    if not data:
        raise DocumentInputError('Choose a non-empty JPG, PNG or PDF document.')
    if len(data) > MAX_BYTES:
        raise DocumentInputError('Document exceeds the 20 MB upload limit.')


def open_pdf(data):
    try:
        doc = pymupdf.open(stream=data, filetype='pdf')
    except Exception as exc:
        raise DocumentInputError('This PDF could not be opened. Try an unencrypted PDF.') from exc
    if doc.needs_pass:
        doc.close()
        raise DocumentInputError('Password-protected PDFs are not supported. Upload an unlocked copy.')
    if not 1 <= doc.page_count <= MAX_PAGES:
        doc.close()
        raise DocumentInputError(f'PDF must contain between 1 and {MAX_PAGES} pages.')
    return doc


def decode_image(data):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.format not in ('JPEG', 'PNG'):
                    raise DocumentInputError('Use a JPG, PNG or PDF document.')
                if source.width * source.height > MAX_PIXELS:
                    raise DocumentInputError('Image exceeds the 20 megapixel limit. Resize it before uploading.')
                corrected = ImageOps.exif_transpose(source).convert('RGBA')
                paper = Image.new('RGBA', corrected.size, 'white')
                paper.alpha_composite(corrected)
                return paper.convert('RGB')
    except DocumentInputError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise DocumentInputError('This image could not be decoded. Try another JPG or PNG.') from exc


def document_info(data, filename):
    validate_bytes(data)
    if data.lstrip().startswith(b'%PDF') or Path(filename).suffix.lower() == '.pdf':
        with open_pdf(data) as doc:
            return dict(kind='pdf', pages=doc.page_count)
    image = decode_image(data)
    return dict(kind='image', pages=1, width=image.width, height=image.height)


def document_page(data, filename, page_index=0):
    info = document_info(data, filename)
    if not 0 <= page_index < info['pages']:
        raise DocumentInputError('Selected page is outside this document.')
    if info['kind'] == 'image':
        return decode_image(data)
    try:
        with open_pdf(data) as doc:
            page = doc.load_page(page_index)
            longest = max(page.rect.width, page.rect.height)
            if longest <= 0 or not np.isfinite(longest):
                raise DocumentInputError('PDF page has invalid dimensions.')
            scale = min(2.0, 1600 / longest)
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), colorspace=pymupdf.csRGB, alpha=False)
            return Image.frombytes('RGB', (pixmap.width, pixmap.height), pixmap.samples)
    except DocumentInputError:
        raise
    except Exception as exc:
        raise DocumentInputError('This PDF page could not be rendered. Try exporting it as a PNG.') from exc


def available_models(root=ROOT):
    preferred = ['transformer_finetuned_local', 'cnn_local_preliminary']
    paths = list((root/'runs').glob('*'))
    paths.sort(key=lambda p: (preferred.index(p.name) if p.name in preferred else 99, p.name))
    found = []
    for path in paths:
        if not all((path/name).is_file() for name in ('best.pt', 'config.json', 'validation.json')):
            continue
        try:
            config = json.loads((path/'config.json').read_text())
            if config.get('freeze_encoder'):
                continue
            kind = config.get('model', 'cnn')
            if kind not in ('cnn', 'transformer'):
                continue
            title = 'MiT-B0 Transformer' if kind == 'transformer' else 'CNN U-Net'
            found.append(dict(path=str(path.resolve()), title=title, run=path.name, config=config,
                              fingerprint=f"{(path/'best.pt').stat().st_mtime_ns}:{(path/'validation.json').stat().st_mtime_ns}"))
        except (ValueError, OSError):
            continue
    return found


def load_trained_model(run):
    from docguard.baseline import SmallUNet
    path = Path(run)
    torch.set_num_threads(4)
    checkpoint = torch.load(path/'best.pt', map_location='cpu', weights_only=True)
    if checkpoint.get('model', 'cnn') == 'transformer':
        from docguard.transformer import from_checkpoint
        model = from_checkpoint(checkpoint)
    else:
        model = SmallUNet(checkpoint['channels'])
    model.load_state_dict(checkpoint['state_dict'])
    model.eval()
    validation = json.loads((path/'validation.json').read_text())
    threshold = float(validation['threshold'])
    if not 0 < threshold < 1:
        raise ValueError('Saved model threshold must lie between zero and one.')
    return dict(model=model, threshold=threshold, width=checkpoint['width'], height=checkpoint['height'],
                kind=checkpoint.get('model', 'cnn'), epoch=checkpoint['epoch'],
                checkpoint_sha256=hashlib.sha256((path/'best.pt').read_bytes()).hexdigest())


@torch.inference_mode()
def predict(bundle, image):
    started = time.perf_counter()
    resized = image.resize((bundle['width'], bundle['height']), Image.Resampling.BILINEAR)
    array = np.asarray(resized, dtype=np.float32)/255
    tensor = torch.from_numpy(array.transpose(2, 0, 1).copy()).unsqueeze(0)
    probability = bundle['model'](tensor).sigmoid()[0, 0].cpu().numpy()
    if probability.shape != (bundle['height'], bundle['width']) or not np.isfinite(probability).all():
        raise RuntimeError('The model returned an invalid prediction.')
    return dict(probability=probability, highlighted_fraction=float((probability >= bundle['threshold']).mean()),
                elapsed_ms=(time.perf_counter()-started)*1000)


def display_images(image, probability, threshold, opacity=.55):
    if not 0 <= opacity <= 1:
        raise ValueError('Opacity must be in [0,1]')
    mask = Image.fromarray(((probability >= threshold)*255).astype(np.uint8)).resize(image.size, Image.Resampling.NEAREST)
    original = np.array(image.convert('RGB'))
    selected = np.array(mask) > 0
    overlay = original.copy()
    overlay[selected] = ((1-opacity)*original[selected]+opacity*np.array([192, 60, 48])).astype(np.uint8)
    confidence = Image.fromarray(probability.astype(np.float32)).resize(image.size, Image.Resampling.BILINEAR)
    intensity = np.asarray(confidence).clip(0, 1)[..., None]
    heat = ((1-.75*intensity)*original + .75*intensity*np.array([192, 60, 48])).clip(0, 255).astype(np.uint8)
    return dict(overlay=Image.fromarray(overlay), heatmap=Image.fromarray(heat), mask=mask)


def png_bytes(image):
    output = io.BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()


def review_metadata(bundle, prediction, image, source_name, source_bytes, page_index):
    return dict(document=Path(source_name).name, source_sha256=hashlib.sha256(source_bytes).hexdigest(),
                page=page_index+1, rendered_size=[image.width, image.height],
                model='MiT-B0 Transformer' if bundle['kind']=='transformer' else 'CNN U-Net',
                checkpoint_sha256=bundle['checkpoint_sha256'], epoch=bundle['epoch'],
                input_size=[bundle['width'], bundle['height']], threshold=bundle['threshold'],
                highlighted_fraction=prediction['highlighted_fraction'],
                highlighted_fraction_definition='Fraction of model-grid pixels above saved validation-selected threshold',
                inference_pipeline_ms=prediction['elapsed_ms'],
                created_utc=datetime.now(timezone.utc).isoformat(), limitation=LIMITATION)


def report_pdf(metadata, overlay):
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase.pdfmetrics import stringWidth
    output = io.BytesIO()
    page = canvas.Canvas(output, pagesize=A4)
    page.setTitle('DocGuard document review')
    width, height = A4
    page.setFillColorRGB(.14, .17, .15)
    page.setFont('Helvetica-Bold', 24)
    page.drawString(36, height-48, 'DocGuard')
    page.setFont('Helvetica', 10)
    page.drawString(36, height-68, 'DOCUMENT REVIEW / RESEARCH PROTOTYPE')
    filename = metadata['document'].encode('ascii', 'replace').decode()
    filename = ''.join(c if ord(c) >= 32 else ' ' for c in filename)
    suffix = f" / Page {metadata['page']}"
    while stringWidth('Document: '+filename+suffix, 'Helvetica', 9) > width-72:
        filename = filename[:-4]+'...' if len(filename)>4 else ''
    details = [f"Document: {filename}{suffix}",
               f"Model: {metadata['model']} / Epoch {metadata['epoch']} / Threshold {metadata['threshold']:.2f}",
               f"Highlighted area: {metadata['highlighted_fraction']*100:.2f}% of model grid / Language: {metadata.get('document_language', 'Unspecified')}",
               f"Source SHA-256: {metadata['source_sha256'][:32]}...", 'Red overlay indicates model-selected pixels; it is not proof of tampering.']
    page.setFont('Helvetica', 9)
    for i, text in enumerate(details):
        page.drawString(36, height-94-i*15, text)
    page.setStrokeColorRGB(.82, .83, .80)
    page.line(36, height-172, width-36, height-172)
    # Fit the reviewed page into a fixed area with generous margins.
    area = (width-72, height-280)
    ratio = min(area[0]/overlay.width, area[1]/overlay.height)
    draw_width, draw_height = overlay.width*ratio, overlay.height*ratio
    page.drawImage(ImageReader(overlay), (width-draw_width)/2, 92+(area[1]-draw_height)/2,
                   width=draw_width, height=draw_height)
    page.setFont('Helvetica', 8)
    page.drawString(36, 62, 'Trained on synthetic documents. Current models have high false-positive rates.')
    page.drawString(36, 49, 'Manual review is required. This report does not certify authenticity or fraud.')
    page.drawString(36, 36, f"Generated (UTC): {metadata['created_utc'][:19]} / Full metadata is available in the review ZIP.")
    page.showPage()
    page.save()
    return output.getvalue()


def export_review(metadata, rendered, pdf):
    output = io.BytesIO()
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
        archive.writestr('review.json', json.dumps(metadata, indent=2, ensure_ascii=False))
        archive.writestr('overlay.png', png_bytes(rendered['overlay']))
        archive.writestr('heatmap.png', png_bytes(rendered['heatmap']))
        archive.writestr('mask.png', png_bytes(rendered['mask']))
        archive.writestr('review.pdf', pdf)
    return output.getvalue()

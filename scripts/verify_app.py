"""Real browser verification against a locally running Streamlit server."""
import json
from pathlib import Path
import pymupdf
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
output = ROOT/'deliverables/app_preview'
output.mkdir(parents=True, exist_ok=True)
fixtures = ROOT/'tmp/pdfs'
fixtures.mkdir(parents=True, exist_ok=True)
with pymupdf.open() as fixture:
    fixture.new_page().insert_text((50, 60), 'DOCGUARD BROWSER TEST / PAGE ONE')
    fixture.new_page().insert_text((50, 60), 'DOCGUARD BROWSER TEST / PAGE TWO')
    fixture.save(fixtures/'two_pages.pdf')

checks, errors = [], []
with sync_playwright() as p:
    try:
        browser = p.chromium.launch(headless=True)
    except Exception:
        browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width':1440, 'height':1050}, device_scale_factor=1)
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:8501', wait_until='domcontentloaded')
    expect(page.get_by_role('button', name='Analyse page', exact=True)).to_be_visible(timeout=60000)
    page.screenshot(path=str(output/'01_workspace.png'), full_page=True)
    page.get_by_role('button', name='Analyse page', exact=True).click()
    expect(page.get_by_role('button', name='Download PDF report', exact=True)).to_be_visible(timeout=90000)
    expect(page.get_by_text('Manual review required', exact=True)).to_be_visible()
    checks.append('Default trained Transformer inference completed')
    page.screenshot(path=str(output/'02_transformer_result.png'), full_page=True)
    with page.expect_download() as downloaded:
        page.get_by_role('button', name='Download PDF report', exact=True).click()
    downloaded.value.save_as(str(output/'downloaded_review.pdf'))
    with pymupdf.open(output/'downloaded_review.pdf') as document:
        assert 'DocGuard' in document[0].get_text()
    with page.expect_download() as downloaded:
        page.get_by_role('button', name='Download review ZIP', exact=True).click()
    downloaded.value.save_as(str(output/'downloaded_review.zip'))
    checks.append('Browser PDF and ZIP downloads completed')
    page.get_by_text('Side by side', exact=True).click()
    expect(page.get_by_text('Model-selected regions', exact=True)).to_be_visible()
    checks.append('Side-by-side view rendered')
    # Model changes must invalidate a previous result, not display stale overlays.
    page.get_by_role('combobox', name='Review model').click()
    page.get_by_role('option', name='CNN U-Net', exact=True).click()
    expect(page.get_by_text('Ready for review', exact=True)).to_be_visible()
    page.get_by_role('button', name='Analyse page', exact=True).click()
    expect(page.get_by_role('button', name='Download PDF report', exact=True)).to_be_visible(timeout=60000)
    checks.append('Model change cleared prior result; CNN inference completed')
    page.get_by_text('Upload document', exact=True).click()
    page.locator('input[type=file]').set_input_files(str(ROOT/'data/synthetic_v2/images/00511_tampered.png'))
    expect(page.get_by_text('Ready for review', exact=True)).to_be_visible()
    page.get_by_role('button', name='Analyse page', exact=True).click()
    expect(page.get_by_role('button', name='Download PDF report', exact=True)).to_be_visible(timeout=60000)
    checks.append('Real PNG upload and inference completed')
    page.locator('input[type=file]').set_input_files(str(fixtures/'two_pages.pdf'))
    expect(page.get_by_text('Ready for review', exact=True)).to_be_visible()
    page.get_by_role('combobox', name='Page', exact=True).click()
    page.get_by_role('option', name='2 of 2', exact=True).click()
    page.get_by_role('button', name='Analyse page', exact=True).click()
    expect(page.get_by_role('button', name='Download PDF report', exact=True)).to_be_visible(timeout=60000)
    page.screenshot(path=str(output/'03_pdf_page_two.png'), full_page=True)
    checks.append('Two-page PDF upload, page selection and inference completed')
    page.get_by_role('combobox', name='Page', exact=True).click()
    page.get_by_role('option', name='1 of 2', exact=True).click()
    expect(page.get_by_text('Ready for review', exact=True)).to_be_visible()
    checks.append('Page change cleared prior result')
    # A malformed file should produce a helpful error rather than a stack trace.
    page.locator('input[type=file]').set_input_files({'name':'broken.pdf', 'mimeType':'application/pdf', 'buffer':b'not a PDF'})
    expect(page.get_by_text('This PDF could not be opened. Try an unencrypted PDF.', exact=True)).to_be_visible()
    checks.append('Invalid PDF handled without a stack trace')
    page.get_by_text('Example document', exact=True).click()
    expect(page.get_by_role('button', name='Analyse page', exact=True)).to_be_visible()
    page.get_by_role('combobox', name='Example', exact=True).click()
    page.get_by_role('option', name='Hindi receipt · original', exact=True).click()
    expect(page.get_by_text('hindi_original.png', exact=True)).to_be_visible()
    expect(page.get_by_text('Ready for review', exact=True)).to_be_visible()
    page.get_by_role('button', name='Analyse page', exact=True).click()
    expect(page.get_by_role('button', name='Download PDF report', exact=True)).to_be_visible(timeout=60000)
    expect(page.get_by_role('button', name='Download Hindi example PDF', exact=True)).to_be_visible()
    page.screenshot(path=str(output/'05_hindi_review.png'), full_page=True)
    with page.expect_download() as downloaded:
        page.get_by_role('button', name='Download review ZIP', exact=True).click()
    downloaded.value.save_as(str(output/'hindi_review.zip'))
    from zipfile import ZipFile
    with ZipFile(output/'hindi_review.zip') as archive:
        metadata = json.loads(archive.read('review.json'))
        assert metadata['document_language']=='Hindi'
        with pymupdf.open(stream=archive.read('review.pdf'), filetype='pdf') as review:
            assert 'Language: Hindi' in review[0].get_text()
    checks.append('Hindi example rendered and inferred; Hindi language recorded in exported review')
    page.get_by_text('Upload document', exact=True).click()
    page.locator('input[type=file]').set_input_files(str(ROOT/'assets/examples/hindi_original.pdf'))
    page.get_by_role('button', name='Analyse page', exact=True).click()
    expect(page.get_by_role('button', name='Download PDF report', exact=True)).to_be_visible(timeout=60000)
    checks.append('Real Hindi PDF upload and inference completed')
    page.get_by_text('Example document', exact=True).click()
    for language in ['Marathi', 'Tamil', 'Bengali']:
        page.get_by_role('combobox', name='Example', exact=True).click()
        page.get_by_role('option', name=f'{language} receipt · original', exact=True).click()
        page.get_by_role('button', name='Analyse page', exact=True).click()
        expect(page.get_by_role('button', name='Download PDF report', exact=True)).to_be_visible(timeout=60000)
        checks.append(f'{language} example rendered and inference completed')
    mobile = browser.new_page(viewport={'width':390, 'height':844}, device_scale_factor=1)
    mobile.goto('http://127.0.0.1:8501', wait_until='domcontentloaded')
    expect(mobile.get_by_role('button', name='Analyse page', exact=True)).to_be_visible(timeout=60000)
    mobile.get_by_role('button', name='Analyse page', exact=True).click()
    expect(mobile.get_by_role('button', name='Download PDF report', exact=True)).to_be_visible(timeout=60000)
    mobile.screenshot(path=str(output/'04_mobile.png'), full_page=True)
    assert mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth+2'), 'Horizontal overflow on mobile'
    expect(mobile.get_by_text('Document review', exact=True)).to_be_visible()
    checks.append('390px mobile inference completed with no horizontal overflow')
    assert not errors, errors
    assert page.locator('[data-testid="stException"]').count()==0
    browser.close()
(output/'browser_checks.json').write_text(json.dumps(dict(checks=checks, browser_errors=errors), indent=2), encoding='utf-8')
print(json.dumps(dict(checks=checks, browser_errors=errors), indent=2))

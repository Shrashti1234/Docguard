"""Verify language switching preserves the reviewed document and predictions."""
import json
from pathlib import Path
from zipfile import ZipFile
from playwright.sync_api import sync_playwright, expect
from docguard.i18n import LANGUAGES, translate

root = Path(__file__).resolve().parents[1]
output = root/'deliverables/app_preview'
output.mkdir(parents=True, exist_ok=True)
checks = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width':1440, 'height':1100})
    errors = []
    page.on('pageerror', lambda error:errors.append(str(error)))
    page.goto('http://127.0.0.1:8501', wait_until='domcontentloaded')
    expect(page.get_by_role('combobox', name='Example', exact=True)).to_be_visible(timeout=60000)
    page.get_by_role('combobox', name='Example', exact=True).click()
    page.get_by_role('option', name='Hindi receipt · original', exact=True).click()
    page.get_by_role('button', name='Analyse page', exact=True).click()
    expect(page.get_by_role('button', name='Download review ZIP', exact=True)).to_be_visible(timeout=90000)
    page.get_by_text('Side by side', exact=True).click()
    expect(page.get_by_text('Model-selected regions', exact=True)).to_be_visible()
    source_hash = None
    prediction_signature = None
    for code in ['hi', 'mr', 'ta', 'bn', 'en']:
        page.get_by_role('combobox', name='Interface language / भाषा', exact=True).click()
        page.get_by_role('option', name=LANGUAGES[code], exact=True).click()
        expect(page.get_by_role('button', name=translate('Analyse page',code), exact=True)).to_be_visible()
        expect(page.get_by_text(translate('Document review',code), exact=True)).to_be_visible()
        expect(page.get_by_role('radio', name=translate('Side by side',code), exact=True)).to_be_checked()
        expect(page.get_by_role('button', name=translate('Download review ZIP',code), exact=True)).to_be_visible()
        with page.expect_download() as download:
            page.get_by_role('button', name=translate('Download review ZIP',code), exact=True).click()
        file = output/f'ui_{code}_review.zip'
        download.value.save_as(str(file))
        with ZipFile(file) as archive:
            metadata = json.loads(archive.read('review.json'))
        assert metadata['document_language']=='Hindi'
        assert metadata['interface_language']==code
        if source_hash is None:
            source_hash = metadata['source_sha256']
        assert source_hash == metadata['source_sha256']
        signature = (metadata['checkpoint_sha256'],metadata['threshold'],metadata['highlighted_fraction'])
        if prediction_signature is None:
            prediction_signature = signature
        assert signature == prediction_signature
        checks.append(f'{code}: localized controls and existing result/view/document language preserved; export metadata verified')
        if code=='hi':
            page.screenshot(path=str(output/'06_hindi_interface.png'), full_page=True)
    page.get_by_text('Upload document', exact=True).click()
    page.locator('input[type=file]').set_input_files(str(root/'assets/examples/hindi_original.pdf'))
    expect(page.get_by_text('Ready for review', exact=True)).to_be_visible()
    page.get_by_role('button', name='Analyse page', exact=True).click()
    expect(page.get_by_role('button', name='Download review ZIP', exact=True)).to_be_visible(timeout=60000)
    page.get_by_role('combobox', name='Interface language / भाषा', exact=True).click()
    page.get_by_role('option', name=LANGUAGES['hi'], exact=True).click()
    expect(page.get_by_role('button', name=translate('Download review ZIP','hi'), exact=True)).to_be_visible()
    expect(page.get_by_text('hindi_original.pdf', exact=True).first).to_be_visible()
    checks.append('Uploaded Hindi PDF and computed result preserved after interface-language switch')
    page.get_by_role('combobox', name='Interface language / भाषा', exact=True).click()
    page.get_by_role('option', name=LANGUAGES['ta'], exact=True).click()
    page.set_viewport_size({'width':390, 'height':844})
    # Collapse the existing desktop sidebar before checking the narrow workspace.
    sidebar = page.locator('[data-testid="stSidebar"]')
    collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
    if collapse.count() and collapse.is_visible():
        collapse.click()
    expect(page.get_by_role('button', name=translate('Analyse page','ta'), exact=True)).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+2'), 'Tamil mobile overflow'
    page.screenshot(path=str(output/'07_tamil_interface_mobile.png'), full_page=True)
    checks.append('Tamil mobile controls visible without horizontal overflow')
    assert not errors, errors
    assert page.locator('[data-testid="stException"]').count()==0
    browser.close()
(output/'language_checks.json').write_text(json.dumps({'checks':checks,'browser_errors':errors},indent=2),encoding='utf-8')
print(json.dumps({'checks':checks,'browser_errors':errors},indent=2))

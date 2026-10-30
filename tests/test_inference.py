import io
import importlib.util
import json
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import numpy as np
from PIL import Image
if not importlib.util.find_spec('pymupdf') or not importlib.util.find_spec('reportlab'):
    raise unittest.SkipTest('Optional app/PDF dependencies not installed')
import pymupdf

from docguard.inference import (DocumentInputError, document_info, document_page,
    display_images, png_bytes, report_pdf, export_review, MAX_PAGES, MAX_BYTES, available_models)


class InferenceChecks(unittest.TestCase):
    def test_image_alpha_composite_and_invalid_uploads(self):
        data = png_bytes(Image.new('RGBA', (30, 40), (255, 0, 0, 0)))
        self.assertEqual(document_info(data, 'alpha.png')['pages'], 1)
        decoded = document_page(data, 'alpha.png')
        self.assertEqual(decoded.getpixel((0, 0)), (255, 255, 255))
        for data, name in [(b'', 'empty.png'), (b'broken', 'bad.pdf'), (b'broken', 'bad.png')]:
            with self.assertRaises(DocumentInputError):
                document_info(data, name)
        with self.assertRaises(DocumentInputError):
            document_page(png_bytes(decoded), 'image.png', 1)

    def test_pdf_selection_and_page_limit(self):
        with pymupdf.open() as pdf:
            pdf.new_page().insert_text((40, 40), 'FIRST PAGE')
            pdf.new_page().insert_text((40, 40), 'SECOND PAGE')
            data = pdf.tobytes()
        self.assertEqual(document_info(data, 'two.pdf')['pages'], 2)
        first = document_page(data, 'two.pdf', 0)
        second = document_page(data, 'two.pdf', 1)
        self.assertNotEqual(first.tobytes(), second.tobytes())
        self.assertLessEqual(max(first.size), 1600)
        with pymupdf.open() as pdf:
            for _ in range(MAX_PAGES+1):
                pdf.new_page()
            oversized = pdf.tobytes()
        with self.assertRaises(DocumentInputError):
            document_info(oversized, 'too_many.pdf')

    def test_password_size_limits_and_missing_models(self):
        import tempfile
        from pathlib import Path
        with pymupdf.open() as pdf:
            pdf.new_page()
            encrypted = pdf.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw='owner', user_pw='secret')
        with self.assertRaisesRegex(DocumentInputError, 'Password-protected'):
            document_info(encrypted, 'locked.pdf')
        with self.assertRaisesRegex(DocumentInputError, '20 MB'):
            document_info(b'x'*(MAX_BYTES+1), 'large.png')
        with patch('docguard.inference.MAX_SOURCE_PIXELS', 3):
            with self.assertRaisesRegex(DocumentInputError, 'megapixel'):
                document_info(png_bytes(Image.new('RGB', (4, 4))), 'large_pixels.png')
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(available_models(Path(root)), [])

    def test_phone_image_resize_and_additional_formats(self):
        for fmt in ('WEBP', 'BMP', 'TIFF'):
            buffer = io.BytesIO()
            Image.new('RGB', (100, 80), 'white').save(buffer, format=fmt)
            with patch('docguard.inference.MAX_PIXELS', 2000):
                image = document_page(buffer.getvalue(), 'phone.'+fmt.lower())
            self.assertLessEqual(image.width*image.height, 2000)
            self.assertEqual(image.mode, 'RGB')

    def test_overlay_and_export_contents(self):
        image = Image.new('RGB', (80, 100), 'white')
        probability = np.zeros((10, 8), dtype=np.float32)
        probability[4:6, 3:5] = .9
        rendered = display_images(image, probability, .8)
        self.assertEqual(rendered['overlay'].getpixel((0, 0)), (255, 255, 255))
        self.assertNotEqual(rendered['overlay'].getpixel((35, 45)), (255, 255, 255))
        self.assertEqual(set(np.asarray(rendered['mask']).ravel()), {0, 255})
        metadata = dict(document='sample.png', document_language='Hindi', page=1, model='CNN U-Net', epoch=3, threshold=.8,
                        highlighted_fraction=.05, source_sha256='a'*64, created_utc='2026-10-26T10:00:00+00:00')
        pdf = report_pdf(metadata, rendered['overlay'])
        with pymupdf.open(stream=pdf, filetype='pdf') as document:
            self.assertEqual(document.page_count, 1)
            text = document[0].get_text()
            self.assertIn('DocGuard', text)
            self.assertIn('Manual review is required', text)
            self.assertIn('Language: Hindi', text)
        long_name = dict(metadata, document='W'*300+'.png')
        with pymupdf.open(stream=report_pdf(long_name, rendered['overlay']), filetype='pdf') as document:
            for block in document[0].get_text('dict')['blocks']:
                for line in block.get('lines', []):
                    for span in line['spans']:
                        self.assertLessEqual(span['bbox'][2], document[0].rect.width-30)
        exported = export_review(metadata, rendered, pdf)
        with ZipFile(io.BytesIO(exported)) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {'review.json', 'overlay.png', 'heatmap.png', 'mask.png', 'review.pdf'})
            self.assertEqual(json.loads(archive.read('review.json'))['page'], 1)


if __name__ == '__main__':
    unittest.main()

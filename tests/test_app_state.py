import importlib.util
from pathlib import Path
import unittest

if not all(importlib.util.find_spec(name) for name in ('streamlit','pymupdf','reportlab')):
    raise unittest.SkipTest('Optional application dependencies not installed')

from streamlit.testing.v1 import AppTest


class AppStateChecks(unittest.TestCase):
    def test_language_switch_keeps_document_and_view(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=40)
        next(w for w in app.selectbox if w.label=='Example').select('Hindi receipt · original').run(timeout=40)
        self.assertEqual(next(w for w in app.selectbox if w.label=='Document language').value,'Hindi')
        next(w for w in app.radio if w.label=='Document view').set_value('Side by side').run(timeout=40)
        next(w for w in app.selectbox if w.label=='Interface language / भाषा').select('hi').run(timeout=40)
        self.assertEqual(next(w for w in app.selectbox if w.label=='दस्तावेज़ की भाषा').value,'Hindi')
        self.assertEqual(next(w for w in app.radio if w.label=='दस्तावेज़ का दृश्य').value,'Side by side')
        self.assertFalse(app.exception)

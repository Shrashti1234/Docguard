import string
import unittest
from docguard.i18n import CATALOG, LANGUAGES, ROWS, translate


class TranslationChecks(unittest.TestCase):
    def test_complete_catalog_and_matching_placeholders(self):
        self.assertEqual(len({row[0] for row in ROWS}), len(ROWS))
        formatter = string.Formatter()
        for language in LANGUAGES:
            self.assertEqual(set(CATALOG[language]), set(CATALOG['en']))
            for key, value in CATALOG[language].items():
                self.assertTrue(value.strip())
                original = {name for _, name, _, _ in formatter.parse(key) if name is not None}
                translated = {name for _, name, _, _ in formatter.parse(value) if name is not None}
                self.assertEqual(original, translated, (language, key))

    def test_localized_action_and_dynamic_values(self):
        self.assertEqual(translate('Analyse page', 'hi'), 'पृष्ठ का विश्लेषण करें')
        for language in LANGUAGES:
            value = translate('{current} of {total}', language, current=2, total=5)
            self.assertIn('2', value)
            self.assertIn('5', value)
        self.assertEqual(translate('Analyse page', 'unknown'), 'Analyse page')
        self.assertIn('Hindi', translate('Download {language} example PDF', 'hi', language='Hindi'))

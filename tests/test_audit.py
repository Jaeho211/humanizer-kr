import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills' / 'humanizer-kr' / 'scripts' / 'audit.py'
spec = importlib.util.spec_from_file_location('korean_audit', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestAudit(unittest.TestCase):
    def test_identical_text_passes(self):
        text = '`--max-num-seqs 32` 사용, 15% 성능. https://example.com/a?id=32\n'
        self.assertTrue(mod.audit(text, text)['passed_literal_checks'])

    def test_changed_number_fails(self):
        report = mod.audit('약 15% 높아질 수 있다.', '약 20% 높아질 수 있다.')
        self.assertFalse(report['passed_literal_checks'])
        self.assertTrue(any(v['type'] == 'numbers' for v in report['violations']))

    def test_code_change_fails(self):
        a = '```bash\necho 1\n```\n본문'
        b = '```bash\necho 2\n```\n본문'
        self.assertFalse(mod.audit(a, b)['passed_literal_checks'])

    def test_inline_code_change_fails(self):
        self.assertFalse(mod.audit('`xodr` 검사', '`xml` 검사')['passed_literal_checks'])

    def test_url_change_fails(self):
        self.assertFalse(mod.audit('https://example.com/a', 'https://example.com/b')['passed_literal_checks'])

    def test_templates_change_fails(self):
        self.assertFalse(mod.audit('안녕 {{name}}', '안녕 {{nickname}}')['passed_literal_checks'])

    def test_changed_numeric_unit_fails(self):
        self.assertFalse(mod.audit('3개가 있습니다.', '3명이 있습니다.')['passed_literal_checks'])

    def test_changed_date_fails(self):
        self.assertFalse(mod.audit('2026-10-29', '2026-10-30')['passed_literal_checks'])

    def test_reorder_numeric_tokens_passes(self):
        self.assertTrue(mod.audit('3개가 있고 15%이다.', '15%이고 3개이다.')['passed_literal_checks'])

    def test_style_signal_not_hard_failure(self):
        report = mod.audit('결론적으로, 이는 시사하는 바가 크다')
        self.assertTrue(report['passed_literal_checks'])
        self.assertGreaterEqual(report['style_signals_before']['empty-conclusion'], 1)

    def test_code_is_not_style_scanned(self):
        report = mod.audit('```txt\n획기적인 새로운 패러다임\n```')
        self.assertEqual(report['style_signals_before']['inflated-language'], 0)

    def test_empty_and_korean_only(self):
        self.assertTrue(mod.audit('', '')['passed_literal_checks'])
        self.assertTrue(mod.audit('안녕하세요', '반갑습니다')['passed_literal_checks'])

if __name__ == '__main__':
    unittest.main()

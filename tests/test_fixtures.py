import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "skills" / "humanizer-kr" / "examples" / "fixtures.jsonl"


class TestConciseFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [json.loads(line) for line in FIXTURES.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_fixture_ids_unique_and_complete(self):
        ids = [row["id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        for row in self.rows:
            self.assertTrue(row["input"].strip())
            self.assertTrue(row["example"].strip())
            self.assertTrue(row["checks"])

    def test_repetitive_examples_are_shorter(self):
        for row in self.rows:
            if row["id"] in ("semantic-duplicate", "intro-recapping", "padded-answer"):
                self.assertLess(len(row["example"]), len(row["input"]))

    def test_document_editing_defaults_to_shorter_when_safe(self):
        docs = [r for r in self.rows if r.get("intent") == "default-document-shorter"]
        self.assertGreaterEqual(len(docs), 4)
        for row in docs:
            self.assertLessEqual(len(row["example"]), len(row["input"]))
            self.assertTrue(row["checks"])
        self.assertTrue(any(len(r["example"]) < len(r["input"]) for r in docs))
        self.assertTrue(any(r["example"] == r["input"] for r in docs))

    def test_document_technical_terms_are_preserved(self):
        for row in self.rows:
            if row.get("intent") != "default-document-shorter":
                continue
            for term in ["lane", "junction", "JSON", "CARLA 0.10.0", "road 43", "junction 100063"]:
                if term in row["input"]:
                    self.assertIn(term, row["example"])

    def test_distinct_conditions_are_preserved(self):
        row = next(r for r in self.rows if r["id"] == "preserve-distinct-conditions")
        for term in ("역방향", "junction 100063"):
            self.assertIn(term, row["example"])


if __name__ == "__main__":
    unittest.main()

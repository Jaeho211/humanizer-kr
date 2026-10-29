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

    def test_distinct_conditions_are_preserved(self):
        row = next(r for r in self.rows if r["id"] == "preserve-distinct-conditions")
        for term in ("역방향", "junction 100063"):
            self.assertIn(term, row["example"])


if __name__ == "__main__":
    unittest.main()

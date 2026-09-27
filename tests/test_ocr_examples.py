import unittest
import json
import tempfile
from pathlib import Path

from scripts.make_ocr_examples import color_diff
from ocr_lab.rescore import rescore_file


class OCRExampleDiffTest(unittest.TestCase):
    def test_correct_text_has_no_error_background(self):
        rendered = color_diff("Příliš 42", "Příliš 42")
        self.assertNotIn("background-color", rendered)
        self.assertIn("Příliš 42", rendered)

    def test_case_only_difference_is_not_marked(self):
        rendered = color_diff("TOTAL Paid", "total paid")
        self.assertNotIn("background-color", rendered)

    def test_punctuation_and_latin_diacritics_are_not_marked(self):
        rendered = color_diff("Příliš, čárka!", "prilis carka")
        self.assertNotIn("background-color", rendered)

    def test_rescore_ignores_case_and_retains_strict_score(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.jsonl"
            output = Path(directory) / "output.jsonl"
            source.write_text(json.dumps({
                "ground_truth_text": "TOTAL Paid",
                "predicted_text": "total paid",
                "latency_seconds": 0.1,
            }) + "\n", encoding="utf-8")
            summary = rescore_file(source, output, "ascii-fold")
        self.assertEqual(summary["cer"], 0.0)
        self.assertEqual(summary["wer"], 0.0)
        self.assertGreater(summary["case_sensitive"]["cer"], 0.0)

    def test_ascii_fold_ignores_punctuation_and_diacritics(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.jsonl"
            output = Path(directory) / "output.jsonl"
            source.write_text(json.dumps({
                "ground_truth_text": "Příliš, čárka!",
                "predicted_text": "prilis carka",
            }) + "\n", encoding="utf-8")
            summary = rescore_file(source, output, "ascii-fold")
        self.assertEqual(summary["cer"], 0.0)
        self.assertEqual(summary["wer"], 0.0)

    def test_substitution_and_insertion_are_marked_red(self):
        rendered = color_diff("cat", "cutx")
        self.assertIn("<span", rendered)
        self.assertIn(">u</span>", rendered)
        self.assertIn(">x</span>", rendered)

    def test_deletion_is_marked_with_missing_character_marker(self):
        rendered = color_diff("cats", "cat")
        self.assertIn("∅", rendered)
        self.assertIn("missing reference character: s", rendered)

    def test_html_is_escaped(self):
        rendered = color_diff("a", "<")
        self.assertIn("&lt;", rendered)
        self.assertNotIn("<span style=\"background-color:#ffb3b3;color:#7f0000;padding:0 1px;border-radius:2px\"><</span>", rendered)


if __name__ == "__main__":
    unittest.main()

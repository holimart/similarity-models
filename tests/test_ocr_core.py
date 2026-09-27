import unittest

from ocr_lab.core import OCRConfig, normalized_result
from ocr_lab.evaluate import edit_distance, normalize


class OCRHarnessUtilitiesTest(unittest.TestCase):
    def test_normalizes_aligned_outputs_and_keeps_unicode(self):
        records = normalized_result([[[1, 2], [3, 2], [3, 5], [1, 5]]], ["Příliš"], [0.91])
        self.assertEqual(records[0]["text"], "Příliš")
        self.assertEqual(records[0]["confidence"], 0.91)
        self.assertEqual(records[0]["polygon"][0], [1.0, 2.0])

    def test_empty_results(self):
        self.assertEqual(normalized_result(None, None, None), [])

    def test_config_defaults_and_json_constructor(self):
        config = OCRConfig()
        self.assertEqual(config.harness, "rapidocr")
        self.assertEqual(config.device, "cpu")

    def test_metrics_helpers(self):
        self.assertEqual(edit_distance("receipt", "reciept"), 2)
        self.assertEqual(normalize("  Částka\n celkem  "), "Částka celkem")


if __name__ == "__main__":
    unittest.main()

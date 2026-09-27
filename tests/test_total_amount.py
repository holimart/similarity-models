import unittest

from ocr_lab.amounts import amount_methods, fit_linear_ranker, normalize_amount, ranker_score


class TotalAmountTest(unittest.TestCase):
    def test_dataset_specific_numeric_normalization(self):
        self.assertEqual(normalize_amount("Rp 45,500", "cord"), "45500")
        self.assertEqual(normalize_amount("1,234.56", "sroie"), "123456")
        self.assertEqual(normalize_amount("15", "sroie"), "1500")

    def test_keyword_proximity_beats_cash_and_largest_amount(self):
        rows = [
            {"text": "SUBTOTAL", "polygon": [[10, 100], [80, 100], [80, 120], [10, 120]], "confidence": 0.99},
            {"text": "20.00", "polygon": [[250, 100], [300, 100], [300, 120], [250, 120]], "confidence": 0.99},
            {"text": "TOTAL", "polygon": [[10, 200], [60, 200], [60, 220], [10, 220]], "confidence": 0.99},
            {"text": "23.25", "polygon": [[250, 200], [300, 200], [300, 220], [250, 220]], "confidence": 0.99},
            {"text": "CASH", "polygon": [[10, 260], [60, 260], [60, 280], [10, 280]], "confidence": 0.99},
            {"text": "70.00", "polygon": [[250, 260], [300, 260], [300, 280], [250, 280]], "confidence": 0.99},
        ]
        candidates, methods, _features = amount_methods(rows, "sroie", 400)
        self.assertEqual(len(candidates), 3)
        self.assertEqual(methods["keyword_nearby"].normalized_value, "2325")
        self.assertEqual(methods["bottommost"].normalized_value, "7000")
        self.assertEqual(methods["largest_amount"].normalized_value, "7000")

    def test_trainable_ranker_learns_a_positive_feature(self):
        examples = [
            ([1.0, 0.0], 0, 0.5),
            ([1.0, 0.1], 0, 0.5),
            ([1.0, 0.9], 1, 0.5),
            ([1.0, 1.0], 1, 0.5),
        ]
        weights = fit_linear_ranker(examples)
        self.assertGreater(ranker_score(weights, [1.0, 0.9]), ranker_score(weights, [1.0, 0.1]))


if __name__ == "__main__":
    unittest.main()

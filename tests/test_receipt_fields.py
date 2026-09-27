import unittest

from ocr_lab.receipt_fields import extract_receipt_fields


def box(y, x=10, width=90):
    return [[x, y], [x + width, y], [x + width, y + 20], [x, y + 20]]


class ReceiptFieldsTest(unittest.TestCase):
    def test_naive_mode_extracts_total_currency_tax_tip_and_purpose(self):
        records = [
            {"text": "Kavárna U Mostu", "polygon": box(10), "confidence": 0.98},
            {"text": "DPH 21% 20,50 Kč", "polygon": box(180), "confidence": 0.94},
            {"text": "TOTAL 120,50 Kč", "polygon": box(220), "confidence": 0.99},
            {"text": "Spropitné 10 Kč", "polygon": box(250), "confidence": 0.90},
        ]
        fields = extract_receipt_fields(records, image_height=1000, dataset="cord", mode="naive")
        self.assertEqual(fields["total"]["amount_raw"], "120,50")
        self.assertEqual(fields["currency"]["code"], "CZK")
        self.assertEqual(fields["purpose"]["category"], "food_dining")
        self.assertEqual(fields["taxes"][0]["amount_raw"], "20,50")
        self.assertEqual(fields["taxes"][0]["rate_percent_raw"], "21")
        self.assertEqual(fields["tip"]["amount_raw"], "10")
        self.assertEqual(fields["line_items"]["status"], "not_extracted_yet")
        self.assertEqual(fields["line_items"]["items"], [])
        self.assertIn("assigned_person_id", fields["line_items"]["item_schema"])

    def test_tuned_mode_requires_a_learned_candidate_ranker(self):
        records = [{"text": "TOTAL 9.00", "polygon": box(300), "confidence": 0.99}]
        with self.assertRaises(ValueError):
            extract_receipt_fields(records, image_height=500, dataset="sroie", mode="tuned")


if __name__ == "__main__":
    unittest.main()

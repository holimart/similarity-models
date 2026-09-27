import unittest
import json
import tempfile
from pathlib import Path

from image_tagger.benchmark import average_precision, compute_metrics, load_coco


class TaggingMetricTests(unittest.TestCase):
    def test_average_precision_uses_ranked_scores(self):
        self.assertAlmostEqual(average_precision([1, 0, 1], [0.9, 0.8, 0.1]), (1 + 2 / 3) / 2)

    def test_average_precision_ignores_class_without_positive(self):
        self.assertIsNone(average_precision([0, 0], [0.8, 0.2]))

    def test_metrics_perfect_predictions(self):
        targets = [[1, 0], [0, 1]]
        scores = [[0.9, 0.1], [0.1, 0.9]]
        metrics = compute_metrics(targets, scores, threshold=0.5, top_k=1)
        self.assertEqual(metrics["macro_map"], 1.0)
        self.assertEqual(metrics["micro_f1_at_threshold"], 1.0)
        self.assertEqual(metrics["precision_at_1"], 1.0)

    def test_coco_loader_uses_non_crowd_image_level_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "images"
            images.mkdir()
            (images / "one.jpg").touch()
            annotations = root / "instances.json"
            annotations.write_text(json.dumps({
                "categories": [{"id": 4, "name": "cat"}, {"id": 8, "name": "dog"}],
                "images": [{"id": 1, "file_name": "one.jpg"}],
                "annotations": [
                    {"image_id": 1, "category_id": 4, "iscrowd": 0},
                    {"image_id": 1, "category_id": 8, "iscrowd": 1},
                ],
            }), encoding="utf-8")
            categories, rows = load_coco(annotations, images)
            self.assertEqual([item["name"] for item in categories], ["cat", "dog"])
            self.assertEqual(rows[0]["labels"], [1, 0])


if __name__ == "__main__":
    unittest.main()

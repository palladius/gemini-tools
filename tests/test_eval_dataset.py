import unittest
import shutil
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import eval_dataset



class TestEvalDataset(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("out/test_evals")
        eval_dataset.BASE_EVAL_DIR = self.test_dir
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_upsert_and_query_pending(self):
        rec = {
            "eval_id": "kate_p1_test",
            "subject": "Kate",
            "model_name": "gemini-2.5-flash-image",
            "prompt": "Test prompt",
            "reference_images": [{"name": "ref1.jpg", "local_path": "/tmp/ref1.jpg"}],
            "generated_image": {"annotated_path": "/tmp/gen1.png"},
            "robot_eval": {"score": 7, "verdict": "GOOD"},
            "human_eval": None,
            "status": "PENDING_HUMAN"
        }
        saved = eval_dataset.upsert_evaluation_record(rec)
        self.assertEqual(saved["eval_id"], "kate_p1_test")

        pending = eval_dataset.get_pending_evaluations("Kate")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["eval_id"], "kate_p1_test")

        # Record human vote
        voted = eval_dataset.record_human_vote("kate_p1_test", 9, "Awesome picture!")
        self.assertIsNotNone(voted)
        self.assertEqual(voted["human_eval"]["score"], 9)

        # Check pending is now empty
        pending_after = eval_dataset.get_pending_evaluations("Kate")
        self.assertEqual(len(pending_after), 0)

    def test_image_files_exist_in_evals(self):
        """Verify that all image paths in out/evals/ reference existing files on disk."""
        eval_base = Path("out/evals")
        if not eval_base.exists():
            return
        
        missing_files = []
        for d in eval_base.iterdir():
            if d.is_dir():
                jsonl = d / "evaluations.jsonl"
                if jsonl.exists():
                    with open(jsonl, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            rec = json.loads(line)
                            img_info = rec.get("generated_image", {})
                            for key in ["face_crop_path", "annotated_path", "raw_path"]:
                                path_str = img_info.get(key)
                                if path_str:
                                    p = Path(path_str)
                                    if not p.exists():
                                        missing_files.append(f"{rec.get('eval_id')}: {key} -> {path_str}")

        self.assertEqual(len(missing_files), 0, f"Found missing image files referenced in evals: {missing_files}")


if __name__ == "__main__":
    unittest.main()


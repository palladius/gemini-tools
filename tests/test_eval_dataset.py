import unittest
import shutil
import json
import sys
import importlib.util
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import eval_dataset

_spec = importlib.util.spec_from_file_location(
    "list_gemini_models",
    Path(__file__).resolve().parent.parent / "bin" / "list-gemini-models.py",
)
list_gemini_models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(list_gemini_models)



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

    def test_kate_bad_examples_registered(self):
        """Verify that bad examples of wrinkled/cloned photos are registered under kate/bad_examples/."""
        kate_dir = Path("data/characters/kate").resolve()
        bad_dir = kate_dir / "bad_examples"
        if not bad_dir.exists():
            return
        self.assertTrue(bad_dir.exists(), "data/characters/kate/bad_examples/ directory must exist")
        
        bad_files = list(bad_dir.glob("*.png")) + list(bad_dir.glob("*.jpg"))
        self.assertGreaterEqual(len(bad_files), 2, f"Expected at least 2 bad example images in {bad_dir}, found {len(bad_files)}")
        
        for p in bad_files:
            self.assertTrue(p.exists(), f"Bad example {p.name} must exist on disk")
            self.assertGreater(p.stat().st_size, 0, f"Bad example {p.name} must not be empty")

        # Verify active clean reference set in grid_cleaned/ does NOT include legacy harsh anchor
        clean_dir = kate_dir / "grid_cleaned"
        if clean_dir.exists():
            clean_names = [p.name for p in clean_dir.glob("*")]
            self.assertNotIn("kate_golden_wine_anchor.png", clean_names, "Legacy harsh anchor must not be in active grid_cleaned set")

    def test_judge_image_calibrated_prompt_and_crop_cli(self):
        """Verify bin/judge_image.py supports --crop-face and uses strict calibrated scoring rules."""
        judge_script = Path("bin/judge_image.py").resolve()
        self.assertTrue(judge_script.exists(), "bin/judge_image.py must exist")
        
        content = judge_script.read_text(encoding="utf-8")
        self.assertIn("--crop-face", content, "judge_image.py must expose --crop-face flag")
        self.assertIn("STRICT BIOMETRIC IDENTITY IS PARAMOUNT", content, "judge_image.py must contain strict biometric criteria")
        self.assertIn("CALIBRATION SCALE", content, "judge_image.py must contain calibrated rating scale")
        self.assertIn("non le somiglia per niente", content, "judge_image.py must penalize zero likeness correctly")

    def test_get_model_release_date(self):
        # 1. Known release map (e.g. gemini-4-argon)
        m_argon = SimpleNamespace(
            name="models/gemini-4-argon",
            version="3.0",
            display_name="Gemini 4 Argon",
            description="Gemini 4 Argon",
            tuned_model_info=None,
        )
        self.assertEqual(list_gemini_models.get_model_release_date(m_argon), "2026-10-13")

        # 2. ISO date in version string
        m_iso = SimpleNamespace(
            name="models/custom-exp",
            version="custom-exp-2026-08-19",
            display_name="Custom Exp",
            description="",
            tuned_model_info=None,
        )
        self.assertEqual(list_gemini_models.get_model_release_date(m_iso), "2026-08-19")

        # 3. MM-YYYY in version string
        m_my = SimpleNamespace(
            name="models/future-flash",
            version="future-flash-11-2026",
            display_name="Future Flash",
            description="",
            tuned_model_info=None,
        )
        self.assertEqual(list_gemini_models.get_model_release_date(m_my), "2026-11")

        # 4. Brand new unmapped model (e.g. gemini-4.1 tomorrow) -> UNKNOWN (*)
        m_unknown = SimpleNamespace(
            name="models/gemini-4.1",
            version="4.1",
            display_name="Gemini 4.1",
            description="Next generation Gemini model",
            tuned_model_info=None,
        )
        self.assertEqual(list_gemini_models.get_model_release_date(m_unknown), "UNKNOWN (*)")

        # 5. Rolling alias (-latest) -> "rolling" (never triggers false-positive UNKNOWN (*))
        m_latest = SimpleNamespace(
            name="models/gemini-flash-latest",
            version="gemini-flash-latest",
            display_name="Gemini Flash Latest",
            description="Latest release of Gemini Flash",
            tuned_model_info=None,
        )
        self.assertEqual(list_gemini_models.get_model_release_date(m_latest), "rolling")

    def test_format_unknown_dates_todo(self):
        self.assertEqual(list_gemini_models.format_unknown_dates_todo([]), "")
        todo_msg = list_gemini_models.format_unknown_dates_todo(["gemini-4-argon"])
        self.assertIn("(*) TODO(Gemini)", todo_msg)
        self.assertIn("gemini-4-argon", todo_msg)
        self.assertIn("https://ai.google.dev/gemini-api/docs/changelog", todo_msg)
        self.assertIn("KNOWN_RELEASE_DATES", todo_msg)
        self.assertIn("list-gemini-models.py", todo_msg)

    def test_ai_help_and_help_discoverability(self):
        help_text = list_gemini_models.get_help_text()
        self.assertIn("--ai-help", help_text)

        ai_help_md = list_gemini_models.get_ai_help_markdown()
        self.assertIn("Uses of the CLI for AI vs Human", ai_help_md)
        self.assertIn("Added Context", ai_help_md)
        self.assertIn("KNOWN_RELEASE_DATES", ai_help_md)
        self.assertIn("https://ai.google.dev/gemini-api/docs/changelog", ai_help_md)
        self.assertIn("list-gemini-models.py", ai_help_md)
        self.assertIn("--max-items", help_text)


if __name__ == "__main__":
    unittest.main()


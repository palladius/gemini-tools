import unittest
import shutil
import json
import re
import sys
import types
import importlib.util
from pathlib import Path
from types import SimpleNamespace

# Provide lightweight stdlib fallbacks when running outside uv venv
if "slugify" not in sys.modules:
    try:
        import slugify  # noqa: F401
    except ImportError:
        _slug_mod = types.ModuleType("slugify")
        _slug_mod.slugify = lambda s: re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
        sys.modules["slugify"] = _slug_mod

if "google.genai" not in sys.modules:
    try:
        from google import genai  # noqa: F401
    except ImportError:
        _google_mod = sys.modules.setdefault("google", types.ModuleType("google"))
        _genai_mod = types.ModuleType("google.genai")
        _genai_mod.Client = object
        _google_mod.genai = _genai_mod
        sys.modules["google.genai"] = _genai_mod

if "rich.console" not in sys.modules:
    try:
        import rich.console  # noqa: F401
        import rich.table  # noqa: F401
    except ImportError:
        _rich_mod = sys.modules.setdefault("rich", types.ModuleType("rich"))
        _console_mod = types.ModuleType("rich.console")
        _console_mod.Console = lambda **kwargs: SimpleNamespace(print=lambda *a, **k: None)
        _table_mod = types.ModuleType("rich.table")
        _table_mod.Table = object
        sys.modules["rich.console"] = _console_mod
        sys.modules["rich.table"] = _table_mod

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
        judge_script = Path(__file__).resolve().parent.parent / "bin" / "judge_image.py"
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
        self.assertIn("etc/gemini_models.yaml", todo_msg)
        self.assertIn("short_description", todo_msg)

    def test_gemini_models_yaml_and_short_descriptions(self):
        yaml_path = Path(__file__).resolve().parent.parent / "etc" / "gemini_models.yaml"
        self.assertTrue(yaml_path.exists(), "etc/gemini_models.yaml must exist")

        # Never mention the word "twitter" in etc/gemini_models.yaml
        raw_yaml = yaml_path.read_text(encoding="utf-8")
        self.assertNotIn("twitter", raw_yaml.lower(), "etc/gemini_models.yaml must not contain the word 'twitter'")

        catalog = list_gemini_models.load_models_catalog()
        self.assertGreaterEqual(len(catalog), 40)

        # Enforce twitter-like short desc max length (<= 280 chars/bytes); test fails if any model exceeds it
        validation_errors = list_gemini_models.validate_models_catalog(catalog, max_chars=280)
        self.assertEqual(validation_errors, [], f"Catalog validation failed: {validation_errors}")

        for model_id, meta in catalog.items():
            self.assertIn("release_date", meta, f"{model_id} missing release_date")
            self.assertIn("short_description", meta, f"{model_id} missing short_description")
            desc = meta["short_description"]
            self.assertTrue(desc and desc != "UNKNOWN (*)", f"{model_id} has empty short_description")
            # twitter-like short desc: strictly <= 280 characters and bytes
            self.assertLessEqual(
                len(desc),
                280,
                f"{model_id} short_description exceeds 280 chars ({len(desc)} chars)",
            )
            self.assertLessEqual(
                len(desc.encode("utf-8")),
                280,
                f"{model_id} short_description exceeds 280 bytes ({len(desc.encode('utf-8'))}B)",
            )

        # Negative test: violating max_chars MUST fail validate_models_catalog
        bad_catalog = {
            "gemini-too-verbose": {
                "release_date": "2026-11-05",
                "short_description": "x" * 281,
            }
        }
        bad_errors = list_gemini_models.validate_models_catalog(bad_catalog, max_chars=280)
        self.assertEqual(len(bad_errors), 1)
        self.assertIn("exceeds 280 chars/bytes", bad_errors[0])

        # Spot check Omni 1.1 Flash & Lyria 3.5 short descriptions
        m_omni = SimpleNamespace(name="models/gemini-omni-1.1-flash", description="Gemini Omni 1.1 Flash")
        omni_desc = list_gemini_models.get_model_short_description(m_omni)
        self.assertIn("40s", omni_desc)
        self.assertIn("interactions", omni_desc.lower())

        m_lyria = SimpleNamespace(name="models/lyria-3.5", description="Lyria 3.5")
        lyria_desc = list_gemini_models.get_model_short_description(m_lyria)
        self.assertIn("30s", lyria_desc)
        self.assertIn("2-3 min", lyria_desc)

        # Unknown model -> UNKNOWN (*)
        m_unknown = SimpleNamespace(name="models/gemini-4.1", description="Gemini 4.1")
        self.assertEqual(list_gemini_models.get_model_short_description(m_unknown), "UNKNOWN (*)")

    def test_ai_help_and_help_discoverability(self):
        help_text = list_gemini_models.get_help_text()
        self.assertIn("--ai-help", help_text)

        ai_help_md = list_gemini_models.get_ai_help_markdown()
        self.assertIn("Uses of the CLI for AI vs Human", ai_help_md)
        self.assertIn("Added Context", ai_help_md)
        self.assertIn("etc/gemini_models.yaml", ai_help_md)
        self.assertIn("short_description", ai_help_md)
        self.assertIn("https://ai.google.dev/gemini-api/docs/changelog", ai_help_md)
        self.assertIn("list-gemini-models.py", ai_help_md)
        self.assertIn("--max-items", help_text)


if __name__ == "__main__":
    unittest.main()


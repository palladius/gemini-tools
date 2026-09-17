import unittest
import os
import json
import shutil
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gcs_backup import (
    compute_file_hash,
    get_target_bucket,
    backup_asset,
    reconcile_asset,
    resolve_remote_uri,
    DEFAULT_BUCKET_ENV
)

class TestGCSBackup(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_gcs_"))
        self.sample_asset = self.temp_dir / "sample_render.png"
        self.sample_asset.write_bytes(b"\x89PNG\r\n\x1a\nFakeImageDataForTesting")
        self.sample_meta = self.temp_dir / "sample_render.json"
        self.sample_meta.write_text(json.dumps({"prompt": "A scenic mountain view", "model": "imagen-3"}), encoding="utf-8")

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_compute_file_hash(self):
        h = compute_file_hash(self.sample_asset)
        self.assertIsInstance(h, str)
        self.assertEqual(len(h), 32)

    def test_target_bucket_resolution(self):
        self.assertEqual(get_target_bucket("my-custom-bucket"), "my-custom-bucket")
        old_env = os.environ.get(DEFAULT_BUCKET_ENV)
        try:
            os.environ[DEFAULT_BUCKET_ENV] = "env-bucket-123"
            self.assertEqual(get_target_bucket(), "env-bucket-123")
        finally:
            if old_env is not None:
                os.environ[DEFAULT_BUCKET_ENV] = old_env
            else:
                os.environ.pop(DEFAULT_BUCKET_ENV, None)

    def test_backup_asset_dry_run(self):
        info = backup_asset(
            self.sample_asset,
            meta_path=self.sample_meta,
            bucket="test-gemini-bucket",
            dry_run=True
        )
        self.assertIsNotNone(info)
        self.assertEqual(info["bucket"], "test-gemini-bucket")
        self.assertEqual(info["gcs_uri"], "gs://test-gemini-bucket/assets/sample_render.png")
        self.assertIn("https://storage.googleapis.com/test-gemini-bucket", info["public_url"])
        self.assertEqual(info["size_bytes"], len(b"\x89PNG\r\n\x1a\nFakeImageDataForTesting"))

    def test_reconcile_missing_asset(self):
        # Setup metadata with gcs coordinates
        meta_with_gcs = {
            "prompt": "Test image",
            "gcs": {
                "bucket": "test-gemini-bucket",
                "object_name": "assets/sample_render.png",
                "gcs_uri": "gs://test-gemini-bucket/assets/sample_render.png",
                "size_bytes": 30
            }
        }
        test_meta_file = self.temp_dir / "restored.json"
        test_meta_file.write_text(json.dumps(meta_with_gcs), encoding="utf-8")
        
        # Simulated reconcile in dry-run mode
        target = reconcile_asset(test_meta_file, dry_run=True)
        self.assertIsNotNone(target)
        self.assertEqual(target.name, "sample_render.png")

    def test_resolve_remote_uri(self):
        meta_with_gcs = {
            "prompt": "Test image",
            "gcs": {
                "bucket": "test-bucket",
                "gcs_uri": "gs://test-bucket/assets/remote_image.png"
            }
        }
        img_path = self.temp_dir / "remote_image.png"
        meta_path = self.temp_dir / "remote_image.json"
        meta_path.write_text(json.dumps(meta_with_gcs), encoding="utf-8")

        uri = resolve_remote_uri(img_path)
        self.assertEqual(uri, "gs://test-bucket/assets/remote_image.png")

        # Missing json returns None
        untracked = self.temp_dir / "untracked.png"
        self.assertIsNone(resolve_remote_uri(untracked))

if __name__ == "__main__":
    unittest.main()

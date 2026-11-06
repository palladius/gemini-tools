"""
GCS Cloud Asset Sync Utility (`IMAGES_BUCKET`)
----------------------------------------------
Provides push and pull functions to sync evaluation reference photos,
generated images, and per-subject `evaluations.jsonl` files to/from Google Cloud Storage.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def get_bucket_name() -> str:
    bucket = os.environ.get("IMAGES_BUCKET")
    if not bucket:
        print("⚠️ IMAGES_BUCKET environment variable not set. Using fallback: 'cc-eval-assets'")
        return "cc-eval-assets"
    if bucket.startswith("gs://"):
        return bucket[5:].rstrip("/")
    return bucket.rstrip("/")

def push_eval_assets(local_dir: str = "out/evals", target_subject: str = None):
    bucket = get_bucket_name()
    local_path = Path(local_dir)
    if not local_path.exists():
        print(f"❌ Local evaluation directory '{local_dir}' does not exist.")
        return
        
    gcs_target = f"gs://{bucket}/evals/"
    print(f"☁️ Syncing local evals '{local_dir}' -> '{gcs_target}'...")
    
    cmd = ["gcloud", "storage", "rsync", "-r", str(local_path), gcs_target]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"✅ GCS Push complete: {gcs_target}")
    else:
        # Fallback to gsutil if gcloud storage CLI is unavailable
        cmd_gsutil = ["gsutil", "-m", "rsync", "-r", str(local_path), gcs_target]
        res_gsutil = subprocess.run(cmd_gsutil, capture_output=True, text=True)
        if res_gsutil.returncode == 0:
            print(f"✅ GCS Push complete via gsutil: {gcs_target}")
        else:
            print(f"⚠️ GCS Push notice (gcloud/gsutil output): {res.stderr or res_gsutil.stderr}")

def pull_eval_assets(local_dir: str = "out/evals"):
    bucket = get_bucket_name()
    gcs_src = f"gs://{bucket}/evals/"
    local_path = Path(local_dir)
    local_path.mkdir(parents=True, exist_ok=True)
    
    print(f"☁️ Syncing GCS evals '{gcs_src}' -> local '{local_dir}'...")
    cmd = ["gcloud", "storage", "rsync", "-r", gcs_src, str(local_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"✅ GCS Pull complete: {local_dir}")
    else:
        cmd_gsutil = ["gsutil", "-m", "rsync", "-r", gcs_src, str(local_path)]
        res_gsutil = subprocess.run(cmd_gsutil, capture_output=True, text=True)
        if res_gsutil.returncode == 0:
            print(f"✅ GCS Pull complete via gsutil: {local_dir}")
        else:
            print(f"⚠️ GCS Pull notice: {res.stderr or res_gsutil.stderr}")

def main():
    parser = argparse.ArgumentParser(description="GCS Sync Utility for Character Consistency Evaluation Assets")
    parser.add_argument("action", choices=["push", "pull"], help="Sync direction: push or pull")
    parser.add_argument("-dir", "--directory", default="out/evals", help="Local directory path (default: out/evals)")
    args = parser.parse_args()
    
    if args.action == "push":
        push_eval_assets(args.directory)
    elif args.action == "pull":
        pull_eval_assets(args.directory)

if __name__ == "__main__":
    main()

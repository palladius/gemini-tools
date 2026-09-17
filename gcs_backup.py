#!/usr/bin/env python3
"""
GCS Asset Backup & Reconciliation Manager for gemini-tools.

Features:
- P1: Automatically backup images/videos and metadata to $GEMINI_TOOLS_BUCKET.
      Updates local metadata JSON with bucket information, allowing large media files
      to be deleted locally while preserving full capability to reconcile ("git pull") later.
- P3: Resolves local media files to their remote gs:// URIs when backed up to save tokens and avoid redundant uploads.
"""

import os
import sys
import json
import hashlib
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any

DEFAULT_BUCKET_ENV = "GEMINI_TOOLS_BUCKET"

def compute_file_hash(file_path: Path) -> str:
    """Compute MD5 checksum of a file."""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_target_bucket(explicit_bucket: Optional[str] = None) -> Optional[str]:
    """Resolve bucket name from argument or environment variable."""
    if explicit_bucket:
        return explicit_bucket.strip()
    return os.environ.get(DEFAULT_BUCKET_ENV, "").strip() or None

def _run_storage_upload(local_path: Path, gcs_uri: str, dry_run: bool = False) -> bool:
    """Upload a file to GCS using gcloud storage or gsutil."""
    if dry_run:
        return True

    # Try gcloud storage first
    try:
        res = subprocess.run(
            ["gcloud", "storage", "cp", str(local_path), gcs_uri],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    # Fallback to gsutil
    try:
        res = subprocess.run(
            ["gsutil", "cp", str(local_path), gcs_uri],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    return False

def _run_storage_download(gcs_uri: str, local_path: Path, dry_run: bool = False) -> bool:
    """Download a file from GCS using gcloud storage or gsutil."""
    if dry_run:
        return True

    local_path.parent.mkdir(parents=True, exist_ok=True)
    # Try gcloud storage first
    try:
        res = subprocess.run(
            ["gcloud", "storage", "cp", gcs_uri, str(local_path)],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    # Fallback to gsutil
    try:
        res = subprocess.run(
            ["gsutil", "cp", gcs_uri, str(local_path)],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    return False

def backup_asset(
    asset_path: str | Path,
    meta_path: Optional[str | Path] = None,
    bucket: Optional[str] = None,
    prefix: Optional[str] = None,
    dry_run: bool = False,
    quiet: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Backs up an image/video file to GCS and enriches its metadata JSON with bucket coordinates.
    """
    asset_p = Path(asset_path).resolve()
    if not asset_p.exists():
        if not quiet:
            print(f"❌ Asset not found: {asset_p}", file=sys.stderr)
        return None

    target_bucket = get_target_bucket(bucket)
    if not target_bucket:
        if not quiet:
            print(f"ℹ️ No GCS bucket specified (set ${DEFAULT_BUCKET_ENV} or pass --bucket). Skipping backup.")
        return None

    # Derive object path
    rel_path = asset_p.name
    if prefix:
        object_name = f"{prefix.strip('/')}/{rel_path}"
    else:
        # Default grouping: assets/filename
        object_name = f"assets/{rel_path}"

    gcs_uri = f"gs://{target_bucket}/{object_name}"
    public_url = f"https://storage.googleapis.com/{target_bucket}/{object_name}"

    if not quiet:
        print(f"☁️ Backing up {asset_p.name} -> {gcs_uri} ...")

    upload_ok = _run_storage_upload(asset_p, gcs_uri, dry_run=dry_run)
    if not upload_ok and not dry_run:
        if not quiet:
            print(f"❌ Failed to upload {asset_p} to {gcs_uri}", file=sys.stderr)
        return None

    # Locate or create metadata JSON
    if meta_path:
        meta_p = Path(meta_path).resolve()
    else:
        meta_p = asset_p.with_suffix(".json")

    metadata: Dict[str, Any] = {}
    if meta_p.exists():
        try:
            with open(meta_p, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}

    gcs_info = {
        "bucket": target_bucket,
        "object_name": object_name,
        "gcs_uri": gcs_uri,
        "public_url": public_url,
        "backed_up_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "size_bytes": asset_p.stat().st_size,
        "md5": compute_file_hash(asset_p)
    }
    metadata["gcs"] = gcs_info

    if not dry_run:
        with open(meta_p, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        # Also upload the metadata JSON to GCS
        json_gcs_uri = f"gs://{target_bucket}/{object_name}.json"
        _run_storage_upload(meta_p, json_gcs_uri, dry_run=False)

    if not quiet:
        print(f"✅ GCS backup complete: {gcs_uri}")
        print(f"📝 Local metadata updated: {meta_p}")

    return gcs_info

def reconcile_asset(
    meta_path: str | Path,
    dest_dir: Optional[str | Path] = None,
    dry_run: bool = False,
    quiet: bool = False
) -> Optional[Path]:
    """
    Reconciles ("git pull" from GCS) a media file using its local metadata JSON.
    If the large media file was removed locally, downloads it from GCS.
    """
    meta_p = Path(meta_path).resolve()
    if not meta_p.exists():
        if not quiet:
            print(f"❌ Metadata JSON not found: {meta_p}", file=sys.stderr)
        return None

    with open(meta_p, "r", encoding="utf-8") as f:
        meta = json.load(f)

    gcs_info = meta.get("gcs")
    if not gcs_info or "gcs_uri" not in gcs_info:
        if not quiet:
            print(f"⚠️ No GCS coordinates found in {meta_p.name}", file=sys.stderr)
        return None

    gcs_uri = gcs_info["gcs_uri"]
    object_name = gcs_info.get("object_name", "")
    asset_name = Path(object_name).name if object_name else meta_p.stem

    if dest_dir:
        target_dest = Path(dest_dir).resolve() / asset_name
    else:
        # Defaults to the same directory as the metadata JSON using original asset filename
        target_dest = meta_p.parent / asset_name

    if target_dest.exists():
        if not quiet:
            print(f"✨ Asset already exists locally: {target_dest}")
        return target_dest

    if not quiet:
        print(f"📥 Reconciling {asset_name} from {gcs_uri} -> {target_dest} ...")

    download_ok = _run_storage_download(gcs_uri, target_dest, dry_run=dry_run)
    if download_ok:
        if not quiet:
            print(f"✅ Asset reconciled successfully: {target_dest}")
        return target_dest
    else:
        if not quiet:
            print(f"❌ Failed downloading {gcs_uri}", file=sys.stderr)
        return None

def resolve_remote_uri(asset_path: str | Path) -> Optional[str]:
    """
    P3: Returns the remote gs:// URI for an asset if it has already been backed up to GCS.
    Allows passing GCS references to Gemini models without redundant uploads.
    """
    asset_p = Path(asset_path).resolve()
    meta_p = asset_p.with_suffix(".json")
    if not meta_p.exists():
        return None

    try:
        with open(meta_p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("gcs", {}).get("gcs_uri")
    except Exception:
        return None

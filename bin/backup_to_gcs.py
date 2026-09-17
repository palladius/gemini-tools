#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "rich>=13.0.0"
# ]
# ///
"""
CLI utility for backing up and reconciling assets with Google Cloud Storage.
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gcs_backup import backup_asset, reconcile_asset, resolve_remote_uri, DEFAULT_BUCKET_ENV

def main():
    parser = argparse.ArgumentParser(description="Backup and reconcile assets with GCS")
    parser.add_argument("--backup", "-b", help="Path to image/video file to backup to GCS")
    parser.add_argument("--metadata", "-m", help="Explicit metadata JSON path (defaults to <asset>.json)")
    parser.add_argument("--reconcile", "-r", help="Path to metadata JSON to reconcile ('git pull') from GCS")
    parser.add_argument("--reconcile-dir", help="Directory containing metadata JSONs to reconcile missing assets from")
    parser.add_argument("--resolve", help="Print remote gs:// URI for asset if backed up")
    parser.add_argument("--bucket", help=f"GCS bucket name (defaults to ${DEFAULT_BUCKET_ENV})")
    parser.add_argument("--prefix", help="GCS object prefix path (defaults to assets/)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without uploading/downloading")

    args = parser.parse_args()

    if args.resolve:
        uri = resolve_remote_uri(args.resolve)
        if uri:
            print(uri)
            sys.exit(0)
        else:
            print(f"No GCS URI found for {args.resolve}", file=sys.stderr)
            sys.exit(1)

    if args.backup:
        res = backup_asset(
            args.backup,
            meta_path=args.metadata,
            bucket=args.bucket,
            prefix=args.prefix,
            dry_run=args.dry_run
        )
        if not res:
            sys.exit(1)
        sys.exit(0)

    if args.reconcile:
        res = reconcile_asset(args.reconcile, dry_run=args.dry_run)
        if not res:
            sys.exit(1)
        sys.exit(0)

    if args.reconcile_dir:
        target_dir = Path(args.reconcile_dir).resolve()
        if not target_dir.exists():
            print(f"Directory not found: {target_dir}", file=sys.stderr)
            sys.exit(1)
        json_files = list(target_dir.glob("**/*.json"))
        reconciled = 0
        for jf in json_files:
            if reconcile_asset(jf, dry_run=args.dry_run, quiet=True):
                reconciled += 1
        print(f"🎉 Reconcile complete: checked {len(json_files)} metadata files, reconciled {reconciled} assets.")
        sys.exit(0)

    parser.print_help()

if __name__ == "__main__":
    main()

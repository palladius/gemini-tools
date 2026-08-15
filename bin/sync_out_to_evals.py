#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "rich>=13.0.0",
#   "python-slugify>=8.0.0"
# ]
# ///

import os
import sys
import json
import glob
from pathlib import Path
from slugify import slugify
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import eval_dataset


def sync_out_folder():
    out_dir = Path("out")
    if not out_dir.exists():
        return 0

    added = 0
    audit_files = list(out_dir.glob("*_audit.json"))
    
    for audit_file in audit_files:
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                audit_data = json.load(f)
        except Exception:
            continue

        base_name = audit_file.name.replace("_multi_biometric_audit.json", "").replace("_biometric_audit.json", "")
        img_png = out_dir / f"{base_name}.png"
        meta_json = out_dir / f"{base_name}.json"
        
        if not img_png.exists():
            continue

        prompt = ""
        model_name = "imagen-4.0-generate-001"
        if meta_json.exists():
            try:
                with open(meta_json, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    prompt = meta.get("prompt", "")
                    model_name = meta.get("model", model_name)
            except Exception:
                pass

        verdicts = audit_data.get("verdicts", {})
        if not verdicts:
            sub = audit_data.get("subject", "General")
            verdicts = {sub: audit_data}

        for sub_name, verdict_info in verdicts.items():
            clean_sub = sub_name.strip().title()
            eval_id = f"{slugify(clean_sub)}_{base_name}"
            robot_score = verdict_info.get("likeness_score", verdict_info.get("character_consistency_score", 7))
            critique = verdict_info.get("critique", verdict_info.get("resemblance_critique", ""))
            verdict_str = verdict_info.get("verdict", "GOOD")

            # Check if record already exists and preserve human_eval if voted
            existing_records = eval_dataset.load_subject_evaluations(clean_sub)
            existing_rec = next((r for r in existing_records if r.get("eval_id") == eval_id), None)
            
            human_eval = existing_rec.get("human_eval") if existing_rec else None

            rec = {
                "eval_id": eval_id,
                "subject": clean_sub,
                "model_name": model_name,
                "prompt": prompt or f"Synthesized asset: {base_name}",
                "reference_images": [],
                "generated_image": {
                    "raw_path": str(img_png),
                    "annotated_path": str(img_png),
                    "face_crop_path": str(img_png)
                },
                "robot_eval": {
                    "character_consistency_score": robot_score,
                    "resemblance_critique": critique,
                    "verdict": verdict_str
                },
                "human_eval": human_eval,
                "status": "COMPLETED" if human_eval else "PENDING_HUMAN"
            }
            eval_dataset.upsert_evaluation_record(rec)
            added += 1

    return added


if __name__ == "__main__":
    count = sync_out_folder()
    print(f"✅ Synced {count} evaluation records from out/ into out/evals/")

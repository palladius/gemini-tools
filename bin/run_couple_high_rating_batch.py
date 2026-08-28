#!/usr/bin/env python3
"""
Run High-Rating (>8/10) Couple Batch for Riccardo & Kate
Generates multi-character couple photos and strictly filters out any assets scoring <= 8.0.
"""
import os
import json
import subprocess
from pathlib import Path

CANDIDATES = [
    {
        "out": "out/riccardo_kate_venice_gondola_v1.png",
        "prompt": "A romantic candid 85mm medium close-up portrait of Riccardo and Kate smiling happily together on a gondola ride in Venice Italy along the Grand Canal during golden hour sunset. Riccardo is wearing a casual dark jacket with open collar shirt (no tie), and Kate is wearing an elegant royal purple silk dress. Warm ambient lighting, soft blurred Venetian architecture background."
    },
    {
        "out": "out/riccardo_kate_kyoto_bamboo_v1.png",
        "prompt": "A joyful candid 85mm medium close-up portrait of Riccardo and Kate laughing cheerfully together standing in the Arashiyama bamboo grove in Kyoto Japan. Riccardo is wearing a casual dark navy sweater, and Kate is wearing a stylish deep violet British tailored coat. Soft diffused daylight, crisp prominent facial features."
    },
    {
        "out": "out/riccardo_kate_paris_eiffel_v1.png",
        "prompt": "A romantic candid 85mm portrait of Riccardo and Kate smiling warmly together on a cafe terrace overlooking the Eiffel Tower in Paris France. Riccardo is wearing a casual dark navy t-shirt, and Kate is wearing a royal purple British dress. Soft evening twilight lights, beautiful cityscape depth of field."
    },
    {
        "out": "out/riccardo_kate_santorini_view_v1.png",
        "prompt": "A sunny romantic 85mm medium close-up portrait of Riccardo and Kate standing close together on a balcony overlooking the blue domes of Santorini Greece. Riccardo is wearing a casual linen shirt with open collar (no tie), and Kate is wearing a plum purple summer dress. Bright Mediterranean sun, clear detailed facial likeness."
    }
]

def main():
    print("🚀 Starting High-Rating (>8/10) Riccardo & Kate Couple Batch Pipeline...\n")
    kept_count = 0

    for item in CANDIDATES:
        out_path = Path(item["out"])
        prompt = item["prompt"]

        print(f"\n========================================================")
        print(f"🎬 Generating: {out_path.name}")
        print(f"========================================================")

        gen_cmd = [
            "./bin/generate_photo.py",
            "-c", "riccardo2016",
            "-c", "kate",
            "-p", prompt,
            "-m", "gemini-3.1-flash-image",

            "--framing", "portrait",
            "-o", str(out_path),
            "--show"
        ]
        subprocess.run(gen_cmd)

        if not out_path.exists():
            print(f"❌ Generation failed for {out_path.name}")
            continue

        audit_file = out_path.with_name(out_path.stem + "_multi_biometric_audit.json")
        score = 0.0
        verdict = "UNKNOWN"

        if audit_file.exists():
            try:
                with open(audit_file, "r", encoding="utf-8") as f:
                    audit_data = json.load(f)
                    score = float(audit_data.get("overall_score", 0.0))
                    verdict = audit_data.get("verdict", "UNKNOWN")
            except Exception as e:
                print(f"⚠️ Error reading audit file: {e}")

        print(f"\n📊 AI Judge Score for {out_path.name}: {score}/10 ({verdict})")

        if score > 8.0:
            print(f"🏆 RATING > 8.0! ({score}/10) -> KEPT ASSET: {out_path.name}")
            kept_count += 1
        else:
            print(f"🗑️ RATING <= 8.0 ({score}/10) -> AUTO-PRUNING: {out_path.name}")
            out_path.unlink(missing_ok=True)
            audit_file.unlink(missing_ok=True)
            out_path.with_suffix(".json").unlink(missing_ok=True)

    subprocess.run(["./bin/sync_out_to_evals.py"])
    print(f"\n========================================================")
    print(f"🎉 Pipeline Completed! Kept {kept_count} top-tier (>8/10) couple assets.")
    print(f"========================================================")

if __name__ == "__main__":
    main()

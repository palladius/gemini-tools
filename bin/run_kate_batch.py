#!/usr/bin/env python3
import os
import json
import subprocess
from pathlib import Path

KATE_PROMPTS = [
    {
        "out": "out/kate_oxford_royal_purple_v1.png",
        "prompt": "A candid 85mm portrait of Kate with a radiant youthful smile, wearing an elegant royal purple British silk dress, walking in the historic courtyard of Oxford University under soft afternoon light."
    },
    {
        "out": "out/kate_positano_plum_dress_v1.png",
        "prompt": "A sunny 85mm medium close-up portrait of Kate with glowing fresh skin and natural smile lines, wearing a stylish plum purple linen dress, enjoying a sunny day at a cafe balcony overlooking Positano."
    },
    {
        "out": "out/kate_kyoto_violet_chic_v1.png",
        "prompt": "A candid 85mm portrait of Kate laughing cheerfully, wearing a sophisticated deep violet British tailored coat, surrounded by vibrant green bamboo trees in Kyoto Japan under soft diffused light."
    },
    {
        "out": "out/kate_venice_purple_evening_v1.png",
        "prompt": "A romantic 85mm portrait of Kate with a radiant smile, wearing a royal purple evening dress, standing near St. Mark's Square in Venice Italy during golden hour sunset."
    }
]

def main():
    print("🚀 Starting Kate Royal British Fashion Synthesis Batch...\n")
    kept = []

    for item in KATE_PROMPTS:
        out_p = Path(item["out"])
        prompt = item["prompt"]

        print(f"📸 Synthesizing: {out_p.name}...")
        gen_cmd = [
            "./bin/generate_photo.py",
            "-p", prompt,
            "-c", "kate",
            "-m", "gemini-3.1-flash-image-preview",
            "--framing", "portrait",
            "-o", str(out_p),
            "--show"
        ]
        subprocess.run(gen_cmd)

        if not out_p.exists():
            print(f"❌ Failed generating {out_p.name}")
            continue

        audit_file = out_p.with_name(out_p.stem + "_multi_biometric_audit.json")
        score = 0
        if audit_file.exists():
            try:
                with open(audit_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    score = data.get("overall_score", 0)
            except Exception:
                pass

        print(f"📊 AI Judge Score: {score}/10")

        if score < 5:
            print(f"🗑️ Score < 5 ({score}/10). Deleting low-quality asset: {out_p.name}")
            out_p.unlink(missing_ok=True)
            audit_file.unlink(missing_ok=True)
            out_p.with_suffix(".json").unlink(missing_ok=True)
        else:
            print(f"🟢 Score >= 5 ({score}/10). Kept asset: {out_p.name}")
            kept.append(str(out_p))

    subprocess.run(["./bin/sync_out_to_evals.py"])
    print(f"\n🎉 Completed! Synthesized & kept {len(kept)} high-quality Kate photos.")

if __name__ == "__main__":
    main()

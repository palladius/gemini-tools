#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from pathlib import Path

SOLO_PROMPTS = [
    {"character": "kate", "out": "out/solo_kate_1.png", "prompt": "A candid photorealistic portrait of Kate, an attractive 40-year-old blonde woman with glowing fresh skin and radiant smile, enjoying a gelato in Florence under soft afternoon light."},
    {"character": "kate", "out": "out/solo_kate_2.png", "prompt": "A sunny 35mm photo of Kate walking in a blooming flower garden in Kyoto Japan wearing a casual linen jacket, laughing happily."},

    {"character": "riccardo2016", "out": "out/solo_riccardo_1.png", "prompt": "A candid photorealistic portrait of Riccardo with dark hair and friendly smile, sitting at a cafe table in Piazza Navona Rome during golden hour sunset."},
    {"character": "riccardo2016", "out": "out/solo_riccardo_2.png", "prompt": "A relaxed 35mm photo of Riccardo walking across the famous Shibuya Crossing in Tokyo under evening neon lights."},

    {"character": "alessandro", "out": "out/solo_alessandro_1.png", "prompt": "A candid photo of 8-year-old boy Alessandro with short brown hair, smiling brightly on the white sand beach of Stintino Sardinia."},
    {"character": "alessandro", "out": "out/solo_alessandro_2.png", "prompt": "Alessandro, an 8-year-old boy, looking amazed inside a colorful Ghibli museum display in Tokyo Japan."},

    {"character": "sebastian", "out": "out/solo_sebastian_1.png", "prompt": "A cute candid photo of 6-year-old boy Sebastian eating authentic ramen noodles at a traditional counter in Tokyo."},
    {"character": "sebastian", "out": "out/solo_sebastian_2.png", "prompt": "Sebastian, a 6-year-old boy with short brown hair, laughing happily while playing on the beach in Sardinia."}
]

def main():
    print("🚀 Running 2x2x2x2 Solo Family Batch (Kate, Riccardo, Alessandro, Sebastian)...\n")
    kept = []
    
    for item in SOLO_PROMPTS:
        char = item["character"]
        out_p = Path(item["out"])
        prompt = item["prompt"]
        
        print(f"📸 Generating {char} -> {out_p.name}...")
        gen_cmd = [
            "./bin/generate_photo.py",
            "-p", prompt,
            "-c", char,
            "-m", "gemini-3.1-flash-image-preview",
            "-o", str(out_p),
            "--show"
        ]
        subprocess.run(gen_cmd)
        
        if not out_p.exists():
            print(f"❌ Failed to generate {out_p.name}")
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
                
        print(f"📊 AI Judge Score for {out_p.name}: {score}/10")
        
        if score < 5:
            print(f"🗑️ Score < 5 ({score}/10). Deleting low-quality asset: {out_p.name}")
            out_p.unlink(missing_ok=True)
            audit_file.unlink(missing_ok=True)
            out_p.with_suffix(".json").unlink(missing_ok=True)
        else:
            print(f"🟢 Score >= 5 ({score}/10). Kept asset: {out_p.name}")
            kept.append(str(out_p))
            
    # Sync dataset
    subprocess.run(["./bin/sync_out_to_evals.py"])
    print(f"\n🎉 Done! Generated and kept {len(kept)} high-quality solo assets.")

if __name__ == "__main__":
    main()

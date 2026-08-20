#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "google-genai>=1.0.0",
#   "rich>=13.0.0",
#   "python-slugify>=8.0.0",
#   "pillow>=10.0.0",
#   "pydantic>=2.0.0"
# ]
# ///

import os
import sys
import json
import glob
import time
import subprocess
from pathlib import Path
from rich.console import Console
from slugify import slugify

console = Console()

TARGET_PROMPTS = [
    # --- STINTINO, SARDEGNA ---
    {"subject": "kate", "location": "stintino", "prompt": "A candid photorealistic portrait of Kate, an attractive 40-year-old blonde woman with a radiant youthful smile, standing on the turquoise water shore of La Pelosa beach in Stintino, Sardinia under soft flattering golden sunlight."},
    {"subject": "kate", "location": "stintino", "prompt": "A sunny afternoon photo of Kate, an elegant 40-year-old blonde woman with natural smile lines and glowing skin, sitting at a beachside cafe in Stintino Sardinia wearing a white summer dress."},
    
    {"subject": "riccardo2016", "location": "stintino", "prompt": "A candid photorealistic portrait of Riccardo sitting on a wooden boat at La Pelosa beach in Stintino Sardinia during sunny afternoon light."},
    {"subject": "riccardo2016", "location": "stintino", "prompt": "A relaxed photo of Riccardo walking along the white sand beach of Stintino Sardinia holding a cold drink at sunset."},

    {"subject": "alessandro", "location": "stintino", "prompt": "A high-resolution candid photograph of 8-year-old boy Alessandro playing in the shallow turquoise water of Stintino beach Sardinia."},
    {"subject": "alessandro", "location": "stintino", "prompt": "Alessandro, an 8-year-old boy with short brown hair, building a sandcastle on La Pelosa beach in Stintino Sardinia."},

    {"subject": "sebastian", "location": "stintino", "prompt": "Sebastian, a 6-year-old boy with short brown hair, smiling happily on the beach of Stintino Sardinia with sea background."},
    {"subject": "sebastian", "location": "stintino", "prompt": "A cute candid snapshot of 6-year-old boy Sebastian eating a gelato cone on the promenade in Stintino Sardinia."},

    {"subject": "kate,riccardo2016,alessandro,sebastian", "location": "stintino", "prompt": "A realistic candid family portrait of Riccardo, Kate (attractive 40-year-old blonde woman), 8-year-old Alessandro and 6-year-old Sebastian sitting together on the white sand beach of Stintino Sardinia under soft natural light."},
    {"subject": "kate,riccardo2016,alessandro,sebastian", "location": "stintino", "prompt": "A happy family photograph of Riccardo and Kate with their two young sons Alessandro and Sebastian walking along the sea in Stintino Sardinia at golden hour sunset."},

    # --- TOKYO, JAPAN ---
    {"subject": "kate", "location": "tokyo", "prompt": "A candid street photograph of Kate, an attractive 40-year-old blonde woman with soft natural makeup and radiant smile, walking through the vibrant neon-lit streets of Shinjuku Tokyo at night."},
    {"subject": "kate", "location": "tokyo", "prompt": "Kate, an elegant 40-year-old blonde woman with glowing skin, standing gracefully under blooming cherry blossom trees in Ueno Park Tokyo during soft afternoon daylight."},

    {"subject": "riccardo2016", "location": "tokyo", "prompt": "A candid 35mm photo of Riccardo walking across the famous Shibuya Crossing in Tokyo surrounded by neon billboards."},
    {"subject": "riccardo2016", "location": "tokyo", "prompt": "Riccardo standing in front of the golden Senso-ji temple in Asakusa Tokyo wearing a casual dark jacket."},

    {"subject": "alessandro", "location": "tokyo", "prompt": "Alessandro, an 8-year-old boy, looking amazed inside an anime arcade in Akihabara Tokyo surrounded by colorful lights."},
    {"subject": "alessandro", "location": "tokyo", "prompt": "A candid photo of 8-year-old boy Alessandro holding a giant vending machine drink at Meiji Shrine in Tokyo."},

    {"subject": "sebastian", "location": "tokyo", "prompt": "Sebastian, a 6-year-old boy, eating authentic ramen noodles at a traditional ramen counter in Tokyo Japan."},
    {"subject": "sebastian", "location": "tokyo", "prompt": "A cute candid snapshot of 6-year-old boy Sebastian posing next to a giant Gundam robot statue in Odaiba Tokyo."},

    {"subject": "kate,riccardo2016,alessandro,sebastian", "location": "tokyo", "prompt": "A candid family photograph of Riccardo and Kate with their sons Alessandro and Sebastian standing together at Shibuya Crossing in Tokyo Japan."},
    {"subject": "kate,riccardo2016,alessandro,sebastian", "location": "tokyo", "prompt": "A happy family photo of Riccardo, Kate, Alessandro, and Sebastian visiting the traditional gardens of the Imperial Palace in Tokyo."}
]

SESSION_KEPT_ASSETS = []

def run_synthesis_batch():
    console.print("\n🚀 [bold green]STARTING STINTINO & TOKYO FAMILY SYNTHESIS ENGINE[/bold green]\n")

    
    for idx, item in enumerate(TARGET_PROMPTS, 1):
        subjects = item["subject"]
        loc = item["location"]
        prompt = item["prompt"]
        
        safe_slug = f"family_{loc}_{slugify(subjects)}_{idx}"
        out_img = Path("out") / f"{safe_slug}.png"
        audit_file = Path("out") / f"{safe_slug}_multi_biometric_audit.json"
        
        console.print(f"📸 [{idx}/{len(TARGET_PROMPTS)}] Generating: [cyan]{safe_slug}[/cyan] ({subjects} @ {loc})")
        
        # 1. Run photo synthesis
        gen_cmd = [
            "./bin/generate_photo.py",
            "-p", prompt,
            "-c", subjects,
            "-m", "gemini-3.1-flash-image-preview",
            "-o", str(out_img),
            "--open"
        ]
        subprocess.run(gen_cmd)

        
        if not out_img.exists():
            console.print(f"[bold red]❌ Failed generating {out_img}[/bold red]")
            continue
            
        # 2. Run AI Judge
        console.print(f"👨‍⚖️ Running AI Judge evaluation on {out_img.name}...")
        judge_cmd = [
            "./bin/judge_image.py",
            "-i", str(out_img),
            "-c", subjects
        ]
        subprocess.run(judge_cmd)
        
        # 3. Check AI score
        score = 0
        if audit_file.exists():
            try:
                with open(audit_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    score = data.get("overall_score", 0)
            except Exception:
                pass

        console.print(f"📊 AI Judge Composite Score: [bold yellow]{score}/10[/bold yellow]")

        # 4. Filter: DELETE photos with score < 5
        if score < 5:
            console.print(f"🗑️ [bold red]SCORE < 5 ({score}/10). DELETING LOW QUALITY ASSET: {out_img.name}[/bold red]")
            if out_img.exists():
                out_img.unlink()
            if audit_file.exists():
                audit_file.unlink()
            meta_json = out_img.with_suffix(".json")
            if meta_json.exists():
                meta_json.unlink()
        else:
            console.print(f"🟢 [bold green]SCORE >= 5 ({score}/10). KEPT ASSET & SYNCING TO EVALS...[/bold green]")
            SESSION_KEPT_ASSETS.append({"subject": subjects, "file": str(out_img), "score": score})
            # Sync to evals dataset
            subprocess.run(["./bin/sync_out_to_evals.py"])

        # Count new kept assets in current session
        kate_cnt = sum(1 for a in SESSION_KEPT_ASSETS if "kate" in a["subject"].lower())
        ricc_cnt = sum(1 for a in SESSION_KEPT_ASSETS if "ricc" in a["subject"].lower())
        alex_cnt = sum(1 for a in SESSION_KEPT_ASSETS if "alessandro" in a["subject"].lower())
        seby_cnt = sum(1 for a in SESSION_KEPT_ASSETS if "sebastian" in a["subject"].lower())

        console.print(f"📈 Session High-Quality Assets: Total = {len(SESSION_KEPT_ASSETS)} | Kate: {kate_cnt}, Riccardo: {ricc_cnt}, Alessandro: {alex_cnt}, Sebastian: {seby_cnt}")

        if len(SESSION_KEPT_ASSETS) >= 10 and kate_cnt >= 2 and ricc_cnt >= 2 and alex_cnt >= 2 and seby_cnt >= 2:
            console.print("\n🎉 [bold green]REQUIREMENT REACHED! At least 10 NEW high-quality photos generated (>=2 per person)![/bold green]\n")
            try:
                subprocess.run(["say", "Riccardino! Ho generato 10 nuove foto della famiglia a Stintino e Tokyo! Le foto brutte sono state eliminate, vieni a votare quelle buone!"])
            except Exception:
                pass
            break


if __name__ == "__main__":
    run_synthesis_batch()

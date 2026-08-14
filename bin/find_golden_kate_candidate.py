#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "google-genai>=1.0.0",
#   "rich>=13.0.0",
#   "pydantic>=2.0.0",
#   "pillow>=10.0.0"
# ]
# ///

import os
import sys
import json
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

PROMPTS = [
    # 1. Anti-glamour authentic portrait
    "A candid unedited 85mm photograph of Kate (the exact 45-year-old woman in reference photo with blonde hair, light blue eyes, authentic natural smile lines around eyes and cheeks, realistic natural skin texture) sitting at an outdoor cafe in Greece, natural afternoon sunlight, photorealistic 8K portrait.",
    
    # 2. Natural daylight, realistic skin texture
    "An unretouched realistic portrait of Kate (blonde hair, light blue eyes, natural smile with fine smile lines, wearing a simple linen shirt) enjoying a glass of white wine by the Aegean sea in Greece, soft natural daylight, authentic real woman photo.",
    
    # 3. Close-up candid, no AI smoothing
    "A candid close-up photograph of Kate (the woman from reference photo, blonde hair, blue eyes, natural jawline and cheek dimples, unedited skin) sitting outdoors at a coastal taverna in Greece, realistic holiday snapshot.",
    
    # 4. Sunset natural lighting
    "A photorealistic candid snapshot of Kate (blonde hair, light blue eyes, authentic expression with visible smile lines) relaxing at a wooden seaside deck in Greece during golden hour sunset, holding a glass of white wine, raw camera photo.",
    
    # 5. Casual outdoor portrait
    "A realistic 85mm candid photo of Kate (45-year-old blonde woman in reference photos, blue eyes, warm natural smile, beige linen shirt) sitting at a sunlit Greek restaurant, authentic facial features, natural lighting.",
    
    # 6. Taverna scene, non-glamour
    "An authentic unedited photograph of Kate (blonde hair, light blue eyes, fine smile lines) eating a Greek salad at a seaside taverna in Naxos, Greece, natural daylight, genuine un-smoothed facial texture.",
    
    # 7. Cliffside sunset, realistic features
    "A candid sunset portrait of Kate (the blonde woman from reference image, blue eyes, natural smile lines) sitting at a cliffside table in Santorini, Greece with a wine glass, raw photographic quality.",
    
    # 8. Island walkway candid
    "A realistic candid snapshot of Kate (blonde hair, blue eyes, wearing casual clothes) walking along a sunny cobblestone street in Crete, Greece, authentic real-life photo, non-model look.",
    
    # 9. Seaside deck, natural lighting
    "A candid 85mm photograph of Kate (blonde hair, light blue eyes, authentic smile lines, natural jaw structure) sitting by the blue water in Paros, Greece, holding a glass of white wine, soft afternoon sun.",
    
    # 10. Ultimate authentic formula
    "A high resolution candid photograph of Kate (the exact woman in reference photo, blonde hair, blue eyes, authentic smile lines, natural facial contours, no AI smoothing) sitting at a coastal table in Greece, 85mm lens, natural outdoor lighting."
]

def main():
    anchor_img = "data/characters/kate/kate_golden_wine_anchor.png"
    if not Path(anchor_img).exists():
        console.print(f"[bold red]Error: Reference anchor {anchor_img} missing![/bold red]")
        sys.exit(1)

    console.print(Panel.fit(
        "🚀 [bold cyan]AUTOMATED GOLDEN SEARCH FOR KATE (TARGET SCORE >= 8.0/10.0)[/bold cyan]\n"
        "🎯 Generating & auditing 10 candidate photos sequentially...\n"
        "🔔 Will STOP immediately and notify Riccardo when a candidate reaches >= 8.0!",
        title="🤖 Anti-Beautification Candidate Search"
    ))

    winner_found = False

    for idx, prompt in enumerate(PROMPTS, 1):
        out_png = f"out/kate_golden_search_cand{idx}.png"
        audit_json = f"out/kate_golden_search_cand{idx}_multi_biometric_audit.json"

        console.print(f"\n🎨 [bold yellow]Generating Candidate {idx}/10...[/bold yellow]")
        console.print(f"📝 Prompt: [italic]'{prompt}'[/italic]")

        # 1. Generate Photo
        gen_cmd = [
            "./bin/generate_photo.py",
            "-i", anchor_img,
            "-p", prompt,
            "--files-api",
            "-o", out_png,
            "--open"
        ]
        res = subprocess.run(gen_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            console.print(f"[bold red]Generation failed for Cand {idx}: {res.stderr}[/bold red]")
            continue

        # 2. Judge Photo
        console.print(f"👨‍⚖️ [bold cyan]Auditing Candidate {idx} with AI Forensic Judge...[/bold cyan]")
        judge_cmd = [
            "./bin/judge_image.py",
            "-i", out_png,
            "-c", "kate"
        ]
        jres = subprocess.run(judge_cmd, capture_output=True, text=True)
        
        # Read audit json if created
        score = 0.0
        if Path(audit_json).exists():
            try:
                with open(audit_json, "r", encoding="utf-8") as jf:
                    adata = json.load(jf)
                    for cscore in adata.get("character_scores", []):
                        if cscore.get("character_name", "").lower() == "kate":
                            score = float(cscore.get("biometric_resemblance_score", 0.0))
            except Exception as e:
                console.print(f"[yellow]Failed to parse audit score: {e}[/yellow]")

        color = "green" if score >= 8.0 else ("yellow" if score >= 6.5 else "red")
        console.print(f"🏆 Candidate {idx} Biometric Score: [{color}]{score:.1f}/10.0[/{color}]")

        if score >= 8.0:
            console.print(Panel.fit(
                f"🎉 [bold green]GOLDEN CANDIDATE FOUND! Candidate {idx} Scored {score:.1f}/10.0![/bold green]\n"
                f"📁 Image: {out_png}\n"
                f"🔔 WAKING UP RICCARDO!",
                title="🏆 SOGLIA EVAL SUPERATA (> 8.0)"
            ))
            winner_found = True
            break

    if not winner_found:
        console.print(f"\n⚠️ Completed all 10 candidates. Highest score audited. Open images for Riccardo's review.")

if __name__ == "__main__":
    main()

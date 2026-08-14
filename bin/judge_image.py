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
import argparse
import datetime
from pathlib import Path
from PIL import Image as PILImage
from pydantic import BaseModel, Field
from rich.console import Console
from google import genai
from google.genai import types

console = Console()

class CharacterBiometricScore(BaseModel):
    character_name: str = Field(description="Name of the evaluated character (e.g. alessandro, sebastian).")
    biometric_resemblance_score: float = Field(description="Biometric face & likeness similarity score for this specific character (1.0 to 10.0).")
    specific_critique: str = Field(description="Forensic analysis of facial features, hair, eyes, and bone structure for this character.")

class ImageAuditReport(BaseModel):
    target_asset_path: str = Field(description="Path to the evaluated image file.")
    source_reference_paths: list[str] = Field(description="Paths to the authentic reference photos used.")
    evaluation_timestamp: str = Field(description="ISO 8601 timestamp.")
    character_scores: list[CharacterBiometricScore] = Field(description="Per-character biometric similarity scores and critiques.")
    image_quality_score: int = Field(description="Overall image visual quality score (1 to 10).")
    overall_score: int = Field(description="Final composite score (1 to 10).")
    verdict: str = Field(description="Verdict label (CAPOLAVORO / GOOD / TRASH).")
    expert_critique: str = Field(description="Summary critique of overall composition and multi-subject fidelity.")
    actionable_next_step: str = Field(description="Concrete recommendation to improve biometric fidelity.")

def to_tilde_path(p: str | Path) -> str:
    res = str(Path(p).resolve())
    home = str(Path.home())
    if res.startswith(home):
        return "~" + res[len(home):]
    return res

def resolve_character_images(character_name: str) -> list[str]:
    char_dir = Path("data/characters") / character_name.lower().strip()
    if not char_dir.exists():
        return []
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    return [str(p) for p in char_dir.iterdir() if p.suffix.lower() in valid_exts]

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY environment variable not set.[/bold red]")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="👨‍⚖️ Image Biometric & Quality Judge (Multi-Character Support).")
    parser.add_argument("-i", "--image", required=True, help="Path to the generated image to evaluate.")
    parser.add_argument("-c", "--character", required=True, help="Character name(s), comma-separated for multi-subject evaluation (e.g. alessandro,sebastian).")
    parser.add_argument("-m", "--model", default="gemini-3.5-flash", help="Model to use for judging (default: gemini-3.5-flash).")
    parser.add_argument("-n", "--note", default=None, help="Optional out-of-band experimental note or version metadata to log into JSON and JSONL.")

    args = parser.parse_args()
    img_path = Path(args.image)
    if not img_path.exists():
        console.print(f"[bold red]Error: Image file '{img_path}' does not exist.[/bold red]")
        sys.exit(1)

    char_names = [c.strip().lower() for c in args.character.split(",") if c.strip()]
    
    all_ref_images = []
    char_ref_map = {}
    for cname in char_names:
        imgs = resolve_character_images(cname)
        char_ref_map[cname] = imgs
        all_ref_images.extend(imgs)

    console.print(f"\n👨‍⚖️ [bold cyan]INITIALIZING BIOMETRIC IMAGE AUDIT FOR:[/bold cyan] {img_path.name}")
    console.print(f"👤 Target Characters: [bold magenta]{', '.join(char_names).upper()}[/bold magenta]")
    for cname, imgs in char_ref_map.items():
        console.print(f"📸 Loaded Reference Photos for [green]{cname.upper()}[/green]: {imgs}")

    client = genai.Client(api_key=api_key)

    contents = []
    try:
        contents.append(PILImage.open(img_path))
        for rpath in all_ref_images:
            contents.append(PILImage.open(rpath))
    except Exception as err:
        console.print(f"[bold red]Failed loading image files: {err}[/bold red]")
        sys.exit(1)

    prompt = f"""
    You are an unsparing forensic biometric likeness and visual quality judge evaluating AI-generated images.
    Target subject character(s) to evaluate: {', '.join(char_names).upper()}.
    
    INPUT IMAGE ORDER:
    - Image 1: The AI-generated target image under evaluation.
    - Subsequent images: Authentic real-life reference photographs for each character listed ({char_ref_map}).

    REQUIREMENTS:
    1. Evaluate EACH character listed in {char_names} individually.
    2. Populate the 'character_scores' array with one entry for each character ({', '.join(char_names)}).
    3. Calculate their specific 'biometric_resemblance_score' (1.0 to 10.0) by scrutinizing facial bone structure, eye color, nose shape, lip shape, hair texture, and distinct facial traits against their authentic reference photos.
    4. Be brutally honest. If a character looks like a generic stock child/person rather than the authentic reference subject, penalize their resemblance score (3.0 - 6.0).

    Output strictly according to the requested JSON schema.
    """
    contents.append(prompt)

    try:
        response = client.models.generate_content(
            model=args.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ImageAuditReport,
                temperature=0.2,
            )
        )
        parsed_json = json.loads(response.text.strip())
        parsed_json["target_asset_path"] = to_tilde_path(img_path)
        parsed_json["source_reference_paths"] = [to_tilde_path(p) for p in all_ref_images]
        parsed_json["evaluation_timestamp"] = datetime.datetime.now().isoformat()
        if args.note:
            parsed_json["note"] = args.note

        console.print(f"\n==========================================================================")
        console.print(f"🏆 MULTI-CHARACTER BIOMETRIC VERDICT FOR: [bold yellow]{', '.join(char_names).upper()}[/bold yellow]")
        if args.note:
            console.print(f"📌 Note / Metadata         : [bold cyan]{args.note}[/bold cyan]")
        console.print(f"==========================================================================")
        console.print(f"🎬 Image Quality Score       : {parsed_json.get('image_quality_score')}/10")
        
        cscores = parsed_json.get("character_scores", [])
        for cs in cscores:
            cname = cs.get("character_name", "UNKNOWN").upper()
            cscore = cs.get("biometric_resemblance_score", 0)
            critique = cs.get("specific_critique", "")
            console.print(f"🧬 Likeness Score [{cname}] : [bold cyan]{cscore}/10.0[/bold cyan]")
            console.print(f"   💬 {critique}")

        console.print(f"👑 Overall Total Score       : [bold green]{parsed_json.get('overall_score')}/10[/bold green]")
        console.print(f"🗑️ FINAL VERDICT             : [bold magenta]{parsed_json.get('verdict')}[/bold magenta]")
        console.print(f"==========================================================================")
        console.print(f"🔍 Summary Critique:\n{parsed_json.get('expert_critique')}")
        console.print(f"➡️ Recommendation:\n{parsed_json.get('actionable_next_step')}")
        console.print(f"==========================================================================\n")

        json_out = img_path.parent / f"{img_path.stem}_multi_biometric_audit.json"
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(parsed_json, f, indent=2)
        console.print(f"📁 Multi-character audit saved to: [blue]{to_tilde_path(json_out)}[/blue]")

        # Append out-of-band note and record to central JSONL log file
        jsonl_out = Path("out/judge_experiments.jsonl")
        jsonl_out.parent.mkdir(parents=True, exist_ok=True)
        jsonl_entry = {
            "timestamp": parsed_json["evaluation_timestamp"],
            "image": to_tilde_path(img_path),
            "characters": char_names,
            "overall_score": parsed_json.get("overall_score"),
            "image_quality_score": parsed_json.get("image_quality_score"),
            "verdict": parsed_json.get("verdict"),
            "note": args.note,
            "audit_file": to_tilde_path(json_out)
        }
        with open(jsonl_out, "a", encoding="utf-8") as f:
            f.write(json.dumps(jsonl_entry) + "\n")
        console.print(f"📝 Appended experiment record to: [green]{to_tilde_path(jsonl_out)}[/green]\n")

    except Exception as e:
        console.print(f"[bold red]Audit failed: {e}[/bold red]")

if __name__ == "__main__":
    main()

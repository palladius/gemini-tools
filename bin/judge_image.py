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
from pathlib import Path
from PIL import Image as PILImage
from pydantic import BaseModel, Field
from rich.console import Console
from google import genai
from google.genai import types

console = Console()

class ImageAuditReport(BaseModel):
    target_asset_path: str = Field(description="Path to the evaluated image file.")
    source_reference_paths: list[str] = Field(description="Paths to the authentic reference photos used.")
    evaluation_timestamp: str = Field(description="ISO 8601 timestamp.")
    character_name: str = Field(description="Name of the character evaluated.")
    image_quality_score: int = Field(description="Overall image quality score (1 to 10).")
    biometric_resemblance_score: float = Field(description="Biometric face & likeness similarity score (1.0 to 10.0).")
    overall_score: int = Field(description="Final composite score (1 to 10).")
    verdict: str = Field(description="Verdict label (CAPOLAVORO / GOOD / TRASH).")
    expert_critique: str = Field(description="Detailed forensic critique of likeness, facial bones, eye color, and hair style.")
    actionable_next_step: str = Field(description="Concrete recommendation to improve biometric fidelity.")

def to_tilde_path(p: str | Path) -> str:
    res = str(Path(p).resolve())
    home = str(Path.home())
    if res.startswith(home):
        return "~" + res[len(home):]
    return res

def resolve_character_images(character_name: str) -> list[str]:
    char_dir = Path("data/characters") / character_name.lower()
    if not char_dir.exists():
        return []
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    return [str(p) for p in char_dir.iterdir() if p.suffix.lower() in valid_exts]

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY environment variable not set.[/bold red]")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="👨‍⚖️ Image Biometric & Quality Judge.")
    parser.add_argument("-i", "--image", required=True, help="Path to the generated image to evaluate.")
    parser.add_argument("-c", "--character", required=True, help="Character name (e.g. alessandro, sebastian).")
    parser.add_argument("-m", "--model", default="gemini-3.5-flash", help="Model to use for judging (default: gemini-3.5-flash).")

    args = parser.parse_args()
    img_path = Path(args.image)
    if not img_path.exists():
        console.print(f"[bold red]Error: Image file '{img_path}' does not exist.[/bold red]")
        sys.exit(1)

    ref_images = resolve_character_images(args.character)
    console.print(f"\n👨‍⚖️ [bold cyan]INITIALIZING BIOMETRIC IMAGE AUDIT FOR:[/bold cyan] {img_path.name}")
    console.print(f"👤 Character Target: [bold magenta]{args.character.upper()}[/bold magenta]")
    console.print(f"📸 Loaded Reference Photos: [green]{ref_images}[/green]")

    client = genai.Client(api_key=api_key)

    contents = []
    try:
        contents.append(PILImage.open(img_path))
        for rpath in ref_images:
            contents.append(PILImage.open(rpath))
    except Exception as err:
        console.print(f"[bold red]Failed loading image files: {err}[/bold red]")
        sys.exit(1)

    prompt = f"""
    You are an unsparing forensic biometric likeness and visual quality judge evaluating AI-generated images.
    Target subject: {args.character.upper()}.
    The first image provided is the generated image under evaluation.
    The remaining images are authentic reference photographs of {args.character.upper()}.

    Analyze facial structure, eye color, hair texture, nose shape, lip shape, and age representation.
    Be brutally honest. If the subject looks like a generic stock child/person rather than the actual person in reference photos, penalize biometric_resemblance_score harshly (3.0 - 6.0).

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
        parsed_json["source_reference_paths"] = [to_tilde_path(p) for p in ref_images]

        console.print(f"\n==========================================================================")
        console.print(f"🏆 BIOMETRIC IMAGE VERDICT FOR: [bold yellow]{args.character.upper()}[/bold yellow]")
        console.print(f"==========================================================================")
        console.print(f"🎬 Image Quality Score       : {parsed_json.get('image_quality_score')}/10")
        console.print(f"🧬 Likeness Resemblance Score  : {parsed_json.get('biometric_resemblance_score')}/10.0")
        console.print(f"👑 Overall Total Score       : [bold green]{parsed_json.get('overall_score')}/10[/bold green]")
        console.print(f"🗑️ FINAL VERDICT             : [bold magenta]{parsed_json.get('verdict')}[/bold magenta]")
        console.print(f"==========================================================================")
        console.print(f"🔍 Expert Critique:\n{parsed_json.get('expert_critique')}")
        console.print(f"➡️ Recommendation:\n{parsed_json.get('actionable_next_step')}")
        console.print(f"==========================================================================\n")

        json_out = img_path.parent / f"{img_path.stem}_biometric_audit.json"
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(parsed_json, f, indent=2)
        console.print(f"📁 Audit saved to: [blue]{to_tilde_path(json_out)}[/blue]\n")

    except Exception as e:
        console.print(f"[bold red]Audit failed: {e}[/bold red]")

if __name__ == "__main__":
    main()

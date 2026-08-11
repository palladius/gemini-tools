#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai",
#     "pydantic>=2.0",
#     "rich",
# ]
# ///

import os
import sys
import argparse
import glob
import time
import json
from pathlib import Path
from rich.console import Console
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

console = Console()

def to_tilde_path(p: str | Path) -> str:
    res = str(Path(p).resolve())
    home = str(Path.home())
    if res.startswith(home):
        return "~" + res[len(home):]
    return res

class SubjectConsistency(BaseModel):
    subject: str = Field(description="Exact normalized name of the recognized subject or character in lowercase (e.g., 'yukihiro', 'john_doe', 'alice'). Must match the character being audited.")
    resemblance_score: float = Field(description="Strict biometric similarity score from 1.0 to 10.0 against real-world authentic photos")
    observations: str = Field(description="Specific anatomical and facial forensic observations comparing the video character to authentic reference photos")

class VideoAuditReport(BaseModel):
    character_name: str = Field(description="Name of the main subject/character evaluated")
    video_quality_score: int = Field(description="Score from 1 to 10 evaluating motion smoothness, cinematic lighting, and lack of flickering/artifacts")
    character_consistencies: list[SubjectConsistency] = Field(description="List of strict biometric resemblance ratings for each recognized subject/character in the scene")
    overall_score: int = Field(description="Combined holistic score from 1 to 10")
    verdict: str = Field(description="Strict verdict: either 'KEEP (CAPOLAVORO)' if overall >= 7 and facial resemblance is authentic, or 'TRASH / QUARANTINE (FA CAGARE)' if under 7 or exhibiting generic AI doll facial drift")
    expert_critique: str = Field(description="Detailed forensic explanation of what worked brilliantly or why the video failed and looks unnatural/generic")
    actionable_next_step: str = Field(description="Concrete advice on whether to re-generate the starting photo, modify prompt keywords, or approve the asset")

def resolve_character_images(character_name: str, max_images: int = 4):
    search_paths = [
        f"data/characters/{character_name.lower()}/*.jpg",
        f"data/characters/{character_name.lower()}/*.png",
        f"data/{character_name.lower()}/*.jpg",
        f"data/{character_name.lower()}/*.png",
    ]
    found = []
    for p in search_paths:
        found.extend(glob.glob(p))
        found = sorted(found, key=lambda x: os.path.getsize(x), reverse=True)
    return found[:max_images]

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY environment variable not set.[/bold red]")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="👨‍⚖️ Universal Biometric & Cinematic Video Judge (Outputs rigorous JSON report & scores)."
    )
    parser.add_argument("-v", "--video", required=True, help="Path to the generated MP4 video to evaluate.")
    parser.add_argument("-c", "--character", default=None, help="Optional character/subject name (auto-loads real photos from data/characters/<name>/).")
    parser.add_argument("-r", "--reference", action="append", default=[], help="Optional specific extra reference image paths.")
    parser.add_argument("-m", "--model", default="gemini-3.5-flash", help="Evaluation model to use (default: gemini-3.5-flash).")
    
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        console.print(f"[bold red]Error: Video file '{video_path}' does not exist.[/bold red]")
        sys.exit(1)

    ref_images = list(args.reference)
    if args.character:
        auto_imgs = resolve_character_images(args.character)
        for img in auto_imgs:
            if img not in ref_images:
                ref_images.append(img)

    console.print(f"\n👨‍⚖️ [bold cyan]INITIALIZING HOLLYWOOD TRIBUNAL FOR:[/bold cyan] {video_path.name}")
    char_label = args.character.upper() if args.character else "STANDALONE_QUALITY_AUDIT"
    console.print(f"👤 Character Target: [bold magenta]{char_label}[/bold magenta]")
    console.print(f"📸 Loaded Authentic Biometric Reference Photos: [green]{ref_images}[/green]")

    client = genai.Client(api_key=api_key)

    console.print(f"📡 Uploading video asset to Google Servers...")
    video_file = client.files.upload(file=str(video_path))
    while video_file.state.name == "PROCESSING":
        console.print("[dim]⏳ Waiting for video ingest on Google servers...[/dim]")
        time.sleep(3)
        video_file = client.files.get(name=video_file.name)
    console.print("✅ Video uploaded and ready for evaluation.")

    uploaded_contents = [video_file]
    for img_path in ref_images:
        if os.path.exists(img_path):
            img_file = client.files.upload(file=img_path)
            uploaded_contents.append(img_file)

    prompt = f"""
    You are an unsparing, elite Hollywood forensic visual quality and biometric character consistency judge.
    We are testing whether an AI-generated video faithfully portrays {args.character} by rigorously comparing the video against his authentic real-life reference photographs.
    
    CRITICAL BIOMETRIC INSTRUCTION:
    Do NOT give high resemblance scores simply because the character looks happy, charming, or well-lighted! You must scrutinize facial bones, eye spacing, nose bridge, lip curves, and expressions against the original reference pictures. If the child/character in the video looks like a generic AI doll or a stylized substitute rather than the authentic person in the reference photos, you MUST harshly penalize the score in the 'character_consistencies' list (giving scores between 3.0 and 6.0 out of 10).
    
    Evaluate two crucial dimensions:
    1. Video Quality (smooth cinematic movement, lighting, zero flickering/morphing/unnatural AI painterly artifacts).
    2. Biometric Consistency per detected character via the 'character_consistencies' list of objects.
    
    Be brutally candid and honest: anticipate whether the user will say this is a triumph ("KEEP (CAPOLAVORO)") or if it degrades into AI stereotypes ("TRASH / QUARANTINE (FA CAGARE)").
    
    Provide your forensic audit strictly matching the required JSON schema.
    """
    uploaded_contents.append(prompt)

    console.print(f"🧠 Running deep cinematic & biometric audit with model: [yellow]{args.model}[/yellow]...")
    try:
        response = client.models.generate_content(
            model=args.model,
            contents=uploaded_contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VideoAuditReport,
                temperature=0.2,
            )
        )
        result = response.text.strip()
        parsed_json = json.loads(result)
    except Exception as e:
        console.print(f"[bold red]Evaluation failed with {args.model}: {e}[/bold red]")
        console.print("[cyan]Trying emergency fallback to gemini-3.5-flash-lite...[/cyan]")
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=uploaded_contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VideoAuditReport,
                temperature=0.2,
            )
        )
        parsed_json = json.loads(response.text.strip())

    report = VideoAuditReport(**parsed_json)
    
    report_file = video_path.parent / f"{video_path.stem}_biometric_audit.json"
    audit_data = {
        "target_asset_path": to_tilde_path(video_path),
        "source_reference_paths": [to_tilde_path(p) for p in ref_images],
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    dump = report.model_dump()
    # Format character_consistencies into clean mapped dictionary for user requirements
    dump["character_consistencies"] = {item["subject"].lower(): str(item["resemblance_score"]) for item in dump["character_consistencies"]}
    audit_data.update(dump)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)

    console.print("\n==========================================================================")
    console.print(f"🏆 [bold yellow]BIOMETRIC & CINEMATIC VERDICT FOR: {report.character_name.upper()}[/bold yellow]")
    console.print("==========================================================================")
    console.print(f"🎬 Video Quality Score       : [bold cyan]{report.video_quality_score}/10[/bold cyan]")
    for item in report.character_consistencies:
        console.print(f"🧬 Consistency ({item.subject:<12})  : [bold magenta]{item.resemblance_score}/10.0[/bold magenta] -> [dim]{item.observations}[/dim]")
    console.print(f"👑 Overall Total Score       : [bold yellow]{report.overall_score}/10[/bold yellow]")
    if "KEEP" in report.verdict.upper():
        console.print(f"🔥 FINAL VERDICT             : [bold green]{report.verdict}[/bold green]")
    else:
        console.print(f"🗑️ FINAL VERDICT             : [bold red]{report.verdict}[/bold red]")
    console.print("==========================================================================")
    console.print(f"🔍 [bold]Expert Forensic Critique:[/bold]\n{report.expert_critique}\n")
    console.print(f"➡️ [bold green]Recommended Action:[/bold green]\n{report.actionable_next_step}")
    console.print("==========================================================================\n")
    console.print(f"📁 Complete JSON structured audit saved to: [blue]{report_file}[/blue]")

if __name__ == "__main__":
    main()

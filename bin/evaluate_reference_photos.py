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
import glob
import argparse
import datetime
from pathlib import Path
from PIL import Image as PILImage
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from google import genai
from google.genai import types

console = Console()

class SingleReferenceEval(BaseModel):
    photo_filename: str = Field(description="Filename of the photo being evaluated.")
    resemblance_score: float = Field(description="Biometric consistency score (1.0 to 10.0) of this photo compared to the other N-1 reference photos.")
    image_quality_score: int = Field(description="Lighting, resolution, and facial clarity score (1 to 10).")
    is_golden_reference: bool = Field(description="True if this is an exceptional high-fidelity reference photo (score >= 7.5).")
    verdict: str = Field(description="GOLDEN_KEEP / ACCEPTABLE / PRUNE_BAD_ANGLE")
    critique: str = Field(description="Detailed forensic explanation of why this photo matches or deviates from the character's consensus features.")
    recommendation: str = Field(description="Actionable advice: KEEP as primary anchor, USE as secondary, or PRUNE from reference directory.")

class DatasetEvalReport(BaseModel):
    character_name: str = Field(description="Name of the character evaluated.")
    total_photos_evaluated: int = Field(description="Total number of photos in the dataset.")
    evaluation_timestamp: str = Field(description="ISO 8601 timestamp.")
    photo_evaluations: list[SingleReferenceEval] = Field(description="Individual leave-one-out evaluations for each photo.")
    golden_photos: list[str] = Field(description="Filenames of top-tier golden reference photos recommended for GenAI pipelines.")
    prune_photos: list[str] = Field(description="Filenames of low-scoring or misleading photos recommended to be removed.")
    executive_summary: str = Field(description="High-level summary of the reference photo dataset quality.")

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
    valid_exts = {".png", ".jpg", ".jpeg", ".webp", ".JPG", ".PNG"}
    return [str(p) for p in char_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]

def resolve_folder_images(folder_path: str) -> list[str]:
    p = Path(folder_path).expanduser().resolve()
    if not p.exists() or not p.is_dir():
        return []
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    return [str(f) for f in p.iterdir() if f.suffix.lower() in valid_exts]

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY environment variable not set.[/bold red]")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="🔬 Universal Leave-One-Out (LOO) Reference Photo Quality Evaluator."
    )
    parser.add_argument(
        "-c", "--character",
        default=None,
        help="Character name (e.g. kate, alessandro, sebastian, riccardo)"
    )
    parser.add_argument(
        "-d", "--dir",
        default=None,
        help="Custom folder path containing reference photos to evaluate (e.g. ~/Desktop/kate/)"
    )
    parser.add_argument(
        "--desc",
        default=None,
        help="Ground-truth text description (e.g. 'Blonde woman born in 1981, ~45 years old, blue eyes, warm natural smile')"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="out",
        help="Directory to store evaluation results (default: out)"
    )

    args = parser.parse_args()
    
    if args.dir:
        photos = resolve_folder_images(args.dir)
        char_name = Path(args.dir).name if not args.character else args.character.lower().strip()
    elif args.character:
        char_name = args.character.lower().strip()
        photos = resolve_character_images(char_name)
    else:
        console.print("[bold red]Error: Please specify either -c <character_name> or -d <folder_path>[/bold red]")
        sys.exit(1)

    if not photos:
        console.print(f"[bold red]Error: No photos found in target directory.[/bold red]")
        sys.exit(1)

    desc_info = f"📝 Description Context: '{args.desc}'\n" if args.desc else ""

    console.print(Panel.fit(
        f"[bold cyan]🔬 LEAVE-ONE-OUT REFERENCE EVALUATOR FOR: {char_name.upper()}[/bold cyan]\n"
        f"📸 Total Reference Photos Found: [green]{len(photos)}[/green]\n"
        f"{desc_info}"
        f"🎯 Strategy: Testing each photo i against the remaining N-1 photos + ground truth text.",
        title="🤖 AI Biometric Cross-Validation Judge"
    ))

    client = genai.Client(api_key=api_key)
    eval_results: list[SingleReferenceEval] = []

    for idx, candidate_path in enumerate(photos, 1):
        filename = Path(candidate_path).name
        other_photos = [p for p in photos if p != candidate_path]

        console.print(f"\n🧪 [bold yellow]Evaluating Photo {idx}/{len(photos)}:[/bold yellow] [bold white]{filename}[/bold white]")

        # Prepare payload: Candidate image first, then N-1 reference images, then prompt
        payload = []

        # Load candidate
        try:
            cand_img = PILImage.open(candidate_path)
            if cand_img.mode != "RGB":
                cand_img = cand_img.convert("RGB")
            payload.append(cand_img)
        except Exception as e:
            console.print(f"[bold red]Failed to load candidate {filename}: {e}[/bold red]")
            continue

        # Load reference set (max 5 for context efficiency)
        ref_count = 0
        for ref_path in other_photos[:5]:
            try:
                ref_img = PILImage.open(ref_path)
                if ref_img.mode != "RGB":
                    ref_img = ref_img.convert("RGB")
                payload.append(ref_img)
                ref_count += 1
            except Exception as e:
                pass

        desc_prompt_part = f"\n- GROUND TRUTH CHARACTER DESCRIPTION: '{args.desc}'\n" if args.desc else ""

        prompt = f"""
You are a Principal Biometric & Photographic Quality Judge.
You are inspecting a reference photo dataset for the person '{char_name.upper()}'.

- The FIRST image provided is the CANDIDATE PHOTO UNDER TEST: '{filename}'.
- The SUBSEQUENT {ref_count} images are the GROUND TRUTH REFERENCE SET for '{char_name.upper()}'.{desc_prompt_part}

YOUR TASK:
Perform a forensic Leave-One-Out (LOO) cross-validation evaluation on the CANDIDATE PHOTO:
1. Resemblance & Facial Consistency (1.0 to 10.0): Does this candidate photo clearly show the SAME real person as described and shown in the reference set? Is the angle, expression, lighting, or resolution misleading?
2. Image Quality (1 to 10): Is the photo sharp, clear, well-lit, and suitable as an AI reference anchor?
3. Verdict:
   - 'GOLDEN_KEEP': High biometric fidelity (score >= 7.5), excellent anchor for GenAI synthesis.
   - 'ACCEPTABLE': Good secondary photo (score 6.0 - 7.4).
   - 'PRUNE_BAD_ANGLE': Outlier, blurry, bad lighting, or misleading angle (score < 6.0) that would degrade AI synthesis.

Provide detailed, rigorous critique and concrete recommendations.
"""
        payload.append(prompt)

        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=payload,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SingleReferenceEval,
                    temperature=0.2,
                )
            )

            eval_item: SingleReferenceEval = SingleReferenceEval.model_validate_json(response.text)
            eval_item.photo_filename = filename
            eval_results.append(eval_item)

            color = "green" if eval_item.resemblance_score >= 7.5 else ("yellow" if eval_item.resemblance_score >= 6.0 else "red")
            console.print(f"  🧬 Likeness Score: [{color}]{eval_item.resemblance_score}/10.0[/{color}] | Verdict: [bold]{eval_item.verdict}[/bold]")
            console.print(f"  💬 Critique: [italic]{eval_item.critique}[/italic]")

        except Exception as e:
            console.print(f"[bold red]Evaluation failed for {filename}: {e}[/bold red]")

    # Build Summary Table
    table = Table(title=f"🏆 Leave-One-Out Reference Leaderboard for {char_name.upper()}", show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="dim", width=6)
    table.add_column("Photo Filename", style="bold white")
    table.add_column("Likeness Score", justify="right")
    table.add_column("Quality Score", justify="right")
    table.add_column("Verdict", style="bold")
    table.add_column("Recommendation")

    # Sort results by score descending
    eval_results.sort(key=lambda x: x.resemblance_score, reverse=True)

    golden_list = []
    prune_list = []

    for rank, item in enumerate(eval_results, 1):
        if item.resemblance_score >= 7.5:
            golden_list.append(item.photo_filename)
            v_color = "[bold green]GOLDEN_KEEP[/bold green]"
        elif item.resemblance_score >= 6.0:
            v_color = "[yellow]ACCEPTABLE[/yellow]"
        else:
            prune_list.append(item.photo_filename)
            v_color = "[bold red]PRUNE_BAD_ANGLE[/bold red]"

        score_str = f"{item.resemblance_score:.1f}/10"
        table.add_row(
            str(rank),
            item.photo_filename,
            score_str,
            f"{item.image_quality_score}/10",
            v_color,
            item.recommendation
        )

    console.print("\n")
    console.print(table)

    # Prepare Report Metadata
    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True)
    json_path = out_dir / f"{char_name}_reference_photos_eval.json"
    md_path = out_dir / f"{char_name}_reference_photos_eval.md"

    summary_text = f"Evaluated {len(eval_results)} reference photos for '{char_name.upper()}'. Found {len(golden_list)} GOLDEN anchors and {len(prune_list)} photos recommended for pruning."

    report = DatasetEvalReport(
        character_name=char_name,
        total_photos_evaluated=len(eval_results),
        evaluation_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        photo_evaluations=eval_results,
        golden_photos=golden_list,
        prune_photos=prune_list,
        executive_summary=summary_text
    )

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(report.model_dump(), jf, indent=2, ensure_ascii=False)

    # Write Markdown Report
    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write(f"# 🔬 Reference Photo Evaluation Report: {char_name.upper()}\n\n")
        mf.write(f"**Timestamp**: `{report.evaluation_timestamp}`  \n")
        mf.write(f"**Total Photos Evaluated**: `{report.total_photos_evaluated}`  \n")
        mf.write(f"**Golden Anchors (>= 7.5)**: `{len(golden_list)}`  \n")
        mf.write(f"**Prune Candidates (< 6.0)**: `{len(prune_list)}`  \n\n")
        mf.write("## 🏆 Reference Photo Leaderboard\n\n")
        mf.write("| Rank | Photo Filename | Likeness Score | Quality Score | Verdict | Critique & Recommendation |\n")
        mf.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for rank, item in enumerate(eval_results, 1):
            mf.write(f"| {rank} | `{item.photo_filename}` | **{item.resemblance_score:.1f}/10** | {item.image_quality_score}/10 | `{item.verdict}` | {item.critique} *Rec: {item.recommendation}* |\n")

    console.print(f"\n📊 Evaluation JSON saved to: [green]{json_path}[/green]")
    console.print(f"📝 Evaluation Markdown saved to: [green]{md_path}[/green]")

if __name__ == "__main__":
    main()

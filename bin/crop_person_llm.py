#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "google-genai>=0.1.1",
#   "pillow>=10.0.0",
#   "pydantic>=2.0.0",
#   "rich>=13.0.0"
# ]
# ///

import os
import sys
import argparse
import subprocess
from pathlib import Path
from PIL import Image
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class BoundingBox(BaseModel):
    box_2d: list[int] = Field(description="Normalized bounding box [ymin, xmin, ymax, xmax] from 0 to 1000")
    label: str = Field(description="Name of the detected person")
    confidence_explanation: str = Field(description="Explanation of visual feature match against reference photos")

class BoundingBoxResult(BaseModel):
    target_found: bool = Field(description="True if the target person in reference photos is present in target image")
    bounding_box: BoundingBox | None = Field(default=None, description="2D bounding box if target found")

class VerificationResult(BaseModel):
    is_correct_person: bool = Field(description="True if the cropped photo contains ONLY the target person from reference photos")
    other_people_visible: bool = Field(description="True if other people's faces or bodies are visibly present in crop")
    likeness_score: float = Field(description="Similarity score 0.0-10.0 comparing cropped face to reference photos")
    feedback: str = Field(description="Actionable critique of the crop")

def get_bounding_box(client: genai.Client, reference_paths: list[Path], target_path: Path, person_name: str) -> BoundingBoxResult:
    """Uses Gemini 2D spatial grounding to find target person in target image."""
    contents = []
    
    # 1. Attach reference images of person alone
    for idx, ref_p in enumerate(reference_paths):
        ref_img = Image.open(ref_p)
        contents.append(f"Reference Image {chr(65+idx)} (Subject '{person_name}' alone):")
        contents.append(ref_img)
        
    # 2. Attach target group image
    target_img = Image.open(target_path)
    contents.append("Target Image to search and crop:")
    contents.append(target_img)
    
    prompt = f"""
Look at the Reference Image(s) showing '{person_name}' alone.
Now locate '{person_name}' in the Target Image.
Return the normalized 2D bounding box [ymin, xmin, ymax, xmax] on a scale of 0 to 1000 for '{person_name}' in the Target Image.
Isolate ONLY '{person_name}', excluding any adjacent individuals or background people.
    """
    contents.append(prompt)
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BoundingBoxResult,
            temperature=0.1
        )
    )
    
    return BoundingBoxResult.model_validate_json(response.text)

def crop_image_with_padding(image_path: Path, box_2d: list[int], output_path: Path, padding_pct: float = 0.12):
    """Crops PIL image using 0-1000 normalized bounding box with configurable padding."""
    img = Image.open(image_path)
    width, height = img.size
    
    ymin_norm, xmin_norm, ymax_norm, xmax_norm = box_2d
    
    # Convert normalized (0-1000) to pixel coordinates
    ymin = int((ymin_norm / 1000.0) * height)
    xmin = int((xmin_norm / 1000.0) * width)
    ymax = int((ymax_norm / 1000.0) * height)
    xmax = int((xmax_norm / 1000.0) * width)
    
    # Calculate box width/height and padding
    box_w = xmax - xmin
    box_h = ymax - ymin
    
    pad_w = int(box_w * padding_pct)
    pad_h = int(box_h * padding_pct)
    
    crop_xmin = max(0, xmin - pad_w)
    crop_ymin = max(0, ymin - pad_h)
    crop_xmax = min(width, xmax + pad_w)
    crop_ymax = min(height, ymax + pad_h)
    
    cropped_img = img.crop((crop_xmin, crop_ymin, crop_xmax, crop_ymax))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cropped_img.save(output_path, quality=95)
    return cropped_img

def verify_cropped_identity(client: genai.Client, reference_paths: list[Path], cropped_path: Path, person_name: str) -> VerificationResult:
    """Verifies cropped photo using gemini-3.5-flash."""
    contents = []
    for idx, ref_p in enumerate(reference_paths):
        contents.append(f"Reference Image {chr(65+idx)}:")
        contents.append(Image.open(ref_p))
        
    contents.append("Cropped Image to Audit:")
    contents.append(Image.open(cropped_path))
    
    prompt = f"""
Audit this cropped photo against the Reference Image(s) of '{person_name}'.
Verify:
1. Is this cropped person '{person_name}'?
2. Are there any OTHER people's faces or bodies intruding into this crop?
3. Likeness score (0.0 to 10.0).
    """
    contents.append(prompt)
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VerificationResult,
            temperature=0.1
        )
    )
    return VerificationResult.model_validate_json(response.text)

def main():
    parser = argparse.ArgumentParser(description="LLM-Driven Person Bounding Box Isolator & Cropper")
    parser.add_argument("-r", "--reference", action="append", help="Reference photo(s) of subject alone")
    parser.add_argument("-t", "--target", help="Target photo or directory containing group photos")
    parser.add_argument("-c", "--character", default="kate2016", help="Character name (default: kate2016)")
    parser.add_argument("-o", "--output-dir", help="Output directory for cropped photos")
    parser.add_argument("-p", "--padding", type=float, default=0.12, help="Padding percentage (default: 0.12)")
    parser.add_argument("--sync-gcs", action="store_true", help="Automatically rsync cropped images to GCS vault")
    
    args = parser.parse_args()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]Error: GEMINI_API_KEY environment variable is not set.[/bold red]")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    # 1. Resolve reference images
    ref_paths = []
    if args.reference:
        ref_paths = [Path(p) for p in args.reference]
    else:
        # Fallback to default character anchor photos
        default_anchor = Path(f"data/characters/kate/kate_golden_wine_anchor.png")
        if default_anchor.exists():
            ref_paths.append(default_anchor)
            
    if not ref_paths:
        console.print("[bold red]Error: No reference anchor photos found.[/bold red]")
        sys.exit(1)
        
    # 2. Resolve target images
    target_files = []
    if args.target:
        t_path = Path(args.target)
        if t_path.is_file():
            target_files.append(t_path)
        elif t_path.is_dir():
            target_files = list(t_path.glob("*.jpg")) + list(t_path.glob("*.JPG")) + list(t_path.glob("*.png"))
    else:
        char_dir = Path(f"data/characters/{args.character}")
        if char_dir.exists():
            target_files = [p for p in char_dir.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png"] and not p.name.startswith(".")]
            
    if not target_files:
        console.print(f"[bold red]Error: No target images found for processing.[/bold red]")
        sys.exit(1)
        
    output_dir = Path(args.output_dir) if args.output_dir else Path(f"data/characters/{args.character}/cleaned")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(Panel(f"[bold cyan]LLM Person Bounding Box Cropper[/bold cyan]\nCharacter: [yellow]{args.character}[/yellow] | References: [green]{len(ref_paths)}[/green] | Targets: [green]{len(target_files)}[/green]"))
    
    summary_table = Table("Target Image", "Status", "Box [ymin, xmin, ymax, xmax]", "LLM Likeness", "Cropped File")
    
    for t_file in target_files:
        console.print(f"🔍 Detecting 2D spatial bounding box for [yellow]{t_file.name}[/yellow]...")
        try:
            bbox_res = get_bounding_box(client, ref_paths, t_file, args.character)
            if bbox_res.target_found and bbox_res.bounding_box:
                box = bbox_res.bounding_box.box_2d
                out_path = output_dir / f"crop_{t_file.name}"
                crop_image_with_padding(t_file, box, out_path, args.padding)
                
                # Verify crop with LLM-as-a-Judge
                audit_res = verify_cropped_identity(client, ref_paths, out_path, args.character)
                
                status_str = "[bold green]ISOLATED[/bold green]" if (audit_res.is_correct_person and not audit_res.other_people_visible) else "[yellow]PARTIAL[/yellow]"
                summary_table.add_row(t_file.name, status_str, str(box), f"{audit_res.likeness_score:.1f}/10", str(out_path))
            else:
                summary_table.add_row(t_file.name, "[red]NOT FOUND[/red]", "-", "-", "-")
        except Exception as e:
            console.print(f"[bold red]Failed to process {t_file.name}: {e}[/bold red]")
            summary_table.add_row(t_file.name, "[red]ERROR[/red]", "-", "-", str(e))
            
    console.print(summary_table)
    
    if args.sync_gcs:
        gcs_bucket = f"gs://ricc-family-character-vault-pvt/{args.character}/"
        console.print(f"☁️ Syncing cleaned cropped images to GCS: [bold cyan]{gcs_bucket}[/bold cyan]...")
        subprocess.run(["gcloud", "storage", "rsync", str(output_dir), gcs_bucket], check=True)
        console.print("[bold green]✅ GCS rsync complete![/bold green]")

if __name__ == "__main__":
    main()

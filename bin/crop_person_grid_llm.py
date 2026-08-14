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
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class GridCropResult(BaseModel):
    success: bool = Field(description="True if target person is found and isolated successfully")
    target_label: str = Field(description="Label of target person (e.g. 'Bride Kate')")
    grid_xmin: int = Field(description="Column index (0 to 9) for left edge of target person")
    grid_xmax: int = Field(description="Column index (0 to 9) for right edge of target person")
    grid_ymin: int = Field(description="Row index (0 to 9) for top edge of target person")
    grid_ymax: int = Field(description="Row index (0 to 9) for bottom edge of target person")
    explanation: str = Field(description="Explanation of why this grid cell range isolates ONLY target person")

def draw_grid_overlay(image_path: Path, grid_size: int = 10, color: str = "#00FF00") -> Image.Image:
    """Draws a crisp numbered N x N grid overlay on a copy of the image."""
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    cell_w = w / grid_size
    cell_h = h / grid_size
    
    # Try loading default font or PIL basic font
    try:
        font = ImageFont.truetype("Arial.ttf", int(min(cell_w, cell_h) * 0.25))
    except Exception:
        font = ImageFont.load_default()
        
    # Draw vertical & horizontal grid lines
    for i in range(1, grid_size):
        # Vertical line
        x = int(i * cell_w)
        draw.line([(x, 0), (x, h)], fill=color, width=2)
        # Horizontal line
        y = int(i * cell_h)
        draw.line([(0, y), (w, y)], fill=color, width=2)
        
    # Add column & row coordinate labels
    for r in range(grid_size):
        for c in range(grid_size):
            cx = int(c * cell_w + 4)
            cy = int(r * cell_h + 4)
            label = f"({c},{r})"
            draw.text((cx, cy), label, fill=color, font=font)
            
    return img

def get_grid_crop_coordinates(client: genai.Client, reference_paths: list[Path], gridded_img: Image.Image, person_name: str, grid_size: int = 10) -> GridCropResult:
    """Queries Gemini 3.5 Flash with gridded visual overlay to return grid cell bounding coordinates."""
    contents = []
    for idx, ref_p in enumerate(reference_paths):
        contents.append(f"Reference Image {chr(65+idx)} (Subject '{person_name}' alone):")
        contents.append(Image.open(ref_p))
        
    contents.append("Target Image with 10x10 Green Grid Overlay (Columns X: 0..9, Rows Y: 0..9):")
    contents.append(gridded_img)
    
    prompt = f"""
Analyze the Reference Image(s) showing '{person_name}' (the blonde bride in white wedding dress).
Now look at the Target Image which has a 10x10 green grid overlay (X columns 0 to 9 left-to-right, Y rows 0 to 9 top-to-bottom).

INSTRUCTIONS:
1. Locate '{person_name}' (the blonde bride) in the Target Image.
2. Determine the minimum and maximum grid cell coordinates [grid_xmin, grid_xmax, grid_ymin, grid_ymax] (0 to 9) framing her head, hair, and upper body.
3. EXCLUDE adjacent people, groom, or husband. Frame ONLY '{person_name}'.
    """
    contents.append(prompt)
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GridCropResult,
            temperature=0.1
        )
    )
    return GridCropResult.model_validate_json(response.text)

def crop_original_by_grid(original_path: Path, grid_res: GridCropResult, output_path: Path, grid_size: int = 10):
    """Crops ungridded original image using grid coordinates."""
    img = Image.open(original_path)
    w, h = img.size
    
    cell_w = w / float(grid_size)
    cell_h = h / float(grid_size)
    
    xmin_px = max(0, int(grid_res.grid_xmin * cell_w))
    xmax_px = min(w, int((grid_res.grid_xmax + 1) * cell_w))
    ymin_px = max(0, int(grid_res.grid_ymin * cell_h))
    ymax_px = min(h, int((grid_res.grid_ymax + 1) * cell_h))
    
    cropped_img = img.crop((xmin_px, ymin_px, xmax_px, ymax_px))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cropped_img.save(output_path, quality=95)
    return cropped_img

def main():
    parser = argparse.ArgumentParser(description="Deterministic 10x10 Grid Overlay LLM Person Isolator & Cropper")
    parser.add_argument("-r", "--reference", action="append", help="Reference photo(s) of subject alone")
    parser.add_argument("-t", "--target", help="Target photo or directory containing group photos")
    parser.add_argument("-c", "--character", default="kate2016", help="Character name (default: kate2016)")
    parser.add_argument("-o", "--output-dir", help="Output directory for cropped photos")
    parser.add_argument("-g", "--grid-size", type=int, default=10, help="Grid size N x N (default: 10)")
    
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
        wedding_anchor = Path("data/characters/kate2016/kate2016  DSC06755.jpg")
        if wedding_anchor.exists():
            ref_paths.append(wedding_anchor)
        else:
            default_anchor = Path("data/characters/kate/kate_golden_wine_anchor.png")
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
            target_files = [p for p in t_path.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png"] and not p.name.startswith(".")]
    else:
        char_dir = Path(f"data/characters/{args.character}")
        if char_dir.exists():
            target_files = [p for p in char_dir.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png"] and not p.name.startswith(".")]
            
    if not target_files:
        console.print(f"[bold red]Error: No target images found for processing.[/bold red]")
        sys.exit(1)
        
    output_dir = Path(args.output_dir) if args.output_dir else Path(f"data/characters/{args.character}/grid_cleaned")
    validation_dir = Path(f"data/characters/{args.character}/grid_validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(Panel(f"[bold green]🟩 Deterministic 10x10 Grid Overlay LLM Cropper[/bold green]\nCharacter: [yellow]{args.character}[/yellow] | References: [green]{len(ref_paths)}[/green] | Targets: [green]{len(target_files)}[/green]"))
    
    summary_table = Table("Target Image", "Status", "Grid X [min..max]", "Grid Y [min..max]", "Validation Triplet Folder")
    
    for t_file in target_files:
        console.print(f"📐 Drawing 10x10 Grid Overlay & Querying LLM for [yellow]{t_file.name}[/yellow]...")
        try:
            gridded_img = draw_grid_overlay(t_file, grid_size=args.grid_size, color="#00FF00")
            grid_res = get_grid_crop_coordinates(client, ref_paths, gridded_img, args.character, grid_size=args.grid_size)
            
            if grid_res.success:
                out_path = output_dir / f"grid_crop_{t_file.name}"
                crop_original_by_grid(t_file, grid_res, out_path, grid_size=args.grid_size)
                
                # Create per-photo triplet validation folder
                stem = t_file.stem.strip()
                item_val_dir = validation_dir / stem
                item_val_dir.mkdir(parents=True, exist_ok=True)
                
                # Save 1_original.jpg, 2_gridded.jpg, 3_cropped.jpg
                Image.open(t_file).save(item_val_dir / "1_original.jpg")
                gridded_img.save(item_val_dir / "2_gridded.jpg")
                crop_original_by_grid(t_file, grid_res, item_val_dir / "3_cropped.jpg", grid_size=args.grid_size)
                
                summary_table.add_row(t_file.name, "[bold green]SUCCESS[/bold green]", f"X: {grid_res.grid_xmin}..{grid_res.grid_xmax}", f"Y: {grid_res.grid_ymin}..{grid_res.grid_ymax}", str(item_val_dir))
            else:
                summary_table.add_row(t_file.name, "[red]FAILED[/red]", "-", "-", "-")
        except Exception as e:
            console.print(f"[bold red]Failed to process {t_file.name}: {e}[/bold red]")
            summary_table.add_row(t_file.name, "[red]ERROR[/red]", "-", "-", str(e))
            
    console.print(summary_table)
    
    # Open validation directory in Finder
    console.print(f"📂 Opening validation folder in Finder: [bold cyan]{validation_dir}[/bold cyan]...")
    subprocess.run(["open", str(validation_dir)])

if __name__ == "__main__":
    main()

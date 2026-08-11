#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pillow",
#     "rich",
# ]
# ///

import os
import sys
import argparse
from pathlib import Path
from PIL import Image
from rich.console import Console

console = Console()

def slice_comic_grid(image_path: Path, rows: int, cols: int, output_dir: Path) -> list[Path]:
    """Slices a grid comic strip into individual panel images."""
    if not image_path.exists():
        console.print(f"[bold red]Error: Image '{image_path}' does not exist.[/bold red]")
        sys.exit(1)

    img = Image.open(image_path)
    total_w, total_h = img.size
    
    panel_w = total_w // cols
    panel_h = total_h // rows

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_panels = []

    console.print(f"✂️ [bold cyan]Slicing Comic Grid ({rows}x{cols}):[/bold cyan] {image_path.name} ({total_w}x{total_h}px)")

    panel_idx = 1
    for r in range(rows):
        for c in range(cols):
            left = c * panel_w
            top = r * panel_h
            right = (c + 1) * panel_w if c < cols - 1 else total_w
            bottom = (r + 1) * panel_h if r < rows - 1 else total_h

            crop_box = (left, top, right, bottom)
            panel_img = img.crop(crop_box)
            
            panel_file = output_dir / f"panel_{panel_idx:02d}.png"
            panel_img.save(panel_file)
            generated_panels.append(panel_file)
            console.print(f"  📸 Panel {panel_idx:02d}: [green]{panel_file}[/green] ({right-left}x{bottom-top}px)")
            panel_idx += 1

    console.print(f"✅ [bold green]Successfully sliced {len(generated_panels)} panels to:[/bold green] [blue]{output_dir}[/blue]")
    return generated_panels

def main():
    parser = argparse.ArgumentParser(
        description="✂️ Universal Comic Strip Panel Slicer (Grid Crop Utility)."
    )
    parser.add_argument(
        "-i", "--image",
        required=True,
        help="Path to the comic strip image file."
    )
    parser.add_argument(
        "-r", "--rows",
        type=int,
        default=2,
        help="Number of horizontal rows in the grid (default: 2)."
    )
    parser.add_argument(
        "-c", "--cols",
        type=int,
        default=3,
        help="Number of vertical columns in the grid (default: 3)."
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Output directory for sliced panel files (default: out/<strip_stem>_panels/)."
    )

    args = parser.parse_args()

    img_path = Path(args.image)
    if args.output_dir:
        out_dir = Path(args.output_dir)
    else:
        out_dir = Path("out") / f"{img_path.stem}_panels"

    slice_comic_grid(img_path, args.rows, args.cols, out_dir)

if __name__ == "__main__":
    main()

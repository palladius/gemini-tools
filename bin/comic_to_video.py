#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai",
#     "pillow",
#     "rich",
# ]
# ///

import os
import sys
import argparse
import glob
import time
import json
import subprocess
from pathlib import Path
from PIL import Image as PILImage
from rich.console import Console
from google import genai
from google.genai import types

console = Console()

def to_tilde_path(p: str | Path) -> str:
    res = str(Path(p).resolve())
    home = str(Path.home())
    if res.startswith(home):
        return "~" + res[len(home):]
    return res

def concatenate_videos(video_paths: list[Path], output_movie: Path) -> bool:
    """Stitches multiple scene videos into a single final movie using ffmpeg."""
    if not video_paths:
        return False
    
    # Check if ffmpeg is available
    if not subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0:
        console.print("[yellow]⚠️ Warning: 'ffmpeg' not found on system. Skipping video concatenation.[/yellow]")
        return False

    concat_file = output_movie.parent / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for vp in video_paths:
            f.write(f"file '{vp.resolve()}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_movie)
    ]
    
    console.print(f"🎬 [bold cyan]Stitching {len(video_paths)} scenes into full movie with ffmpeg...[/bold cyan]")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and output_movie.exists():
        console.print(f"✅ [bold green]Full movie created successfully:[/bold green] [blue]{to_tilde_path(output_movie)}[/blue]")
        return True
    else:
        # Fallback to re-encoding if stream copy fails
        cmd_reencode = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(output_movie)
        ]
        res2 = subprocess.run(cmd_reencode, capture_output=True, text=True)
        if res2.returncode == 0 and output_movie.exists():
            console.print(f"✅ [bold green]Full movie re-encoded & created successfully:[/bold green] [blue]{to_tilde_path(output_movie)}[/blue]")
            return True
        console.print(f"[bold red]ffmpeg concatenation failed: {res.stderr or res2.stderr}[/bold red]")
        return False

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY environment variable not set.[/bold red]")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="🎨 Multi-Scene Comic Strip Video Orchestrator (Slices panels, generates scenes via Veo, & stitches with ffmpeg)."
    )
    parser.add_argument(
        "-i", "--comic-strip",
        help="Path to full grid comic strip PNG image."
    )
    parser.add_argument(
        "-d", "--panels-dir",
        help="Directory containing pre-sliced panel PNG images (panel_01.png, panel_02.png, ...)."
    )
    parser.add_argument(
        "-r", "--rows", type=int, default=2,
        help="Grid rows (default: 2)."
    )
    parser.add_argument(
        "-c", "--cols", type=int, default=3,
        help="Grid columns (default: 3)."
    )
    parser.add_argument(
        "-p", "--prompt", default="Cinematic animation brought to life from this comic panel.",
        help="Base prompt / cinematic directive for panel animation."
    )
    parser.add_argument(
        "--character", default=None,
        help="Optional character name for biometric verification."
    )
    parser.add_argument(
        "-m", "--model", default="veo-2.0-generate-001",
        help="Veo / Omni video model to use (default: veo-2.0-generate-001)."
    )
    parser.add_argument(
        "-o", "--output-dir", default=None,
        help="Output directory for generated scenes & final stitched movie."
    )

    args = parser.parse_args()

    if not args.comic_strip and not args.panels-dir:
        console.print("[bold red]Error: Specify either --comic-strip <file> or --panels-dir <directory>[/bold red]")
        sys.exit(1)

    # 1. Determine or slice panels
    panel_files = []
    if args.panels_dir:
        pdir = Path(args.panels_dir)
        panel_files = sorted(list(pdir.glob("*.png")) + list(pdir.glob("*.jpg")))
        out_dir = Path(args.output_dir) if args.output_dir else pdir / "video_scenes"
    else:
        strip_path = Path(args.comic_strip)
        out_dir = Path(args.output_dir) if args.output_dir else Path("out") / f"{strip_path.stem}_movie"
        panels_output_dir = out_dir / "panels"
        
        # Import slice utility dynamically
        sys.path.insert(0, str(Path(__file__).parent))
        from slice_comic import slice_comic_grid
        panel_files = slice_comic_grid(strip_path, args.rows, args.cols, panels_output_dir)

    if not panel_files:
        console.print("[bold red]Error: No panel images found to animate.[/bold red]")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"\n🚀 [bold magenta]Starting Comic-to-Video Orchestration for {len(panel_files)} panels...[/bold magenta]")
    
    client = genai.Client(api_key=api_key)
    scene_videos = []

    # 2. Animate each panel
    for idx, pfile in enumerate(panel_files, 1):
        scene_output = out_dir / f"scene_{idx:02d}.mp4"
        console.print(f"\n🎥 [bold cyan]Processing Scene {idx}/{len(panel_files)}:[/bold cyan] {pfile.name}")

        scene_prompt = f"{args.prompt} Animate this comic panel realistically."
        
        try:
            # Check interaction endpoint vs models endpoint
            console.print(f"📡 Sending Veo request for panel {idx}...")
            img_input = PILImage.open(pfile)
            
            # Use interactions or generate_content based on model
            operation = client.models.generate_content(
                model=args.model,
                contents=[img_input, scene_prompt],
                config=types.GenerateContentConfig(response_modalities=["VIDEO"])
            )
            
            # Save output if inline video returned
            saved = False
            if operation.candidates and operation.candidates[0].content and operation.candidates[0].content.parts:
                for part in operation.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("video/"):
                        with open(scene_output, "wb") as vf:
                            vf.write(part.inline_data.data)
                        saved = True
                        break
            
            if saved:
                console.print(f"✅ Saved scene video to: [blue]{to_tilde_path(scene_output)}[/blue]")
                scene_videos.append(scene_output)
            else:
                console.print(f"[yellow]⚠️ Scene {idx} video generation completed without video bytes.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Scene {idx} failed: {e}[/bold red]")

    # 3. Concatenate scenes into final movie
    final_movie = out_dir / "full_comic_movie.mp4"
    if scene_videos:
        concatenate_videos(scene_videos, final_movie)

    # 4. Save Metadata
    meta_file = out_dir / "comic_video_orchestration.json"
    meta = {
        "comic_strip_source": to_tilde_path(args.comic_strip) if args.comic_strip else None,
        "panel_sources": [to_tilde_path(pf) for pf in panel_files],
        "generated_scene_videos": [to_tilde_path(sv) for sv in scene_videos],
        "final_movie_path": to_tilde_path(final_movie) if final_movie.exists() else None,
        "model_used": args.model,
        "prompt": args.prompt,
        "character": args.character,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(meta_file, "w", encoding="utf-8") as mf:
        json.dump(meta, mf, indent=2, ensure_ascii=False)
    console.print(f"📊 Orchestration metadata saved to: [blue]{to_tilde_path(meta_file)}[/blue]")

    # 5. Optional Biometric Audit
    if args.character and final_movie.exists():
        console.print(f"\n👨‍⚖️ [bold cyan]Launching Biometric Audit on final movie for character '{args.character}'...[/bold cyan]")
        subprocess.run([
            sys.executable, str(Path(__file__).parent / "judge_video.py"),
            "-v", str(final_movie),
            "-c", args.character
        ])

if __name__ == "__main__":
    main()

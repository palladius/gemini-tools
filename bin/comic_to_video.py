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
import base64
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
        "-C", "--character", default=None,
        help="Optional character name for biometric verification."
    )
    parser.add_argument(
        "-m", "--model", default="gemini-omni-flash-preview",
        help="Veo / Omni video model to use (default: gemini-omni-flash-preview)."
    )
    parser.add_argument(
        "-o", "--output-dir", default=None,
        help="Output directory for generated scenes & final stitched movie."
    )
    parser.add_argument(
        "--judge-per-scene", action="store_true", default=True,
        help="Run LLM-as-a-Judge audit on each individual scene video as soon as generated."
    )
    parser.add_argument(
        "--max-scene-retries", type=int, default=2,
        help="Max retries for individual scenes that fail quality/biometric audit (default: 2)."
    )

    args = parser.parse_args()

    if not args.comic_strip and not args.panels_dir:
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

    # 2. Animate each panel (with optional per-scene forensic judging and selective retry)
    for idx, pfile in enumerate(panel_files, 1):
        scene_output = out_dir / f"scene_{idx:02d}.mp4"
        console.print(f"\n🎥 [bold cyan]Processing Scene {idx}/{len(panel_files)}:[/bold cyan] {pfile.name}")

        attempt = 1
        max_attempts = args.max_scene_retries if hasattr(args, "max_scene_retries") else 2
        scene_passed = False
        scene_prompt = f"{args.prompt} Animate this comic panel realistically."

        while attempt <= max_attempts and not scene_passed:
            if attempt > 1:
                console.print(f"🔄 [bold yellow]Retrying Scene {idx} (Attempt {attempt}/{max_attempts})...[/bold yellow]")

            try:
                console.print(f"📡 Sending video request for panel {idx} via Interactions API ({args.model})...")
                with open(pfile, "rb") as pf_file:
                    b64_data = base64.b64encode(pf_file.read()).decode("utf-8")
                
                payload = [
                    {"type": "image", "data": b64_data, "mime_type": "image/png"},
                    {"type": "text", "text": scene_prompt}
                ]
                
                interaction = client.interactions.create(
                    model=args.model,
                    input=payload,
                    background=True
                )
                
                # Poll for completion
                start_time = time.time()
                while True:
                    status = interaction.status
                    if status == "completed":
                        break
                    elif status in ["failed", "canceled"]:
                        raise RuntimeError(f"Interaction failed with status: {status}")
                    time.sleep(4)
                    elapsed = int(time.time() - start_time)
                    console.print(f"  [scene {idx}] Status: {status}... ({elapsed}s elapsed)")
                    interaction = client.interactions.get(interaction.id)

                # Extract video bytes
                saved = False
                output_video = getattr(interaction, "output_video", None)
                if output_video and getattr(output_video, "data", None):
                    vdata = output_video.data
                    raw_bytes = base64.b64decode(vdata) if isinstance(vdata, str) else vdata
                    with open(scene_output, "wb") as vf:
                        vf.write(raw_bytes)
                    saved = True
                
                if saved:
                    console.print(f"✅ Saved scene video to: [blue]{to_tilde_path(scene_output)}[/blue]")
                    
                    # Run per-scene judging if character specified or --judge-per-scene active
                    if args.character and args.judge_per_scene:
                        console.print(f"👨‍⚖️ [bold cyan]Auditing Scene {idx} with LLM-as-a-Judge for character '{args.character}'...[/bold cyan]")
                        audit_res = subprocess.run([
                            sys.executable, str(Path(__file__).parent / "judge_video.py"),
                            "-v", str(scene_output),
                            "-c", args.character
                        ], capture_output=True, text=True)
                        
                        # Read per-scene audit sidecar JSON if generated
                        audit_json = scene_output.parent / f"{scene_output.stem}_biometric_audit.json"
                        if audit_json.exists():
                            try:
                                with open(audit_json, "r", encoding="utf-8") as ajf:
                                    adata = json.load(ajf)
                                score = float(adata.get("overall_score", 0))
                                feedback = adata.get("actionable_next_step", "")
                                console.print(f"  👨‍⚖️ Scene {idx} Score: [bold yellow]{score}/10[/bold yellow]")
                                if score >= 7:
                                    console.print(f"  🎉 [bold green]Scene {idx} PASSED audit! Keeping scene video.[/bold green]")
                                    scene_passed = True
                                else:
                                    console.print(f"  ⚠️ [bold red]Scene {idx} score low ({score}/10). Incorporating judge feedback for retry...[/bold red]")
                                    if feedback:
                                        scene_prompt += f" Feedback to fix: {feedback}"
                            except Exception as parse_err:
                                console.print(f"[yellow]Could not parse audit JSON: {parse_err}[/yellow]")
                                scene_passed = True
                        else:
                            scene_passed = True
                    else:
                        scene_passed = True

                    if scene_output not in scene_videos:
                        scene_videos.append(scene_output)
                else:
                    console.print(f"[yellow]⚠️ Scene {idx} video completed without video bytes.[/yellow]")
            except Exception as e:
                console.print(f"[bold red]Scene {idx} failed: {e}[/bold red]")

            attempt += 1

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

#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "google-genai>=1.0.0",
#   "rich>=13.0.0"
# ]
# ///

import os
import sys
import time
import base64
import argparse
from pathlib import Path
from rich.console import Console
from google import genai

console = Console()

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY not set.[/bold red]")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="🎥 Image-to-Video Animator for Character Consistency (EVAL Step 3).")
    parser.add_argument("-i", "--image", required=True, help="Path to high-fidelity anchor image (score >= 8.0).")
    parser.add_argument("-p", "--prompt", required=True, help="Motion prompt for video animation.")
    parser.add_argument("-c", "--character", default=None, help="Character name for audit (e.g. alessandro).")
    parser.add_argument("-o", "--output", default="out/animated_video.mp4", help="Output MP4 filepath.")

    args = parser.parse_args()
    img_path = Path(args.image)
    if not img_path.exists():
        console.print(f"[bold red]Error: Anchor image '{img_path}' does not exist.[/bold red]")
        sys.exit(1)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    client = genai.Client(api_key=api_key)

    console.print(f"🎬 [bold magenta]Starting Image-to-Video Animation...[/bold magenta]")
    console.print(f"🖼️ Anchor Image: [cyan]{img_path}[/cyan]")
    console.print(f"📝 Motion Prompt: [italic]'{args.prompt}'[/italic]")

    with open(img_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("utf-8")

    payload = [
        {"type": "image", "data": b64_data, "mime_type": "image/png"},
        {"type": "text", "text": args.prompt}
    ]

    try:
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=payload,
            background=True
        )

        start_time = time.time()
        while True:
            status = interaction.status
            if status == "completed":
                break
            elif status in ["failed", "canceled"]:
                raise RuntimeError(f"Video animation failed with status: {status}")
            time.sleep(4)
            elapsed = int(time.time() - start_time)
            console.print(f"  Status: {status}... ({elapsed}s elapsed)")
            interaction = client.interactions.get(interaction.id)

        output_video = getattr(interaction, "output_video", None)
        if output_video and getattr(output_video, "data", None):
            vdata = output_video.data
            raw_bytes = base64.b64decode(vdata) if isinstance(vdata, str) else vdata
            with open(out_path, "wb") as vf:
                vf.write(raw_bytes)
            console.print(f"\n✅ [bold green]SUCCESS! Saved video to:[/bold green] [blue]{out_path}[/blue]")
            os.system(f"open '{out_path}'")

            if args.character:
                console.print(f"\n👨‍⚖️ Running Video Biometric Audit...")
                os.system(f"./bin/judge_video.py -v '{out_path}' -c {args.character}")

        else:
            console.print(f"[bold yellow]⚠️ No video bytes returned from model.[/bold yellow]")

    except Exception as e:
        console.print(f"[bold red]Video animation error: {e}[/bold red]")

if __name__ == "__main__":
    main()

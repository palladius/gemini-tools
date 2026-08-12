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
from pathlib import Path
from rich.console import Console
from google import genai

console = Console()

TEST_VIDEOS = [
    (
        "alessandro_dragon_video",
        "out/alessandro_dragon_test1.png",
        "alessandro",
        "Cinematic 3D animation of Alessandro (8-year-old boy with short brown hair and green eyes) holding a glowing golden baby dragon in a magical crystal cavern. The baby dragon softly chirps and blinks."
    ),
    (
        "sebastian_superhero_video",
        "out/sebastian_superhero_test1.png",
        "sebastian",
        "Cinematic 3D animation of Sebastian (6-year-old boy with short brown hair) wearing a red superhero cape, smiling and racing a toy car in a sunny garden."
    )
]

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY not set.[/bold red]")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    out_dir = Path("out/kids_video_experiment")
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"🚀 [bold magenta]Starting Video Experiment for Minors (Alessandro & Sebastian)...[/bold magenta]\n")

    for name, img_path_str, char_name, prompt_text in TEST_VIDEOS:
        img_path = Path(img_path_str)
        if not img_path.exists():
            console.print(f"[yellow]Skipping {name}: {img_path} not found.[/yellow]")
            continue

        console.print(f"🎥 [bold cyan]Generating Video:[/bold cyan] {name}")
        output_file = out_dir / f"{name}.mp4"

        with open(img_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        payload = [
            {"type": "image", "data": b64_data, "mime_type": "image/png"},
            {"type": "text", "text": prompt_text}
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
                    raise RuntimeError(f"Interaction failed: {status}")
                time.sleep(4)
                elapsed = int(time.time() - start_time)
                console.print(f"  Status: {status}... ({elapsed}s elapsed)")
                interaction = client.interactions.get(interaction.id)

            output_video = getattr(interaction, "output_video", None)
            if output_video and getattr(output_video, "data", None):
                vdata = output_video.data
                raw_bytes = base64.b64decode(vdata) if isinstance(vdata, str) else vdata
                with open(output_file, "wb") as vf:
                    vf.write(raw_bytes)
                console.print(f"✅ Saved video to: [green]{output_file}[/green]")
                os.system(f"open {output_file}")
                os.system(f"./bin/judge_video.py -v {output_file} -c {char_name}")
            else:
                console.print(f"[yellow]⚠️ No video bytes returned for {name}[/yellow]")

        except Exception as e:
            console.print(f"[bold red]Video generation for {name} failed/blocked: {e}[/bold red]\n")

if __name__ == "__main__":
    main()

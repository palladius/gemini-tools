#!/usr/bin/env uv run python
# /// script
# dependencies = [
#   "google-genai>=1.0.0",
#   "rich>=13.0.0",
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

TEST_PROMPTS = [
    (
        "formula_1_live_action_convert",
        "Live-action 3D IMAX movie scene. Convert the characters and scene in this 2D cartoon reference into photorealistic human actors in real high-budget film sets. Photorealistic skin, cinematic lighting, 70mm camera movement. Zero 2D drawing elements."
    ),
    (
        "formula_2_recreate_cinematic",
        "A cinematic live-action film sequence recreating this comic book scene. Real-world human actors, photorealistic 8k movie capture, volumetric dungeon lighting, slow camera motion. Completely replace 2D illustration with 3D real life."
    ),
    (
        "formula_3_hollywood_blockbuster",
        "Hollywood blockbuster movie shot inspired by this cartoon panel. Live action fantasy movie, real actors wearing detailed medieval armor and robes, walking into a mysterious glowing ancient stone grotto. Cinematic 35mm film grain."
    ),
]

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY not set.[/bold red]")
        sys.exit(1)

    panel_path = Path("out/dnd_v1_panels/panel_01.png")
    if not panel_path.exists():
        console.print(f"[bold red]Error: Panel path '{panel_path}' not found.[/bold red]")
        sys.exit(1)

    out_dir = Path("out/test_cartoon_to_film")
    out_dir.mkdir(parents=True, exist_ok=True)

    client = genai.Client(api_key=api_key)

    with open(panel_path, "rb") as pf:
        b64_data = base64.b64encode(pf.read()).decode("utf-8")

    console.print(f"🚀 [bold magenta]Testing 3 Cartoon-to-Film Prompt Formulas on {panel_path}...[/bold magenta]\n")

    for name, prompt_text in TEST_PROMPTS:
        output_file = out_dir / f"{name}.mp4"
        console.print(f"🎬 [bold cyan]Testing Formula:[/bold cyan] [yellow]{name}[/yellow]")
        console.print(f"📝 Prompt: [dim]{prompt_text}[/dim]")

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
                console.print(f"✅ Saved video to: [green]{output_file}[/green]\n")

                # Run judge on each formula
                console.print(f"👨‍⚖️ [bold cyan]Auditing Formula '{name}' with LLM Judge...[/bold cyan]")
                os.system(f"./bin/judge_video.py -v {output_file}")
            else:
                console.print(f"[yellow]⚠️ No video output for {name}[/yellow]\n")

        except Exception as e:
            console.print(f"[bold red]Failed formula {name}: {e}[/bold red]\n")

if __name__ == "__main__":
    main()

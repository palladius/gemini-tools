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
import glob
import argparse
import time
import json
from pathlib import Path
from PIL import Image as PILImage
from rich.console import Console
from google import genai
from google.genai import types

console = Console()

COMIC_TEMPLATES = {
    "dnd": (
        "A vibrant 4-panel 2x2 grid comic book page depicting a D&D fantasy adventure. "
        "Top-Left Panel: A party of 6 adventurers (wizard, cleric, dwarf warrior, elf ranger, rogue, and hero) standing outside a dark mysterious grotto entrance. "
        "Top-Right Panel: Inside a dark dungeon corridor lit by a flickering torch, shadows dancing on stone walls. "
        "Bottom-Left Panel: The rogue accidentally triggers a stone floor trap, a flock of panicked mice squirting out of a wall hole, heroes surprised but unhurt. "
        "Bottom-Right Panel: Epic climax battle against a massive majestic BLUE DRAGON breathing lightning in a glowing cavernous chamber. "
        "Clean black comic panel borders, vibrant comic book illustration style."
    ),
    "marvel": (
        "A dramatic 4-panel 2x2 grid superhero comic book page. "
        "Top-Left Panel: Thanos standing menacingly on a ruined battlefield with a glowing Infinity Gauntlet. "
        "Top-Right Panel: Thor summoning thunder and lightning alongside Iron Man firing repulsor rays. "
        "Bottom-Left Panel: The Incredible Hulk roaring and smashing giant debris. "
        "Bottom-Right Panel: The heroes standing united in an epic Avengers Assemble finale pose. "
        "Dynamic Marvel comic art style, vivid colors, crisp panel borders."
    ),
    "mtg": (
        "A mystical 4-panel 2x2 grid Magic: The Gathering inspired comic book page. "
        "Top-Left Panel: A hero sealed inside an ornate glowing MTG card frame titled 'The Planeswalker'. "
        "Top-Right Panel: Ancestral Recall magic animation with glowing sapphire cards drawing rapidly from a levitating deck. "
        "Bottom-Left Panel: Summoning a magical creature emerging from a swirling mana vortex. "
        "Bottom-Right Panel: Epic showdown confronting the fierce Shivan Dragon in a mountain wilderness. "
        "High-fantasy trading card art style, rich magical lighting, crisp 2x2 grid borders."
    )
}

def to_tilde_path(p: str | Path) -> str:
    res = str(Path(p).resolve())
    home = str(Path.home())
    if res.startswith(home):
        return "~" + res[len(home):]
    return res

def load_character_references(character_name: str) -> list[PILImage.Image]:
    char_dir = Path("data/characters") / character_name.lower()
    if not char_dir.exists():
        console.print(f"[yellow]⚠️ Character directory '{char_dir}' not found.[/yellow]")
        return []
    
    extensions = ["*.png", "*.jpg", "*.jpeg", "*.webp"]
    files = []
    for ext in extensions:
        files.extend(glob.glob(str(char_dir / ext)))
    
    files.sort()
    images = []
    for f in files[:4]:  # Max 4 reference images
        try:
            images.append(PILImage.open(f))
            console.print(f"📸 Loaded character reference: [cyan]{to_tilde_path(f)}[/cyan]")
        except Exception as e:
            console.print(f"[yellow]Failed loading {f}: {e}[/yellow]")
    return images

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY environment variable not set.[/bold red]")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="🎨 2x2 Grid Comic Strip Generator (D&D, Marvel, MTG, or Custom)."
    )
    parser.add_argument(
        "-t", "--template",
        choices=["dnd", "marvel", "mtg", "custom"],
        default="dnd",
        help="Comic strip template to generate (default: dnd)."
    )
    parser.add_argument(
        "-p", "--prompt",
        default=None,
        help="Custom prompt for --template custom (or overrides template prompt)."
    )
    parser.add_argument(
        "-c", "--character",
        default=None,
        help="Optional character name (e.g. riccardo, yukihiro) to embed into comic."
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output image path (default: out/comic_<template>.png)."
    )
    parser.add_argument(
        "-m", "--model",
        default="gemini-3.1-flash-image-preview",
        help="Primary image generation model."
    )

    args = parser.parse_args()

    if args.template == "custom" and not args.prompt:
        console.print("[bold red]Error: --prompt is required when using --template custom[/bold red]")
        sys.exit(1)

    base_prompt = args.prompt if args.prompt else COMIC_TEMPLATES.get(args.template, COMIC_TEMPLATES["dnd"])
    
    if args.character:
        char_prompt = f" Feature the character '{args.character}' (preserving their face, hair, glasses, and likeness from the reference photos) as the main hero in the panels."
        full_prompt = base_prompt + char_prompt
    else:
        full_prompt = base_prompt

    out_file = Path(args.output) if args.output else Path("out") / f"comic_{args.template}.png"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    console.print(f"🎨 [bold cyan]Synthesizing 2x2 Comic Strip Template ({args.template.upper()}):[/bold cyan]")
    console.print(f"📝 Prompt: [italic]{full_prompt}[/italic]")

    client = genai.Client(api_key=api_key)
    contents = []

    if args.character:
        ref_imgs = load_character_references(args.character)
        contents.extend(ref_imgs)

    contents.append(full_prompt)

    try:
        console.print(f"📡 Generating with model: [bold green]{args.model}[/bold green]...")
        response = client.models.generate_content(
            model=args.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        saved = False
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    with open(out_file, "wb") as f:
                        f.write(part.inline_data.data)
                    saved = True
                    break

        if saved:
            console.print(f"✅ [bold green]Successfully saved comic strip to:[/bold green] [blue]{to_tilde_path(out_file)}[/blue]")
            
            # Save provenance sidecar JSON
            sidecar = out_file.with_suffix(".json")
            meta = {
                "generated_comic_path": to_tilde_path(out_file),
                "template": args.template,
                "character": args.character,
                "prompt": full_prompt,
                "model_used": args.model,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            with open(sidecar, "w", encoding="utf-8") as sf:
                json.dump(meta, sf, indent=2, ensure_ascii=False)
            console.print(f"📊 Provenance metadata saved to: [blue]{to_tilde_path(sidecar)}[/blue]")
        else:
            console.print("[bold red]Generation completed but no image bytes were returned.[/bold red]")

    except Exception as e:
        console.print(f"[bold red]Error during comic generation: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()

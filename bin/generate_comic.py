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
        "A vibrant 4-panel 2x2 grid cartoon fantasy comic page depicting an epic D&D adventure. "
        "Top-Left Panel: A heroic party of 5 fantasy adventurers (a female elven ranger with long golden hair and bow, a female dwarf cleric with warhammer, a female halfling rogue, a male wizard with glowing staff, and a paladin in armor) standing outside a mystical glowing grotto entrance. "
        "Top-Right Panel: Deep inside a moody dungeon corridor, torchlight casting warm golden light and flickering shadows on ancient stone runes. "
        "Bottom-Left Panel: The halfling rogue accidentally triggers a pressure plate trap, causing a flock of cute panicked mice to scurry from a stone crevice, the heroes reacting with humor. "
        "Bottom-Right Panel: Epic climax battle against a majestic colossal BLUE DRAGON breathing crackling blue lightning in a massive crystal cavern chamber. "
        "Clean black 2x2 grid panel borders, vibrant cartoon fantasy comic art style."
    ),
    "marvel": (
        "A colorful 4-panel 2x2 comic page showing futuristic fantasy champions. "
        "Top-Left Panel: A space warrior holding a glowing crystal gauntlet on a rocky planet. "
        "Top-Right Panel: A hammer knight and a metallic armor defender standing side-by-side. "
        "Bottom-Left Panel: A colossal emerald beast crushing boulders in anger. "
        "Bottom-Right Panel: Four champions standing victorious together in a hero stance. "
        "Vibrant fantasy comic illustration style, crisp 2x2 grid panel borders."
    ),
    "mtg": (
        "A mystical 4-panel 2x2 grid Magic: The Gathering inspired comic book page. "
        "Top-Left Panel: A hero sealed inside an ornate glowing MTG card frame titled 'The Planeswalker'. "
        "Top-Right Panel: Ancestral Recall magic animation with glowing sapphire cards drawing rapidly from a levitating deck. "
        "Bottom-Left Panel: Summoning a magical creature emerging from a swirling mana vortex. "
        "Bottom-Right Panel: Epic showdown confronting the fierce Shivan Dragon in a mountain wilderness. "
        "High-fantasy trading card art style, rich magical lighting, crisp 2x2 grid borders."
    ),
    "lake_garda_family": (
        "A cheerful, colorful 4-panel 2x2 grid cartoon comic page depicting a happy family vacationing at Lake Garda (Altomincio Water Park resort). "
        "The family consists of 4 people: a friendly father with short dark hair, a beautiful mother with long blonde hair, an 8-year-old son with dark hair, and a 6-year-old son with dark hair. "
        "Top-Left Panel: The family of 4 arriving at a sunny Lake Garda resort with palm trees, blue water slides, and scenic Italian mountains, waving happily. "
        "Top-Right Panel: Swimming together in a turquoise resort pool with water park splash buckets spilling water. "
        "Bottom-Left Panel: Eating Italian gelato cones together under a sunny outdoor pergola overlooking the blue lake. "
        "Bottom-Right Panel: Enjoying a sunset boat cruise on Lake Garda, smiling together with scenic Italian hills behind them. "
        "Clean black 2x2 grid panel borders, vibrant cartoon family comic illustration style."
    ),
    "alessandro_dragon": (
        "A magical 4-panel 2x2 grid cinematic comic page depicting Alessandro's Golden Dragon Adventure. "
        "Hero: Alessandro, a brave 8-year-old boy with short brown hair and bright green eyes, wearing a red t-shirt. "
        "Top-Left Panel: Alessandro enters a glowing underground cavern filled with sparkling diamonds and glittering gemstones, discovering a cute baby golden dragon surrounded by sparkling diamonds. "
        "Top-Right Panel: Two giant friendly golden Mother & Father Dragons arrive inside the diamond cavern; Alessandro smiles, holds out his hand asking 'Volete essere miei amici?' and the baby golden dragon happily nods. "
        "Bottom-Left Panel: Alessandro and his new baby golden dragon friend sliding down a massive blue water park slide at a sunny water park resort with splashes of water and sparkling floating diamonds. "
        "Bottom-Right Panel: Alessandro, the baby golden dragon, and the giant golden parent dragons celebrating together in a pool at sunset, surrounded by shiny gold coins and diamonds, waving happily. "
        "Clean black 2x2 grid panel borders, vibrant cinematic fantasy comic illustration style."
    ),
    "riccardo_altomincio": (
        "A colorful 4-panel 2x2 grid cartoon comic page depicting a hilarious summer vacation at Lake Garda (Altomincio Glamping resort). "
        "Top-Left Panel: A man standing on a scenic cliff overlooking Lake Garda at sunrise with palm trees and mountains. "
        "Top-Right Panel: The Altomincio glamping resort campsite surrounded by loud, cheerful Dutch tourists from Eindhoven, featuring a 15-year-old Dutch girl wearing a dark navy blue and white Eindhoven sports t-shirt. "
        "Bottom-Left Panel: A man sitting under a sunny outdoor pergola enjoying a delicious slice of Neapolitan pizza and Italian espresso. "
        "Bottom-Right Panel: A man piloting a sleek speedboat across sparkling blue waters of Lake Garda into the sunset. "
        "Clean black 2x2 grid panel borders, vibrant cartoon comic illustration style."
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
        choices=["dnd", "marvel", "mtg", "lake_garda_family", "alessandro_dragon", "riccardo_altomincio", "custom"],
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
        char_prompt = f" Feature the character '{args.character}' (preserving their facial features, mature Italian man with short balding grey-brown hair, clean-shaved face with NO beard, and exact biometric likeness from the reference photos) as the main hero in the panels."
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

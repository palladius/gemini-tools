#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai",
#     "pillow",
#     "rich",
#     "python-slugify",
# ]
# ///

import os
import sys
import argparse
import glob
import io
import time
import json
from pathlib import Path
from PIL import Image as PILImage
from rich.console import Console
from slugify import slugify
from google import genai
from google.genai import types

console = Console()

def to_tilde_path(p: str | Path) -> str:
    res = str(Path(p).resolve())
    home = str(Path.home())
    if res.startswith(home):
        return "~" + res[len(home):]
    return res

def resolve_character_images(character_name: str, max_images: int = 4):
    """Finds reference photos for a character under data/characters/ or data/."""
    search_paths = [
        f"data/characters/{character_name.lower()}/*.jpg",
        f"data/characters/{character_name.lower()}/*.png",
        f"data/{character_name.lower()}/*.jpg",
        f"data/{character_name.lower()}/*.png",
    ]
    found = []
    for p in search_paths:
        found.extend(glob.glob(p))
    # Sort by size descending (usually better resolution/detail)
    found = sorted(found, key=lambda x: os.path.getsize(x), reverse=True)
    return found[:max_images]

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY environment variable not set.[/bold red]")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="🎨 Universal GenAI Photo Synthesizer (Image-to-Image & Text-to-Image with fallback models)."
    )
    parser.add_argument(
        "-p", "--prompt",
        required=True,
        help="The scene description and requirements for the generated photo."
    )
    parser.add_argument(
        "-i", "--image",
        action="append",
        default=[],
        help="Path to one or more reference images (can be specified multiple times)."
    )
    parser.add_argument(
        "-c", "--character",
        default=None,
        help="Load reference images automatically from data/characters/<name>/"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output filepath (default: out/<slug>.png)"
    )
    parser.add_argument(
        "-m", "--model",
        default="gemini-3.1-flash-image-preview",
        help="Primary image model to try (default: gemini-3.1-flash-image-preview)"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Automatically open the generated picture on screen."
    )

    args = parser.parse_args()

    # Gather images
    image_paths = list(args.image)
    if args.character:
        chars = [c.strip() for c in args.character.split(",") if c.strip()]
        for char_name in chars:
            char_imgs = resolve_character_images(char_name, max_images=2)
            if not char_imgs:
                console.print(f"[bold yellow]⚠️ No images found for character '{char_name}' in data/.[/bold yellow]")
            else:
                console.print(f"👤 Found {len(char_imgs)} reference photo(s) for character [bold cyan]{char_name}[/bold cyan]: {char_imgs}")
                image_paths.extend(char_imgs)

    loaded_images = []
    for img_path in image_paths:
        if os.path.exists(img_path):
            try:
                loaded_images.append(PILImage.open(img_path))
                console.print(f"📸 Loaded reference: [green]{img_path}[/green]")
            except Exception as e:
                console.print(f"[bold red]Failed to load image {img_path}: {e}[/bold red]")
        else:
            console.print(f"[bold red]Error: image path '{img_path}' does not exist.[/bold red]")
            sys.exit(1)

    # Prepare Output Path
    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    if args.output:
        output_path = Path(args.output)
    else:
        safe_slug = slugify(args.prompt, max_length=50, word_boundary=True) or "synthesizer_photo"
        output_path = out_dir / f"{safe_slug}.png"
        counter = 1
        while output_path.exists():
            output_path = out_dir / f"{safe_slug}_{counter}.png"
            counter += 1

    # Prepare Models with Fallbacks
    models_to_try = [args.model]
    defaults = [
        "gemini-3.1-flash-image-preview",
        "nano-banana-pro-preview",
        "gemini-3-pro-image-preview",
        "gemini-3-pro-image"
    ]
    for d in defaults:
        if d not in models_to_try:
            models_to_try.append(d)

    client = genai.Client(api_key=api_key)
    payload = loaded_images + [args.prompt]

    console.print(f"\n🎨 [bold magenta]Starting Synthesis...[/bold magenta]")
    console.print(f"📝 Prompt: [italic]'{args.prompt}'[/italic]")

    def save_provenance(out_path, win_model):
        meta = {
            "generated_asset_path": to_tilde_path(out_path),
            "source_reference_paths": [to_tilde_path(p) for p in image_paths],
            "prompt": args.prompt,
            "model_used": win_model,
            "generation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        meta_file = out_path.with_suffix(".json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        console.print(f"📊 Provenance metadata saved to: [blue]{meta_file}[/blue]")

    for model_name in models_to_try:
        console.print(f"\n⚡ Trying generator model: [cyan]{model_name}[/cyan] (via generate_content)")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=payload,
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        out_img = PILImage.open(io.BytesIO(part.inline_data.data))
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        out_img.save(output_path)
                        console.print(f"✅ [bold green]SUCCESS![/bold green] Saved photo to: [blue]{output_path}[/blue]")
                        save_provenance(output_path, model_name)
                        if args.open:
                            os.system(f"open '{output_path}'")
                        return
            console.print(f"[dim]No image data returned from {model_name}.[/dim]")
        except Exception as e:
            console.print(f"[red]Failed with {model_name}: {e}[/red]")

    # Fallback to interactions API
    console.print("\n🍌 Trying fallback via client.interactions.create...")
    for model_name in models_to_try:
        try:
            console.print(f"Calling interactions API with model: [cyan]{model_name}[/cyan]...")
            interaction = client.interactions.create(
                model=model_name,
                input=payload,
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            for event in interaction:
                if event.candidates and event.candidates[0].content and event.candidates[0].content.parts:
                    for part in event.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                            out_img = PILImage.open(io.BytesIO(part.inline_data.data))
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            out_img.save(output_path)
                            console.print(f"✅ [bold green]SUCCESS via Interactions![/bold green] Saved to: [blue]{output_path}[/blue]")
                            save_provenance(output_path, f"interactions/{model_name}")
                            if args.open:
                                os.system(f"open '{output_path}'")
                            return
        except Exception as e:
            console.print(f"[red]Interaction failed with {model_name}: {e}[/red]")

    console.print("\n❌ [bold red]All models and endpoints failed to generate the photo.[/bold red]")
    sys.exit(1)

if __name__ == "__main__":
    main()

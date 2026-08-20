#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "google-genai>=1.0.0",
#   "rich>=13.0.0",
#   "python-slugify>=8.0.0",
#   "pillow>=10.0.0"
# ]
# ///

import os
import sys
import glob
import time
import io
import json
import argparse
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

def resolve_character_images(character_name: str, max_images: int = 4) -> list[str]:
    """Finds reference photos for characters, round-robin distributing up to max_images."""
    char_names = [c.strip().lower() for c in character_name.split(",") if c.strip()]
    if not char_names:
        return []
        
    char_image_lists = []
    for cname in char_names:
        char_imgs = []
        grid_cleaned_dir = Path(f"data/characters/{cname}/grid_cleaned")
        if grid_cleaned_dir.exists():
            valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
            grid_imgs = [str(p) for p in grid_cleaned_dir.iterdir() if p.suffix.lower() in valid_exts]
            if grid_imgs:
                char_imgs.extend(sorted(grid_imgs, key=lambda x: os.path.getsize(x), reverse=True))
                
        if not char_imgs:
            search_paths = [
                f"data/characters/{cname}/*.jpg",
                f"data/characters/{cname}/*.png",
                f"data/characters/{cname}/*.JPG",
                f"data/characters/{cname}/*.PNG",
                f"data/{cname}/*.jpg",
                f"data/{cname}/*.png",
            ]
            sub_found = []
            for p in search_paths:
                sub_found.extend(glob.glob(p))
            char_imgs.extend(sorted(sub_found, key=lambda x: os.path.getsize(x), reverse=True))
            
        if char_imgs:
            char_image_lists.append(char_imgs)

    found = []
    # Round-robin selection
    while len(found) < max_images:
        added_in_round = False
        for img_list in char_image_lists:
            if img_list and len(found) < max_images:
                found.append(img_list.pop(0))
                added_in_round = True
        if not added_in_round:
            break
            
    return found

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY environment variable not set.[/bold red]")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="📸 Multipic Synthesizer: Generate an image from multiple reference photos and a predefined prompt."
    )
    parser.add_argument(
        "-p", "--prompt",
        required=True,
        help="Name of the prompt file in etc/prompts/ (e.g., 'snowglobe')"
    )
    parser.add_argument(
        "-i", "--images",
        default="",
        help="Comma-separated paths to reference images (up to 3)."
    )
    parser.add_argument(
        "-d", "--dir",
        default="",
        help="Path to a directory containing reference images."
    )
    parser.add_argument(
        "-c", "--characters",
        default="",
        help="Comma-separated character names to automatically load images from data/characters/<name>/"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output filepath (default: out/<prompt_name>_<timestamp>.png)"
    )
    parser.add_argument(
        "-m", "--model",
        default="gemini-3.1-flash-image-preview",
        help="Primary image model to try (default: gemini-3.1-flash-image-preview)"
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not automatically open the generated picture on screen."
    )
    parser.add_argument(
        "-a", "--append-prompt",
        default="",
        help="Syntactic sugar: additional text to append to the predefined prompt."
    )

    args = parser.parse_args()

    # Resolve Prompt
    prompt_name = args.prompt
    prompt_file = Path(f"etc/prompts/{prompt_name}.md")
    if not prompt_file.exists():
        prompt_file = Path(f"etc/prompts/{prompt_name}.txt")
    if not prompt_file.exists():
        console.print(f"[bold red]ERROR: Prompt file not found in etc/prompts/ for '{prompt_name}'[/bold red]")
        sys.exit(1)
        
    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_text = f.read().strip()
        
    if args.append_prompt:
        prompt_text += "\n\n" + args.append_prompt
        
    console.print(f"📜 Loaded prompt '{prompt_name}':\n[italic dim]{prompt_text}[/italic dim]")

    # Gather images
    image_paths = []
    
    if args.images:
        paths = [p.strip() for p in args.images.split(",") if p.strip()]
        for p in paths:
            if os.path.exists(p):
                image_paths.append(p)
            else:
                console.print(f"[bold yellow]⚠️ Image path not found: {p}[/bold yellow]")

    if args.dir and os.path.exists(args.dir):
        valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
        dir_imgs = [str(p) for p in Path(args.dir).iterdir() if p.suffix.lower() in valid_exts]
        image_paths.extend(dir_imgs)
        
    if args.characters:
        char_imgs = resolve_character_images(args.characters, max_images=3)
        if not char_imgs:
            console.print(f"[bold yellow]⚠️ No images found for characters '{args.characters}' in data/.[/bold yellow]")
        else:
            console.print(f"👤 Found {len(char_imgs)} reference photo(s) for characters [bold cyan]{args.characters}[/bold cyan]")
            image_paths.extend(char_imgs)

    # De-duplicate while preserving order
    unique_paths = []
    for p in image_paths:
        if p not in unique_paths:
            unique_paths.append(p)
    image_paths = unique_paths

    if not image_paths:
        console.print("[bold red]ERROR: No reference images found. Provide --images, --dir, or --characters.[/bold red]")
        sys.exit(1)

    if len(image_paths) > 3:
        console.print(f"[bold yellow]⚠️ Found {len(image_paths)} images, limiting to 3 for optimal results.[/bold yellow]")
        image_paths = image_paths[:3]

    console.print(f"📸 Using {len(image_paths)} reference images: {image_paths}")

    client = genai.Client(api_key=api_key)
    loaded_images = []

    for img_path in image_paths:
        try:
            im = PILImage.open(img_path)
            if im.mode != "RGB":
                im = im.convert("RGB")
            loaded_images.append(im)
            console.print(f"📸 Loaded reference: [green]{img_path}[/green]")
        except Exception as e:
            console.print(f"[bold red]Failed to load image {img_path}: {e}[/bold red]")

    # Prepare Output Path
    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    if args.output:
        output_path = Path(args.output)
    else:
        safe_slug = slugify(prompt_name, max_length=30, word_boundary=True) or "multipic"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = out_dir / f"{safe_slug}_{timestamp}.png"

    models_to_try = [args.model]
    if "gemini-3.1-flash-image-preview" not in models_to_try:
        models_to_try.append("gemini-3.1-flash-image-preview")

    payload = loaded_images + [prompt_text]

    console.print(f"\n🎨 [bold magenta]Starting Synthesis...[/bold magenta]")

    def save_provenance(out_path, win_model):
        meta = {
            "generated_asset_path": to_tilde_path(out_path),
            "source_reference_paths": [to_tilde_path(p) for p in image_paths],
            "prompt_name": prompt_name,
            "prompt_text": prompt_text,
            "model_used": win_model,
            "generation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        meta_file = out_path.with_suffix(".json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        console.print(f"📊 Provenance metadata saved to: [blue]{meta_file}[/blue]")

    for model_name in models_to_try:
        console.print(f"\n⚡ Trying multimodal generator model: [cyan]{model_name}[/cyan] (via generate_content)")
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
                        
                        judge_script = Path("bin/judge_image.py")
                        if judge_script.exists():
                            console.print(f"\n👨‍⚖️ [bold cyan]Automatically running AI Judge on generated asset...[/bold cyan]")
                            import subprocess
                            cmd = ["python3", str(judge_script), "-i", str(output_path), "-c", args.characters or "multipic"]
                            note_str = f"Auto-evaluated photo generated with prompt '{prompt_name}'"
                            cmd.extend(["--note", note_str])
                            subprocess.run(cmd)
                            
                        if not args.no_open and sys.platform == "darwin":
                            os.system(f"open '{output_path}'")
                        elif not args.no_open and sys.platform.startswith("linux"):
                            os.system(f"xdg-open '{output_path}'")
                        return
            console.print(f"[dim]No image data returned from {model_name}.[/dim]")
        except Exception as e:
            console.print(f"[red]Failed with {model_name}: {e}[/red]")

    console.print("\n❌ [bold red]All models failed to generate the photo.[/bold red]")
    sys.exit(1)

if __name__ == "__main__":
    main()

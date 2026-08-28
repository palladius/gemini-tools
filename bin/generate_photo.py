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

import platform
import subprocess

def open_image_on_system(file_path: str | Path):
    p = str(Path(file_path).resolve())
    sys_name = platform.system()
    try:
        if sys_name == "Darwin":
            subprocess.run(["open", p], check=False)
        elif sys_name == "Linux":
            subprocess.run(["xdg-open", p], check=False)
        elif sys_name == "Windows":
            os.startfile(p)
    except Exception as e:
        console.print(f"[yellow]Could not auto-open image {p}: {e}[/yellow]")

def to_tilde_path(p: str | Path) -> str:

    res = str(Path(p).resolve())
    home = str(Path.home())
    if res.startswith(home):
        return "~" + res[len(home):]
    return res

def resolve_character_images(character_name: str, max_images: int = 3) -> list[str]:

    """Finds reference photos for a character, prioritizing grid_cleaned/ crops if available."""
    found = []
    char_names = [c.strip().lower() for c in character_name.split(",") if c.strip()]
    
    for cname in char_names:
        grid_cleaned_dir = Path(f"data/characters/{cname}/grid_cleaned")
        if grid_cleaned_dir.exists():
            valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
            grid_imgs = [str(p) for p in grid_cleaned_dir.iterdir() if p.suffix.lower() in valid_exts]
            if grid_imgs:
                grid_imgs = sorted(grid_imgs, key=lambda x: os.path.getsize(x), reverse=True)
                found.extend(grid_imgs[:max_images])
                continue
                
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
        sub_found = sorted(sub_found, key=lambda x: os.path.getsize(x), reverse=True)
        found.extend(sub_found[:max_images])
        
    return found

def load_character_guidelines(character_name: str) -> str:
    """Loads prompt guidelines from data/characters/<cname>/character.yaml if available."""
    guidelines = []
    char_names = [c.strip().lower() for c in character_name.split(",") if c.strip()]
    for cname in char_names:
        yaml_p = Path(f"data/characters/{cname}/character.yaml")
        if yaml_p.exists():
            try:
                import yaml
                with open(yaml_p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    must_inc = data.get("prompt_guidelines", {}).get("must_include", [])
                    must_avd = data.get("prompt_guidelines", {}).get("must_avoid", [])
                    if must_inc:
                        guidelines.append(f"Subject '{cname}': " + ", ".join(must_inc))
                    if must_avd:
                        guidelines.append(f"Avoid for '{cname}': " + ", ".join(must_avd))
            except Exception:
                pass
    return " ".join(guidelines)



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
        action="append",
        default=[],
        help="Load reference images automatically from data/characters/<name>/ (can be specified multiple times)."
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output filepath (default: out/<slug>.png)"
    )
    parser.add_argument(
        "-m", "--model",
        default="gemini-3.1-flash-image",
        help="Primary image model to try (default: gemini-3.1-flash-image)"
    )


    parser.add_argument(
        "-s", "--show", "--open",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Automatically open generated photo on Mac/Linux screen (default: True, use --no-show to disable)."
    )


    parser.add_argument(
        "--files-api",
        action="store_true",
        help="Upload reference images via Google Files API (client.files.upload) for full uncompressed resolution."
    )
    parser.add_argument(
        "--gcs-bucket",
        default="ricc-family-character-vault-pvt",
        help="Private GCS bucket containing character photos for direct gs:// URI references (default: ricc-family-character-vault-pvt)"
    )
    parser.add_argument(
        "--framing",
        default="portrait",
        choices=["portrait", "full-body", "any"],
        help="Composition framing preference (default: 'portrait' for large, clear, easily evaluable faces)."
    )
    parser.add_argument(
        "--use-gcs",
        action="store_true",
        help="Pass references as direct gs:// URIs (types.Part.from_uri) via Google Cloud Storage."
    )



    args = parser.parse_args()

    # Gather images
    image_paths = list(args.image)
    characters = args.character if isinstance(args.character, list) else ([args.character] if args.character else [])
    for cname in characters:
        char_imgs = resolve_character_images(cname)
        if not char_imgs:
            console.print(f"[bold yellow]⚠️ No images found for character '{cname}' in data/.[/bold yellow]")
        else:
            console.print(f"👤 Found {len(char_imgs)} reference photo(s) for character [bold cyan]{cname}[/bold cyan]: {char_imgs}")
            image_paths.extend(char_imgs)


    client = genai.Client(api_key=api_key)
    loaded_images = []

    for img_path in image_paths:
        if args.use_gcs:
            # Map local path or filename to GCS URI gs://bucket/char_lowercase/filename
            fname = Path(img_path).name
            char_folder = Path(img_path).parent.name.lower()
            gcs_uri = f"gs://{args.gcs_bucket}/{char_folder}/{fname}"
            mime_type = "image/png" if fname.lower().endswith(".png") else "image/jpeg"
            console.print(f"☁️ Passing direct GCS URI reference: [bold cyan]{gcs_uri}[/bold cyan]...")
            gcs_part = types.Part.from_uri(file_uri=gcs_uri, mime_type=mime_type)
            loaded_images.append(gcs_part)
        elif os.path.exists(img_path):
            try:
                if args.files_api:
                    console.print(f"📡 Uploading lossless reference via Files API: [cyan]{img_path}[/cyan]...")
                    fref = client.files.upload(file=img_path)
                    loaded_images.append(fref)
                else:
                    im = PILImage.open(img_path)
                    if im.mode != "RGB":
                        im = im.convert("RGB")
                    loaded_images.append(im)
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
        "gemini-3.1-flash-image",
        "gemini-3.1-flash-image-preview",
        "gemini-2.5-flash-image"
    ]

    for d in defaults:
        if d not in models_to_try:
            models_to_try.append(d)

    # Append framing & YAML character guidelines if applicable
    final_prompt = args.prompt
    framing_rule = ""
    if args.framing == "portrait":
        framing_rule = "Composition requirement: Medium close-up 85mm portrait shot, chest-up framing with a prominent, large, clearly detailed face for biometric evaluation. Avoid tiny distant faces or wide full-body landscape shots where the face is too small."
    elif args.framing == "full-body":
        framing_rule = "Composition requirement: Full-body photograph showing head to toe."

    char_guidelines_list = []
    for cname in characters:
        g = load_character_guidelines(cname)
        if g:
            char_guidelines_list.append(f"Character '{cname}': {g}")
    char_guidelines = "; ".join(char_guidelines_list)

    combined_rules = [r for r in [framing_rule, char_guidelines] if r]
    if combined_rules:
        final_prompt = f"{args.prompt} [{'; '.join(combined_rules)}]"
        console.print(f"📋 [bold cyan]Injected Composition & Guidelines:[/bold cyan] {'; '.join(combined_rules)}")


    payload = loaded_images + [final_prompt]



    console.print(f"\n🎨 [bold magenta]Starting Synthesis...[/bold magenta]")
    console.print(f"📝 Prompt: [italic]'{args.prompt}'[/italic]")

    def run_auto_judge(out_path, char_list, prompt_note=None):
        if not char_list:
            return
        if isinstance(char_list, str):
            char_list = [char_list]
        import subprocess
        judge_script = Path("bin/judge_image.py")
        if judge_script.exists():
            console.print(f"\n👨‍⚖️ [bold cyan]Automatically running AI Judge on generated asset...[/bold cyan]")
            cmd = ["python3", str(judge_script), "-i", str(out_path)]
            for cname in char_list:
                cmd.extend(["-c", cname])
            note_str = f"Auto-evaluated photo generated with character(s) '{', '.join(char_list)}'"
            cmd.extend(["--note", note_str])
            subprocess.run(cmd)

    def get_git_commit():
        try:
            res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
            return res.stdout.strip()
        except Exception:
            return None

    def get_software_version():
        ver_file = Path("VERSION")
        if ver_file.exists():
            try:
                return ver_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass
        return "0.2.11"

    def save_provenance(out_path, win_model):
        import hashlib
        img_md5 = ""
        if out_path.exists():
            try:
                with open(out_path, "rb") as f:
                    img_md5 = hashlib.md5(f.read()).hexdigest()
            except Exception:
                pass

        meta = {
            "generated_asset_path": to_tilde_path(out_path),
            "md5": img_md5,
            "source_reference_paths": [to_tilde_path(p) for p in image_paths],
            "prompt": args.prompt,
            "final_injected_prompt": final_prompt,
            "model_used": win_model,
            "seed": getattr(args, "seed", None),
            "software_version": get_software_version(),
            "git_commit": get_git_commit(),
            "generation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        meta_file = out_path.with_suffix(".json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        console.print(f"📊 Provenance metadata saved to: [blue]{meta_file}[/blue]")
        run_auto_judge(out_path, characters)



    # Try Imagen direct API if model starts with imagen
    for model_name in models_to_try:
        if "imagen" in model_name.lower():
            console.print(f"\n⚡ Trying Imagen model: [cyan]{model_name}[/cyan] (via generate_images)")
            try:
                result = client.models.generate_images(
                    model=model_name,
                    prompt=args.prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/png",
                        aspect_ratio="1:1"
                    )
                )
                if result.generated_images:
                    img_bytes = result.generated_images[0].image.image_bytes
                    out_img = PILImage.open(io.BytesIO(img_bytes))
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    out_img.save(output_path)
                    console.print(f"✅ [bold green]SUCCESS![/bold green] Saved photo to: [blue]{output_path}[/blue]")
                    save_provenance(output_path, model_name)
                    if args.show:
                        open_image_on_system(output_path)

                    return
            except Exception as e:
                console.print(f"[red]Imagen failed with {model_name}: {e}[/red]")

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
                        if args.show:
                            open_image_on_system(output_path)

                        return
            console.print(f"[dim]No image data returned from {model_name}.[/dim]")
        except Exception as e:
            console.print(f"[red]Failed with {model_name}: {e}[/red]")
            if "Google Cloud Storage" in str(e) or "Register" in str(e):
                console.print("[yellow]🔄 Falling back to local reference images for all models...[/yellow]")
                new_payload = []
                for p_item in payload:
                    if isinstance(p_item, types.Part) and hasattr(p_item, "file_data") and p_item.file_data and p_item.file_data.file_uri and p_item.file_data.file_uri.startswith("gs://"):
                        pass
                    else:
                        new_payload.append(p_item)
                # Append local PIL images
                local_imgs = []
                for img_p in image_paths:
                    if os.path.exists(img_p):
                        im = PILImage.open(img_p)
                        if im.mode != "RGB":
                            im = im.convert("RGB")
                        local_imgs.append(im)
                payload = local_imgs + new_payload
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
                                if args.show:
                                    open_image_on_system(output_path)

                                return
                except Exception as fb_e:
                    console.print(f"[red]Fallback failed with {model_name}: {fb_e}[/red]")

    console.print("\n❌ [bold red]All models failed to generate the photo.[/bold red]")
    sys.exit(1)

if __name__ == "__main__":
    main()

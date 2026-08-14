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

"""
🎨 Universal Character Consistency Evaluator & LLM Judge
------------------------------------------------------
Evaluates character/person consistency across Gemini/Nanobanana image models.
Supports generic character directories, custom prompt suites, FFmpeg banner overlays,
and automated multimodal LLM judging.
"""

import os
import sys
import glob
import io
import time
import json
import argparse
import subprocess
from pathlib import Path
from slugify import slugify
from PIL import Image as PILImage, ImageDraw, ImageFont
from rich.console import Console
from google import genai
from google.genai import types

console = Console()

DEFAULT_PROMPT_TEMPLATES = [
    "A realistic, high-resolution portrait photograph of the person in the reference images. Sitting at a charming outdoor cafe on a soft sunny afternoon, smiling warmly at the camera with natural expressions. Soft bokeh background, sharp details.",
    "A professional studio portrait photograph of the person in the reference images. Wearing elegant formal attire, against a clean neutral dark gray studio background. Warm key lighting, dramatic soft shadows, high detail facial features, smiling naturally.",
    "A beautiful lifestyle photograph of the person in the reference images walking along a scenic coastal trail during golden hour. Sunset lighting illuminating their face, wind gently in their hair, smiling happily. Cinematic photo."
]

def judge_image_consistency(client: genai.Client, generated_img_path: Path, ref_imgs: list[PILImage.Image], subject_name: str) -> dict:
    console.print(f"⚖️ [bold yellow]Running LLM Judge for Character Consistency ({subject_name})...[/bold yellow]")
    gen_pil = PILImage.open(generated_img_path)
    
    judge_prompt = (
        "You are an expert biometric character consistency judge. "
        f"The first images provided are reference photographs of a person ('{subject_name}'). "
        "The last image provided is an AI-generated image created based on those reference photographs.\n\n"
        "Evaluate the character consistency between the generated image and the reference photos. "
        "Examine facial features, eye shape, smile, nose, cheekbones, hair color/texture, and general identity resemblance.\n\n"
        "Output your evaluation strictly as a valid JSON object with the following fields:\n"
        "{\n"
        '  "character_consistency_score": <integer from 1 to 10>,\n'
        '  "resemblance_critique": "<2-3 sentence brief analysis of facial and identity consistency>",\n'
        '  "verdict": "<EXCELLENT | GOOD | MODERATE | POOR>"\n'
        "}"
    )
    
    payload = ref_imgs + [gen_pil, judge_prompt]
    
    for judge_model in ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.1-pro-preview"]:
        try:
            res = client.models.generate_content(
                model=judge_model,
                contents=payload,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(res.text)
            console.print(f"   [green]Judge Verdict ({judge_model}): Score {data.get('character_consistency_score')}/10 - {data.get('verdict')}[/green]")
            return data
        except Exception as e:
            console.print(f"   [dim]Judge model {judge_model} failed: {e}[/dim]")
            
    return {
        "character_consistency_score": 5,
        "resemblance_critique": "Failed to obtain automated judge feedback.",
        "verdict": "UNKNOWN"
    }

def create_text_banner(model_name: str, subject_name: str, seed_val: int, out_dir: Path) -> Path:
    line1 = f"[P] {subject_name} - [S] {seed_val}"
    line2 = f"model: {model_name}"
    text = f"{line1}\n{line2}"
    
    font_size = 26
    padding_x = 25
    padding_y = 12
    spacing = 6
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except Exception:
        font = ImageFont.load_default()
        
    dummy = PILImage.new("RGBA", (1, 1))
    draw_dummy = ImageDraw.Draw(dummy)
    bbox = draw_dummy.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    banner_w = text_w + (padding_x * 2)
    banner_h = text_h + (padding_y * 2)
    
    banner = PILImage.new("RGBA", (banner_w, banner_h), (0, 0, 0, 195))
    draw = ImageDraw.Draw(banner)
    draw.multiline_text((padding_x, padding_y), text, font=font, fill=(255, 255, 255, 255), align="center", spacing=spacing)
    
    out_banner_path = out_dir / f"banner_{slugify(model_name)}_{slugify(subject_name)}_{seed_val}.png"
    out_banner_path.parent.mkdir(parents=True, exist_ok=True)
    banner.save(out_banner_path)
    return out_banner_path

def apply_ffmpeg_overlay(input_img_path: Path, banner_path: Path, output_img_path: Path):
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_img_path),
        "-i", str(banner_path),
        "-filter_complex", "[0:v][1:v]overlay=(W-w)/2:H-h-30",
        "-vframes", "1",
        str(output_img_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        console.print(f"[bold red]FFmpeg failed: {res.stderr}[/bold red]")
        input_img_path.replace(output_img_path)
    else:
        console.print(f"🎬 FFmpeg overlay appended text to: [bold green]{output_img_path}[/bold green]")

def eval_model(
    model_name: str,
    character_dir: str,
    subject_name: str = None,
    prompts: list[str] = None,
    output_base_dir: str = "out/cc_eval",
    enable_judge: bool = True,
    open_mac: bool = True,
    max_ref_photos: int = 4,
    seed: int = None
):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]ERROR: GEMINI_API_KEY environment variable not set.[/bold red]")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    char_path = Path(character_dir).expanduser().resolve()
    if not char_path.exists():
        console.print(f"[bold red]Character directory '{char_path}' does not exist.[/bold red]")
        sys.exit(1)
        
    if not subject_name:
        subject_name = char_path.name.capitalize()
        
    ref_file_paths = sorted(glob.glob(str(char_path / "*.jpg"))) + \
                     sorted(glob.glob(str(char_path / "*.jpeg"))) + \
                     sorted(glob.glob(str(char_path / "*.png")))
                     
    # Filter out AI generated, low quality (schifo), or synthesized files
    exclude_keywords = ["aigen", "schifo", "banner_", "BEST_"]
    ref_file_paths = [
        p for p in ref_file_paths 
        if not any(kw.lower() in Path(p).name.lower() for kw in exclude_keywords)
        and not Path(p).name.endswith("_annotated.png")
        and not Path(p).name.endswith("_face.png")
        and not Path(p).name.endswith("_raw.png")
    ]

    if not ref_file_paths:
        console.print(f"[bold red]No valid reference .jpg, .jpeg, or .png images found in {char_path}[/bold red]")
        sys.exit(1)
        
    console.print(f"📸 Found {len(ref_file_paths)} reference photo(s) for character [bold cyan]{subject_name}[/bold cyan].")
    
    subject_slug = slugify(subject_name)
    model_slug = slugify(model_name)
    
    out_dir = Path(output_base_dir) / subject_slug / model_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    
    eval_prompts = prompts if prompts else DEFAULT_PROMPT_TEMPLATES
    generated_results = []
    
    for idx, prompt_text in enumerate(eval_prompts, 1):
        import random
        current_seed = seed if seed is not None else random.randint(1, 2147483647)
        banner_path = create_text_banner(model_name, subject_name, current_seed, out_dir)
        
        # Sample reference images and strictly verify all sampled files exist and open cleanly
        requested_count = min(max_ref_photos, len(ref_file_paths))
        iter_ref_paths = random.sample(ref_file_paths, k=requested_count)
        iter_ref_imgs = []
        for img_p in iter_ref_paths:
            if not os.path.exists(img_p):
                raise FileNotFoundError(f"CRITICAL ERROR: Reference photo does not exist on disk: {img_p}")
            try:
                img = PILImage.open(img_p)
                img.verify() # Verify file integrity
                iter_ref_imgs.append(PILImage.open(img_p)) # Reopen after verify
            except Exception as e:
                raise RuntimeError(f"CRITICAL ERROR: Reference photo '{img_p}' is corrupted or unreadable: {e}")
                
        if len(iter_ref_imgs) < requested_count:
            raise RuntimeError(f"CRITICAL ERROR: Requested {requested_count} reference photos, but only {len(iter_ref_imgs)} passed verification. Halting execution!")
                
        console.print(f"\n🎨 [bold cyan][{model_name} | {subject_name} | Seed: {current_seed}][/bold cyan] Generating picture {idx}/{len(eval_prompts)}...")
        console.print(f"   Prompt: [italic]\"{prompt_text}\"[/italic]")
        console.print(f"   Sampled References ({len(iter_ref_imgs)} verified): [dim]{[Path(p).name for p in iter_ref_paths]}[/dim]")
        
        payload = iter_ref_imgs + [prompt_text]
        
        if len(prompt_text) > 40:
            prompt_slug = slugify(prompt_text[:25] + "_" + prompt_text[-25:])
        else:
            prompt_slug = slugify(prompt_text)
            
        raw_out_path = out_dir / f"{subject_slug}_p{idx}_s{current_seed}_{prompt_slug}_raw.png"
        final_out_path = out_dir / f"{subject_slug}_p{idx}_s{current_seed}_{prompt_slug}_annotated.png"
        
        if not raw_out_path.exists():
            success = False
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=payload,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        seed=current_seed
                    )
                )
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                            out_img = PILImage.open(io.BytesIO(part.inline_data.data))
                            out_img.save(raw_out_path)
                            success = True
                            break
            except Exception as e:
                console.print(f"[bold red]Error generating image with {model_name}: {e}[/bold red]")
                
            if not success:
                console.print(f"[bold red]Failed to generate image {idx} for model {model_name}[/bold red]")
                continue
        else:
            console.print(f"   [dim]Re-using existing raw image for seed {current_seed}: {raw_out_path}[/dim]")

        # Apply FFmpeg banner overlay
        apply_ffmpeg_overlay(raw_out_path, banner_path, final_out_path)
        
        # Generate face crop image
        face_out_path = out_dir / f"{subject_slug}_p{idx}_s{current_seed}_{prompt_slug}_face.png"
        try:
            import face_cropper
            face_cropper.detect_and_crop_face(final_out_path, face_out_path)
        except Exception as e:
            console.print(f"[dim]Face crop failed: {e}[/dim]")
            face_out_path = final_out_path

        judge_res = {}
        if enable_judge:
            judge_res = judge_image_consistency(client, raw_out_path, iter_ref_imgs, subject_name)
            judge_meta_file = out_dir / f"{subject_slug}_p{idx}_s{current_seed}_{prompt_slug}_judge.json"
            with open(judge_meta_file, "w", encoding="utf-8") as f:
                json.dump(judge_res, f, indent=2)
            
        if open_mac:
            os.system(f"open '{final_out_path}'")
            console.print(f"🖥️ Opened on Mac: [blue]{final_out_path}[/blue]")
        
        record_id = f"{subject_slug}_{model_slug}_p{idx}_s{current_seed}_{prompt_slug}"
        eval_record = {
            "eval_id": record_id,
            "subject": subject_name,
            "model_name": model_name,
            "seed": current_seed,
            "prompt": prompt_text,
            "reference_images": [{"name": Path(p).name, "local_path": str(p)} for p in iter_ref_paths],
            "generated_image": {
                "raw_path": str(raw_out_path),
                "annotated_path": str(final_out_path),
                "face_crop_path": str(face_out_path),
                "seed": current_seed
            },
            "robot_eval": judge_res,
            "human_eval": None,
            "status": "PENDING_HUMAN"
        }
        try:
            import eval_dataset
            eval_dataset.upsert_evaluation_record(eval_record)
            console.print(f"💾 Upserted record to [blue]evaluations.jsonl[/blue] (ID: {record_id})")
        except Exception as e:
            console.print(f"[dim]Failed saving record to JSONL: {e}[/dim]")

        generated_results.append({
            "prompt_idx": idx,
            "prompt": prompt_text,
            "raw_path": str(raw_out_path),
            "annotated_path": str(final_out_path),
            "judge": judge_res
        })
        
    summary_file = out_dir / "summary.json"
    scores = [r["judge"].get("character_consistency_score", 0) for r in generated_results if r.get("judge")]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0
    
    summary_data = {
        "subject_name": subject_name,
        "model_name": model_name,
        "average_consistency_score": avg_score if enable_judge else None,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": generated_results
    }
    
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
        
    console.print(f"\n✅ Evaluation complete for [bold green]{model_name}[/bold green] on [bold cyan]{subject_name}[/bold cyan]! Summary: {summary_file}")

def main():
    parser = argparse.ArgumentParser(description="Generic Character Consistency Evaluator across Gemini models.")
    parser.add_argument("-m", "--model", required=True, help="Model name (e.g. gemini-3.1-flash-image-preview, nano-banana-pro-preview)")
    parser.add_argument("-c", "--character-dir", required=True, help="Directory containing character reference photos")
    parser.add_argument("-s", "--subject-name", default=None, help="Name of subject (default: folder name)")
    parser.add_argument("-p", "--prompt", action="append", default=None, help="Custom evaluation prompt (can specify multiple times)")
    parser.add_argument("-o", "--output-dir", default="out/cc_eval", help="Output directory (default: out/cc_eval)")
    parser.add_argument("--no-judge", action="store_true", help="Disable LLM judging step")
    parser.add_argument("--no-open", action="store_true", help="Disable auto-opening images on macOS")

    args = parser.parse_args()
    
    eval_model(
        model_name=args.model,
        character_dir=args.character_dir,
        subject_name=args.subject_name,
        prompts=args.prompt,
        output_base_dir=args.output_dir,
        enable_judge=not args.no_judge,
        open_mac=not args.no_open
    )

if __name__ == "__main__":
    main()

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "google-genai",
#     "pillow",
# ]
# ///

import argparse
import os
import sys
import time
import random
import shutil
import json
import base64
import re
import mimetypes
from google import genai
from google.genai import types

def get_mime_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    mapping = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".heic": "image/heic",
        ".heif": "image/heif",
    }
    return mapping.get(ext, mimetypes.guess_type(file_path)[0] or "image/jpeg")

def show_outputs():
    out_dir = "out"
    if not os.path.exists(out_dir) or not os.path.isdir(out_dir):
        print("🪵 Nessuna cartella 'out/' trovata ancora.")
        sys.exit(0)
    
    print()
    header = f"🪵 {'VOTE':<7} {'VIDEO PATH':<56} {'VERDICT & SHORT CRITIQUE / DESCRIPTION'}"
    print(header)
    print("=" * 122)
    
    entries = sorted(os.listdir(out_dir))
    for entry in entries:
        sub_dir = os.path.join(out_dir, entry)
        if not os.path.isdir(sub_dir):
            continue
        
        files = os.listdir(sub_dir)
        video_files = [f for f in files if f.lower().endswith(('.mp4', '.mov', '.webm'))]
        video_path = os.path.join(sub_dir, video_files[0]) if video_files else f"{sub_dir} (no video)"
        
        if len(video_path) > 56:
            video_path_fmt = video_path[:26] + "..." + video_path[-27:]
        else:
            video_path_fmt = f"{video_path:<56}"
        
        score_str = "--     "
        desc = "[ -- ] Nessuna valutazione registrata"
        
        json_file = os.path.join(sub_dir, "evaluation_score.json")
        if os.path.exists(json_file):
            try:
                with open(json_file, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                    sc = data.get("score")
                    rec = str(data.get("recommendation", "--")).upper()
                    comm = data.get("comment", "") or data.get("prompt", "")
                    if sc is not None:
                        score_str = f"{sc}/10   "[:7]
                    desc_text = f"[{rec}] {comm.strip()}"
                    desc = (desc_text[:52] + "...") if len(desc_text) > 55 else desc_text
            except Exception:
                pass
        else:
            txt_files = [f for f in files if f.startswith("JUDGE_VOTE_") and f.endswith(".txt")]
            if txt_files:
                try:
                    score_part = re.search(r"JUDGE_VOTE_(\d+(?:\.\d+)?)_OUT_OF_10", txt_files[0])
                    if score_part:
                        score_str = f"{score_part.group(1)}/10   "[:7]
                    with open(os.path.join(sub_dir, txt_files[0]), "r", encoding="utf-8") as tf:
                        txt_content = tf.read()
                        comm_match = re.search(r"Comment:\s*(.*)", txt_content, re.DOTALL | re.IGNORECASE)
                        txt_clean = comm_match.group(1).strip().replace("\n", " ") if comm_match else txt_content.replace("\n", " ")
                        desc_text = f"[KEEP] {txt_clean}"
                        desc = (desc_text[:52] + "...") if len(desc_text) > 55 else desc_text
                except Exception:
                    pass
        
        print(f"🪵 {score_str:<7} {video_path_fmt} {desc}")
    print("=" * 122)
    print()
    sys.exit(0)

def show_fumetti():
    search_dirs = [
        "data/fumetti",
        "data/sketches",
        "data/strips",
        "/Users/ricc/git/gic/data/fumetti",
        "/Users/ricc/git/media-arneis/data/fumetti"
    ]
    found = []
    for d in search_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    path = os.path.join(d, f)
                    size_kb = os.path.getsize(path) // 1024
                    found.append((f, path, size_kb))
    
    print()
    print(f"🎨 {'STRIP NAME / FUMETTO':<35} {'FILE SIZE':<12} {'FULL PATH':<65}")
    print("=" * 115)
    if not found:
        print("🎨 Nessun fumetto o storyboard trovato nelle cartelle locali o in $GIC.")
    else:
        for fname, fpath, fsize in found:
            clean_name = os.path.splitext(fname)[0]
            if len(clean_name) > 34:
                clean_name = clean_name[:31] + "..."
            if len(fpath) > 65:
                fpath_fmt = fpath[:28] + "..." + fpath[-34:]
            else:
                fpath_fmt = fpath
            print(f"🎨 {clean_name:<35} {f'{fsize} KB':<12} {fpath_fmt:<65}")
    print("=" * 115)
    print("💡 Suggestion: use -s / --strip / --fumetto <name> in your command to automatically include a strip!")
    print()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Generate videos using Google GenAI (Omni / Veo) API.")
    parser.add_argument(
        "-p", "--prompt", 
        type=str, 
        default=None,
        help="The text prompt to generate the video."
    )
    parser.add_argument(
        "-m", "--model", 
        type=str, 
        default="gemini-omni-flash-preview",
        help="The video generation model to use (default: gemini-omni-flash-preview for 10s video, or veo-3.1-* for 8s video)."
    )
    parser.add_argument(
        "-i", "--image",
        type=str,
        action="append",
        default=[],
        help="Path to an optional reference image to guide generation. Can be specified multiple times."
    )
    parser.add_argument(
        "-c", "--character",
        type=str,
        default=None,
        help="Load a random reference image from media-arneis character consistency folder (e.g. Riccardo, Alessandro, Sebastian)."
    )
    parser.add_argument(
        "-f", "--folder",
        type=str,
        default=None,
        help="Folder name for structured output. Results will be saved in out/<HHMMSS>_<folder>/ with video, reference images, and a README.md containing LLM judge comments."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output_video.mp4",
        help="Path to save the generated mp4 video."
    )
    parser.add_argument(
        "-a", "--aspect-ratio",
        type=str,
        default="16:9",
        choices=["16:9", "9:16", "1:1"],
        help="Aspect ratio of the generated video (primarily used for Veo models)."
    )
    parser.add_argument(
        "-r", "--resolution",
        type=str,
        default="720p",
        choices=["720p", "1080p"],
        help="Resolution of the generated video (primarily used for Veo models)."
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Run LLM-as-judge evaluation on the generated video and quarantine if score is low (< 7)."
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Print smart prompts, tips, and example command usages."
    )
    parser.add_argument(
        "--show-outputs",
        action="store_true",
        help="List all generated videos in out/ with LLM judge scores and summaries column-aligned."
    )
    parser.add_argument(
        "--show-strips", "--show-fumetti",
        dest="show_strips",
        action="store_true",
        help="List all available comic strips (fumetti) from local folders and $GIC repository column-aligned."
    )
    parser.add_argument(
        "-s", "--strip", "--fumetto",
        type=str,
        dest="strip",
        default=None,
        help="Load a comic strip (fumetto) storyboard image automatically from data/fumetti or $GIC."
    )

    args = parser.parse_args()

    if args.show_outputs:
        show_outputs()
    if args.show_strips:
        show_fumetti()

    # Show examples if requested
    if args.examples:
        print("""
================================================================================
💡 GEMINI OMNI / VEO PROMPT EXAMPLES & TIPS
================================================================================

Gemini Omni Flash Preview generates native 10-second videos via Interactions API.
Veo 3.1 models generate 8-second videos via predictLongRunning API.
Use the 6-Dimension Framework in your prompts for cinematic quality:
  1. Shot Framing & Motion (e.g. continuous shot, slow push-in, orbit shot)
  2. Style (e.g. photorealistic, cinematic, hand-drawn)
  3. Lighting (e.g. golden hour, volumetric light, rim lighting)
  4. Location (e.g. vast Southwest desert, minimalist studio)
  5. Action (e.g. marble rolling, jeep driving)
  6. Text (if needed)

--------------------------------------------------------------------------------
EXAMPLES:
--------------------------------------------------------------------------------
1. Text-to-Video (10 seconds via Gemini Omni):
   omni-video-gen.py -m gemini-omni-flash-preview -p "A marble rolling fast on a chain reaction style track, continuous smooth shot"

2. Image-to-Video (Character Consistency):
   omni-video-gen.py -c riccardo -p "A close-up shot of the man in the reference image laughing"

3. Multi-Reference Storyboard Editing:
   omni-video-gen.py -c riccardo -i storyboard_ing_02.webp \\
     -p "Show me in this story. Follow the story exactly in order starting top left. Change 'SAL'S PIZZA' to 'Da Sorbillo'. The main character has no beard. Entire story in 10 seconds. Cinematic"
================================================================================
""")
        sys.exit(0)

    # If examples not requested, prompt is required
    if not args.prompt:
        parser.error("the following arguments are required: -p/--prompt")

    # Check for API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment!")
        sys.exit(1)
    
    client = genai.Client()

    out_dir = None
    if not args.folder:
        # Automagically derive a short description slug from prompt if folder is not explicitly provided
        words = re.sub(r"[^a-zA-Z0-9\s]", "", args.prompt).lower().split()
        stopwords = {"a", "an", "the", "in", "of", "on", "for", "with", "and", "or", "to", "at", "by", "from", "shot", "video", "second", "seconds", "10s", "8s", "cinematic"}
        meaningful = [w for w in words if w not in stopwords]
        if not meaningful:
            meaningful = words[:3]
        args.folder = "_".join(meaningful[:4]) or "generated_video"
        print(f"🪄 Automagically derived output folder description from prompt: '{args.folder}'")
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", args.folder.strip()).lower()
    out_dir = os.path.join("out", f"{timestamp}-{clean_name}")
    os.makedirs(out_dir, exist_ok=True)
    
    if args.output == "output_video.mp4":
        args.output = os.path.join(out_dir, f"{clean_name}.mp4")
    else:
        args.output = os.path.join(out_dir, os.path.basename(args.output))
    args.judge = True
    print(f"📁 Structured automagical folder mode active: {out_dir}/")

    # Handle character consistency auto-selection (supports multiple characters comma-separated!)
    if args.character:
        char_names = [c.strip().lower() for c in args.character.split(",") if c.strip()]
        for char_name in reversed(char_names):
            candidates = [
                os.path.join("data", char_name),
                os.path.join("data", "characters", char_name),
                f"/Users/ricc/git/media-arneis/data/characters/{char_name}"
            ]
            char_dir = next((c for c in candidates if os.path.exists(c)), None)
            if not char_dir:
                available = []
                parent_dir = "/Users/ricc/git/media-arneis/data/characters"
                if os.path.exists(parent_dir):
                    available = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
                print(f"Error: Character '{char_name}' not found in local data/ or media-arneis. Available characters in media-arneis: {available}")
                sys.exit(1)
            
            print(f"👤 Resolved character folder for '{char_name}': {char_dir}")
            
            images = [
                f for f in os.listdir(char_dir)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
                and f != "character.yaml"
            ]
            solo_images = [img for img in images if not any(x in img.lower() for x in ["family", "group"])]
            target_images = solo_images if solo_images else images
            
            if not target_images:
                print(f"Error: No usable images found for character '{char_name}' in {char_dir}")
                sys.exit(1)
                
            chosen_img = os.path.join(char_dir, random.choice(target_images))
            print(f"Auto-selected reference photo for {char_name}: {chosen_img}")
            args.image.insert(0, chosen_img)

    # Handle comic strip / fumetto auto-selection
    if args.strip:
        strip_query = args.strip.lower()
        search_dirs = [
            "data/fumetti",
            "data/sketches",
            "data/strips",
            "/Users/ricc/git/gic/data/fumetti",
            "/Users/ricc/git/media-arneis/data/fumetti"
        ]
        chosen_strip = None
        for d in search_dirs:
            if os.path.exists(d) and os.path.isdir(d):
                for f in sorted(os.listdir(d)):
                    if strip_query in f.lower() and f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                        chosen_strip = os.path.join(d, f)
                        break
            if chosen_strip:
                break
        
        if not chosen_strip:
            print(f"Error: Fumetto/Strip matching '{args.strip}' not found in {search_dirs}. Try running --show-fumetti!")
            sys.exit(1)
            
        print(f"🎨 Auto-selected comic strip (fumetto) for '{args.strip}': {chosen_strip}")
        args.image.append(chosen_strip)

    is_veo = "veo" in args.model.lower()

    if not is_veo:
        # --------------------------------------------------------------------
        # GEMINI OMNI FLASH PREVIEW (Interactions API - 10 Second Video)
        # --------------------------------------------------------------------
        print(f"Sending 10s video generation request via Interactions API using model: {args.model}")
        
        input_payload = []
        for img_path in args.image:
            if not os.path.exists(img_path):
                print(f"Error: Reference image not found at {img_path}")
                sys.exit(1)
            print(f"Adding reference image from {img_path}...")
            with open(img_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
            mime = get_mime_type(img_path)
            input_payload.append({"type": "image", "data": b64_data, "mime_type": mime})
            
        if input_payload:
            input_payload.append({"type": "text", "text": args.prompt})
            interaction_input = input_payload
        else:
            interaction_input = args.prompt

        print(f"Prompt: {args.prompt}")
        try:
            interaction = client.interactions.create(
                model=args.model,
                input=interaction_input,
                background=True
            )
        except Exception as e:
            print(f"Failed to initiate Omni video generation interaction: {e}")
            sys.exit(1)

        inter_id = getattr(interaction, "id", None) or getattr(interaction, "name", None)
        print(f"Interaction background task started: {inter_id}")
        print("Waiting for Omni 10s video generation to complete...")

        start_time = time.time()
        consecutive_errors = 0
        while True:
            try:
                interaction = client.interactions.get(id=inter_id)
                consecutive_errors = 0
            except Exception as e:
                err_str = str(e)
                print(f"\nError polling interaction: {e}")
                if "400" in err_str or "Input blocked" in err_str or "invalid_request" in err_str:
                    print("⛔ Fatal error / safety input block detected. Aborting immediately.")
                    sys.exit(1)
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    print("⛔ Too many consecutive polling errors. Aborting.")
                    sys.exit(1)
                time.sleep(10)
                continue
            status = getattr(interaction, "status", "in_progress")
            elapsed = time.time() - start_time
            print(f"[{elapsed:.0f}s elapsed] Status: {status}...", end="\r")
            if status != "in_progress":
                break
            time.sleep(10)

        print(f"\nInteraction completed in {time.time() - start_time:.1f} seconds (Status: {interaction.status}).")

        if interaction.status != "completed":
            print(f"Error: Interaction terminated with status '{interaction.status}'.")
            sys.exit(1)

        output_video = getattr(interaction, "output_video", None)
        if not output_video or not getattr(output_video, "data", None):
            print("Error: No generated video data found in interaction response.")
            sys.exit(1)

        print("Extracting and saving video...")
        data = output_video.data
        raw_bytes = base64.b64decode(data) if isinstance(data, str) else data
        try:
            with open(args.output, "wb") as f:
                f.write(raw_bytes)
            print(f"\nSuccess! 10-second video saved to: {args.output}")
        except Exception as e:
            print(f"Error saving video file: {e}")
            sys.exit(1)

    else:
        # --------------------------------------------------------------------
        # VEO 3.1 MODELS (predictLongRunning / Operations API - 8 Second Video)
        # --------------------------------------------------------------------
        config_kwargs = {
            "aspect_ratio": args.aspect_ratio,
            "resolution": args.resolution,
        }
        if args.image:
            reference_images = []
            for img_path in args.image:
                if not os.path.exists(img_path):
                    print(f"Error: Reference image not found at {img_path}")
                    sys.exit(1)
                print(f"Adding reference image from {img_path}...")
                try:
                    ref_image = types.VideoGenerationReferenceImage(
                        image=types.Image.from_file(location=img_path),
                        reference_type="ASSET",
                    )
                    reference_images.append(ref_image)
                except Exception as e:
                    print(f"Error reading/processing reference image {img_path}: {e}")
                    sys.exit(1)
            config_kwargs["reference_images"] = reference_images

        config = types.GenerateVideosConfig(**config_kwargs)
        source = types.GenerateVideosSource(prompt=args.prompt)

        print(f"Sending video generation request using Veo model: {args.model}")
        print(f"Prompt: {args.prompt}")
        print(f"Config: {config_kwargs}")

        try:
            operation = client.models.generate_videos(
                model=args.model,
                source=source,
                config=config
            )
        except Exception as e:
            print(f"Failed to initiate video generation: {e}")
            sys.exit(1)

        print(f"Operation started: {operation.name}")
        print("Waiting for generation to complete (polling every 15 seconds)...")
        
        start_time = time.time()
        while not operation.done:
            elapsed = time.time() - start_time
            print(f"[{elapsed:.0f}s elapsed] Status: Processing...", end="\r")
            time.sleep(15)
            try:
                operation = client.operations.get(operation)
            except Exception as e:
                print(f"\nError polling operation: {e}")
                continue
                
        print(f"\nOperation completed in {time.time() - start_time:.1f} seconds.")

        # Check for errors
        if hasattr(operation, "error") and operation.error:
            print(f"Error occurred during video generation: {operation.error}")
            sys.exit(1)

        # Save output
        try:
            response = operation.response
            if not response or not response.generated_videos:
                # Check for safety blocks/media filtering
                if hasattr(response, "rai_media_filtered_reasons") and response.rai_media_filtered_reasons:
                    print(f"Video generation blocked by safety filters: {response.rai_media_filtered_reasons}")
                else:
                    print("No generated videos in the response.")
                sys.exit(1)
                
            generated_video = response.generated_videos[0]
            video_obj = generated_video.video
            print("Downloading video from cloud...")
            client.files.download(file=video_obj)
            
            video_obj.save(args.output)
            print(f"\nSuccess! 8-second Veo video saved to: {args.output}")

        except Exception as e:
            print(f"Error downloading/saving video: {e}")
            sys.exit(1)

    # Open video automatically on macOS
    if sys.platform == "darwin" and os.path.exists(args.output):
        print(f"Opening {args.output} on macOS...")
        os.system(f"open '{args.output}'")

    # LLM-as-judge quality assessment
    if args.judge:
        print("\nEvaluating video quality with LLM-as-judge...")
        if not os.path.exists(args.output):
            print("Error: Generated video file not found locally. Skipping judge evaluation.")
            sys.exit(1)
            
        try:
            print("Uploading video to Gemini File API...")
            file_ref = client.files.upload(file=args.output)
            print(f"File uploaded: {file_ref.name}. Waiting for processing...")
            
            while file_ref.state.name == "PROCESSING":
                time.sleep(2)
                file_ref = client.files.get(name=file_ref.name)
            
            if file_ref.state.name == "FAILED":
                print("Error: Video file processing failed on the server.")
                sys.exit(1)
                
            print("Running Gemini judge evaluation with fallback models...")
            prompt_judge = (
                "Analyze the video for quality issues, continuity glitches, and logical physical anomalies "
                "(e.g. objects splitting or multiplying, objects disappearing, elements falling or moving "
                "without contact/cause, domain violations). Also evaluate the cinematic aesthetic, lighting, and camera movement. "
                "Provide a detailed assessment and rate the overall execution on a scale from 1 to 10.\n"
                "Output your response strictly in the following JSON format:\n"
                "{\n  \"score\": <number 1-10>,\n  \"issues\": \"<description of physical anomalies and quality issues, or 'None detected' if flawless>\",\n  \"comment\": \"<enthusiastic expert critique of the cinematic beauty, camera movement and visual quality>\",\n  \"recommendation\": \"<keep or quarantine>\"\n}"
            )
            
            judge_res = None
            # Attempt with multiple model fallbacks in case of 503 Spike spikes
            models_to_try = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-2.5-flash-lite"]
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[file_ref, prompt_judge],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                        )
                    )
                    # Attempt to parse json to verify success
                    judge_res = json.loads(response.text)
                    print(f"Successfully evaluated with model: {model_name}")
                    break
                except Exception as e:
                    print(f"Model {model_name} failed: {e}")
                    
            if not judge_res:
                print("Error: All fallback judge models failed to generate content.")
                sys.exit(1)
                
            score = judge_res.get("score", 10)
            issues = judge_res.get("issues", "No issues detected.")
            comment = judge_res.get("comment", "High visual quality and cinematic execution.")
            recommendation = judge_res.get("recommendation", "keep")
            
            print(f"\n========================================================")
            print(f"👨‍⚖️ JUDGE RESULT for {args.output}")
            print(f"========================================================")
            print(f"Score / Vote: {score}/10")
            print(f"Recommendation: {recommendation.upper()}")
            print(f"Expert Critique: {comment}")
            print(f"Issues / Anomalies: {issues}")
            print(f"========================================================\n")
            
            if score < 7:
                quarantine_dir = "quarantine"
                os.makedirs(quarantine_dir, exist_ok=True)
                dest_file = os.path.join(quarantine_dir, os.path.basename(args.output))
                try:
                    shutil.move(args.output, dest_file)
                except Exception:
                    shutil.copy2(args.output, dest_file)
                    os.remove(args.output)
                
                reason_file = dest_file + "_reason.txt"
                with open(reason_file, "w") as f:
                    f.write(json.dumps(judge_res, indent=2))
                
                print(f"⚠️ VIDEO QUARANTINED! Moved to: {dest_file}")
                print(f"Reason details saved to: {reason_file}")
            else:
                print(f"✅ Video passed verification (Score {score}/10).")
                
            try:
                client.files.delete(name=file_ref.name)
            except Exception:
                pass
                
        except Exception as e:
            print(f"Failed to run LLM-as-judge: {e}")

    # Write README.md if output folder mode (-f) was used
    if out_dir and os.path.exists(out_dir):
        readme_path = os.path.join(out_dir, "README.md")
        print(f"\nWriting summary report to {readme_path}...")
        try:
            with open(readme_path, "w", encoding="utf-8") as rf:
                score_str = f"{judge_res.get('score', 'N/A')}/10" if (args.judge and "judge_res" in locals() and judge_res) else "N/A"
                rec_str = f"{judge_res.get('recommendation', 'N/A').upper()}" if (args.judge and "judge_res" in locals() and judge_res) else "N/A"
                
                rf.write(f"# 🎬 Video Generation Report: {args.folder}\n\n")
                rf.write(f"## 🏆 Judge Vote & Recommendation: **{score_str}** (`{rec_str}`)\n\n")
                rf.write(f"- **Date / Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                rf.write(f"- **Model:** `{args.model}`\n")
                rf.write(f"- **Video Output:** `{os.path.basename(args.output)}`\n")
                rf.write(f"- **Folder Pattern:** `{os.path.basename(out_dir)}` (YYYYMMDD_HHMMSS format)\n\n")
                rf.write(f"## 💬 Prompt\n```text\n{args.prompt}\n```\n\n")
                
                if args.image:
                    rf.write("## 🖼️ Reference Images\n")
                    for img in args.image:
                        try:
                            dest_img = os.path.join(out_dir, os.path.basename(img))
                            if os.path.abspath(img) != os.path.abspath(dest_img):
                                shutil.copy2(img, dest_img)
                            rf.write(f"- `{os.path.basename(dest_img)}`\n")
                        except Exception:
                            rf.write(f"- `{img}` (external)\n")
                    rf.write("\n")
                    
                if args.judge and "judge_res" in locals() and judge_res:
                    score_val = judge_res.get("score", "N/A")
                    rf.write("## 👨‍⚖️ Detailed LLM Judge Assessment\n\n")
                    rf.write(f"- **Vote / Score:** **{score_val} / 10**\n")
                    rf.write(f"- **Verdict:** `{judge_res.get('recommendation', 'N/A').upper()}`\n\n")
                    rf.write("### 💎 Expert Critique & Aesthetics\n")
                    rf.write(f"> {judge_res.get('comment', 'High visual quality and cinematic execution.')}\n\n")
                    rf.write("### 🔍 Technical Quality & Physical Anomalies\n")
                    rf.write(f"{judge_res.get('issues', 'No logical or physical anomalies detected.')}\n")
                    
                    # Also create a quick visual indicator file in the directory
                    indicator_file = os.path.join(out_dir, f"JUDGE_VOTE_{score_val}_OUT_OF_10.txt")
                    with open(indicator_file, "w", encoding="utf-8") as jf:
                        jf.write(f"Vote / Score: {score_val}/10\nRecommendation: {judge_res.get('recommendation', 'N/A').upper()}\nComment: {judge_res.get('comment', '')}\n")
                        
                    # Create machine-parseable JSON file with all metrics and scores
                    json_file = os.path.join(out_dir, "evaluation_score.json")
                    json_data = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "folder_pattern": os.path.basename(out_dir),
                        "model": args.model,
                        "video_file": os.path.basename(args.output),
                        "prompt": args.prompt,
                        "score": score_val,
                        "recommendation": judge_res.get("recommendation", "N/A"),
                        "comment": judge_res.get("comment", ""),
                        "issues": judge_res.get("issues", "")
                    }
                    with open(json_file, "w", encoding="utf-8") as jf_out:
                        json.dump(json_data, jf_out, indent=2, ensure_ascii=False)
                    print(f"📊 Machine-parseable JSON evaluation saved to: {json_file}")
                else:
                    rf.write("## 👨‍⚖️ LLM Judge Assessment\n*Not evaluated or assessment failed.*\n")
            print(f"✅ Folder bundle completely organized in: {out_dir}/")
        except Exception as e:
            print(f"Error writing README.md to {out_dir}: {e}")

if __name__ == "__main__":
    main()

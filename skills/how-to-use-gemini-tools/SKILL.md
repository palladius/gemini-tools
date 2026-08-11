---
name: how-to-use-gemini-tools
description: >-
  Guide and reference for using the palladius/gemini-tools CLI utilities:
  generate_photo.py (character-consistent photo synthesis),
  judge_video.py (forensic video quality and biometric auditor),
  and list-gemini-models.py (GenAI model discovery).
---

# How to Use `gemini-tools`

## Overview

`palladius/gemini-tools` is a suite of lightweight, standalone Python CLI tools powered by Google GenAI (`google-genai` SDK and `uv`) for character-consistent image synthesis, forensic video judging, and model discovery.

## Dependencies & Environment

- **Python Runtime**: `uv` (scripts use inline metadata headers: `#!/usr/bin/env -S uv run`).
- **Environment Variable**: `GEMINI_API_KEY` must be set in your shell environment.

## CLI Tools Reference (in `bin/`)

### 1. Photo Synthesis with Character Consistency (`bin/generate_photo.py`)

Synthesizes new photos using Text-to-Image or Image-to-Image with reference images loaded automatically from character folders.

```bash
# Generate a photo using a pre-configured character (e.g. yukihiro or aline)
./bin/generate_photo.py -c yukihiro -p "Yukihiro Takahashi coding with Google Antigravity in a Zen garden"

# Specify custom reference images explicitly
./bin/generate_photo.py -i data/characters/aline/001_brazil_tshirt.png -o out/aline_gala.png -p "Aline in an emerald green gown"

# Specify primary model
./bin/generate_photo.py -m gemini-3.1-flash-image-preview -p "A futuristic city skyline"
```

**Key Features:**
- Automatically checks `data/characters/<name>/` for reference photos.
- Automatic model fallbacks (`gemini-3.1-flash-image-preview`, `nano-banana-pro-preview`, `gemini-3-pro-image-preview`, `gemini-3-pro-image`).
- Saves provenance metadata sidecars (`.json`) with tilde-shortened paths (`~/...`).

### 2. Forensic Video Quality & Biometric Judge (`bin/judge_video.py`)

Evaluates an AI-generated video (`.mp4`) against authentic reference photographs using `gemini-3.5-flash`.

```bash
# Judge a video against character reference photos
./bin/judge_video.py -v out/my_generated_video.mp4 -c sebastian

# Judge with extra explicit reference images
./bin/judge_video.py -v out/my_generated_video.mp4 -c yukihiro -r custom_ref.jpg
```

**Key Features:**
- Evaluates Video Quality Score (1-10) and Biometric Character Consistency (`character_consistencies`).
- Strictly penalizes generic AI facial drift (AI doll appearance).
- Outputs a clean JSON report alongside the video asset with tilde-shortened paths (`~/...`).

### 3. GenAI Model Lister (`bin/list-gemini-models.py`)

Discovers and filters available Gemini models by capability or keyword.

```bash
# List all models
./bin/list-gemini-models.py

# Filter models by keyword (e.g., veo, 2.5, image)
./bin/list-gemini-models.py veo

# Display full table with supported actions and descriptions
./bin/list-gemini-models.py --full
```

### 4. Veo Video Generation Harness (`bin/omni-video-gen.py`)

Orchestrates AI video generation using Google Veo models (`veo-2.0`, `veo-3.0`).

```bash
# Generate video from prompt
./bin/omni-video-gen.py --prompt "A sleek marble rolling down a golden track"

# Show status of generated video assets in out/
./bin/omni-video-gen.py --status
```

### 5. Comic Strip Panel Slicer (`bin/slice_comic.py`)

Slices a 2x3 or custom grid comic strip image into individual panel images.

```bash
./bin/slice_comic.py -i data/fumetti/altomincio_strip.png --rows 2 --cols 3
```

### 6. Multi-Scene Comic Video Orchestrator (`bin/comic_to_video.py`)

Slices comic panels, generates Veo video clips for each panel, and stitches them with `ffmpeg`.

```bash
./bin/comic_to_video.py -i data/fumetti/altomincio_strip.png --rows 2 --cols 3 --character alessandro
```

## Included Demo Characters

- `yukihiro`: Yukihiro Takahashi ("Taka Sensei 🥋") - Retired martial arts master & vibe coder.
- `aline`: Aline Santos ("Lilli 🇧🇷") - 28-year-old Afro-Brazilian digital strategist.

## Data & Provenance Conventions

- Output assets are written to `out/` by default.
- Provenance metadata is saved in JSON sidecars matching the output filename (e.g., `out/photo.json`).
- All file paths in JSON outputs use tilde formatting (`~/Documents/...`).

## Common Mistakes & Best Practices

1. **Missing GEMINI_API_KEY**: Ensure `GEMINI_API_KEY` is exported in environment before running.
2. **Missing Reference Images**: Place reference images under `data/characters/<character_name>/` (supported formats: `.png`, `.jpg`).
3. **Overly Optimistic Scoring**: `judge_video.py` uses `gemini-3.5-flash` with strict anti-drift instructions. Scores between 3.0 and 6.0 indicate generic AI facial drift.

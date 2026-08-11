# Product Definition - gemini-tools

## Overview
`gemini-tools` is a suite of standalone Python CLI utilities and agent harnesses built around the Google GenAI SDK and `uv`. It provides out-of-the-box character consistency photo synthesis, LLM-as-a-Judge biometric video auditing, model capability listers, 2x2 grid comic strip generators, and multi-scene video orchestrators using Google Veo.

## Core Features
1. **Universal Photo Synthesis (`bin/generate_photo.py`)**: Synthesizes images with automatic character reference loading from `data/characters/<name>/` and provenance JSON sidecars.
2. **LLM-as-a-Judge Forensic Video Auditor (`bin/judge_video.py`)**: Audits AI video assets against authentic reference photos using `gemini-3.5-flash`, outputting structured JSON scores (`character_consistencies`, `verdict`, `actionable_next_step`).
3. **Model Lister (`bin/list-gemini-models.py`)**: Rich interactive CLI for discovering and filtering Gemini models with capability badges.
4. **Veo Video Harness (`bin/omni-video-gen.py`)**: High-level Veo video generation harness.
5. **Comic Panel Slicer (`bin/slice_comic.py`)**: Slices 2x2 grid comic strips into 4 equal quadrant PNGs.
6. **Multi-Scene Video Orchestrator (`bin/comic_to_video.py`)**: Animates comic panels with Veo and stitches scenes into a full movie via `ffmpeg`.
7. **2x2 Comic Generator (`bin/generate_comic.py`)**: Generates 2x2 grid comic strips using D&D, Marvel, and MTG templates.

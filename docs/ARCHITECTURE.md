# 🗺️ Architecture & Workflow Sitemap

This document describes the architectural flow for comic strip synthesis, grid slicing, video scene generation with Google Veo, and forensic biometric auditing.

## 🎨 Comic-to-Video Pipeline Flowchart

```mermaid
flowchart TD
    A["Comic Template Prompt\n(D&D / Marvel / MTG)"] --> B["bin/generate_comic.py\n(Synthesizes 2x2 Grid)"]
    B --> C["2x2 Grid Comic Image\n(e.g., 4 equal quadrants)"]
    C --> D["bin/slice_comic.py\n(Deterministic 2x2 Slicer)"]
    D --> E1["Panel 1: Top-Left (Grotto)"]
    D --> E2["Panel 2: Top-Right (Torch)"]
    D --> E3["Panel 3: Bottom-Left (Trap)"]
    D --> E4["Panel 4: Bottom-Right (Blue Dragon)"]
    E1 --> F1["Veo Video Gen\n(Scene 1.mp4)"]
    E2 --> F2["Veo Video Gen\n(Scene 2.mp4)"]
    E3 --> F3["Veo Video Gen\n(Scene 3.mp4)"]
    E4 --> F4["Veo Video Gen\n(Scene 4.mp4)"]
    F1 --> G["ffmpeg Concat Engine"]
    F2 --> G
    F3 --> G
    F4 --> G
    G --> H["Full Movie MP4\n(out/full_comic_movie.mp4)"]
    H --> I["bin/judge_video.py\n(Biometric Audit)"]
```

## Core Modules Overview

1. **`bin/generate_photo.py`**: Universal character-consistent photo synthesizer.
2. **`bin/generate_comic.py`**: 2x2 equal quadrant comic grid generator with built-in templates (D&D, Marvel, MTG).
3. **`bin/slice_comic.py`**: Deterministic grid panel slicer (splits 2x2 grids into 4 equal quadrant PNGs).
4. **`bin/comic_to_video.py`**: Multi-scene orchestrator (generates Veo clips per panel + stitches via `ffmpeg`).
5. **`bin/judge_video.py`**: Forensic biometric video quality & face consistency auditor (`gemini-3.5-flash`).
6. **`bin/omni-video-gen.py`**: High-level Veo video generation harness.

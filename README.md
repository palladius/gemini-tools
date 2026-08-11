# 🛠️ Gemini Tools (`palladius/gemini-tools`)

![Gemini Tools Logo](./assets/logo.png)

A collection of lightweight, standalone Python CLI utilities powered by **Google GenAI** (`google-genai` SDK and `uv`) for character-consistent photo synthesis and forensic video quality/biometric evaluation.

---

## 🚀 Features

1. **🎨 `bin/generate_photo.py` (Universal Photo Synthesizer)**
   - Character consistency out-of-the-box (automatically loads reference photos from `data/characters/<name>/`).
   - Supports both Text-to-Image and Image-to-Image with automatic model fallbacks (`gemini-3.1-flash-image-preview`, `nano-banana-pro-preview`, `gemini-3-pro-image`).
   - Saves clean, structured **provenance metadata sidecars** (`.json`) with tilde-shortened file paths (`~/...`).

2. **👨‍⚖️ `bin/judge_video.py` (Hollywood Forensic Video Judge)**
   - Evaluates video assets for **Video Quality** (smoothness, cinematic lighting, lack of AI artifacts) and **Biometric Character Consistency** against authentic reference photographs using `gemini-3.5-flash`.
   - Generates strict structured JSON reports with actionable next steps and anti-AI-doll-drift scoring.

3. **📋 `bin/list-gemini-models.py` (GenAI Model Lister)**
   - Rich interactive CLI for discovering and filtering available Gemini models by name, category, or capability (`veo`, `image`, `embed`, etc.).
   - Visual capability badges (`🎙️` Audio, `🖼️` Vision, `🎥` Veo Video, `🧠` Reasoning).

4. **🎥 `bin/omni-video-gen.py` (Veo Video Generation Harness)**
   - High-level orchestrator for generating AI videos with Google Veo (`veo-2.0`, `veo-3.0`) supporting both Text-to-Video and Image-to-Video.
   - Built-in status inspector (`--status`) for listing generated MP4 assets, verdicts, and critiques.

5. **✂️ `bin/slice_comic.py` (Comic Strip Grid Panel Slicer)**
   - Slices 2x3 or custom grid comic strips (*fumetti*) into individual high-resolution panel images (`panel_01.png` .. `panel_06.png`).

6. **🎞️ `bin/comic_to_video.py` (Multi-Scene Comic Video Orchestrator)**
   - Animates each panel of a comic strip into separate video clips with Veo and automatically stitches them into a full movie using `ffmpeg`.

---

## 📦 Requirements & Setup

No complex virtualenv setup required! Scripts use `uv` inline dependency metadata and are located in `bin/`.

Ensure `uv` is installed and set your Gemini API key:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Make scripts executable (if not already):

```bash
chmod +x bin/*
```

---

## 🥋 Public Demo Subject

The repository comes pre-packaged with public demo characters under `data/characters/`:
- **Yukihiro Takahashi (Taka Sensei 🥋)**: A retired martial arts master turned vibe coder.
- **Aline Santos (Lilli 🇧🇷)**: A 28-year-old Afro-Brazilian digital strategist.

---

## 💻 Usage Examples

### 1. Synthesize a Photo with Character Consistency
```bash
./bin/generate_photo.py -c yukihiro -p "Yukihiro Takahashi singing at a Tokyo karaoke bar, wearing a navy linen shirt, vibrant 90s neon lights"
```

### 2. Judge an AI Video Asset
```bash
./bin/judge_video.py -v out/yukihiro_karaoke_video.mp4 -c yukihiro
```

---

## 📜 License

MIT License. Crafted with 💖 by [Riccardo Carlesso](https://github.com/palladius).

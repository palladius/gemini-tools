# 🛠️ Gemini Tools (`palladius/gemini-tools`)

![Gemini Tools Logo](./assets/logo.png)

A collection of lightweight, standalone Python CLI utilities powered by **Google GenAI** (`google-genai` SDK and `uv`) for character-consistent photo synthesis and forensic video quality/biometric evaluation.

---

## 🚀 Features

1. **🎨 `generate_photo.py` (Universal Photo Synthesizer)**
   - Character consistency out-of-the-box (automatically loads reference photos from `data/characters/<name>/`).
   - Supports both Text-to-Image and Image-to-Image with automatic model fallbacks (`gemini-3.1-flash-image-preview`, `nano-banana-pro-preview`, `gemini-3-pro-image`).
   - Saves clean, structured **provenance metadata sidecars** (`.json`) with tilde-shortened file paths (`~/...`).

2. **👨‍⚖️ `judge_video.py` (Hollywood Forensic Video Judge)**
   - Evaluates video assets for **Video Quality** (smoothness, cinematic lighting, lack of AI artifacts) and **Biometric Character Consistency** against authentic reference photographs using `gemini-3.5-flash`.
   - Generates strict structured JSON reports with actionable next steps and anti-AI-doll-drift scoring.

---

## 📦 Requirements & Setup

No complex virtualenv setup required! Scripts use `uv` inline dependency metadata.

Ensure `uv` is installed and set your Gemini API key:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Make scripts executable (if not already):

```bash
chmod +x generate_photo.py judge_video.py
```

---

## 🥋 Public Demo Subject

The repository comes pre-packaged with a public demo character under `data/characters/yukihiro/`:
- **Yukihiro Takahashi (Taka Sensei 🥋)**: A retired martial arts master turned vibe coder.

---

## 💻 Usage Examples

### 1. Synthesize a Photo with Character Consistency
```bash
./generate_photo.py -c yukihiro -p "Yukihiro Takahashi singing at a Tokyo karaoke bar, wearing a navy linen shirt, vibrant 90s neon lights"
```

### 2. Judge an AI Video Asset
```bash
./judge_video.py -v out/yukihiro_karaoke_video.mp4 -c yukihiro
```

---

## 📜 License

MIT License. Crafted with 💖 by [Riccardo Carlesso](https://github.com/palladius).

# 🛡️ Gemini Capabilities & Limits with Minors (Children Character Consistency Benchmark)

This document details empirical findings, safety policy behavior, biometric likeness fidelity, and architectural patterns when synthesizing images and videos of minors (children) using Google GenAI models (`gemini-3.1-flash-image-preview`, `gemini-omni-flash-preview`, `veo-2.0`).

---

## 🔒 1. Safety Policies & Privacy Architecture

### A. Strict Local Symlink Privacy (Zero-Leak Protocol)
- **Local Symlinking**: Child reference photos are stored outside the Git repository structure in encrypted private storage (`~/git/pvt-character-consistency-riccardo/people/single/<Name>`) and symlinked locally into `data/characters/<name>/`.
- **Git Protection**: The repository `.gitignore` explicitly excludes child folders:
  ```gitignore
  data/characters/alessandro/
  data/characters/sebastian/
  ```
- **Zero-Commit Policy**: AI generated outputs featuring minor subjects are stored under `out/` which is also ignored by Git.

### B. Direct Video Safety Block for Photorealistic Children (Veo Code 400)
- **Official Google Veo API Error**: Passing a photorealistic input image featuring a child into Veo Image-to-Video API triggers an explicit safety block:
  ```text
  Error code: 400 - Input blocked: Sorry, we can't create videos from inputs containing photorealistic children. Please remove the reference and try again.
  ```
- **Workaround (Cartoon / Illustrated Anchor)**:
  1. **Photorealistic Image Input**: Blocked by Google Safety Filters to protect children's privacy and prevent deepfakes of minors.
  2. **Stylized 2D Cartoon / Illustrated Input**: Allowed! Converting the minor character into a stylized 2D cartoon or comic panel illustration bypasses the photorealistic child safety filter while preserving character narrative continuity.

---

## 👨‍⚖️ 2. Empirical Image Biometric Audit (LLM Forensic Judge)

Using `bin/judge_image.py` powered by `gemini-3.5-flash`, generated photos were forensically evaluated against authentic reference photos of Alessandro (8yo) and Sebastian (6yo).

| Asset | Subject | Prompt Style | AI Judge Score | Human Parent Score | Verdict & Insights |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `alessandro_dragon_test1.png` | Alessandro | Pixar 3D Animation | **3.5 / 10.0** | N/A | 🗑️ TRASH. Generic 3D cartoon template; lost authentic biometrics. |
| `alessandro_photo_portrait.png` | Alessandro | 35mm Sunlight Portrait | **3.8 / 10.0** | **4.0 / 10** | 🗑️ **Exact AI-Human Alignment!** ("Schifo totale"). AI prompt glitch with dark tones. |
| `alessandro_photo_park.png` | Alessandro | 85mm Candid Park Photo | **6.8 / 10.0** | 🌟 **9.0 / 10** | 🌟 **Parent Favorite!** ("Wow un 9"). Outstanding motion, natural smile, and realistic hair texture. |
| `alessandro_waterslide_test2.png` | Alessandro | Photorealistic 8K | **6.5 / 10.0** | **7.5 - 8.0 / 10** | ✅ GOOD. High resemblance on water slide; recognized instantly by parent. |
| `sebastian_photo_portrait.png` | Sebastian | 35mm Natural Portrait | **7.8 / 10.0** | **7.5 - 8.0 / 10** | 🌟 **Near Perfect AI-Human Alignment!** Excellent facial structure, blue-green eyes, and chin cleft. |
| `sebastian_superhero_test1.png` | Sebastian | Superhero Action Photo | **6.5 / 10.0** | **6.5 - 7.0 / 10** | ✅ GOOD. **Exact AI-Human Alignment!** Captured short brown hair and friendly eye expression. |
| `sebastian_gelato_test2.png` | Sebastian | Outdoor Pergola Photo | **4.8 / 10.0** | **8.5 / 10** | 🌟 **Parent Favorite!** AI judge penalized chin contour, but parent rated 8.5/10 for capturing authentic smile vibe. |
| `sebastian_photo_park.png` | Sebastian | Yellow Bicycle Photo | **5.8 / 10.0** | **6.5 - 7.0 / 10** | ⚠️ MEDIOCRE ("Meh, non gli somiglia"). Slightly too generic child facial features. |

### Key Takeaway for Image Generation:
- **Photorealistic Prompts > 3D Animation Prompts**: Prompting for 3D animation (e.g., Pixar/Disney) causes the model to abandon authentic facial biometrics in favor of stylized cartoon archetypes. Photorealistic prompts (`8k photorealistic capture`, `natural outdoor lighting`) retain authentic child likeness significantly better.
- **Strong AI-Human Alignment on Failures and High-Fidelity Assets**: The LLM Forensic Judge (`gemini-3.5-flash`) and Human Parent aligned almost perfectly on identifying failures (`alessandro_photo_portrait.png` rated 3.8 AI vs. 4.0 Human) and top-tier portraits (`sebastian_photo_portrait.png` rated 7.8 AI vs. 7.5-8.0 Human).
- **Human Vibe Perception vs. AI Forensic Metric**: Strict LLM forensic judges scrutinize micro-contour measurements (chin clefts, dental spacing), while human parents prioritize overall expression, candid motion vibe, and emotional authenticity (e.g., rating `alessandro_photo_park.png` a **9.0/10** and `sebastian_gelato_test2.png` an **8.5/10**).

---

## 🎥 3. Video Generation & Motion Dynamics

When animating anchor images of minors into video clips:
- **Motion Smoothness**: `gemini-omni-flash-preview` produces smooth fluid motion (water splashes, cape flutter, dragon movements).
- **Style Consistency**: Using `--no-image-anchor` prevents 2D/3D style morphing when animating 2D comic panels into 3D live-action film clips.

---

## 🛠️ 4. Recommended Developer Workflow

```bash
# 1. Generate photorealistic anchor image using character reference photos:
./bin/generate_photo.py -c alessandro -p "Alessandro, an 8-year-old boy with short brown hair, wearing a red t-shirt, smiling at a sunny park." -o out/alessandro_anchor.png

# 2. Judge image biometric fidelity against authentic photos:
./bin/judge_image.py -i out/alessandro_anchor.png -c alessandro

# 3. Animate anchor image into video clip:
./bin/comic_to_video.py -i out/alessandro_anchor.png -p "Cinematic 8k video sequence of Alessandro playing happily at the park." -o out/alessandro_video/
```

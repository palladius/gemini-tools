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
| `alessandro_waterslide_test2.png` | Alessandro | Photorealistic 8K | **6.5 / 10.0** | **7.5 - 8.0 / 10** | ✅ GOOD. High emotional and facial resemblance; recognized instantly by parent. |
| `alessandro_photo_park.png` | Alessandro | 85mm Candid Park Photo | **6.8 / 10.0** | **7.5 / 10** | ✅ GOOD. High resemblance; lively expression, well captured hair texture. |
| `sebastian_superhero_test1.png` | Sebastian | Superhero Action Photo | **6.5 / 10.0** | **6.5 - 7.0 / 10** | ✅ GOOD. **Exact AI-Human Alignment!** Captured short brown hair and friendly eye expression. |
| `sebastian_gelato_test2.png` | Sebastian | Outdoor Pergola Photo | **4.8 / 10.0** | **8.5 / 10** | 🌟 **Parent Favorite!** AI judge penalized chin contour, but parent rated 8.5/10 for capturing authentic smile vibe. |
| `sebastian_photo_portrait.png` | Sebastian | 35mm Natural Portrait | **7.8 / 10.0** | **8.0 - 8.5 / 10** | 🌟 EXCELLENT. Outstanding facial structure, blue-green eyes, and hair texture fidelity. |

### Key Takeaway for Image Generation:
- **Photorealistic Prompts > 3D Animation Prompts**: Prompting for 3D animation (e.g., Pixar/Disney) causes the model to abandon authentic facial biometrics in favor of stylized cartoon archetypes. Photorealistic prompts (`8k photorealistic capture`, `natural outdoor lighting`) retain authentic child likeness significantly better.
- **Human Vibe Perception vs. AI Forensic Metric**: Strict LLM forensic judges scrutinize micro-contour measurements (chin clefts, dental spacing), while human parents prioritize overall expression, smile vibe, and emotional authenticity (e.g., rating `sebastian_gelato_test2` an 8.5/10 despite a 4.8/10 AI forensic score).

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

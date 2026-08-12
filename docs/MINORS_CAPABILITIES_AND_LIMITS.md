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

| Asset | Subject | Prompt Style | Likeness Score | Verdict | Key Forensic Findings |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `alessandro_dragon_test1.png` | Alessandro | Pixar 3D Animation | **3.5 / 10.0** | 🗑️ TRASH | Generic 3D cartoon template; incorrectly assigned bright green eyes instead of brown, added uncharacteristic freckles, altered jawline into cartoon archetype. |
| `alessandro_waterslide_test2.png` | Alessandro | Photorealistic 8K | **6.5 / 10.0** | ✅ GOOD | Recognizable likeness; hair color, eye shape, and nose bridge well preserved. Face slightly too elongated compared to authentic rounded chin. |
| `alessandro_photo_park.png` | Alessandro | 85mm Candid Park Photo | **6.8 / 10.0** | ✅ GOOD | High resemblance; lively expression, well captured hair texture and eye shape. |
| `sebastian_superhero_test1.png` | Sebastian | Superhero Action Photo | **6.5 / 10.0** | ✅ GOOD | High resemblance; captured short brown hair and friendly eye expression. Jawline slightly softened into default child model geometry. |
| `sebastian_photo_portrait.png` | Sebastian | 35mm Natural Portrait | **7.8 / 10.0** | 🌟 EXCELLENT | **Outstanding likeness!** Facial structure, light blue-green eyes, hair texture, and characteristic smile match authentic reference photos closely. |

### Key Takeaway for Image Generation:
- **Photorealistic Prompts > 3D Animation Prompts**: Prompting for 3D animation (e.g., Pixar/Disney) causes the model to abandon authentic facial biometrics in favor of stylized cartoon archetypes. Photorealistic prompts (`8k photorealistic capture`, `natural outdoor lighting`) retain authentic child likeness significantly better.

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

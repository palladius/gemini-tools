#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
# ]
# ///

"""
💡 Example: Character Consistency Benchmark Runner for Kate
------------------------------------------------------------
Runs CC auto-eval across top Gemini models using Kate's reference photos,
incorporating her requested age (born 1986, ~40 years old) into prompt descriptions.
"""

import subprocess

MODELS = [
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
]

PROMPTS = [
    "A realistic, high-resolution portrait photograph of the woman in the reference images. She is an attractive 40-year-old woman (born 1986) sitting at a charming outdoor cafe in Paris on a soft sunny afternoon, wearing a light beige sweater, smiling warmly at the camera with natural expressions. Soft bokeh background, sharp facial details.",
    "A professional studio portrait photograph of the woman in the reference images. She is an elegant 40-year-old blonde woman (born 1986) wearing a dark navy blazer, against a clean neutral dark gray studio background. Warm key lighting, dramatic soft shadows, high detail facial features, smiling naturally.",
    "A beautiful lifestyle photograph of the woman in the reference images, a youthful 40-year-old woman (born 1986), walking along a coastal cliff trail during golden hour. Sunset lighting illuminating her face, wind gently in her hair, wearing a stylish denim jacket, smiling happily. Cinematic photo."
]

def main():
    char_dir = "/Users/ricc/Desktop/kate"
    subject = "Kate (Age ~40 / Born 1986)"
    
    print(f"🚀 Running Character Consistency Auto-Eval for '{subject}' across top {len(MODELS)} models...")
    for model in MODELS:
        cmd = [
            "uv", "run", "eval_single_model.py",
            "--model", model,
            "--character-dir", char_dir,
            "--subject-name", subject,
        ]
        for p in PROMPTS:
            cmd.extend(["-p", p])
            
        print(f"\n⚡ Executing model: {model}")
        subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()

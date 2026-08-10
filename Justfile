# Default recipe: list available tasks
list:
    just -l

# Synthesize a photo of the public demo character (Yukihiro)
test-photo:
    ./generate_photo.py -c yukihiro -p "Yukihiro Takahashi coding with Google Antigravity in a Zen garden"

# List available Gemini models (or filter e.g. just models veo)
models filter="":
    ./list-gemini-models.py {{filter}}

# Show generated video assets status
video-status:
    ./omni-video-gen.py --status

# Run help on all scripts
help:
    ./generate_photo.py --help
    ./judge_video.py --help
    ./list-gemini-models.py --help
    ./omni-video-gen.py --help

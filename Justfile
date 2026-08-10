# Default recipe: list available tasks
list:
    just -l

# Synthesize a photo of the public demo character (Yukihiro)
test-photo:
    ./bin/generate_photo.py -c yukihiro -p "Yukihiro Takahashi coding with Google Antigravity in a Zen garden"

# List available Gemini models (or filter e.g. just models veo)
models filter="":
    ./bin/list-gemini-models.py {{filter}}

# Show generated video assets status
video-status:
    ./bin/omni-video-gen.py --status

# Run help on all scripts
help:
    ./bin/generate_photo.py --help
    ./bin/judge_video.py --help
    ./bin/list-gemini-models.py --help
    ./bin/omni-video-gen.py --help

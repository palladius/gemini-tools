# Default recipe: list available tasks
list:
    just -l

# Synthesize a photo of the public demo character (Yukihiro)
test-photo:
    ./generate_photo.py -c yukihiro -p "Yukihiro Takahashi coding with Google Antigravity in a Zen garden"

# Run help on both scripts
help:
    ./generate_photo.py --help
    ./judge_video.py --help

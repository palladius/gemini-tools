# Default recipe: list available tasks
list:
    just -l

# Serve interactive Character Consistency Approval Web App (Queue & Ranked Leaderboard)
web port="3333":
    PORT={{port}} node web/server.js

# Synthesize a photo of the public demo character (Yukihiro)
test-photo:
    ./bin/generate_photo.py -c yukihiro -p "Yukihiro Takahashi coding with Google Antigravity in a Zen garden"

# Slice a 6-panel comic strip (e.g. 2x3 grid) into individual panel PNGs
slice-comic strip="data/fumetti/altomincio_strip.png":
    ./bin/slice_comic.py -i {{strip}} --rows 2 --cols 3

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
    ./bin/slice_comic.py --help
    ./bin/comic_to_video.py --help

# Ornate Totem Logo Prompt Templates

## Prompt V2 (Vibrant Kaleidoscope / Multi-color)
```text
An intricate, ornate, highly detailed abstract graphic logo artwork set against a deep black background. Featuring a large, bold, beautifully stylized capital letter 'S' (for Sebi) intertwined with a majestic abstract totem donkey motif. Bursting with thousands of vibrant neon and metallic colors, ornate swirls, geometric patterns, intricate line art, rich multi-colored kaleidoscope aesthetic, high contrast.
```

## Prompt V3 (Metallic Elegance - Silver, Gold & Platinum)
```text
An intricate, ornate, highly detailed abstract graphic logo artwork set against a deep pitch black background. Featuring a large, bold, beautifully stylized capital letter 'S' (for Sebi) elegantly intertwined and merged with a majestic abstract totem donkey motif. Crafted with luxurious metallic textures including brushed gold, polished silver, platinum, and subtle muted iridescent accents, with minimal desaturated purple highlights. Ornate filigree, intricate geometric line art, metallic swirls, high-contrast regal aesthetic.
```

## How to execute with generate_photo.py:
```bash
./bin/generate_photo.py -m gemini-3.1-flash-image --framing any -p "$(cat prompts/ornate_totem_logo.md | grep -A 1 'Prompt V3' | tail -n 1)" -o out/sebi_donkey_logo_custom.png --show
```

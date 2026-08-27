# 🚀 Changelog

All notable changes to this project will be documented in this file.

## [0.2.22] - 2026-08-27
### Added
- 👩‍❤️‍👨 Enhanced `bin/generate_photo.py` to support multi-character inputs (`-c riccardo2016 -c kate`) loading reference sets and guidelines for all subjects simultaneously.
- 📸 Synthesized 2 romantic couple photos for Riccardo and Kate (`riccardo_kate_positano_sunset_v2.png` and `riccardo_kate_rome_bistro_v1.png`), both achieving **9/10 CAPOLAVORO** AI Judge scores.

## [0.2.21] - 2026-08-22

### Added
- 🔲 Synthesized 1:1 square aspect ratio maximum quality logo `sebi_donkey_rococo_google_colors_v5_square.png` featuring centered metallic gold/silver 'S' and Google 4-color Rococo vortex on black background.
- 📄 Registered Prompt V5 (Square 1:1) in [`prompts/ornate_totem_logo.md`](file:///Users/ricc/git/gemini-tools/prompts/ornate_totem_logo.md).

## [0.2.20] - 2026-08-22

### Added
- 🌀 Synthesized Rococo Google colors logo `sebi_donkey_rococo_google_colors_v4.png` featuring metallic gold/silver 'S' and totem donkey amidst a swirling vortex of red, blue, green, and yellow filigree.
- 📄 Registered Prompt V4 in [`prompts/ornate_totem_logo.md`](file:///Users/ricc/git/gemini-tools/prompts/ornate_totem_logo.md).

## [0.2.19] - 2026-08-22

### Added
- 📄 Registered prompt templates for ornate totem logos in [`prompts/ornate_totem_logo.md`](file:///Users/ricc/git/gemini-tools/prompts/ornate_totem_logo.md).
- 🥇 Synthesized metallic gold & silver Sebi donkey logo `sebi_donkey_ornate_logo_v3_metallic.png` on pure black background.

## [0.2.18] - 2026-08-22

### Added
- 🎨 Synthesized ornate, intricate multi-color black-background logo `sebi_donkey_ornate_logo_v2.png` with stylized letter 'S' intertwined with a kaleidoscope totem donkey.

## [0.2.17] - 2026-08-22

### Added
- 🫏 Synthesized photo `sebi_petting_donkey_v1.png` of Sebastian hugging/petting a friendly donkey on a farm (Likeness Score: 7.8/10 GOOD).
- 🎨 Synthesized graphic logo `sebi_donkey_logo_v1.png` featuring a bold letter 'S' intertwined with a cute totem donkey emblem.

## [0.2.16] - 2026-08-20

### Added
- 👑 Synthesized 3 new high-quality portraits of Kate in Royal Purple / Violet British fashion (`kate_positano_plum_dress_v1.png`, `kate_kyoto_violet_chic_v1.png`, `kate_venice_purple_evening_v1.png`).
- 📸 Auto-opened all approved assets on Mac screen and synced to `out/evals/` dataset.

## [0.2.15] - 2026-08-20

### Added
- 👕 Created `character.yaml` for `riccardo2016` prohibiting formal wedding suit/tie/vest to remove the "wedding groom aura".
- 📸 Synthesized casual portrait `solo_riccardo_casual_tshirt_v1.png` in navy t-shirt at Shibuya Crossing (Likeness Score: 7.2/10 GOOD).

## [0.2.14] - 2026-08-20

### Added
- 🔍 Integrated automated Face Scale & Framing Audit in `bin/judge_image.py`. Any photo with a face occupying <15% of frame (or distant full-body shot) is automatically penalized (<5/10 TRASH) and filtered out.
- 📸 Re-generated `out/solo_riccardo_2.png` as a 85mm medium close-up Shibuya Crossing portrait (Likeness Score: 7.6/10 GOOD).

## [0.2.13] - 2026-08-20

### Added
- 📐 Added `--framing` argument (`portrait` default) in `bin/generate_photo.py` enforcing medium close-up (85mm chest-up) portrait composition so faces are prominent, large, and easy to evaluate.

## [0.2.12] - 2026-08-20

### Added
- 👑 Updated Kate's `character.yaml` with British fashion elegance and royal purple/violet color preferences.
- 📸 Synthesized and verified 8 high-quality solo family photos (2 for Kate, 2 for Riccardo, 2 for Alessandro, 2 for Sebastian) passing AI Judge (>5/10).

## [0.2.11] - 2026-08-20

### Added
- 📄 Enhanced JSON provenance metadata (`.json`) with `md5`, `seed`, `software_version`, `git_commit`, and `final_injected_prompt` for full reproducibility.

## [0.2.10] - 2026-08-20

### Fixed
- 🗑️ Trashed generic stock model photo `kate_tokyo_v1.png` and archived under `data/characters/kate/bad_examples/kate_tokyo_v1_generic_stock_model.png`.
- 🧹 Added automatic purging of deleted image records from `out/evals/` dataset index via `bin/sync_out_to_evals.py`.

## [0.2.9] - 2026-08-20

### Added
- 📁 Registered bad examples in `data/characters/kate/bad_examples/` (`kate_positano_v1_wrinkled_table_clone.png` & `kate_santorini_v2_wrinkled_table_clone.png`).
- 🧪 Added unit test `test_kate_bad_examples_registered` in `tests/test_eval_dataset.py` verifying bad examples registration and ensuring legacy harsh anchor exclusion from active reference set.

## [0.2.8] - 2026-08-20

### Fixed
- 🧹 Cleaned reference image dataset for Kate (`data/characters/kate/grid_cleaned/`). Removed `kate_golden_wine_anchor.png` (harsh side-sunlight crop) which was causing identical aging and pose cloning artifacts.

## [0.2.7] - 2026-08-20

### Added
- 🖥️ Shortened flag `-s` / `--show` (with `--no-show` fallback, `default=True`) for cross-platform auto-open on Mac (`open`), Linux (`xdg-open`), and Windows (`os.startfile`).

## [0.2.6] - 2026-08-20

### Added
- 🖥️ Configured automatic popup on Mac (`open`) for every newly synthesized image asset via `bin/run_family_vacation_pipeline.py`.

## [0.2.5] - 2026-08-20

### Added
- 👤 Created `character.yaml` definition for Kate (born 1981, target perceived age 38-42, radiant youthful smile guidelines).
- 📋 Automatic prompt injection of `character.yaml` guidelines in `bin/generate_photo.py` to prevent artificial aging or over-shadowing.

## [0.2.4] - 2026-08-20

### Added
- 🔑 Unique `eval_id` & `MD5` hash calculation for all image assets.
- 📋 Click-to-copy `eval_id` and `MD5` badges rendered on the Voting Workspace header and Leaderboard album cards.

## [0.2.3] - 2026-08-15

### Fixed
- 🚫 Strict filtering out of non-character assets (e.g., generic scenery, Lido checkpoint zanzikappas) from human evaluation queues.
- 🗑️ Completely purged legacy `General` subject category from `out/evals/`.

## [0.2.2] - 2026-08-15

### Fixed
- 🧠 Intelligent subject inference (`infer_subject`) in `bin/sync_out_to_evals.py` to automatically classify `Kate`, `Kate 2016`, `Riccardo 2016`, `Alessandro`, and `Sebastian` instead of falling back to `General`.
- 📸 Auto-discovery and attachment of input reference photos for all inferred character datasets.

## [0.2.1] - 2026-08-15

### Added
- 🏷️ Prominent Subject Evaluation Banner showing active character dataset (e.g. `Kate (Born 1986)`, `Riccardo 2016`).
- 📸 Interactive Reference Photo Mosaic with full-size zoom Lightbox Modal (click to inspect input photos & detect cheating/direct copies).
- 🚩 Quick `1.0 (Cheating/Direct Edit)` preset button to flag un-creative direct reference edits.

## [0.2.0] - 2026-08-15

### Added
- 🚀 Interactive Character Consistency Approval Web App (`node web/server.js`) on port 3333.
- 🧪 Automated evaluation dataset sync utility (`bin/sync_out_to_evals.py`) for all synthesized assets in `out/`.
- 🛡️ Robust static file path resolution & frontend fallback for rendered images.
- 🧪 Comprehensive unit test suite (`tests/test_eval_dataset.py`) integrated into `just test`.

## [0.1.0] - 2026-08-13
### Added
- 📜 Added MIT License
- 🛠️ Initial setup of Gemini Tools with photo/video synthesis scripts


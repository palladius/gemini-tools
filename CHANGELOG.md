# 🚀 Changelog

All notable changes to this project will be documented in this file.

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


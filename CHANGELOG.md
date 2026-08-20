# 🚀 Changelog

All notable changes to this project will be documented in this file.

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


# Implementation Plan: Human Approval & Closed-Loop Character Consistency Framework

## Phase 1: Closed-Loop Dataset Infrastructure (`evaluations.jsonl`)
- [ ] Task: Create dataset management utility (`eval_dataset.py`)
  - [ ] Implement `out/evals/<subject>/evaluations.jsonl` reader and writer.
  - [ ] Implement `master_index.jsonl` aggregator.
  - [ ] Implement missing human evaluation query function (`get_pending_evaluations()`).
  - [ ] Write unit tests for dataset loading, updating, and JSONL serialization in `test_eval_dataset.py`.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 2: GCS Cloud Asset Sync (`IMAGES_BUCKET`)
- [ ] Task: Create GCS sync helper script (`gcs_sync.py`)
  - [ ] Support `IMAGES_BUCKET` environment variable for bucket targeting.
  - [ ] Implement `push_eval_assets()` (upload reference photos, generated images, and `evaluations.jsonl`).
  - [ ] Implement `pull_eval_assets()` (download references and dataset from GCS).
  - [ ] Write unit tests for GCS sync utility.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 3: Ephemeral Node.js Human Approval Web App (`eval-web`)
- [ ] Task: Build Node.js approval backend (`web/server.js`)
  - [ ] Create Node.js Express server reading pending evaluations from JSONL API.
  - [ ] Implement `/api/pending` endpoint returning un-voted samples.
  - [ ] Implement `/api/vote` endpoint recording human score (1-10), critique, and timestamp.
  - [ ] Implement auto-close/exit logic (`process.exit(0)`) when all pending items are voted on.
- [ ] Task: Build Dark-Mode Dual-Pane UI (`web/public/index.html`, `style.css`, `app.js`)
  - [ ] Build left pane featuring large target image preview, model banner overlay, prompt, and robot LLM judge score.
  - [ ] Build right pane featuring reference photo mosaic/grid thumbnail view.
  - [ ] Add 1-10 rating buttons, text input for critique, and keyboard hotkeys (1-9, 0, Enter).
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 4: Justfile Orchestration & E2E Verification
- [ ] Task: Update `justfile` with eval-web and GCS recipes
  - [ ] Add `just eval-web` recipe launching the Node.js server and opening browser.
  - [ ] Add `just gcs-push` and `just gcs-pull` recipes.
- [ ] Task: End-to-End System Verification
  - [ ] Generate sample images, run LLM judge, launch `just eval-web`, cast a vote, verify auto-close and `evaluations.jsonl` record closure.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

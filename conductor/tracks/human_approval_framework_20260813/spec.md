# Specification: Human Approval & Closed-Loop Character Consistency Framework

## Overview
An interactive human feedback and closed-loop evaluation framework for model character consistency (CC). It provides an ephemeral Node.js web approval UI (`just eval-web`), GCS cloud sync (`IMAGES_BUCKET`), per-subject JSONL tracking (`out/evals/<subject>/evaluations.jsonl`), and automated identification of missing human evaluations to close the eval loop.

## Functional Requirements

### 1. Ephemeral Node.js Human Approval Web App (`eval-web`)
- **CLI Trigger**: Launched via `just eval-web` (or `node server.js`).
- **Interactive UI**:
  - Dark mode dual-pane layout.
  - **Left Pane (Target)**: Large preview of the AI-generated target image with FFmpeg overlay banner (`Gemini model: $MODELNAME | Person: $PERSON`), robot LLM judge score, model name, prompt, and subject info.
  - **Right Pane (References)**: Grid/mosaic display of reference photos used during generation.
  - **Voting Controls**: Rating input accepting float values from **0.0 to 10.0** with max 1 decimal place (e.g. `7.2` valid, `7.25` invalid), preset buttons (5.0, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0), optional critique text box, and Enter hotkey (submits vote only if valid float score is entered).
- **Auto-Close Behavior**: Ephemeral web server automatically shuts down cleanly once all pending (un-voted) evaluation items are voted on.

### 2. Closed-Loop Dataset & Schema (`evaluations.jsonl`)
- **Partitioning**: Per-subject JSONL files (`out/evals/<subject_slug>/evaluations.jsonl`) + global `out/evals/master_index.jsonl`.
- **JSON Record Schema**:
  ```json
  {
    "eval_id": "kate_p1_gemini_2_5_flash_image_20260813",
    "subject": "Kate",
    "model_name": "gemini-2.5-flash-image",
    "prompt": "...",
    "reference_images": [
      {"name": "COLOR_POP.jpg", "local_path": "...", "gcs_uri": "gs://bucket/kate/COLOR_POP.jpg"}
    ],
    "generated_image": {
      "raw_path": "...",
      "annotated_path": "...",
      "gcs_uri": "gs://bucket/evals/kate/kate_p1_annotated.png"
    },
    "robot_eval": {
      "judge_model": "gemini-3.5-flash",
      "score": 7,
      "verdict": "GOOD",
      "critique": "..."
    },
    "human_eval": {
      "score": 8.5,
      "critique": "User favorite Paris cafe shot",
      "timestamp": "2026-08-13T14:48:00Z"
    },
    "status": "COMPLETED"
  }
  ```

### 3. GCS Asset Storage & Persistence (`IMAGES_BUCKET`)
- **Bucket Configuration**: Uses `IMAGES_BUCKET` environment variable (e.g. `gs://my-cc-eval-bucket`).
- **Sync Operations**:
  - `just gcs-sync-push`: Uploads reference images, generated samples, and `evaluations.jsonl` records to GCS.
  - `just gcs-sync-pull`: Downloads reference images and evaluation dataset from GCS.

### 4. Evaluation Loop Closure & Missing Items Query
- Script/CLI command to scan evaluation records, identify items lacking human evaluation (`human_eval: null`), and feed missing items directly into `just eval-web`.

## Acceptance Criteria
1. Running `just eval-web` opens the Node.js web approval UI in the default browser when unvoted items exist.
2. Voting on a sample updates the subject's `evaluations.jsonl` record with human score, critique, and timestamp.
3. The server auto-closes once all pending items are voted on.
4. GCS sync tools (`just gcs-sync-push` / `pull`) successfully upload and download evaluation assets using `IMAGES_BUCKET`.
5. Automated tests verify JSONL read/write operations and missing-item query logic.

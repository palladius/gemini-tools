# Implementation Plan: LLM-Driven Person Bounding Box Isolator & Image Cropper

## Overview
Implement `bin/crop_person_llm.py` to automate single-subject identification, 2D spatial bounding box detection, PIL image cropping, LLM-as-a-Judge identity verification, and GCS synchronization.

## Phases & Tasks

### Phase 1: Core Bounding Box Detector & PIL Cropper Script
- [x] Task: Create `bin/crop_person_llm.py` with `uv` inline dependencies (`google-genai`, `pillow`, `pydantic`, `rich`).
- [x] Task: Implement Gemini 2D spatial grounding prompt returning structured Pydantic schema for `[ymin, xmin, ymax, xmax]` normalized coordinates.
- [x] Task: Implement PIL image cropping logic with configurable padding (default 10%) and aspect ratio preservation.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 2: LLM Verification & Batch Processing Pipeline
- [x] Task: Integrate `gemini-3.5-flash` identity verification step comparing crop against anchor reference photos.
- [x] Task: Implement batch processing CLI mode for character directories (e.g. `data/characters/kate2016/`).
- [x] Task: Add automatic GCS sync via `gcloud storage rsync` to `gs://ricc-family-character-vault-pvt/<character>/`.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 3: Integration, Documentation & Verification
- [x] Task: Update `skills/how-to-use-gemini-tools/SKILL.md` with new `crop_person_llm.py` command documentation.
- [x] Task: Execute test crop on `data/characters/kate2016/` wedding group photos and verify isolated Kate crops.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)

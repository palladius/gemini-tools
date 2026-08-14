# Specification: LLM-Driven Person Bounding Box Isolator & Image Cropper

## Overview
A standalone Python CLI utility (`bin/crop_person_llm.py`) that leverages Gemini's 2D spatial understanding capabilities to locate a specific target person (e.g., Kate) in group photos using reference anchor images of the person alone, compute bounding box coordinates `[ymin, xmin, ymax, xmax]`, crop the target subject using Pillow while cutting out surrounding people, verify identity match with an LLM-as-a-Judge step, and sync cleaned images to GCS.

## Functional Requirements
1. **Gemini 2D Spatial Grounding**:
   - Provide candidate photo along with 1-2 single-subject reference anchor photos (e.g. `kate_golden_wine_anchor.png`).
   - Query Gemini multimodal API to return normalized bounding box coordinates `[ymin, xmin, ymax, xmax]` targeting ONLY the specified person.
2. **Pillow Image Cropping**:
   - Convert normalized bounding box coordinates into exact pixel coordinates.
   - Crop the image with configurable padding (default 10-15%) to preserve head, hair, and shoulders without including adjacent individuals.
3. **LLM Identity & Quality Verification**:
   - Run a verification pass using `gemini-3.5-flash` comparing the cropped result against anchor photos to ensure the correct subject was isolated and no severe clipping occurred.
4. **Batch Processing & GCS Sync**:
   - Support batch execution over character directories (`data/characters/kate2016/`).
   - Output cropped images to `data/characters/<character_name>/cleaned/` or in-place.
   - Automatically sync cleaned images to GCS `gs://ricc-family-character-vault-pvt/<character_name>/`.

## Non-Functional Requirements
- Executive CLI runner using `#!/usr/bin/env -S uv run`.
- Rich CLI output with progress bars, visual bounding box details, and audit status tables.
- Retry mechanism if bounding box detection produces invalid or out-of-bounds coordinates.

## Acceptance Criteria
- Executing `bin/crop_person_llm.py -c kate2016 -i data/characters/kate/kate_golden_wine_anchor.png` successfully isolates Kate from group wedding photos into single-subject reference crops.
- AI Judge confirms face identity match >= 7.0/10.
- Cleaned images are uploaded to GCS `gs://ricc-family-character-vault-pvt/kate2016/`.

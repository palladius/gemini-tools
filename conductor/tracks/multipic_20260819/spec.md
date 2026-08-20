# Specification for multipic.py

## Overview
A new script `bin/multipic.py` that accepts up to 3 input photos and places the subjects in a generated image based on a prompt read from `etc/prompts/<prompt>.md`. 

## Functional Requirements
- **Inputs**: Accept up to 3 images via:
  - `--images` (comma-separated paths)
  - `--dir` (path to a directory containing photos)
  - `--characters` (comma-separated names, resolving to `data/characters/<name>/` images)
- **Prompt**: Accept `--prompt <name>` which resolves to `etc/prompts/<name>.md`.
- **Generation**: Send the prompt and images to `gemini-3.1-flash-image-preview` via `google-genai`.
- **Output**: Save the generated image and a provenance JSON sidecar. The JSON sidecar must use tilde paths for absolute paths.
- **Workflow**: Auto-open the generated image on macOS/Linux.

# Technology Stack - gemini-tools

- **Language**: Python 3.11+
- **Script Runner**: `uv` (standalone execution via inline script metadata)
- **AI SDK**: `google-genai` (Google GenAI Python SDK)
- **Models**:
  - Image Synthesis: `gemini-3.1-flash-image-preview`, `nano-banana-pro-preview`, `gemini-3-pro-image`
  - Video Judging: `gemini-3.5-flash`
  - Video Generation: `veo-2.0-generate-001`, `gemini-omni-flash-preview`
- **Image Processing**: Pillow (`PIL`)
- **CLI Formatting**: `rich` (Console, Tables)
- **Video Processing**: `ffmpeg` (via subprocess for scene concatenation)
- **Task Runner**: `just` (`Justfile`)

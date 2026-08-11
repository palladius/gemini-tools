# Specification - Automated Judge Feedback Loop & CLI Retry Mechanism

## Overview
Enable deterministic, automated feedback loops for AI video generation CLI tools. When a video asset fails biometric/quality evaluation (score < 8), the system reads the actionable feedback from the LLM-as-a-Judge audit JSON (`actionable_next_step`) and automatically re-generates the video with updated prompt directives until the quality threshold is satisfied.

## Functional Requirements
1. **Feedback Ingestion (`--feedback-from <audit.json>`)**:
   - Parses `actionable_next_step` and `expert_critique` from a previous `judge_video` audit JSON file.
   - Automatically augments the generation prompt with the corrective feedback directives.

2. **Automated Iterative Retry Loop (`--auto-retry`)**:
   - Configurable flags: `--min-score 8` (default: 8), `--max-attempts 3` (default: 3).
   - Generates unique timestamped output folders/files for each iteration (`attempt_1/`, `attempt_2/`, etc.).
   - Runs `judge_video.py` after each generation.
   - Terminates loop when `overall_score >= min_score` or max attempts reached.

3. **Audit Provenance Tracking**:
   - Saves `feedback_loop_summary.json` documenting all attempts, scores, feedback incorporated, and final verdict.

## Acceptance Criteria
- CLI invocation `bin/omni-video-gen.py --prompt "..." --auto-retry --min-score 8` automatically retries failed generations incorporating judge feedback.
- Clean timestamped JSON logs track progress across iterations.

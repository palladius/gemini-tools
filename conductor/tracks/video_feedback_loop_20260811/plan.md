# Implementation Plan - Automated Judge Feedback Loop & CLI Retry Mechanism

## Phase 1: Feedback Ingestion Module
- [ ] Task: Extend `bin/omni-video-gen.py` to accept `--feedback-from <json_path>`.
  - [ ] Parse `actionable_next_step` and `expert_critique` from target JSON.
  - [ ] Append feedback directives to video generation prompt.
- [ ] Task: Verify manual feedback re-generation via CLI.

## Phase 2: Autonomous Iterative Loop (`--auto-retry`)
- [ ] Task: Implement `--auto-retry`, `--min-score`, and `--max-attempts` flags in `bin/omni-video-gen.py`.
  - [ ] Implement `while attempts < max_attempts and score < min_score` loop.
  - [ ] Invoke `bin/judge_video.py` programmatically after each attempt.
  - [ ] Save iteration history in `feedback_loop_summary.json`.
- [ ] Task: Add test cases and verify threshold termination.

## Phase 3: Verification & Documentation
- [ ] Task: Update `skills/how-to-use-gemini-tools/SKILL.md` and `README.md`.
- [ ] Task: Phase Verification & Checkpoint.

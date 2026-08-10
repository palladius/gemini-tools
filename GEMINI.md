# 🛠️ Gemini Agent Guidelines for `gemini-tools`

This repository contains standalone Python CLI tools for Google GenAI photo synthesis, video biometric judging, and model discovery.

## CRITICAL ANTI-DRIFT INSTRUCTION FOR AI AGENTS

> ⚠️ **IMPORTANT**: Whenever you modify, add, or refactor CLI scripts, subcommands, or arguments in this repository (e.g. `generate_photo.py`, `judge_video.py`, `list-gemini-models.py`), you **MUST** update the corresponding skill file at [skills/how-to-use-gemini-tools/SKILL.md](file:///Users/ricc/git/gemini-tools/skills/how-to-use-gemini-tools/SKILL.md) in the same commit.
>
> Do **NOT** allow the repository scripts and `SKILL.md` instructions to drift apart over time!

## Repository Conventions

1. **Executable Scripts Location**: Place all invokable standalone Python CLI scripts under `bin/`. Always use `#!/usr/bin/env -S uv run` with inline script dependencies.
2. **Tilde Paths**: All generated `.json` metadata sidecars and audit reports must format absolute paths using `~` (e.g., `~/Documents/...`) via `to_tilde_path()`.
3. **Character Folder Structure**: Reference images must be organized under `data/characters/<character_name>/`.
4. **Justfile**: Maintain `Justfile` tasks pointing to `./bin/<script_name>`. The default target must always be `list -> just -l`.
5. **Git Commit Messages**: Use single quotes in `git commit -m '...'` to avoid backtick expansion issues in shell.

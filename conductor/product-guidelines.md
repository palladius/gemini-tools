# Product Guidelines - gemini-tools

## Voice & Tone
- Developer-friendly, crisp, and informative CLI output utilizing `rich.console`.
- Clear status indicators (`📸`, `🎨`, `📡`, `✅`, `👨‍⚖️`, `⚠️`, `🗑️`).

## Architectural Principles
- **No Complex Virtualenvs**: Standalone CLI scripts use `uv` inline metadata headers (`#!/usr/bin/env -S uv run`).
- **Tilde Path Hygiene**: All provenance sidecars and audit JSON files use `~` formatting (`to_tilde_path()`).
- **Anti-Drift Requirement**: Any script modification MUST update `skills/how-to-use-gemini-tools/SKILL.md` in the same commit.
- **Single Quotes in Git**: Git commit messages use single quotes (`git commit -m '...'`).
